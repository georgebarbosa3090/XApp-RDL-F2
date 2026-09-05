import pytest
from src.agents.refinement_agent import RefinementAgent
from src.conflict_types import ResolutionAction, ResolutionStrategy, ConflictEvent, XAppAction
import uuid

def test_safety_guard_out_of_bounds(mock_memory, action_tx_power, direct_conflict):
    agent = RefinementAgent(memory=mock_memory)
    
    # Injetando um valor absurdo para forcar o Safety Guard
    action_tx_power.value = 50.0  # Limite e 23 dBm
    
    resolution = ResolutionAction(
        conflict_id=direct_conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[action_tx_power],
        modified_value=50.0,
        confidence=1.0,
        validation_level=0
    )
    
    is_valid, level, reason = agent.validate(resolution, direct_conflict)
    assert is_valid is False
    assert "out of bounds" in reason.lower()

def test_safety_guard_frequency_limit(mock_memory, action_prb_quota, direct_conflict):
    agent = RefinementAgent(memory=mock_memory)
    
    resolution = ResolutionAction(
        conflict_id=direct_conflict.conflict_id,
        strategy_used=ResolutionStrategy.TVS,
        winning_actions=[action_prb_quota],
        modified_value=50.0,
        confidence=1.0,
        validation_level=0
    )
    
    # Primeira chamada deve passar
    is_valid, level, reason = agent.validate(resolution, direct_conflict)
    assert is_valid is True
    
    # Segunda chamada imediata (mesmo alvo) deve falhar pelo limite de 1000ms
    is_valid_2, level_2, reason_2 = agent.validate(resolution, direct_conflict)
    assert is_valid_2 is False
    assert "frequency exceeded" in reason_2.lower()

def test_safety_guard_single_action_pass_through(mock_memory):
    agent = RefinementAgent(memory=mock_memory)
    action = XAppAction(
        xapp_id="xslice",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=50.0,
        priority=80
    )
    is_safe, level, reason = agent.validate_single_action(action)
    assert is_safe is True
    assert "passed" in reason.lower()

def test_safety_guard_single_action_invalid_bounds(mock_memory):
    agent = RefinementAgent(memory=mock_memory)
    action = XAppAction(
        xapp_id="energy_saving",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=45.0,  # Acima de 23 dBm
        priority=60
    )
    is_safe, level, reason = agent.validate_single_action(action)
    assert is_safe is False
    assert "out of bounds" in reason.lower()

def test_zero_trust_quarantine_behavioral(mock_memory):
    """Valida que xApp infratora reincidente (>3 violações) é colocada em Quarentena Zero-Trust."""
    agent = RefinementAgent(memory=mock_memory)
    agent.config["max_violations_before_quarantine"] = 3
    
    rogue_act = XAppAction(
        xapp_id="rogue_vendor_xapp",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=55.0, # Ilegal (> 43 dBm)
        priority=99
    )
    
    # 3 violações consecutivas
    for _ in range(3):
        is_safe, level, reason = agent.validate_single_action(rogue_act)
        assert is_safe is False
        
    # A 4ª ação deve ser bloqueada diretamente por Quarentena Zero-Trust
    legal_act = XAppAction(
        xapp_id="rogue_vendor_xapp",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=50.0,
        priority=50
    )
    is_safe_q, level_q, reason_q = agent.validate_single_action(legal_act)
    assert is_safe_q is False
    assert "quarantine" in reason_q.lower()

def test_safety_guard_beam_and_isac_bounds(mock_memory):
    """Valida os limites determinísticos para parâmetros de Beam Downtilt e ISAC Sensing Ratio."""
    agent = RefinementAgent(memory=mock_memory)
    
    # Beam Downtilt válido (0 a 15 graus)
    beam_valid = XAppAction("beamformer", "gnb_01", "BEAM_DOWNTILT", 8.0, 70)
    is_safe, _, _ = agent.validate_single_action(beam_valid)
    assert is_safe is True
    
    # Beam Downtilt inválido (> 15 graus)
    beam_invalid = XAppAction("beamformer", "gnb_02", "BEAM_DOWNTILT", 22.0, 70)
    is_safe_inv, _, reason_inv = agent.validate_single_action(beam_invalid)
    assert is_safe_inv is False
    assert "downtilt" in reason_inv.lower()
    
    # ISAC Sensing Ratio válido (0.0 a 0.5)
    isac_valid = XAppAction("isac_radar", "gnb_03", "ISAC_SENSING_RATIO", 0.35, 60)
    is_safe_isac, _, _ = agent.validate_single_action(isac_valid)
    assert is_safe_isac is True
    
    # ISAC Sensing Ratio inválido (> 0.5)
    isac_invalid = XAppAction("isac_radar", "gnb_04", "ISAC_SENSING_RATIO", 0.85, 60)
    is_safe_isac_inv, _, reason_isac = agent.validate_single_action(isac_invalid)
    assert is_safe_isac_inv is False
    assert "isac" in reason_isac.lower()
