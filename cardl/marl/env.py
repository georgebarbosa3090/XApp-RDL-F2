"""
Ambiente de treino da RDL-N2 calibrado com medições da Fase 1 (CMDP multiagente).

Um passo é uma janela de decisão. Há dois alvos (agentes), o teto de PRB de cada fatia:

- fatia 0, crítica (ex.: câmeras da App1-Vigilância do GreenRAN): SLA de vazão; sua violação
  é o custo do CMDP;
- fatia 1, eMBB / melhor esforço.

Em cada janela, xApps propõem tetos para cada fatia (conflito direto por alvo):
- RANSlicer (prioridade 90 na crítica, 70 na outra): o teto que atende a demanda, com margem;
- EnergySaver (prioridade 65): um teto menor, para desativar PRBs (economia de PRBs ativos,
  proposta GreenRAN, seção 6.3);
- Rogue (prioridade 50, ocasional): teto fora dos limites, que o Safety Guard da Fase 1 rejeita.

Cada agente escolhe uma proposta do seu alvo ou mantém o teto atual (no-op). Ações
rejeitadas pelo Safety Guard da Fase 1 (``Refinement.check_bounds``) são mascaradas.

Resposta da RAN: vazão servida = base × razão(teto), com a curva medida no NORI
(``calibration.py``), limitada pela demanda. Energia: proporcional aos PRBs ativos
(soma dos tetos, até 100 %).

Este ambiente é um substituto calibrado: os resultados dele não são evidência de RAN
(``publication_eligible: false``); servem para treinar e comparar políticas antes da
validação pré-registrada com E2 real no NORI.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from cardl.marl.calibration import CapCurve, load_curve

N_AGENTS = 2
SLOTS = 3                      # propostas por alvo (RANSlicer, EnergySaver, Rogue)
ACTION_DIM = SLOTS + 1         # + no-op
SLOT_FEATURES = 4              # presente, valor/100, prioridade/100, vem de xApp de energia
OBS_DIM = N_AGENTS + 5 + SLOTS * SLOT_FEATURES
GLOBAL_DIM = N_AGENTS * OBS_DIM + 2


@dataclass
class EnvConfig:
    steps_per_episode: int = 96            # 96 janelas = um "dia" em passos de 15 min de perfil
    critical_sla: float = 0.95             # fração mínima da demanda crítica atendida
    w_sla: float = 0.6
    w_energy: float = 0.3
    w_stability: float = 0.1
    critical_weight: float = 0.6
    slicer_margin: float = 1.10
    energy_factor: float = 0.6
    rogue_probability: float = 0.1
    demand_noise: float = 0.05


@dataclass
class Proposal:
    xapp_id: str
    value: float
    priority: int
    is_energy: bool


@dataclass
class StepInfo:
    caps: Tuple[float, float]
    satisfaction: Tuple[float, float]
    energy_ratio: float
    cost: float
    chosen: List[Optional[Proposal]] = field(default_factory=list)


class CalibratedSliceEnv:
    def __init__(self, config: Optional[EnvConfig] = None, curve: Optional[CapCurve] = None,
                 safety_guard=None, seed: int = 0):
        self.config = config or EnvConfig()
        self.curve = curve or load_curve()
        self.saturation = self.curve.saturation_cap_pct()
        self.rng = np.random.default_rng(seed)
        self.safety_guard = safety_guard or _default_safety_guard()
        self.t = 0
        self.caps = [50.0, 50.0]
        self.demand = [0.5, 0.5]
        self.proposals: List[List[Proposal]] = [[], []]

    # ------------------------------------------------------------------ dinâmica
    def _demand_profile(self, t: int) -> Tuple[float, float]:
        """Perfil diário: baixa demanda à noite (oportunidade de economia), pico no dia."""
        phase = 2 * np.pi * (t / self.config.steps_per_episode)
        day = 0.5 - 0.5 * np.cos(phase)              # 0 à meia-noite, 1 ao meio-dia
        critical = 0.15 + 0.55 * day
        embb = 0.10 + 0.70 * day
        noise = self.rng.normal(0.0, self.config.demand_noise, 2)
        return float(np.clip(critical + noise[0], 0.05, 1.0)), float(np.clip(embb + noise[1], 0.05, 1.0))

    def needed_cap(self, demand_fraction: float) -> float:
        """Menor teto (%) cuja vazão atende a demanda (fração da base), pela curva."""
        lo, hi = 0.0, 100.0
        for _ in range(30):
            mid = (lo + hi) / 2
            if self.curve.ratio(mid) >= demand_fraction:
                hi = mid
            else:
                lo = mid
        return hi

    def _make_proposals(self) -> None:
        cfg = self.config
        self.proposals = []
        for s in range(N_AGENTS):
            need = self.needed_cap(self.demand[s])
            slicer = float(np.clip(round(need * cfg.slicer_margin), 5, 100))
            energy = float(np.clip(round(min(self.caps[s], need) * cfg.energy_factor), 5, 100))
            props = [Proposal("ranslicer", slicer, 90 if s == 0 else 70, False),
                     Proposal("energysaver", energy, 65, True)]
            if self.rng.random() < cfg.rogue_probability:
                props.append(Proposal("rogue", 150.0, 50, False))
            self.proposals.append(props)

    def action_mask(self, agent: int) -> np.ndarray:
        mask = np.zeros(ACTION_DIM, dtype=np.float32)
        for k, p in enumerate(self.proposals[agent][:SLOTS]):
            if self.safety_guard(agent, p):
                mask[k] = 1.0
        mask[SLOTS] = 1.0  # no-op sempre admissível
        return mask

    # ------------------------------------------------------------------ observação
    def observe(self, agent: int) -> np.ndarray:
        other = 1 - agent
        obs = np.zeros(OBS_DIM, dtype=np.float32)
        obs[agent] = 1.0
        base = N_AGENTS
        obs[base + 0] = self.demand[agent]
        obs[base + 1] = self.demand[other]
        obs[base + 2] = self.caps[agent] / 100.0
        obs[base + 3] = self.caps[other] / 100.0
        obs[base + 4] = self._satisfaction(agent, self.caps[agent])
        for k, p in enumerate(self.proposals[agent][:SLOTS]):
            j = base + 5 + k * SLOT_FEATURES
            obs[j:j + SLOT_FEATURES] = (1.0, min(p.value, 150.0) / 100.0, p.priority / 100.0, float(p.is_energy))
        return obs

    def global_state(self) -> np.ndarray:
        phase = 2 * np.pi * (self.t / self.config.steps_per_episode)
        return np.concatenate([self.observe(a) for a in range(N_AGENTS)] +
                              [np.array([np.sin(phase), np.cos(phase)], dtype=np.float32)])

    def _satisfaction(self, s: int, cap: float) -> float:
        return float(min(1.0, self.curve.ratio(cap) / max(self.demand[s], 1e-6)))

    # ------------------------------------------------------------------ API
    def reset(self, seed: Optional[int] = None) -> List[np.ndarray]:
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.t = 0
        self.caps = [50.0, 50.0]
        self.demand = list(self._demand_profile(0))
        self._make_proposals()
        return [self.observe(a) for a in range(N_AGENTS)]

    def step(self, actions: List[int]) -> Tuple[List[np.ndarray], float, float, bool, StepInfo]:
        cfg = self.config
        old = list(self.caps)
        chosen: List[Optional[Proposal]] = []
        for s, a in enumerate(actions):
            mask = self.action_mask(s)
            if a < SLOTS and a < len(self.proposals[s]) and mask[a] > 0:
                self.caps[s] = self.proposals[s][a].value
                chosen.append(self.proposals[s][a])
            else:
                chosen.append(None)
        sat = tuple(self._satisfaction(s, self.caps[s]) for s in range(N_AGENTS))
        energy_ratio = min(100.0, self.caps[0] + self.caps[1]) / 100.0
        changes = sum(1 for s in range(N_AGENTS) if self.caps[s] != old[s])
        reward = (cfg.w_sla * (cfg.critical_weight * sat[0] + (1 - cfg.critical_weight) * sat[1])
                  + cfg.w_energy * (1.0 - energy_ratio)
                  - cfg.w_stability * changes / N_AGENTS)
        cost = 1.0 if sat[0] < cfg.critical_sla else 0.0
        info = StepInfo(caps=tuple(self.caps), satisfaction=sat, energy_ratio=energy_ratio, cost=cost, chosen=chosen)

        self.t += 1
        done = self.t >= cfg.steps_per_episode
        if not done:
            self.demand = list(self._demand_profile(self.t))
            self._make_proposals()
        return [self.observe(a) for a in range(N_AGENTS)], float(reward), cost, done, info


_GUARD = None


def _default_safety_guard():
    """Safety Guard da Fase 1 (Refinement.check_bounds) sobre a proposta como PRB_QUOTA (instância única)."""
    global _GUARD
    if _GUARD is not None:
        return _GUARD
    from src.conflict_types import XAppAction
    from src.core.refinement import Refinement
    from src.infrastructure.memory_module import MemoryModule

    guard = Refinement(MemoryModule())

    def check(agent: int, proposal: Proposal) -> bool:
        action = XAppAction(xapp_id=proposal.xapp_id, node_id=f"slice_{agent}", parameter="PRB_QUOTA",
                            value=float(proposal.value), priority=int(proposal.priority))
        return guard.check_bounds(action)[0]

    _GUARD = check
    return check
