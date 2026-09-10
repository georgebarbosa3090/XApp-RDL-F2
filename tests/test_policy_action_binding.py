import pytest
torch = pytest.importorskip("torch")
import numpy as np
from src.conflict_types import ConflictEvent, ConflictType, ConflictSeverity, XAppAction, ResolutionStrategy
from src.agents.marl.mappo_agent import MAPPOCoordinator
from src.agents.reasoning_agent import ReasoningAgent
from src.infrastructure.memory_module import MemoryModule

def test_actor_critic_gradient_flow():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7, lr_actor=1e-3, lr_critic=1e-3)
    
    # Fake batch of observations and actions
    obs = np.random.uniform(0.0, 1.0, size=(4, 60)).astype(np.float32)
    actions = [1, 2, 0, 1]
    rewards = [1.0, 0.5, -0.2, 0.8]
    dones = [False, False, False, True]
    
    # Store experience
    for o, a, r, d in zip(obs, actions, rewards, dones):
        mask = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0] # 2 proposals + No-Op
        coord.store_transition(o, a, r, d, action_mask=mask)
        
    metrics = coord.train_step(batch_size=4)
    assert metrics is not None
    assert "loss_actor" in metrics
    assert "loss_critic" in metrics
    
    # Verify non-zero parameters and finite losses
    assert np.isfinite(metrics["loss_actor"])
    assert np.isfinite(metrics["loss_critic"])
    
    # Verify gradients flowed to actor network
    has_grad = any(p.grad is not None and torch.sum(torch.abs(p.grad)) > 0 for p in coord.actor.parameters())
    assert has_grad

def test_action_masking_blocks_invalid_actions():
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    
    # Only 2 proposals present -> mask allows index 0 (No-Op), 1 (act1), 2 (act2). Indices 3..6 masked.
    act1 = XAppAction(xapp_id="xapp1", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=50)
    act2 = XAppAction(xapp_id="xapp2", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=60)
    conflict = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=[act1, act2])
    
    obs = coord.extract_features(conflict, None)
    mask = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    
    with torch.no_grad():
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
        mask_tensor = torch.FloatTensor(mask).unsqueeze(0)
        probs = coord.actor.get_action_probs(obs_tensor, mask_tensor)
        probs_np = probs.squeeze(0).numpy()
        
    # Masked positions must have probability 0.0
    for idx in range(3, 7):
        assert probs_np[idx] == pytest.approx(0.0, abs=1e-6)
    # Valid positions sum to 1.0
    assert pytest.approx(probs_np[:3].sum(), abs=1e-5) == 1.0

def test_marl_noop_resolution_preservation():
    mem = MemoryModule()
    agent = ReasoningAgent(memory=mem, tau1=0.1, tau2=0.2) # Forces MARL routing
    
    act1 = XAppAction(xapp_id="x1", node_id="gnb_01", parameter="PRB_QUOTA", value=50, priority=50)
    act2 = XAppAction(xapp_id="x2", node_id="gnb_01", parameter="PRB_QUOTA", value=60, priority=50)
    conflict = ConflictEvent(
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[act1, act2],
        affected_kpis=["RRU.PrbTotDl"]
    )
    
    # Mock coord.decide to return (None, 0.95) simulating No-Op
    agent.mappo.decide = lambda c, k: (None, 0.95)
    
    resolution = agent.resolve(conflict, kpm_state=None)
    assert resolution.strategy_used == ResolutionStrategy.MARL_AGENT
    assert resolution.winning_actions == []
    assert resolution.modified_value is None

def test_safe_rl_cost_gradient_flow_and_lagrange_multiplier_update():
    """Valida o fluxo de gradiente Safe-RL comparando custo zero vs custo alto e verificando aumento do multiplicador de Lagrange."""
    coord_zero = MAPPOCoordinator(obs_dim=60, act_dim=7, lr_actor=1e-3, lr_critic=1e-3)
    coord_high = MAPPOCoordinator(obs_dim=60, act_dim=7, lr_actor=1e-3, lr_critic=1e-3)
    
    # Sincroniza pesos iniciais
    coord_high.agents[0].actor.load_state_dict(coord_zero.agents[0].actor.state_dict())
    coord_high.agents[0].critic.load_state_dict(coord_zero.agents[0].critic.state_dict())
    
    obs = np.random.uniform(0.0, 1.0, size=(4, 60)).astype(np.float32)
    actions = [0, 1, 2, 0]
    rewards = [0.5, 0.8, -0.1, 0.6]
    dones = [False, False, False, True]
    mask = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    
    # Treina coord_zero com custo 0.0
    for o, a, r, d in zip(obs, actions, rewards, dones):
        coord_zero.store_transition(o, a, r, d, action_mask=mask, cost=0.0)
    metrics_zero = coord_zero.train_step(batch_size=4)
    
    # Treina coord_high com custo 1.0 (viola limite de custo d = 0.05)
    for o, a, r, d in zip(obs, actions, rewards, dones):
        coord_high.store_transition(o, a, r, d, action_mask=mask, cost=1.0)
    metrics_high = coord_high.train_step(batch_size=4)
    
    # 1. Lagrange multiplier deve aumentar com custos altos
    assert metrics_high["lagrange_mult"] > metrics_zero["lagrange_mult"]
    assert metrics_high["lagrange_mult"] > 0.05 # Valor inicial
    
    # 2. As perdas do ator devem diferir devido ao termo de vantagem penalizada \hat{A}_t^{safe}
    assert metrics_high["loss_actor"] != metrics_zero["loss_actor"]
    assert np.isfinite(metrics_high["loss_actor"])
    assert np.isfinite(metrics_high["loss_critic"])

def test_pure_policy_inference_without_ad_hoc_reweighting():
    """Valida que a inferência do ator utiliza estritamente a distribuição aprendida π_θ(a|s) mascarada sem reponderação por prioridade."""
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    
    # Proposta 1 tem prioridade baixa (10), Proposta 2 tem prioridade alta (90)
    act1 = XAppAction(xapp_id="xapp1", node_id="gnb_01", parameter="TX_POWER", value=20.0, priority=10)
    act2 = XAppAction(xapp_id="xapp2", node_id="gnb_01", parameter="TX_POWER", value=23.0, priority=90)
    conflict = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=[act1, act2])
    
    # Força a política a emitir prob maior para act1 (0.45) que para act2 (0.40)
    # Sob reponderação ad-hoc: act2 seria 0.40 * (1 + 0.9*2) = 1.12 > act1 (0.45 * (1 + 0.1*2) = 0.54)
    # Sob inferência pura: act1 DEVE vencer pois 0.45 > 0.40
    mock_probs = torch.tensor([[0.45, 0.40, 0.0, 0.0, 0.0, 0.0, 0.15]], dtype=torch.float32)
    
    class MockActor:
        def get_action_probs(self, obs, mask=None):
            return mock_probs
        def __call__(self, obs):
            return mock_probs
            
    coord.agents[0].actor = MockActor()
    
    selected_act, conf = coord.decide(conflict, kpm_state=None)
    
    assert selected_act is not None
    assert selected_act.xapp_id == "xapp1", "Inferência pura deve escolher a ação com maior probabilidade da política aprendida (act1)"
    assert conf == pytest.approx(0.45, abs=1e-4) or conf >= 0.80

def test_action_cardinality_and_noop_disambiguation_with_many_proposals():
    """Valida que com 7 propostas, o índice reservado (6) é estritamente tratado como No-Op."""
    coord = MAPPOCoordinator(obs_dim=60, act_dim=7)
    
    # 7 propostas (índice 6 seria proposal #7 se não fosse reservado a No-Op)
    proposals = [
        XAppAction(xapp_id=f"xapp_{i}", node_id="gnb_01", parameter="PRB_QUOTA", value=10 + i * 5, priority=50)
        for i in range(7)
    ]
    conflict = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, involved_xapps=proposals)
    
    # Força o ator a emitir probabilidade máxima no índice reservado 6 (No-Op)
    mock_probs = torch.zeros((1, 7))
    mock_probs[0, 6] = 100.0
    
    class MockNoOpActor:
        def get_action_probs(self, obs, mask=None):
            return mock_probs
        def __call__(self, obs):
            return mock_probs
            
    coord.agents[0].actor = MockNoOpActor()
    coord.agents[0].select_action = lambda obs, mask=None: (6, 0.0)
    
    selected_act, conf = coord.decide(conflict, kpm_state=None)
        
    # Deve retornar None (No-Op), NÃO a 7ª proposta
    assert selected_act is None, "Índice action_dim-1 com 7 propostas deve retornar estritamente No-Op (None)"


