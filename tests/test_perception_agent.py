import pytest
from src.agents.perception_agent import PerceptionAgent
from src.conflict_types import XAppAction, ConflictType

def test_detect_direct_conflict(action_tx_power):
    agent = PerceptionAgent()
    
    action2 = XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=15.0,
        priority=80
    )
    
    # Processando em lote (Janela de 200ms)
    conflicts = agent.register_action_group([action_tx_power, action2])
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DIRECT
    assert "TX_POWER" in conflicts[0].description
    assert len(conflicts[0].involved_xapps) == 2

def test_detect_indirect_conflict(action_tx_power, action_prb_quota):
    agent = PerceptionAgent()
    
    # Ambas afetam Throughput e Delay
    conflicts = agent.register_action_group([action_tx_power, action_prb_quota])
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert len(conflicts[0].involved_xapps) == 2
    
def test_no_conflict():
    agent = PerceptionAgent()
    
    # Ações em nós diferentes e independentes não devem causar conflito
    action1 = XAppAction("xapp_1", "gnb_01", "TX_POWER", 20.0, 50)
    action2 = XAppAction("xapp_2", "gnb_02", "TX_POWER", 20.0, 50)
    
    conflicts = agent.register_action_group([action1, action2])
    assert len(conflicts) == 0

def test_inter_cell_interference_conflict():
    """Valida detecção de interferência co-canal entre gNodeBs vizinhas mapeadas."""
    agent = PerceptionAgent()
    agent.add_neighbor_relation("gnb_01", "gnb_02")
    
    action_macro = XAppAction("energy_saving", "gnb_01", "TX_POWER", 38.0, 60)
    action_neighbor = XAppAction("beamformer", "gnb_02", "BEAM_DOWNTILT", 4.0, 75)
    
    conflicts = agent.register_action_group([action_macro, action_neighbor])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert "Inter-Cell" in conflicts[0].description

def test_perception_5ga_6g_parameters():
    """Valida detecção de conflito indireto em parâmetros 5G-Adv e 6G (Beamforming e ISAC)."""
    agent = PerceptionAgent()
    
    action_isac = XAppAction("isac_radar", "gnb_01", "ISAC_SENSING_RATIO", 0.35, 70)
    action_beam = XAppAction("beamformer", "gnb_01", "BEAM_DOWNTILT", 8.0, 65)
    
    # Ambos afetam DRB.UEThpDl
    conflicts = agent.register_action_group([action_isac, action_beam])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert "DRB.UEThpDl" in conflicts[0].affected_kpis
