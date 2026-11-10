"""Testes da CA-RDL (Fase 2) sobre o núcleo da Fase 1."""
import hashlib
from pathlib import Path

import numpy as np
import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, ResolutionStrategy, XAppAction
from src.infrastructure.memory_module import MemoryModule

from cardl.engine import CARDLReasoning, build_cardl_xapp
from cardl.marl.baselines import BASELINES
from cardl.marl.calibration import EXPECTED_SHA256, load_curve
from cardl.marl.env import ACTION_DIM, SLOTS, CalibratedSliceEnv, EnvConfig
from cardl.marl.mappo import MAPPO, MappoConfig


# --- calibração ----------------------------------------------------------------------

def test_curve_is_the_measured_nori_curve():
    curve = load_curve()
    assert curve.sha256 == EXPECTED_SHA256
    assert curve.points[0] == (10.0, pytest.approx(37.458 / 151.488))
    assert curve.ratio(30.0) == pytest.approx(113.986 / 151.488)
    assert 39.0 < curve.saturation_cap_pct() < 41.0     # achado 41: satura perto de 40 %
    assert curve.ratio(70.0) == 1.0
    assert curve.ratio(0.0) == 0.0


# --- ambiente ------------------------------------------------------------------------

def test_safety_guard_of_phase1_masks_rogue_proposals():
    env = CalibratedSliceEnv(EnvConfig(rogue_probability=1.0), seed=1)
    env.reset(seed=1)
    for agent in range(2):
        rogue = [k for k, p in enumerate(env.proposals[agent]) if p.xapp_id == "rogue"]
        assert rogue and env.action_mask(agent)[rogue[0]] == 0.0
        assert env.action_mask(agent)[SLOTS] == 1.0   # no-op sempre admissível


def test_needed_cap_meets_demand():
    env = CalibratedSliceEnv(seed=2)
    for demand in (0.1, 0.5, 0.9):
        cap = env.needed_cap(demand)
        assert env.curve.ratio(cap) >= demand - 1e-6
        assert env.curve.ratio(cap - 1.0) < demand


def test_episode_and_baselines_run():
    env = CalibratedSliceEnv(EnvConfig(steps_per_episode=8), seed=3)
    for name, policy in BASELINES.items():
        env.reset(seed=3)
        done, steps = False, 0
        while not done:
            _, reward, cost, done, info = env.step(policy(env))
            assert cost in (0.0, 1.0) and 0.0 <= info.energy_ratio <= 1.0
            steps += 1
        assert steps == 8, name


# --- motor CA-RDL --------------------------------------------------------------------

def _conflict(values=((70, 90, "ranslicer"), (30, 65, "energysaver"))):
    actions = [XAppAction(xapp_id=x, node_id="gnb_0", parameter="PRB_QUOTA", value=float(v), priority=p)
               for v, p, x in values]
    return ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, actions)


@pytest.fixture(scope="module")
def checkpoint(tmp_path_factory):
    path = tmp_path_factory.mktemp("ckpt") / "actor_critic.pt"
    MAPPO(MappoConfig(), seed=0).save(str(path), {"seed": 0})
    return str(path), hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_without_checkpoint_behaves_like_phase1():
    from src.core.reasoning import Reasoning
    conflict = _conflict()
    expected = Reasoning(MemoryModule()).resolve(conflict)
    engine = CARDLReasoning(MemoryModule())
    got = engine.resolve(conflict)
    assert [a.action_id for a in got.winning_actions] == [a.action_id for a in expected.winning_actions]
    assert engine.last_decision.source == "H_RDL" and engine.last_decision.reason == "sem checkpoint"


def test_checkpoint_sha256_is_enforced(checkpoint):
    path, _ = checkpoint
    with pytest.raises(ValueError):
        CARDLReasoning(MemoryModule(), checkpoint_path=path, expected_sha256="0" * 64)


def test_mappo_decides_prb_conflicts_with_confidence_floor_and_fallback(checkpoint):
    path, digest = checkpoint
    engine = CARDLReasoning(MemoryModule(), checkpoint_path=path, expected_sha256=digest, min_confidence=0.0,
                            time_budget_ms=10_000)   # este teste não é sobre tempo (ver test_time_budget_forces_fallback)
    resolution = engine.resolve(_conflict())
    if engine.last_decision.source == "MAPPO":
        assert resolution.strategy_used == ResolutionStrategy.MARL_AGENT
        assert resolution.winning_actions[0] in _conflict().involved_xapps or resolution.winning_actions
    else:
        assert engine.last_decision.reason == "MAPPO escolheu no-op"

    strict = CARDLReasoning(MemoryModule(), checkpoint_path=path, expected_sha256=digest, min_confidence=1.01)
    strict.resolve(_conflict())
    assert strict.last_decision.source == "H_RDL"


def test_out_of_scope_conflicts_go_to_phase1(checkpoint):
    path, digest = checkpoint
    engine = CARDLReasoning(MemoryModule(), checkpoint_path=path, expected_sha256=digest, min_confidence=0.0)
    power = ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [
        XAppAction(xapp_id="xslice", node_id="gnb_0", parameter="TX_POWER", value=40.0, priority=90),
        XAppAction(xapp_id="energy_saving", node_id="gnb_0", parameter="TX_POWER", value=10.0, priority=65)])
    engine.resolve(power)
    assert engine.last_decision.source == "H_RDL" and "fora do escopo" in engine.last_decision.reason


def test_time_budget_forces_fallback(checkpoint):
    path, digest = checkpoint
    engine = CARDLReasoning(MemoryModule(), checkpoint_path=path, expected_sha256=digest,
                            min_confidence=0.0, time_budget_ms=0.0)
    engine.resolve(_conflict())
    assert engine.last_decision.source == "H_RDL"


def test_cardl_xapp_registers_model_policy_and_keeps_phase1_policies(checkpoint, monkeypatch):
    path, digest = checkpoint
    monkeypatch.setenv("CARDL_CHECKPOINT", path)
    monkeypatch.setenv("CARDL_CHECKPOINT_SHA256", digest)
    app = build_cardl_xapp()
    try:
        assert isinstance(app.reasoning, CARDLReasoning) and app.reasoning.policy is not None
        assert app.a1_policies.put_policy("20002", "m", {"marl_enabled": False, "min_confidence": 0.8})[0]
        assert app.reasoning.marl_enabled is False and app.reasoning.min_confidence == 0.8
        assert app.a1_policies.put_policy("20001", "g", {"energy_weight": 0.4})[0]
        assert app.reasoning.w_energy == 0.4      # política da Fase 1 continua aplicada
        assert app.reasoning.knowledge_graph is app.knowledge_graph
        app.reasoning.resolve(_conflict())
        assert set(app.reasoning.last_decision.context) >= {"neighbor_count", "recent_conflicts"}
    finally:
        app.stop()
