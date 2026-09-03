try:
    import pytest
except ImportError:
    pytest = None
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

def test_mappo_gae_computation():
    agent = MAPPOAgent(obs_dim=10, action_dim=5, n_agents=2, gamma=0.99, gae_lambda=0.95)
    rewards = [1.0, 0.5, 0.8, -0.2]
    values = np.array([0.5, 0.4, 0.6, 0.1], dtype=np.float32)
    dones = [False, False, False, True]
    
    advantages, returns = agent.compute_gae(rewards, values, dones)
    
    assert len(advantages) == 4
    assert len(returns) == 4
    assert isinstance(advantages, np.ndarray)
    assert isinstance(returns, np.ndarray)
    
    # Delta at t=3: r_3 + gamma * 0 * (1 - 1) - V_3 = -0.2 - 0.1 = -0.3
    np.testing.assert_almost_equal(advantages[3], -0.3, decimal=4)
    # Returns at t=3: A_3 + V_3 = -0.3 + 0.1 = -0.2
    np.testing.assert_almost_equal(returns[3], -0.2, decimal=4)

def test_mappo_rollout_buffer_and_train_step():
    coordinator = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5)
    
    obs = np.ones(10, dtype=np.float32) * 0.5
    global_obs = np.ones(20, dtype=np.float32) * 0.5
    
    # Record full transitions (o_t, s_t^global, a_t, log \pi(a_t), r_t, d_t)
    for i in range(5):
        coordinator.record_transition(
            obs=obs,
            action=1,
            log_prob=-0.693,
            reward=0.8,
            global_obs=global_obs,
            done=(i == 4)
        )
        
    assert len(coordinator.rollout_buffer) == 5
    assert coordinator.rollout_buffer[0]["obs"] is not None
    assert coordinator.rollout_buffer[0]["global_obs"] is not None
    assert coordinator.rollout_buffer[0]["log_prob"] == -0.693
    
    losses = coordinator.train_step()
    assert "agent_0_actor_loss" in losses
    assert "agent_0_critic_loss" in losses
    assert len(coordinator.rollout_buffer) == 0  # Buffer cleared after training

