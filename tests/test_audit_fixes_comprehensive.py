from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import pytest
import numpy as np
import time
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, KPMReport, ResolutionAction, ResolutionStrategy
from src.agents.marl.mappo_agent import MAPPOCoordinator
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.perception_agent import PerceptionAgent
from src.agents.refinement_agent import RefinementAgent, XAppLifecycleState
from src.e2.rc_encoder import RCEncoder, PARAM_PROFILES
from src.infrastructure.sdl_repository import SdlRepository

def test_8_2_and_9_7_reasoning_agent_hierarchical_routing():
    """
    Valida a fórmula exata de complexidade C(c, s) e o roteamento hierárquico entre Nível 1 e Nível 2A:
    C = type_factor + num_apps_factor + kpis_factor + prio_factor + state_degradation
    """
    memory = SdlRepository(host="localhost", port=6379)
    reasoner = ReasoningAgent(memory=memory, config={"tau1": 1.6, "tau2": 3.0})
    
    # 1. Caso Nível 1: Par direto com prioridades distintas (90 e 40, delta=50) e 0 KPIs extras
    # C = 0.5 (direto) + 2*0.4 (2 apps) + 0*0.3 (0 extra) + max(0, 1.0 - 50/50) = 0.5 + 0.8 + 0.0 + 0.0 = 1.3 <= 1.6
    act1 = XAppAction(xapp_id="xapp_ts", node_id="gnb_01", parameter="PRB_QUOTA", value=50.0, priority=90)
    act2 = XAppAction(xapp_id="xapp_es", node_id="gnb_01", parameter="PRB_QUOTA", value=30.0, priority=40)
    conflict_level1 = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1, act2],
        affected_kpis=[],
        description="Direct conflict level 1"
    )
    score_l1 = reasoner.estimate_complexity(conflict_level1)
    assert score_l1 <= 1.6, f"Score {score_l1} deveria ser <= 1.6 para Heurística Nível 1"
    res_l1 = reasoner.resolve(conflict_level1)
    assert res_l1.strategy_used == ResolutionStrategy.PRIORITY_TABLE, "Deveria usar Heurística Nível 1"

    # 2. Caso Nível 2A: Par direto com prioridades próximas (90 e 70, delta=20) e 1 KPI extra
    # C = 0.5 + 2*0.4 + 1*0.3 + (1.0 - 20/50) = 0.5 + 0.8 + 0.3 + 0.6 = 2.2 (1.6 < C <= 3.0)
    act2_diff = XAppAction(xapp_id="xapp_es", node_id="gnb_01", parameter="PRB_QUOTA", value=30.0, priority=70)
    conflict_level2a = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1, act2_diff],
        affected_kpis=["DRB.UEThpDl"],
        description="Direct conflict level 2a"
    )
    score_l2a = reasoner.estimate_complexity(conflict_level2a)
    assert 1.6 < score_l2a <= 3.0, f"Score {score_l2a} deveria estar no intervalo (1.6, 3.0] para Nível 2A"
    res_l2a = reasoner.resolve(conflict_level2a)
    assert res_l2a.strategy_used in (ResolutionStrategy.TVS, ResolutionStrategy.EEVS), "Deveria usar Utilidade Nível 2A"

def test_9_2_noop_preservation_in_reasoning_and_marl():
    """Valida que a decisão de No-Op é preservada como winning_actions=[] no fluxo completo."""
    memory = SdlRepository(host="localhost", port=6379)
    reasoner = ReasoningAgent(memory=memory)
    
    act1 = XAppAction(xapp_id="xapp_ts", node_id="gnb_01", parameter="PRB_QUOTA", value=50.0, priority=90)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1],
        affected_kpis=[],
        description="No-op test"
    )
    
    # Mock do retorno No-Op do coordenador
    reasoner.mappo.decide = lambda c, k=None: (None, 0.9)
    res = reasoner._resolve_by_marl(conflict, None, time.time())
    
    assert res.winning_actions == [], "No-Op deve preservar winning_actions vazio"
    assert res.modified_value is None
    assert res.strategy_used == ResolutionStrategy.MARL_AGENT

def test_9_4_refinement_public_validation_with_node_profiles():
    """Valida a interface pública validate() com perfil Macro vs Small Cell."""
    refinement = RefinementAgent(node_profiles={"gnb_01": "macro", "gnb_03": "small_cell"})
    
    act_macro = XAppAction(xapp_id="xapp_ts", node_id="gnb_01", parameter="TX_POWER", value=40.0, priority=90)
    act_small = XAppAction(xapp_id="xapp_ts", node_id="gnb_03", parameter="TX_POWER", value=40.0, priority=90)
    
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT, 
        severity=ConflictSeverity.HIGH, 
        involved_xapps=[], 
        affected_kpis=[],
        description="Public validation test"
    )
    
    # 1. Macro gNodeB aceita 40 dBm (< 43 dBm)
    res_macro = ResolutionAction("c1", ResolutionStrategy.PRIORITY_TABLE, [act_macro], 40.0, 0.9, 0)
    is_valid_macro, _, _ = refinement.validate(res_macro, conflict)
    assert is_valid_macro is True, "Macro deveria aceitar 40 dBm"
    
    # 2. Small Cell rejeita 40 dBm (> 23 dBm) através da interface pública validate()
    res_small = ResolutionAction("c2", ResolutionStrategy.PRIORITY_TABLE, [act_small], 40.0, 0.9, 0)
    is_valid_small, _, reason = refinement.validate(res_small, conflict)
    assert is_valid_small is False, "Small Cell deveria rejeitar 40 dBm"
    assert "small_cell" in reason

def test_8_4_rc_encoder_systematic_profiles():
    """Valida codificação precisa em ponto fixo e decodificação reversível para todos os parâmetros."""
    encoder = RCEncoder()
    
    test_cases = [
        ("ISAC_SENSING_RATIO", 0.25, 0.25),
        ("SCHEDULER_WEIGHT", 0.25, 0.25),
        ("A3_OFFSET", 3.5, 3.5),
        ("BEAM_DOWNTILT", 6.5, 6.5),
        ("TX_POWER", 23.5, 23.5),
        ("PRB_QUOTA", 80.0, 80.0)
    ]
    
    for param, val_in, expected in test_cases:
        aper_bytes = encoder.encode_control_request("gnb_01", param, val_in)
        assert isinstance(aper_bytes, bytes)
        assert len(aper_bytes) > 0
        
        # Teste de reversibilidade e preservação numérica
        val_decoded = encoder.decode_control_request(aper_bytes, param)
        assert abs(val_decoded - expected) < 1e-3, f"Falha na decodificação de {param}: {val_decoded} != {expected}"

def test_9_3_perception_unavailable_context_handling():
    """Valida que nó desconhecido ou não cadastrado retorna (None, False) (indisponibilidade estrita)."""
    perception = PerceptionAgent()
    
    # Nó não cadastrado
    rep, is_valid = perception.get_kpm_report("gnb_unknown_999")
    assert rep is None
    assert is_valid is False

if __name__ == "__main__":
    pytest.main(["-v", __file__])
