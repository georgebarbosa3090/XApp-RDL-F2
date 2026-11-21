"""Testes das famílias de conflito da RDL-N2 (docs/17): classificação, registro, motor, ambiente da família C,
calibração e extrator do dataset offline."""
import json
import math

import numpy as np
import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction
from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule

from cardl.families import (A, B, C, D, HOLD_BOTH, HOLD_FIRST, HOLD_SECOND, KEEP_BOTH, P, FamilyPolicy,
                            FamilyRegistry, classify, classify_params)
from cardl.hierarchy import HierarchicalReasoning
from cardl.marl import env_handover_prb as envc


# ---------------------------------------------------------------- classificação
@pytest.mark.parametrize("kind,params,family", [
    ("DIRECT", ["PRB_QUOTA", "PRB_QUOTA"], A),
    ("INDIRECT", ["PRB_QUOTA", "TX_POWER"], B),
    ("INDIRECT", ["HANDOVER", "PRB_QUOTA"], C),
    ("INDIRECT", ["CELL_STATE", "TX_POWER"], D),
    ("INTER_CELL", ["CELL_STATE", "HANDOVER", "TX_POWER"], D),
    ("INDIRECT", ["HANDOVER", "TX_POWER"], D),
    ("INTER_CELL", ["HANDOVER", "HANDOVER"], P),
    ("DIRECT", ["TX_POWER", "TX_POWER"], None),
    ("INDIRECT", ["SCHEDULER_WEIGHT", "PRB_QUOTA"], None),
])
def test_classify_params(kind, params, family):
    assert classify_params(kind, params) == family


def test_registry_rejects_a_and_p_and_respects_a1():
    reg = FamilyRegistry()
    for fam in (A, P):
        with pytest.raises(ValueError):
            reg.register(FamilyPolicy(fam, model=None, sha256=None, observe=None))
    reg.register(FamilyPolicy(C, model=None, sha256=None, observe=None))
    assert reg.get(C) is not None and reg.get(B) is None
    reg.apply_model_policy({"families": ["B"]})
    assert reg.get(C) is None
    reg.apply_model_policy({"families": None})
    assert reg.get(C) is not None
    reg.apply_model_policy({"marl_enabled": True})        # sem o campo: não muda
    assert reg.get(C) is not None


# ---------------------------------------------------------------- motor
class Memory(MemoryModule):
    def __init__(self, committed=None):
        super().__init__()
        self.committed = committed or {}

    def get_committed_action(self, node, parameter):
        return self.committed.get((node, parameter))


class StubModel:
    """Modelo que escolhe sempre a mesma ação (respeitando a máscara)."""
    def __init__(self, action, confidence=0.9):
        from cardl.marl.mappo import Dims
        self.dims = Dims(obs=envc.OBS_DIM, global_=envc.GLOBAL_DIM, actions=envc.ACTION_DIM, agents=1)
        self.action, self.confidence = action, confidence
        self.last_mask = None

    def probabilities(self, obs, mask):
        self.last_mask = mask.copy()
        p = np.full(len(mask), (1 - self.confidence) / max(1, len(mask) - 1)) * mask
        a = self.action if mask[self.action] > 0 else int(np.argmax(mask))
        p[a] = self.confidence
        return p / p.sum()


def _ho_prb(prb_first=True):
    prb = XAppAction(xapp_id="load_balancer", node_id="gnb_0", parameter="PRB_QUOTA", value=90.0, priority=70)
    ho = XAppAction(xapp_id="traffic_steering", node_id="gnb_0", parameter="HANDOVER", value=1.0, priority=80)
    return ConflictEvent(ConflictType.INDIRECT, ConflictSeverity.MEDIUM, [prb, ho] if prb_first else [ho, prb]), ho, prb


def _engine(memory=None, policy=None):
    engine = HierarchicalReasoning(memory or Memory())
    if policy is not None:
        engine.families.register(policy)
    return engine


def _family_c(model):
    return FamilyPolicy(C, model=model, sha256="x", observe=envc.observe_from_reasoning,
                        order=envc.order_candidates, mask=envc.mask_from_reasoning)


def test_without_family_policy_behaviour_is_unchanged():
    conflict, _, _ = _ho_prb()
    expected = Reasoning(MemoryModule()).resolve(conflict)
    engine = _engine()
    got = engine.resolve(conflict)
    trace = engine.trace_last()
    assert trace["family"] == C and trace["source"] == "H_RDL" and trace["fallback_reason"] == "sem checkpoint"
    assert [a.action_id for a in got.winning_actions] == [a.action_id for a in expected.winning_actions]


def test_family_policy_holds_handover():
    conflict, ho, prb = _ho_prb(prb_first=True)    # ordem do conflito não importa: a canônica é HO, PRB
    engine = _engine(policy=_family_c(StubModel(HOLD_FIRST)))
    got = engine.resolve(conflict)
    trace = engine.trace_last()
    assert trace["source"] == "MAPPO" and trace["family"] == C
    assert [a.action_id for a in got.winning_actions] == [prb.action_id]


def test_family_policy_hold_both_falls_back_to_n1():
    conflict, _, _ = _ho_prb()
    engine = _engine(policy=_family_c(StubModel(HOLD_BOTH)))
    engine.resolve(conflict)
    trace = engine.trace_last()
    assert trace["source"] == "H_RDL" and "segurou todas" in trace["fallback_reason"]


def test_incumbent_prb_cannot_be_held():
    conflict, ho, prb = _ho_prb()
    model = StubModel(HOLD_SECOND)
    engine = _engine(memory=Memory({("gnb_0", "PRB_QUOTA"): prb}), policy=_family_c(model))
    got = engine.resolve(conflict)
    assert model.last_mask[HOLD_SECOND] == 0 and model.last_mask[HOLD_BOTH] == 0
    assert {a.action_id for a in got.winning_actions} == {ho.action_id, prb.action_id}   # mascarado: manter as duas


def test_a1_turns_family_off():
    conflict, _, _ = _ho_prb()
    engine = _engine(policy=_family_c(StubModel(HOLD_FIRST)))
    engine.apply_model_policy({"marl_enabled": True, "families": []})
    engine.resolve(conflict)
    assert engine.trace_last()["source"] == "H_RDL"


def test_classify_conflict_event():
    conflict, _, _ = _ho_prb()
    assert classify(conflict) == C


# ---------------------------------------------------------------- ambiente da família C
def _episode(env, action, seed):
    env.reset(seed=seed)
    total, done = 0.0, False
    while not done:
        _, r, _, done, _ = env.step([action])
        total += r
    return total


def test_env_shapes_and_determinism():
    env = envc.HandoverPrbEnv(seed=1)
    obs = env.reset(seed=1)
    assert obs[0].shape == (envc.OBS_DIM,) and env.global_state().shape == (envc.GLOBAL_DIM,)
    assert _episode(env, KEEP_BOTH, 3) == _episode(env, KEEP_BOTH, 3)


def test_env_reward_direction_when_handover_helps():
    ctx = envc.Context(load_src=0.9, load_dst=0.2, cap_src=90, cap_new=90, rsrp_gap_db=10, sinr_db=-3, ue_sat=0.2,
                       prb_incumbent=True)
    model = envc.ResponseModel(contexts=(ctx,), loss_a=-50.0, loss_b=0.0, sat_after_ho=(1.0, 1.0, 1.0))
    env = envc.HandoverPrbEnv(model=model, seed=0)
    assert _episode(env, KEEP_BOTH, 0) > _episode(env, HOLD_FIRST, 0)


def test_env_incumbent_mask_and_loss_cost():
    ctx = envc.Context(load_src=0.9, load_dst=0.3, cap_src=90, cap_new=90, rsrp_gap_db=-5, sinr_db=-3, ue_sat=0.3,
                       prb_incumbent=True)
    model = envc.ResponseModel(contexts=(ctx,), loss_a=50.0, loss_b=0.0)       # perda certa no handover
    env = envc.HandoverPrbEnv(model=model, seed=0)
    env.reset(seed=0)
    assert list(env.action_mask()) == [1, 1, 0, 0]
    _, _, cost, _, info = env.step([KEEP_BOTH])
    assert cost == 1.0 and info.lost and info.ue_sat == 0.0
    _, _, cost, _, info = env.step([HOLD_SECOND])                               # mascarada: vira manter as duas
    assert info.action == KEEP_BOTH
    _, _, cost, _, info = env.step([HOLD_FIRST])
    assert cost == 0.0 and not info.ho_applied


def test_fit_response_recovers_logistic():
    rng = np.random.default_rng(0)
    gaps = rng.uniform(-8, 12, 4000)
    p = 1 / (1 + np.exp(-(-1.0 - 0.3 * gaps)))
    events = [{"rsrp_gap_db": float(g), "lost": bool(rng.random() < q), "sat_after": 0.8, "load_dst": 0.5}
              for g, q in zip(gaps, p)]
    m = envc.fit_response(events, l2=0.0)
    assert m.loss_a == pytest.approx(-1.0, abs=0.15) and m.loss_b == pytest.approx(-0.3, abs=0.03)
    assert m.sat_after_ho[1] == pytest.approx(0.8)


# ---------------------------------------------------------------- MAPPO com dimensões de outro ambiente
def test_mappo_dims_roundtrip(tmp_path):
    from cardl.marl.mappo import MAPPO, Dims, MappoConfig
    dims = Dims(obs=envc.OBS_DIM, global_=envc.GLOBAL_DIM, actions=envc.ACTION_DIM, agents=1)
    agent = MAPPO(MappoConfig(hidden=8), seed=1, dims=dims)
    path = tmp_path / "c.pt"
    agent.save(str(path), {})
    with pytest.raises(ValueError):
        MAPPO.load(str(path))                         # padrão: só aceita a família A
    loaded = MAPPO.load(str(path), expected=dims)
    obs, mask = np.zeros(envc.OBS_DIM, np.float32), envc.hold_mask(True)
    assert np.allclose(loaded.probabilities(obs, mask), agent.probabilities(obs, mask))
    assert loaded.probabilities(obs, mask)[HOLD_SECOND] < 1e-6


# ---------------------------------------------------------------- extrator do dataset
def _fake_run(root, name="cl_t_S5_B3_completo_seed1", status="SUCCESS"):
    run = root / name
    (run / "raw").mkdir(parents=True)
    (run / "execution_manifest.json").write_text(json.dumps({"run_status": status, "repo_git_sha": "abc",
                                                             "repo_dirty": False}), encoding="utf-8")

    def window(t, ues, proposals=(), actions=(), resolutions=()):
        return {"type": "window", "t": t, "kpm": {"cells": [
            {"gnb": 0, "cell_id": 1, "prb_util": 0.9, "prb_quota": 90.0, "thp_mbps": 50.0},
            {"gnb": 1, "cell_id": 2, "prb_util": 0.3, "prb_quota": 100.0, "thp_mbps": 20.0}], "ues": ues},
            "proposals": list(proposals), "actions": list(actions),
            "decision": {"selected": [a["id"] for a in actions], "resolutions": list(resolutions)}}

    def ue(t, cell, connected=True, thp=2.0):
        return [{"ue": 3, "cell_id": cell, "gnb": cell - 1, "connected": connected, "thp_mbps": thp, "sinr_db": 1.0,
                 "rsrp_dbm": {"1": -100.0, "2": -98.0}}]

    prb = {"id": "load_balancer-g0-PRB_QUOTA-0.200-1", "xapp_id": "load_balancer", "gnb": 0, "parameter": "PRB_QUOTA",
           "value": 90.0, "priority": 70, "ue": -1}
    ho = {"id": "traffic_steering-g0-HANDOVER-0.600-1", "xapp_id": "traffic_steering", "gnb": 0,
          "parameter": "HANDOVER", "value": 1.0, "priority": 80, "ue": 3}
    res = {"conflict_type": "INDIRECT", "involved": [ho["id"], prb["id"]], "winners": [ho["id"], prb["id"]],
           "strategy": "EEVS"}
    lines = [{"type": "header", "scenario": "S5", "baseline": "B3", "seed": 1,
              "hello": {"gnbs": [{"gnb": 0, "cell_id": 1}, {"gnb": 1, "cell_id": 2}], "ue_offered_mbps": {"3": 4.0}}},
             window(0.2, ue(0.2, 1), [prb], [prb]), window(0.4, ue(0.4, 1)),
             window(0.6, ue(0.6, 1), [ho], [ho], [res]), window(0.8, ue(0.8, 2, thp=4.0)),
             window(1.0, ue(1.0, 2, connected=False, thp=0.0)), window(1.6, ue(1.6, 2, thp=4.0))]
    (run / "raw" / "closed_loop_log.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return run


def test_extractor_outputs_transitions_handovers_and_manifest(tmp_path):
    import importlib.util
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "experiments" / "closed_loop" / "extrair_transicoes.py"
    spec = importlib.util.spec_from_file_location("extrair_transicoes", script)
    ex = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ex)
    _fake_run(tmp_path)
    _fake_run(tmp_path, name="cl_t_S5_B0_completo_seed1", status="FAILED")
    out = tmp_path / "out"
    assert ex.main([str(out), str(tmp_path / "cl_t_*")]) == 0
    man = json.loads((out / "manifesto.json").read_text(encoding="utf-8"))
    assert man["transicoes"] == 2 and man["handovers"] == 1 and man["resolucoes_por_familia"] == {"C": 1}
    assert [p["run_id"] for p in man["puladas"]] == ["cl_t_S5_B0_completo_seed1"]
    assert man["saidas"]["transicoes.jsonl"] == ex.sha256_file(out / "transicoes.jsonl")
    ev = json.loads((out / "handovers.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert ev["rsrp_gap_db"] == pytest.approx(2.0) and ev["lost"] is True and ev["load_dst"] == 0.3
    assert ev["sat_before"] == pytest.approx(0.5)
    trs = [json.loads(l) for l in (out / "transicoes.jsonl").read_text(encoding="utf-8").splitlines()]
    ctx = envc.contexts_from_transitions(trs)
    assert len(ctx) == 1 and ctx[0].prb_incumbent and ctx[0].rsrp_gap_db == pytest.approx(2.0)
    assert ctx[0].ue_sat == pytest.approx(0.5) and ctx[0].load_dst == pytest.approx(0.3)
