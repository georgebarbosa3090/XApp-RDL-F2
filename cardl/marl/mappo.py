"""
MAPPO com restrição (CMDP, multiplicador de Lagrange) e mascaramento de ações.

- Ator compartilhado entre os agentes (a identidade do agente vai na observação).
- Crítico centralizado sobre o estado global (CTDE).
- Custo do CMDP: violação do SLA da fatia crítica; o multiplicador λ sobe enquanto o custo
  médio do episódio passa do limite e desce quando fica abaixo (ascensão dual projetada).
- Ações mascaradas (rejeitadas pelo Safety Guard da Fase 1) recebem logit −1e9.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn

from cardl.marl.env import ACTION_DIM, GLOBAL_DIM, N_AGENTS, OBS_DIM


@dataclass
class MappoConfig:
    hidden: int = 64
    lr_actor: float = 3e-4
    lr_critic: float = 1e-3
    gamma: float = 0.97
    gae_lambda: float = 0.95
    clip: float = 0.2
    epochs: int = 4
    minibatch: int = 256
    entropy: float = 0.01
    cost_limit: float = 0.05
    lr_lagrange: float = 0.05
    lagrange_init: float = 0.5


class Actor(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(OBS_DIM, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(),
                                 nn.Linear(hidden, ACTION_DIM))

    def dist(self, obs: torch.Tensor, mask: torch.Tensor) -> torch.distributions.Categorical:
        logits = self.net(obs)
        logits = torch.where(mask > 0.5, logits, torch.full_like(logits, -1e9))
        return torch.distributions.Categorical(logits=logits)


class Critic(nn.Module):
    def __init__(self, hidden: int, outputs: int = 2):  # valor da recompensa e do custo
        super().__init__()
        self.net = nn.Sequential(nn.Linear(GLOBAL_DIM, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh(),
                                 nn.Linear(hidden, outputs))

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state)


class MAPPO:
    def __init__(self, config: MappoConfig, seed: int = 0):
        torch.manual_seed(seed)
        self.cfg = config
        self.actor = Actor(config.hidden)
        self.critic = Critic(config.hidden)
        self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=config.lr_actor)
        self.opt_critic = torch.optim.Adam(self.critic.parameters(), lr=config.lr_critic)
        self.lagrange = float(config.lagrange_init)

    # ---------------------------------------------------------------- inferência
    @torch.no_grad()
    def act(self, obs: List[np.ndarray], masks: List[np.ndarray], greedy: bool = False) -> Tuple[List[int], List[float]]:
        o = torch.as_tensor(np.stack(obs), dtype=torch.float32)
        m = torch.as_tensor(np.stack(masks), dtype=torch.float32)
        d = self.actor.dist(o, m)
        a = torch.argmax(d.probs, dim=-1) if greedy else d.sample()
        return a.tolist(), d.log_prob(a).tolist()

    @torch.no_grad()
    def probabilities(self, obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
        d = self.actor.dist(torch.as_tensor(obs[None], dtype=torch.float32), torch.as_tensor(mask[None], dtype=torch.float32))
        return d.probs[0].numpy()

    # ---------------------------------------------------------------- treino
    def update(self, batch: Dict[str, np.ndarray]) -> Dict[str, float]:
        cfg = self.cfg
        T = batch["reward"].shape[0]
        with torch.no_grad():
            values = self.critic(torch.as_tensor(batch["state"], dtype=torch.float32)).numpy()
            next_values = self.critic(torch.as_tensor(batch["next_state"], dtype=torch.float32)).numpy()
        adv = np.zeros((T, 2), dtype=np.float32)
        last = np.zeros(2, dtype=np.float32)
        signals = np.stack([batch["reward"], batch["cost"]], axis=1)
        for t in reversed(range(T)):
            nonterminal = 1.0 - batch["done"][t]
            delta = signals[t] + cfg.gamma * next_values[t] * nonterminal - values[t]
            last = delta + cfg.gamma * cfg.gae_lambda * nonterminal * last
            adv[t] = last
        returns = adv + values
        # Vantagem lagrangiana: recompensa menos λ × custo
        lag_adv = adv[:, 0] - self.lagrange * adv[:, 1]
        lag_adv = (lag_adv - lag_adv.mean()) / (lag_adv.std() + 1e-8)

        obs = torch.as_tensor(batch["obs"], dtype=torch.float32)          # T × N × OBS
        masks = torch.as_tensor(batch["mask"], dtype=torch.float32)
        actions = torch.as_tensor(batch["action"], dtype=torch.int64)
        old_logp = torch.as_tensor(batch["logp"], dtype=torch.float32)
        state = torch.as_tensor(batch["state"], dtype=torch.float32)
        ret = torch.as_tensor(returns, dtype=torch.float32)
        adv_t = torch.as_tensor(lag_adv, dtype=torch.float32)

        idx = np.arange(T)
        stats = {"actor_loss": 0.0, "critic_loss": 0.0, "entropy": 0.0}
        for _ in range(cfg.epochs):
            np.random.shuffle(idx)
            for start in range(0, T, cfg.minibatch):
                mb = torch.as_tensor(idx[start:start + cfg.minibatch])
                d = self.actor.dist(obs[mb].reshape(-1, OBS_DIM), masks[mb].reshape(-1, masks.shape[-1]))
                logp = d.log_prob(actions[mb].reshape(-1)).reshape(-1, N_AGENTS)
                ratio = torch.exp(logp - old_logp[mb])
                a = adv_t[mb].unsqueeze(1)
                loss_actor = -torch.min(ratio * a, torch.clamp(ratio, 1 - cfg.clip, 1 + cfg.clip) * a).mean()
                ent = d.entropy().mean()
                self.opt_actor.zero_grad()
                (loss_actor - cfg.entropy * ent).backward()
                nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
                self.opt_actor.step()

                loss_critic = ((self.critic(state[mb]) - ret[mb]) ** 2).mean()
                self.opt_critic.zero_grad()
                loss_critic.backward()
                nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
                self.opt_critic.step()
                stats["actor_loss"] = float(loss_actor.detach())
                stats["critic_loss"] = float(loss_critic.detach())
                stats["entropy"] = float(ent.detach())

        # Ascensão dual: custo médio por passo contra o limite
        mean_cost = float(batch["cost"].mean())
        self.lagrange = max(0.0, self.lagrange + cfg.lr_lagrange * (mean_cost - cfg.cost_limit))
        stats["lagrange"] = self.lagrange
        stats["mean_cost"] = mean_cost
        return stats

    # ---------------------------------------------------------------- persistência
    def save(self, path: str, extra: Dict) -> None:
        torch.save({"actor": self.actor.state_dict(), "critic": self.critic.state_dict(),
                    "lagrange": self.lagrange, "config": asdict(self.cfg),
                    "dims": {"obs": OBS_DIM, "global": GLOBAL_DIM, "actions": ACTION_DIM, "agents": N_AGENTS},
                    **extra}, path)

    @classmethod
    def load(cls, path: str) -> "MAPPO":
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        dims = ckpt["dims"]
        if (dims["obs"], dims["global"], dims["actions"], dims["agents"]) != (OBS_DIM, GLOBAL_DIM, ACTION_DIM, N_AGENTS):
            raise ValueError(f"checkpoint incompatível com o ambiente atual: {dims}")
        agent = cls(MappoConfig(**ckpt["config"]))
        agent.actor.load_state_dict(ckpt["actor"])
        agent.critic.load_state_dict(ckpt["critic"])
        agent.lagrange = float(ckpt["lagrange"])
        return agent
