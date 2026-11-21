"""Testes da RDL hierárquica (RDL-N1 e RDL-N2 juntas, cardl/hierarchy.py)."""
import hashlib
from pathlib import Path

import pytest

from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, ResolutionStrategy, XAppAction
from src.core.knowledge_graph import KnowledgeGraph
from src.core.reasoning import Reasoning
from src.infrastructure.memory_module import MemoryModule

from cardl.hierarchy import HIGH, LOW, HierarchicalReasoning, attach_hierarchical


class Clock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


def _prb(values=((70, 90, "ranslicer"), (30, 65, "energysaver")), node="gnb_0"):
    return ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, [
        XAppAction(xapp_id=x, node_id=node, parameter="PRB_QUOTA", value=float(v), priority=p) for v, p, x in values])


def _indirect():
    return ConflictEvent(ConflictType.INDIRECT, ConflictSeverity.MEDIUM, [
        XAppAction(xapp_id="xslice", node_id="gnb_0", parameter="PRB_QUOTA", value=60.0, priority=80),
        XAppAction(xapp_id="energy_saving", node_id="gnb_0", parameter="TX_POWER", value=10.0, priority=65)])


def _engine(clock=None, kg=None, **kw):
    engine = HierarchicalReasoning(MemoryModule(), clock=clock or Clock(), **kw)
    engine.knowledge_graph = kg
    return engine


def _winners(resolution):
    return [a.action_id for a in resolution.winning_actions]


def test_low_complexity_goes_to_n1_with_phase1_result():
    conflict = _prb()
    expected = Reasoning(MemoryModule()).resolve(conflict)
    engine = _engine()
    got = engine.resolve(conflict)
    trace = engine.trace_last()
    assert trace["level"] == LOW and trace["complexity"] == 1.0 and trace["source"] == "H_RDL"
    assert _winners(got) == _winners(expected)
    assert engine.route_counts == {LOW: 1, HIGH: 0}


def test_high_complexity_goes_to_n2_and_falls_back_with_reason():
    conflict = _indirect()                      # C = 1,8 + 0,4 (dois parâmetros) = 2,2
    expected = Reasoning(MemoryModule()).resolve(conflict)
    engine = _engine()
    got = engine.resolve(conflict)
    trace = engine.trace_last()
    assert trace["level"] == HIGH and trace["complexity"] == 2.2
    assert trace["source"] == "H_RDL" and trace["fallback_reason"] == "sem checkpoint"
    assert _winners(got) == _winners(expected)  # reserva = RDL-N1


def test_many_direct_proposals_are_high_complexity():
    conflict = _prb(tuple((10 * k, 60 + k, f"x{k}") for k in range(5)))   # C = 1,0 + 0,3 × 3 = 1,9
    engine = _engine()
    engine.resolve(conflict)
    assert engine.trace_last()["level"] == HIGH


def test_recurrent_dispute_in_knowledge_graph_raises_complexity_within_lookback():
    kg, clock = KnowledgeGraph(), Clock(10.0)
    engine = _engine(clock=clock, kg=kg, kg_lookback_s=5.0)
    first = _prb()
    kg.record_conflict(first)                   # como no pipeline: o grafo registra antes da arbitragem
    engine.resolve(first)
    assert engine.trace_last()["level"] == LOW and engine.trace_last()["kg_recent_conflicts"] == 0
    assert kg.node(f"conflict:{first.conflict_id}").attrs["t_route"] == 10.0

    clock.t = 13.0
    second = _prb()
    kg.record_conflict(second)
    engine.resolve(second)
    trace = engine.trace_last()
    assert trace["level"] == HIGH and trace["kg_recent_conflicts"] == 1 and "grafo" in trace["route_reason"]

    clock.t = 30.0                              # fora da janela: volta a ser baixa complexidade
    third = _prb()
    kg.record_conflict(third)
    engine.resolve(third)
    assert engine.trace_last()["level"] == LOW


def test_knowledge_graph_history_is_per_target():
    kg, clock = KnowledgeGraph(), Clock(1.0)
    engine = _engine(clock=clock, kg=kg)
    a = _prb(node="gnb_0")
    kg.record_conflict(a)
    engine.resolve(a)
    b = _prb(node="gnb_1")                      # outra célula: sem histórico
    kg.record_conflict(b)
    engine.resolve(b)
    assert engine.trace_last()["level"] == LOW


def test_attach_installs_router_with_phase1_policies_and_a1_20002():
    from src.rdl_xapp import RDLxApp

    app = RDLxApp(serve_http=False)
    clock = Clock(2.0)
    reasoning = attach_hierarchical(app, clock=clock)
    assert app.reasoning is reasoning and isinstance(reasoning, HierarchicalReasoning)
    assert reasoning.knowledge_graph is app.knowledge_graph and reasoning.clock is clock
    assert app.a1_policies.put_policy("20001", "g", {"energy_weight": 0.4})[0]
    assert reasoning.w_energy == 0.4
    assert app.a1_policies.put_policy("20002", "m", {"marl_enabled": False})[0]
    assert reasoning.marl_enabled is False


# --- com modelo (exige PyTorch) ---------------------------------------------------------

@pytest.fixture(scope="module")
def checkpoint(tmp_path_factory):
    pytest.importorskip("torch")
    from cardl.marl.mappo import MAPPO, MappoConfig
    path = tmp_path_factory.mktemp("ckpt") / "actor_critic.pt"
    MAPPO(MappoConfig(), seed=0).save(str(path), {"seed": 0})
    return str(path), hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_recurrent_prb_dispute_reaches_the_mappo(checkpoint):
    path, digest = checkpoint
    kg, clock = KnowledgeGraph(), Clock(0.0)
    engine = _engine(clock=clock, kg=kg, checkpoint_path=path, expected_sha256=digest, min_confidence=0.0,
                     time_budget_ms=10_000)
    for t in (0.0, 1.0):
        clock.t = t
        c = _prb()
        kg.record_conflict(c)
        resolution = engine.resolve(c)
    trace = engine.trace_last()
    assert trace["level"] == HIGH
    if trace["source"] == "MAPPO":
        assert resolution.strategy_used == ResolutionStrategy.MARL_AGENT and trace["fallback_reason"] == ""
    else:
        assert trace["fallback_reason"] == "MAPPO escolheu no-op"


def test_low_complexity_never_calls_the_mappo(checkpoint):
    path, digest = checkpoint
    engine = _engine(checkpoint_path=path, expected_sha256=digest, min_confidence=0.0, time_budget_ms=10_000)
    engine.resolve(_prb())
    assert engine.trace_last()["level"] == LOW and engine.trace_last()["source"] == "H_RDL"
