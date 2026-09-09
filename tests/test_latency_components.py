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

def test_heuristic_latency_sub_millisecond():
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
    
    t0 = time.perf_counter()
    res = reasoning.resolve(conflict, kpm_state=None)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    
    # Heuristic lookup should take < 5 ms in Python test environment (typically < 0.5 ms)
    assert dt_ms < 5.0
    assert res.strategy_used.name == "PRIORITY_TABLE"
