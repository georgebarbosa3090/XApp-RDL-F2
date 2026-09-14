import os
import csv
import time
import json
import subprocess
import numpy as np
from typing import Dict, Any, List
from src.agents.marl.mappo_agent import MAPPOCoordinator, PYTORCH_AVAILABLE, torch
from src.observability.logging import setup_logger

logger = setup_logger("MAPPOTrainer")

def _get_git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "UNKNOWN_GIT_SHA"

class MAPPOTrainer:
    """
    Orquestrador de Treinamento Algorítmico / Smoke Test Multi-Agente MAPPO.
    Escopo: Treinamento e validação algorítmica de pipelines (Safe-RL/CMDP).
    Nota de Proveniência: Treinamentos para dados científicos de publicação na RAN devem ser executados sobre o ambiente de co-simulação ns-3/NORI.
    """

    def __init__(
        self,
        n_agents: int = 6,
        obs_dim: int = 60,
        action_dim: int = 7,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        cost_limit: float = 0.05
    ):
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.cost_limit = cost_limit
        self.lr = lr
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        
        self.coordinator = MAPPOCoordinator(
            n_agents=n_agents,
            obs_dim=obs_dim,
            action_dim=action_dim,
            lr_actor=lr,
            lr_critic=lr
        )

    def train_campaign(
        self,
        episodes: int = 50,
        steps_per_episode: int = 100,
        seed: int = 42,
        output_dir: str = "experiments/training/seed_042"
    ) -> Dict[str, Any]:
        """
        Executa campanha algorítmica de treinamento multi-semente com salvamento de checkpoints e manifesto.
        """
        os.makedirs(output_dir, exist_ok=True)
        np.random.seed(seed)
        
        rewards_history = []
        costs_history = []
        lagrange_history = []
        
        t0 = time.time()
        logger.info(f"Iniciando campanha de treinamento MAPPO [Seed={seed}, Ep={episodes}]")
        
        for ep in range(1, episodes + 1):
            ep_reward = 0.0
            ep_cost = 0.0
            
            # Simula trajetória de rollout para smoke test algorítmico
            for step in range(steps_per_episode):
                obs = np.random.randn(self.n_agents, self.obs_dim).astype(np.float32)  # unit-smoke-only
                global_obs = obs.reshape(-1)
                
                r_step = float(np.mean(np.sin(step * 0.1) * 0.5 + 0.5))
                c_step = float(np.clip(0.1 * np.cos(step * 0.2), 0.0, 0.2))
                
                for agent_idx in range(self.n_agents):
                    agent = self.coordinator.agents[agent_idx]
                    action, log_prob = agent.select_action(obs[agent_idx])
                    
                    self.coordinator.store_transition(
                        obs=obs[agent_idx],
                        action=action,
                        reward=r_step,
                        done=(step == steps_per_episode - 1),
                        log_prob=log_prob,
                        global_obs=global_obs,
                        cost=c_step
                    )
                
                ep_reward += r_step
                ep_cost += c_step
                
            loss_info = self.coordinator.train_step()
            
            rewards_history.append(ep_reward)
            costs_history.append(ep_cost)
            lagrange_val = loss_info.get("lagrange_mult", 0.05)
            lagrange_history.append(lagrange_val)
            
            if ep % 10 == 0 or ep == episodes:
                logger.info(f"Episódio {ep}/{episodes} - Recompensa Média: {ep_reward:.2f}, Custo Médio: {ep_cost:.4f}")

        elapsed_s = time.time() - t0
        
        # Exporta CSV de convergência
        csv_path = os.path.join(output_dir, "convergence.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["episode", "total_reward", "total_cost", "lagrange_multiplier"])
            for ep_idx, (r, c, l) in enumerate(zip(rewards_history, costs_history, lagrange_history), 1):
                writer.writerow([ep_idx, round(r, 4), round(c, 4), round(l, 4)])
                
        # Salva checkpoints dos modelos (PyTorch .pt ou NumPy .npy)
        actor_ckpt = os.path.join(output_dir, "actor.pt" if PYTORCH_AVAILABLE else "actor_weights.npy")
        critic_ckpt = os.path.join(output_dir, "critic.pt" if PYTORCH_AVAILABLE else "critic_weights.npy")
        
        if PYTORCH_AVAILABLE and torch is not None:
            torch.save(self.coordinator.actor.state_dict(), actor_ckpt)
            torch.save(self.coordinator.critic.state_dict(), critic_ckpt)
        else:
            np.save(actor_ckpt, self.coordinator.agents[0].weights)
            np.save(critic_ckpt, self.coordinator.agents[0].value_weights)

        # Salva manifesto detalhado de treinamento com reprodutibilidade
        manifest = {
            "git_sha": _get_git_sha(),
            "environment": "MAPPO_SMOKE_ENV",
            "publication_eligible": False,
            "seed": seed,
            "episodes": episodes,
            "steps_per_episode": steps_per_episode,
            "training_time_s": round(elapsed_s, 2),
            "final_reward": round(rewards_history[-1], 4),
            "final_cost": round(costs_history[-1], 4),
            "n_agents": self.n_agents,
            "obs_dim": self.obs_dim,
            "action_dim": self.action_dim,
            "hyperparameters": {
                "lr": self.lr,
                "gamma": self.gamma,
                "gae_lambda": self.gae_lambda,
                "cost_limit": self.cost_limit
            },
            "pytorch_available": PYTORCH_AVAILABLE,
            "checkpoints": {
                "actor": os.path.basename(actor_ckpt),
                "critic": os.path.basename(critic_ckpt)
            }
        }
        
        with open(os.path.join(output_dir, "training_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            
        logger.info(f"Treinamento concluído em {elapsed_s:.2f}s. Artefatos salvos em {output_dir}")
        return manifest


