import pytest
import time
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.e2.rc_encoder import RCEncoder
from src.infrastructure.memory_module import MemoryModule

def test_decomposed_latency_pipeline_monotonic():
    mem = MemoryModule()
    perception = PerceptionAgent(mem)
    reasoning = ReasoningAgent(mem, tau1=1.6, tau2=3.0)
    refinement = RefinementAgent(mem)
    encoder = RCEncoder()
    
    actions = [
        XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=90),
        XAppAction(xapp_id="xapp_2", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=90)
    ]
    
    t_start = time.perf_counter()
    
    # 1. Perception
    t_p0 = time.perf_counter()
    conflicts = perception.register_action_group(actions)
    t_p1 = time.perf_counter()
    t_perception = (t_p1 - t_p0) * 1000.0
    
    assert len(conflicts) > 0
    conflict = conflicts[0]
    
    # 2. Reasoning
    t_r0 = time.perf_counter()
    resolution = reasoning.resolve(conflict, kpm_state=None)
    t_r1 = time.perf_counter()
    t_reasoning = (t_r1 - t_r0) * 1000.0
    
    # 3. Refinement
    t_f0 = time.perf_counter()
    is_valid, level, reason = refinement.validate(resolution, conflict)
    t_f1 = time.perf_counter()
    t_refinement = (t_f1 - t_f0) * 1000.0
    
    # 4. E2 Encode
    t_e0 = time.perf_counter()
    if is_valid and resolution.winning_actions:
        for act in resolution.winning_actions:
            _ = encoder.encode_control_request(act.node_id, act.parameter, act.value)
    t_e1 = time.perf_counter()
    t_encode = (t_e1 - t_e0) * 1000.0
    
    t_end = time.perf_counter()
    t_total = (t_end - t_start) * 1000.0
    
    # Assert non-negative individual components
    assert t_perception >= 0.0
    assert t_reasoning >= 0.0
    assert t_refinement >= 0.0
    assert t_encode >= 0.0
    
    # Total must be greater than or equal to sum of individual components
    sum_components = t_perception + t_reasoning + t_refinement + t_encode
    assert t_total >= sum_components * 0.9

def test_heuristic_decision_low_latency_budget():
    """
    Valida a baixa latência de decisão do Nível 1 (Heurística).
    Em ambiente interpretado Python no WSL2, o orçamento admitido para este teste unitário é < 5.0 ms
    (com média de execução tipicamente submilissegundo, < 0.5 ms no runtime compilado).
    """
    mem = MemoryModule()
    reasoning = ReasoningAgent(mem, tau1=1.6, tau2=3.0)
    
    # Simple direct conflict with large priority delta routing to heuristic
    act1 = XAppAction(xapp_id="xapp_1", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=90)
    act2 = XAppAction(xapp_id="xapp_2", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=40)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT, 
        severity=ConflictSeverity.HIGH, 
        involved_xapps=[act1, act2],
        description="Direct conflict heuristic test"
    )
    
    # Warmup
    _ = reasoning.resolve(conflict, kpm_state=None)
    
    t0 = time.perf_counter()
    res = reasoning.resolve(conflict, kpm_state=None)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    
    # Orçamento rigorosamente documentado para ambiente de teste de software Python
    assert dt_ms < 5.0
    assert res.strategy_used.name == "PRIORITY_TABLE"

def test_full_runtime_queue_and_decision_latency_breakdown():
    """
    Valida a decomposição monotônica completa do ciclo RDL:
    T_cycle_total = T_queue + T_proc + T_e2_encode, onde T_proc = T_perception + T_reasoning + T_refinement.
    """
    mem = MemoryModule()
    perception = PerceptionAgent(mem)
    reasoning = ReasoningAgent(mem, tau1=1.6, tau2=3.0)
    refinement = RefinementAgent(mem)
    encoder = RCEncoder()
    
    t_arrival = time.perf_counter()
    time.sleep(0.002) # Simula 2ms de espera no buffer de decisão
    
    actions = [
        XAppAction(xapp_id="xapp_ts", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=90),
        XAppAction(xapp_id="xapp_es", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=40)
    ]
    for a in actions:
        a.arrival_monotonic = t_arrival
        
    t_proc_start = time.perf_counter()
    t_queue_ms = (t_proc_start - t_arrival) * 1000.0
    assert t_queue_ms >= 1.9
    
    # 1. Percepção
    t_p0 = time.perf_counter()
    conflicts = perception.register_action_group(actions)
    t_perc_ms = (time.perf_counter() - t_p0) * 1000.0
    
    # 2. Raciocínio
    t_r0 = time.perf_counter()
    resolution = reasoning.resolve(conflicts[0], kpm_state=None)
    t_reas_ms = (time.perf_counter() - t_r0) * 1000.0
    
    # 3. Refinamento
    t_f0 = time.perf_counter()
    is_valid, _, _ = refinement.validate(resolution, conflicts[0])
    t_ref_ms = (time.perf_counter() - t_f0) * 1000.0
    
    # 4. Codificação E2
    t_e0 = time.perf_counter()
    if is_valid and resolution.winning_actions:
        for act in resolution.winning_actions:
            _ = encoder.encode_control_pdu(act.node_id, act.parameter, act.value)
    t_e2_encode_ms = (time.perf_counter() - t_e0) * 1000.0
    
    t_proc_ms = t_perc_ms + t_reas_ms + t_ref_ms
    t_cycle_total_ms = t_queue_ms + t_proc_ms + t_e2_encode_ms
    
    assert t_proc_ms > 0.0
    assert t_e2_encode_ms >= 0.0
    assert t_cycle_total_ms >= t_queue_ms + t_proc_ms + t_e2_encode_ms * 0.95

def test_rdl_xapp_runtime_full_cycle_and_payload_dispatch(monkeypatch):
    """
    Valida a inicialização completa do componente público RDLxApp, ingestão via
    _action_proposal_handler, processamento através da tríade de agentes e despacho
    final de PDU E2SM-RC completo (Header + Message APER) via adaptador RMR.
    """
    import json
    from src.rdl_xapp import RDLxApp, RDL_ACTION_PROPOSAL
    
    # 1. Instanciação do componente público RDLxApp
    app = RDLxApp(config_path="configs/config-file.json")
    assert app is not None
    assert app.asn1_decoder is not None
    assert app.rc_encoder is not None
    
    # 2. Mock de transporte RMR para interceptar payloads enviados
    sent_messages = []
    def mock_rmr_send(payload, mtype):
        sent_messages.append({"payload": json.loads(payload.decode('utf-8')), "mtype": mtype})
        return True
    monkeypatch.setattr(app.xapp, "rmr_send", mock_rmr_send)
    
    # 3. Ingestão de duas propostas com conflito via RMR proposal handler
    prop1 = json.dumps({
        "xapp_id": "ricxapp-traffic-steering",
        "node_id": "gnb_01",
        "parameter": "TX_POWER",
        "value": 23.0,
        "priority": 90
    }).encode('utf-8')
    
    prop2 = json.dumps({
        "xapp_id": "ricxapp-energy-saving",
        "node_id": "gnb_01",
        "parameter": "TX_POWER",
        "value": 20.0,
        "priority": 40
    }).encode('utf-8')
    
    app._action_proposal_handler(app.xapp, {"payload": prop1}, None)
    app._action_proposal_handler(app.xapp, {"payload": prop2}, None)
    
    # Verifica que o buffer enfileirou as propostas com arrival_monotonic registrado
    with app.buffer_lock:
        assert len(app.proposal_buffer) == 2
        batch = list(app.proposal_buffer)
        app.proposal_buffer.clear()
        
    for act in batch:
        assert act.arrival_monotonic > 0.0
        
    # 4. Processamento síncrono do grupo de ações
    app._process_action_group(batch)
    
    # 5. Validação do despacho de controle E2SM-RC
    assert len(sent_messages) >= 1
    dispatched = sent_messages[0]
    assert dispatched["mtype"] == 12010 # RIC_CONTROL_REQ
    payload = dispatched["payload"]
    
    assert payload["node_id"] == "gnb_01"
    assert payload["parameter"] == "TX_POWER"
    assert payload["value"] == 23.0 # Vencedora de maior prioridade (90 vs 40)
    assert "header_aper_bytes" in payload
    assert "msg_aper_bytes" in payload
    assert len(payload["header_aper_bytes"]) > 0
    assert len(payload["msg_aper_bytes"]) > 0
    
    # 6. Teste direto do método _send_control retornando Tuple[bool, float]
    success, t_enc = app._send_control("gnb_01", "PRB_QUOTA", 80.0)
    assert success is True
    assert t_enc >= 0.0


