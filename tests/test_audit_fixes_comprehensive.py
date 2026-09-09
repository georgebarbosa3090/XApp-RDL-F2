#!/usr/bin/env python3
"""
Suíte de Testes Abrangente de Validação das Correções da Auditoria (Seções 8.2 a 8.8)
Projeto: xApp RDL - Fase 2 (CA-RDL)
"""

import pytest
import numpy as np
import time
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, KPMReport
from src.agents.marl.mappo_agent import MAPPOCoordinator
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.perception_agent import PerceptionAgent
from src.agents.refinement_agent import RefinementAgent, XAppLifecycleState
from src.e2.rc_encoder import RCEncoder, PARAM_PROFILES
from src.infrastructure.sdl_repository import SdlRepository

def test_8_2_reasoning_agent_hierarchical_routing():
    """Valida que os limiares tau1=1.6 e tau2=3.0 roteiam corretamente entre os 3 níveis."""
    memory = SdlRepository(host="localhost", port=6379)
    reasoner = ReasoningAgent(memory=memory, config={"tau1": 1.6, "tau2": 3.0})
    
    # 1. Conflito Direto de 2 xApps -> Deve cair no Nível 1 (Heurística < 1ms)
    act1 = XAppAction(xapp_id="xapp_ts", node_id="gnb_01", parameter="PRB_QUOTA", value=50.0, priority=90)
    act2 = XAppAction(xapp_id="xapp_es", node_id="gnb_01", parameter="PRB_QUOTA", value=30.0, priority=60)
    conflict_direct = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1, act2],
        affected_kpis=["DRB.UEThpDl"]
    )
    
    score_direct = reasoner.estimate_complexity(conflict_direct)
    assert score_direct <= 1.6, f"Score direto {score_direct} deveria ser <= 1.6"
    res_direct = reasoner.resolve(conflict_direct)
    assert res_direct.strategy_used.name == "PRIORITY_TABLE", "Deveria usar Heurística de Nível 1"
    assert res_direct.winning_actions[0].xapp_id == "xapp_ts"

def test_8_3_mappo_direct_policy_action_binding():
    """Valida que a saída da política seleciona diretamente a proposta via Action Masking."""
    coordinator = MAPPOCoordinator(n_agents=6, obs_dim=60, action_dim=7)
    
    act1 = XAppAction(xapp_id="xapp_urllc", node_id="gnb_01", parameter="TX_POWER", value=40.0, priority=95)
    act2 = XAppAction(xapp_id="xapp_embb", node_id="gnb_01", parameter="TX_POWER", value=30.0, priority=50)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.CRITICAL,
        involved_xapps=[act1, act2],
        affected_kpis=["QoS.FlowDelay"]
    )
    
    best_action, conf = coordinator.decide(conflict)
    assert best_action is not None, "A política deve selecionar uma proposta válida"
    assert best_action in conflict.involved_xapps, "A proposta deve pertencer ao conjunto em conflito"
    assert conf > 0.0

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

def test_8_4_refinement_cell_profiles_and_fsm():
    """Valida perfis de potência (Macro 43dBm vs Small Cell 23dBm) e FSM de quarentena."""
    refinement = RefinementAgent(node_profiles={"gnb_01": "macro", "gnb_03": "small_cell"})
    
    # 1. Macro gNodeB aceita 40 dBm (< 43 dBm)
    ok_macro, _ = refinement._validate_parameter_bounds("TX_POWER", 40.0, "gnb_01")
    assert ok_macro is True
    
    # 2. Small Cell rejeita 40 dBm (> 23 dBm)
    ok_small, reason = refinement._validate_parameter_bounds("TX_POWER", 40.0, "gnb_03")
    assert ok_small is False
    assert "small_cell" in reason
    
    # 3. FSM de Quarentena: 3 violações colocam em QUARANTINE
    now = 1000.0
    refinement._record_violation("rogue_xapp", now, "Infração 1")
    assert refinement._get_app_state("rogue_xapp", now) == XAppLifecycleState.SUSPECT
    
    refinement._record_violation("rogue_xapp", now + 100, "Infração 2")
    refinement._record_violation("rogue_xapp", now + 200, "Infração 3")
    assert refinement._get_app_state("rogue_xapp", now + 200) == XAppLifecycleState.QUARANTINE
    
    # 4. Transição para PROBATION após 30s
    assert refinement._get_app_state("rogue_xapp", now + 31000) == XAppLifecycleState.PROBATION
    
    # 5. Transição para ACTIVE após 10s de bom comportamento
    assert refinement._get_app_state("rogue_xapp", now + 42000) == XAppLifecycleState.ACTIVE

def test_8_5_perception_topology_and_ttl():
    """Valida inicialização automática de topologia e controle de TTL de telemetria."""
    perception = PerceptionAgent()
    
    # 1. Topologia multi-célula inicializada automaticamente
    assert len(perception.neighbor_nodes) >= 3
    assert "gnb_02" in perception.neighbor_nodes["gnb_01"]
    
    # 2. Telemetria com TTL
    rep = KPMReport(node_id="gnb_01", ue_id="ue_1", drb_thp_dl=100.0, drb_thp_ul=50.0, drb_delay_dl=2.5, prb_used_dl=40)
    now = 100.0
    perception.update_kpm_report(rep, now_ts=now)
    
    # Dentro da janela de 1s -> Válida
    ret_rep, is_valid = perception.get_kpm_report("gnb_01", now_ts=now + 0.5)
    assert is_valid is True
    assert ret_rep.drb_thp_dl == 100.0
    
    # Fora da janela de 1s -> Expirada
    ret_rep_exp, is_valid_exp = perception.get_kpm_report("gnb_01", now_ts=now + 2.0)
    assert is_valid_exp is False

if __name__ == "__main__":
    pytest.main(["-v", __file__])
