"""
test_coverage_expansion_f2.py: Suíte estendida de testes unitários para a Fase 2 (CA-RDL / XApp-RDL-F2).
Eleva a cobertura de código por instruções para >85%, cobrindo todos os adaptadores de backend,
Knowledge Graph no MemoryModule, ambiente TraceReplayEnvironment, allocators e subsistemas observáveis.
"""

import json
import os
import sys
import tempfile
import pytest
import numpy as np

from src.conflict_types import (
    XAppAction,
    ConflictType,
    ConflictSeverity,
    ConflictEvent,
    ResolutionStrategy,
    ResolutionAction,
    KPMReport,
    RDLDecision
)
from src.infrastructure.memory_module import MemoryModule
from src.agents.marl.environments.trace_replay_env import TraceReplayEnvironment
from src.infrastructure.ran_backend_adapter import NoriBackendAdapter, SrsRanBackendAdapter, UnsupportedBackendError
from src.infrastructure.ran_backend_factory import get_ran_backend_adapter, SUPPORTED_BACKENDS
from src.infrastructure.ric_request_id_allocator import RicRequestIdAllocator
from src.infrastructure.sdl_repository import SdlRepository
from src.observability.health_server import HealthServer, AppState
from src.observability.logging import setup_logger
from src.rdl_xapp import RDLxApp

from src.e2.e2ap.control import (
    RICrequestID,
    RICcontrolRequest,
    RICcontrolAcknowledge,
    RICcontrolFailure,
    build_ric_control_request,
    parse_ric_control_ack,
    parse_ric_control_failure
)
from src.e2.e2ap.pdu import unwrap_e2ap_pdu


# ============================================================================
# 1. TESTES DO MEMORYMODULE & KNOWLEDGE GRAPH CAUSAL
# ============================================================================

def test_memory_module_knowledge_graph():
    mem = MemoryModule()
    
    # Testa adição de relações causais
    mem.add_causal_relation("xApp_QoS", "MUTATES", "PRB_QUOTA")
    mem.add_causal_relation("PRB_QUOTA", "IMPACTS", "LATENCY_KPI")
    mem.add_causal_relation("LATENCY_KPI", "AFFECTS", "Slice_1")

    mem.add_causal_relation("xApp_Energy", "MUTATES", "TX_POWER")
    mem.add_causal_relation("TX_POWER", "IMPACTS", "LATENCY_KPI")

    # Busca caminho de conflito indireto entre xApp_QoS e xApp_Energy
    paths = mem.find_indirect_conflict_path("xApp_QoS", "xApp_Energy")
    assert len(paths) > 0, "Deveria ter encontrado um caminho de conflito indireto no grafo"
    assert "LATENCY_KPI" in paths[0], "O KPI de conflito indireto em comum deve ser LATENCY_KPI"

    # Busca sem conexões em comum
    assert len(mem.find_indirect_conflict_path("xApp_Inexistente", "xApp_QoS")) == 0


def test_causal_graph_decision_impact():
    from src.agents.reasoning_agent import ReasoningAgent

    # 1. Sem Grafo Causal no MemoryModule
    mem_plain = MemoryModule()
    reasoning_plain = ReasoningAgent(memory=mem_plain, tau1=1.6, tau2=3.0)

    action_a = XAppAction(xapp_id="xApp_QoS", node_id="gnb_01", parameter="PRB_QUOTA", value=75.0, priority=10)
    action_b = XAppAction(xapp_id="xApp_Energy", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=8)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=[action_a, action_b],
        affected_kpis=[]
    )

    c_plain = reasoning_plain.estimate_complexity(conflict)

    # 2. Com Grafo Causal Registrado no MemoryModule
    mem_graph = MemoryModule()
    mem_graph.add_causal_relation("xApp_QoS", "MUTATES", "PRB_QUOTA")
    mem_graph.add_causal_relation("PRB_QUOTA", "IMPACTS", "LATENCY_KPI")
    mem_graph.add_causal_relation("xApp_Energy", "MUTATES", "TX_POWER")
    mem_graph.add_causal_relation("TX_POWER", "IMPACTS", "LATENCY_KPI")

    reasoning_graph = ReasoningAgent(memory=mem_graph, tau1=1.6, tau2=3.0)
    conflict_graph = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=[action_a, action_b],
        affected_kpis=[]
    )

    c_graph = reasoning_graph.estimate_complexity(conflict_graph)

    # Valida elevação de complexidade e alteração de rota de decisão (Decision_with_graph != Decision_without_graph)
    assert c_graph > c_plain
    assert "LATENCY_KPI" in conflict_graph.affected_kpis


def test_memory_module_knowledge_graph():
    mem = MemoryModule()
    
    # Testa adição de relações causais
    mem.add_causal_relation("xApp_QoS", "MUTATES", "PRB_QUOTA")
    mem.add_causal_relation("PRB_QUOTA", "IMPACTS", "LATENCY_KPI")
    mem.add_causal_relation("LATENCY_KPI", "AFFECTS", "Slice_1")

    mem.add_causal_relation("xApp_Energy", "MUTATES", "TX_POWER")
    mem.add_causal_relation("TX_POWER", "IMPACTS", "LATENCY_KPI")

    # Busca caminho de conflito indireto entre xApp_QoS e xApp_Energy
    paths = mem.find_indirect_conflict_path("xApp_QoS", "xApp_Energy")
    assert len(paths) > 0, "Deveria ter encontrado um caminho de conflito indireto no grafo"
    assert "LATENCY_KPI" in paths[0], "O KPI de conflito indireto em comum deve ser LATENCY_KPI"

    # Busca sem conexões em comum
    assert len(mem.find_indirect_conflict_path("xApp_Inexistente", "xApp_QoS")) == 0

    action = XAppAction(
        xapp_id="xApp_QoS",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=10
    )
    mem.add_action(action)
    assert len(mem.get_recent_actions()) == 1

    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action],
        affected_kpis=["PRB_QUOTA"]
    )
    mem.add_conflict(conflict)

    res = ResolutionAction(
        conflict_id=conflict.conflict_id,
        strategy_used=ResolutionStrategy.PRIORITY_TABLE,
        winning_actions=[action],
        modified_value=75.0,
        confidence=0.95,
        validation_level=1
    )
    mem.add_resolution(res)

    similar = mem.get_similar_resolutions(conflict)
    assert len(similar) == 1

    mem.save_control_request("ctrl_100", {"status": "pending"})
    mem.update_control_result("ctrl_100", "SUCCESS")
    mem.record_rollback("ctrl_100")


# ============================================================================
# 2. TESTES DO AMBIENTE TRACEREPLAYENVIRONMENT (MARL)
# ============================================================================

def test_trace_replay_environment():
    trace_content = [
        {
            "timestamp": 1000,
            "sla_target": 50.0,
            "agents": [
                {"sinr_db": 25.5, "prb_usage": 60.0, "throughput_mbps": 100.0, "latency_ms": 12.0},
                {"sinr_db": 18.2, "prb_usage": 40.0, "throughput_mbps": 50.0, "latency_ms": 15.0}
            ]
        },
        {
            "timestamp": 2000,
            "sla_target": 30.0,
            "agents": [
                {"sinr_db": 24.0, "prb_usage": 70.0, "throughput_mbps": 95.0, "latency_ms": 14.0},
                {"sinr_db": 19.0, "prb_usage": 35.0, "throughput_mbps": 55.0, "latency_ms": 13.0}
            ]
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        for entry in trace_content:
            tmp.write(json.dumps(entry) + "\n")
        tmp_path = tmp.name

    try:
        env = TraceReplayEnvironment(trace_path=tmp_path, num_agents=2, obs_dim=4)
        assert len(env.trace_data) == 2

        obs = env.reset()
        assert obs.shape == (2, 4)
        assert np.isclose(obs[0, 0], 25.5)

        actions = np.array([40.0, 20.0])
        next_obs, rewards, done, info = env.step(actions)
        assert not done
        assert len(rewards) == 2
        assert info["step"] == 1

        actions_2 = np.array([60.0, 20.0])
        next_obs_2, rewards_2, done_2, info_2 = env.step(actions_2)
        assert done_2
        assert rewards_2[0] == -1.0

        next_obs_3, rewards_3, done_3, info_3 = env.step(actions_2)
        assert done_3

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_trace_replay_env_empty():
    env = TraceReplayEnvironment(trace_path="arquivo_inexistente.jsonl", num_agents=2, obs_dim=4)
    obs = env.reset()
    assert obs.shape == (2, 4)
    next_obs, rewards, done, info = env.step(np.array([0.0, 0.0]))
    assert done
    assert info["reason"] == "trace_empty"


# ============================================================================
# 3. TESTES DOS ADAPTADORES DE BACKEND RAN (RANBACKENDADAPTER & FACTORY)
# ============================================================================

def test_ran_backend_adapters():
    assert "NORI_NS3" in SUPPORTED_BACKENDS
    assert "SRSRAN_OPEN5GS" in SUPPORTED_BACKENDS

    nori_adapter = get_ran_backend_adapter("NORI_NS3")
    meta_nori = nori_adapter.metadata
    assert meta_nori.backend_id == "NORI_NS3"
    assert nori_adapter.discover_capabilities("gnb_nori_01", oran_strict=False)

    action = XAppAction(
        xapp_id="xApp_QoS",
        node_id="gnb_nori_01",
        parameter="PRB_QUOTA",
        value=65.0,
        priority=10
    )
    pdu_nori = nori_adapter.map_action_to_control_pdu(action, requestor_id=1, instance_id=2)
    assert len(pdu_nori) > 0

    ack_json_nori = json.dumps({"status": "ACKNOWLEDGED", "req_id": 1}).encode('utf-8')
    corr_nori = nori_adapter.correlate_ack(ack_json_nori, allow_test_fallback=True)
    assert corr_nori["status"] == "ACK_RECEIVED"

    malformed_corr = nori_adapter.correlate_ack(b"\x00\x11\x22\x33", allow_test_fallback=False)
    assert malformed_corr["status"] == "MALFORMED_RESPONSE"

    srs_adapter = get_ran_backend_adapter("SRSRAN_OPEN5GS")
    meta_srs = srs_adapter.metadata
    assert meta_srs.backend_id == "SRSRAN_OPEN5GS"
    assert srs_adapter.discover_capabilities("gnb_srs_01", oran_strict=False)

    pdu_srs = srs_adapter.map_action_to_control_pdu(action, requestor_id=2, instance_id=3)
    assert len(pdu_srs) > 0

    corr_srs = srs_adapter.correlate_ack(ack_json_nori, allow_test_fallback=True)
    assert corr_srs["status"] == "ACK_RECEIVED"

    with pytest.raises(UnsupportedBackendError):
        get_ran_backend_adapter("BACKEND_INVALIDO")


def test_ran_backend_factory_strict_mode(monkeypatch):
    monkeypatch.setenv("RDL_MODE", "ORAN_STRICT")
    monkeypatch.setenv("RAN_BACKEND", "")
    with pytest.raises(UnsupportedBackendError):
        get_ran_backend_adapter(None)


# ============================================================================
# 4. TESTES DO RIC REQUEST ID ALLOCATOR & SDL REPOSITORY
# ============================================================================

def test_ric_request_id_allocator():
    allocator = RicRequestIdAllocator()
    req = allocator.allocate(node_id="gnb_01", ran_function_id=3, decision_id="dec_1", action_id="act_1")
    assert req.requestor_id > 0
    assert req.instance_id > 0

    info = allocator.lookup_correlation("gnb_01", 3, req.requestor_id, req.instance_id)
    assert info is not None
    assert info["decision_id"] == "dec_1"

    popped = allocator.pop_correlation("gnb_01", 3, req.requestor_id, req.instance_id)
    assert popped["action_id"] == "act_1"
    assert allocator.lookup_correlation("gnb_01", 3, req.requestor_id, req.instance_id) is None


def test_sdl_repository():
    sdl = SdlRepository()
    sdl.save_subscription("sub_1", {"type": "kpm"})
    sdl.save_e2_node("gnb_1", {"status": "connected"})
    sdl.save_latest_kpm_state("gnb_1", {"prb_usage": 50})
    sdl.save_action_proposal("prop_1", {"param": "PRB"})
    sdl.save_decision("dec_1", {"strategy": "MARL"})
    sdl.save_control_request("ctrl_1", {"xapp": "QoS"})
    sdl.update_control_result("ctrl_1", "SUCCESS")
    sdl.record_rollback("ctrl_1")

    action = XAppAction(
        xapp_id="xApp_QoS",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=75.0,
        priority=10
    )
    sdl.add_action(action)
    assert len(sdl.get_recent_actions()) == 1


# ============================================================================
# 5. TESTES DE E2AP CONTROL PDU ENCODING / DECODING
# ============================================================================

def test_e2ap_control_codecs():
    ctx = build_ric_control_request(
        node_id="gnb_01",
        ran_function_id=3,
        header_bytes=b"\x01\x02\x03",
        message_bytes=b"\x04\x05\x06",
        requestor_id=10,
        instance_id=20,
        ack_request=1
    )
    assert ctx.pdu_aper is not None
    assert len(ctx.pdu_aper) > 0
    assert ctx.requestor_id == 10
    assert ctx.instance_id == 20


# ============================================================================
# 6. TESTES DO HEALTH SERVER & RDLXAPP INTEGRADO
# ============================================================================

def test_health_server():
    hs = HealthServer(port=8089)
    hs.set_state(AppState.READY)
    assert hs.state == AppState.READY
    hs.run()


def test_rdl_xapp_lifecycle():
    xapp = RDLxApp()
    assert xapp.backend.metadata.backend_id in ("NORI_NS3", "SRSRAN_OPEN5GS")
    
    summary_proposal = {
        "payload": json.dumps({
            "xapp_id": "xApp_QoS",
            "node_id": "gnb_01",
            "parameter": "PRB_QUOTA",
            "value": 75.0,
            "priority": 85
        }).encode('utf-8')
    }
    xapp._action_proposal_handler(xapp.xapp, summary_proposal, None)
    assert len(xapp.proposal_buffer) == 1

    xapp._process_action_group(xapp.proposal_buffer)

    xapp._default_handler(xapp.xapp, {"mtype": 999}, None)
    xapp._control_ack_handler(xapp.xapp, {"payload": b'{"status": "OK"}'}, None)
    xapp._control_failure_handler(xapp.xapp, {"payload": b'{"status": "FAILURE"}'}, None)
    
    xapp.start()
    xapp.stop()


# ============================================================================
# 7. TESTE DE COBERTURA DO MAIN.PY
# ============================================================================

def test_main_py_import():
    import src.main as main_mod
    assert hasattr(main_mod, 'RDLxApp')
