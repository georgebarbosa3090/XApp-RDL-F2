import pytest
import numpy as np
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction
from src.agents.marl.mappo_agent import MAPPOCoordinator, MAPPOAgent, TORCH_AVAILABLE

def test_mappo_coordinator_initialization():
    coordinator = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5)
    assert coordinator.n_agents == 2
    assert coordinator.obs_dim == 10
    assert len(coordinator.agents) == 2

def test_mappo_feature_extraction():
    coordinator = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5)
    action1 = XAppAction(xapp_id="xapp-ts", node_id="gnb-001", parameter="tx_power", value=40.0, priority=9)
    action2 = XAppAction(xapp_id="xapp-es", node_id="gnb-001", parameter="tx_power", value=20.0, priority=6)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action1, action2],
        affected_kpis=["throughput"],
        description="Tx power collision"
    )
    
    kpm_state = {"DRB.UEThpDl": 85.0, "RRU.PrbTotDl": 60.0, "QoS.FlowDelay": 8.0}
    obs = coordinator.extract_features(conflict, kpm_state)
    
    assert isinstance(obs, np.ndarray)
    assert len(obs) == 10
    assert obs[0] == 1.0  # DIRECT conflict
    assert obs[2] == 0.85 # Throughput normalized

def test_mappo_multiobjective_reward():
    coordinator = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5, config={"w_qos": 0.6, "w_ee": 0.3, "w_pen": 0.1})
    action = XAppAction(xapp_id="xapp-ts", node_id="gnb-001", parameter="tx_power", value=40.0, priority=10)
    kpm_state = {"QoS.FlowDelay": 10.0}
    
    reward = coordinator.calculate_multiobjective_reward(action, kpm_state, conflict_resolved=True)
    assert isinstance(reward, float)
    assert reward > 0.0

def test_mappo_decision_making():
    coordinator = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5)
    action_critical = XAppAction(xapp_id="xapp-urllc", node_id="gnb-001", parameter="tx_power", value=42.0, priority=10)
    action_low = XAppAction(xapp_id="xapp-mmtc", node_id="gnb-001", parameter="tx_power", value=20.0, priority=3)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.CRITICAL,
        involved_xapps=[action_critical, action_low],
        affected_kpis=["delay"],
        description="URLLC vs mMTC"
    )
    
    best_action, confidence = coordinator.decide(conflict)
    assert best_action is not None
    assert best_action.xapp_id == "xapp-urllc"
    assert confidence >= 0.75
