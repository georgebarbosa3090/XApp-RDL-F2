import pytest
from src.agents.reasoning_agent import ReasoningAgent
from src.conflict_types import ResolutionStrategy, ConflictEvent, ConflictType, ConflictSeverity, XAppAction
import uuid

def test_resolve_by_heuristic_priority(mock_memory, direct_conflict):
    agent = ReasoningAgent(memory=mock_memory, config={"tau1": 1.5})
    
    # Resolve the direct conflict using H-RDL priority heuristic
    resolution = agent.resolve(direct_conflict)
    
    assert resolution is not None
    assert resolution.conflict_id == direct_conflict.conflict_id
    assert resolution.strategy_used in [ResolutionStrategy.PRIORITY_TABLE, ResolutionStrategy.TVS, ResolutionStrategy.EEVS]
    assert len(resolution.winning_actions) >= 1
    assert resolution.modified_value in [15.0, 20.0, 40.0]

def test_resolve_by_sla_utility(mock_memory, action_tx_power, action_prb_quota):
    agent = ReasoningAgent(memory=mock_memory, config={"tau1": 0.1, "tau2": 5.0})
    
    conflict = ConflictEvent(
        conflict_id=str(uuid.uuid4()),
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action_tx_power, action_prb_quota],
        affected_kpis=["DRB.UEThpDl"],
        detected_at=0.0,
        description="Conflito direto para avaliacao de utilidade"
    )
    
    resolution = agent.resolve(conflict)
    assert resolution is not None
    assert resolution.strategy_used in [ResolutionStrategy.TVS, ResolutionStrategy.EEVS, ResolutionStrategy.PRIORITY_TABLE]

def test_marl_escalation(mock_memory, action_tx_power, action_prb_quota):
    # Se conflito for complexo ou indireto, escalona para MARL
    agent = ReasoningAgent(memory=mock_memory, config={"tau1": 0.5, "tau2": 1.0})
    
    indirect_conflict = ConflictEvent(
        conflict_id=str(uuid.uuid4()),
        conflict_type=ConflictType.INDIRECT,
        severity=ConflictSeverity.MEDIUM,
        involved_xapps=[action_tx_power, action_prb_quota],
        affected_kpis=["DRB.UEThpDl", "L1M.DL-sinr", "QoS.FlowDelay"],
        detected_at=0.0,
        description="Conflito indireto de alta complexidade"
    )
    
    resolution = agent.resolve(indirect_conflict)
    assert resolution.strategy_used == ResolutionStrategy.MARL_AGENT
