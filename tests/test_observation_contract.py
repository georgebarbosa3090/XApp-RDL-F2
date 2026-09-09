import pytest
import numpy as np
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction
from src.agents.marl.mappo_agent import MAPPOCoordinator

def test_canonical_observation_dimension_60():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    act1 = XAppAction(xapp_id="xapp_ml", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=90)
    act2 = XAppAction(xapp_id="xapp_heur", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=40)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1, act2],
        affected_kpis=["QoS.FlowDelay"]
    )
    kpm_state = {"DRB.UEThpDl": 80.0, "DRB.UEThpUl": 30.0, "QoS.FlowDelay": 5.0, "RRU.PrbTotDl": 45.0, "L1M.DL-sinr": 18.0}
    obs = coord.extract_features(conflict, kpm_state)
    
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (60,)
    assert 0.0 <= obs.min() and obs.max() <= 1.0

def test_linear_priority_preservation():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    priorities = [40, 50, 80, 90]
    expected_prio_norms = [0.40, 0.50, 0.80, 0.90]
    
    actions = [
        XAppAction(xapp_id=f"xapp_{p}", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=p)
        for p in priorities
    ]
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=actions
    )
    obs = coord.extract_features(conflict, None)
    
    # Check linear normalization for each action slot
    for idx, expected in enumerate(expected_prio_norms):
        base_idx = 12 + (idx * 8)
        prio_val = obs[base_idx + 4]
        assert pytest.approx(prio_val, abs=1e-3) == expected

def test_presence_mask_and_slot_allocation():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    
    # Test with 2 proposals
    actions_2 = [
        XAppAction(xapp_id="a1", node_id="gnb_01", parameter="PRB_QUOTA", value=30, priority=50),
        XAppAction(xapp_id="a2", node_id="gnb_01", parameter="PRB_QUOTA", value=50, priority=80)
    ]
    conf_2 = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=actions_2)
    obs_2 = coord.extract_features(conf_2, None)
    
    # Presence mask (indices 6..11): 2 active, 4 empty
    assert list(obs_2[6:12]) == [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    
    # Test with 4 proposals
    actions_4 = actions_2 + [
        XAppAction(xapp_id="a3", node_id="gnb_01", parameter="BEAM_DOWNTILT", value=6.0, priority=40),
        XAppAction(xapp_id="a4", node_id="gnb_01", parameter="ISAC_SENSING_RATIO", value=0.2, priority=90)
    ]
    conf_4 = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=actions_4)
    obs_4 = coord.extract_features(conf_4, None)
    assert list(obs_4[6:12]) == [1.0, 1.0, 1.0, 1.0, 0.0, 0.0]

def test_exceeding_proposals_safe_handling():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    actions_8 = [
        XAppAction(xapp_id=f"a_{i}", node_id="gnb_01", parameter="PRB_QUOTA", value=10 + i * 5, priority=50)
        for i in range(8)
    ]
    conf_8 = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=actions_8)
    obs_8 = coord.extract_features(conf_8, None)
    
    assert obs_8.shape == (60,)
    # All 6 slots in mask are filled
    assert list(obs_8[6:12]) == [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

def test_deterministic_feature_hashing():
    """Valida que o hash de identificadores de xApp e Nó é estável e reproduzível."""
    from src.agents.marl.mappo_agent import _stable_hash
    
    # Hashes devem ser constantes independentemente do processo ou semente aleatória
    hash_xapp1 = _stable_hash("xapp_traffic_steering", 100)
    hash_xapp2 = _stable_hash("xapp_traffic_steering", 100)
    assert hash_xapp1 == hash_xapp2
    assert 0 <= hash_xapp1 < 100
    
    hash_node1 = _stable_hash("gnb_01", 10)
    hash_node2 = _stable_hash("gnb_01", 10)
    assert hash_node1 == hash_node2
    assert 0 <= hash_node1 < 10

