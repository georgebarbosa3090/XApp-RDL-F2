"""
Ambiente da família C (docs/17): conflito indireto handover × teto de PRB no mesmo gNB.

Em cada passo há um conflito: o Traffic Steering (ou o Load Balancer) pede o handover de um UE da célula de
origem para a vizinha, e outra xApp pede um novo teto de PRB na célula de origem. A RDL-N1 (EEVS) mantém as
duas ações em quase todos os casos reais. A política escolhe (``cardl.families.HOLD_ACTIONS``):

- 0: manter as duas; 1: segurar o handover; 2: segurar o teto de PRB; 3: segurar as duas.

Ordem canônica das candidatas: índice 0 = handover, índice 1 = teto de PRB (``order_candidates``).

Resposta da RAN (``ResponseModel``, calibrável com os registros da malha fechada da Fase 1):

- contexto do conflito (carga das duas células, teto atual e pedido, diferença de RSRP destino − origem, SINR
  e satisfação do UE): sorteado entre contextos observados;
- handover aplicado: perda de conexão com probabilidade logística na diferença de RSRP; sem perda, a satisfação
  do UE passa a ``sat_after_ho`` (mediana observada depois do handover, por faixa de carga do destino; sem
  calibração, fica igual à de antes);
- teto aplicado: a satisfação da célula de origem segue a curva teto de PRB → vazão medida no NORI (docs/15);
- as duas aplicadas: termo de interação ``interaction`` somado à satisfação da célula (0 sem calibração).

Recompensa: satisfação do UE e da célula, menos o custo de cada controle aplicado. Custo do CMDP: perda de
conexão do UE depois do handover.

Sem calibração, ``ResponseModel.prior()`` serve só para testes: nele os controles têm custo e quase nenhum
benefício, e segurar tudo sai melhor, o que não representa a rede. Treino e avaliação usam o modelo calibrado
(``fit_response`` e ``contexts_from_transitions``). Resultado neste ambiente não é evidência de RAN
(``publication_eligible: false``).
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import math

import numpy as np

from cardl.families import HOLD_ACTIONS, HOLD_BOTH, HOLD_FIRST, HOLD_SECOND, KEEP_BOTH
from cardl.marl.calibration import CapCurve, load_curve

N_AGENTS = 1
ACTION_DIM = len(HOLD_ACTIONS)
OBS_FEATURES = ("carga_origem", "carga_destino", "teto_atual", "gap_rsrp", "sinr_ue", "satisfacao_ue",
                "teto_pedido", "prioridade_ho", "prioridade_prb", "ho_presente", "prb_presente")
OBS_DIM = len(OBS_FEATURES)
GLOBAL_DIM = OBS_DIM + 2
LOAD_BINS = (0.33, 0.66)        # faixas de carga do destino: baixa, média, alta


@dataclass(frozen=True)
class Context:
    load_src: float          # uso de PRB da origem (0–1)
    load_dst: float          # uso de PRB do destino (0–1)
    cap_src: float           # teto atual da origem (%)
    cap_new: float           # teto pedido (%)
    rsrp_gap_db: float       # RSRP destino − RSRP origem (dB)
    sinr_db: float           # SINR do UE na origem (dB)
    ue_sat: float            # satisfação do UE antes (vazão / oferta, 0–1)
    prio_ho: int = 80
    prio_prb: int = 70
    prb_incumbent: bool = False   # o teto já estava em vigor (aplicado antes): só dá para manter ou segurar o HO


def _load_bin(load: float) -> int:
    return sum(load > b for b in LOAD_BINS)


@dataclass
class ResponseModel:
    contexts: Tuple[Context, ...]
    loss_a: float                       # p_perda = 1 / (1 + exp(−(a + b·gap)))
    loss_b: float
    sat_after_ho: Optional[Tuple[float, float, float]] = None   # satisfação depois, por faixa de carga do destino
    interaction: float = 0.0
    source: str = "prior"
    n_handovers: int = 0

    def p_loss(self, gap_db: float) -> float:
        z = self.loss_a + self.loss_b * gap_db
        return 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, z))))

    @classmethod
    def prior(cls) -> "ResponseModel":
        """Só para testes: contextos de borda simples, perda rara e satisfação mantida depois do handover."""
        ctx = tuple(Context(load_src=ls, load_dst=ld, cap_src=100.0, cap_new=cn, rsrp_gap_db=g, sinr_db=s, ue_sat=u)
                    for ls, ld, cn, g, s, u in [(0.9, 0.3, 90.0, -2.0, 0.0, 0.4), (0.8, 0.5, 80.0, 1.0, 3.0, 0.6),
                                                (0.95, 0.2, 90.0, -3.0, -4.0, 0.3), (0.7, 0.6, 70.0, 2.0, 5.0, 0.8)])
        return cls(contexts=ctx, loss_a=-5.0, loss_b=-0.2, sat_after_ho=None)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["contexts"] = len(self.contexts)
        return d


def fit_response(handovers: Sequence[Dict], contexts: Sequence[Context] = (), l2: float = 1.0) -> ResponseModel:
    """Calibra o modelo com eventos de handover da malha fechada (``extrair_transicoes.py``: campos
    ``rsrp_gap_db``, ``load_dst``, ``sat_before``, ``sat_after``, ``lost``) e contextos de conflitos reais.

    Perda: regressão logística com penalidade L2 na inclinação (Newton amortecido). Satisfação: mediana da
    satisfação depois do handover por faixa de carga do destino, entre os eventos sem perda (absoluta, porque a
    razão depois/antes explode nos UEs quase sem vazão antes); faixa sem eventos usa a mediana geral."""
    ev = [h for h in handovers if h.get("rsrp_gap_db") is not None]
    a, b = -5.0, 0.0
    if ev:
        x = np.array([float(h["rsrp_gap_db"]) for h in ev])
        y = np.array([1.0 if h.get("lost") else 0.0 for h in ev])
        X = np.stack([np.ones_like(x), x], axis=1)
        rate = float(np.clip(y.mean(), 1e-3, 1 - 1e-3))
        w = np.array([math.log(rate / (1 - rate)), 0.0])   # começa na taxa média de perdas

        def objective(v):   # log-verossimilhança negativa + L2 na inclinação
            z = np.clip(X @ v, -50, 50)
            return float(np.sum(np.logaddexp(0.0, z) - y * z) + 0.5 * l2 * v[1] ** 2)

        for _ in range(100):   # Newton amortecido: meio passo enquanto a função objetivo não cair
            p = 1.0 / (1.0 + np.exp(-np.clip(X @ w, -50, 50)))
            g = X.T @ (p - y) + l2 * np.array([0.0, w[1]])
            H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.diag([1e-6, 1.0])
            step = np.linalg.solve(H, g)
            f0, s = objective(w), 1.0
            while objective(w - s * step) > f0 and s > 1e-6:
                s *= 0.5
            w = w - s * step
            if np.max(np.abs(s * step)) < 1e-8:
                break
        a, b = float(w[0]), float(w[1])
    after: List[List[float]] = [[], [], []]
    for h in ev:
        if not h.get("lost") and h.get("sat_after") is not None and h.get("load_dst") is not None:
            after[_load_bin(float(h["load_dst"]))].append(min(1.0, float(h["sat_after"])))
    pooled = [v for r in after for v in r]
    sat = tuple(float(np.median(r)) if r else float(np.median(pooled)) for r in after) if pooled else None
    ctx = tuple(contexts) or ResponseModel.prior().contexts
    return ResponseModel(contexts=ctx, loss_a=a, loss_b=b, sat_after_ho=sat, source="calibrado",
                         n_handovers=len(ev))


@dataclass
class EnvConfig:
    steps_per_episode: int = 64
    w_ue: float = 0.5
    w_cell: float = 0.5
    c_ho: float = 0.05           # custo de um handover aplicado (sinalização, interrupção)
    c_prb: float = 0.02          # custo de mudar o teto
    ues_per_cell: int = 12
    cost_limit: float = 0.05     # fração de passos com perda de conexão aceita pelo CMDP


@dataclass
class StepInfo:
    action: int
    ho_applied: bool
    prb_applied: bool
    lost: bool
    ue_sat: float
    cell_sat: float


class HandoverPrbEnv:
    def __init__(self, model: Optional[ResponseModel] = None, config: Optional[EnvConfig] = None,
                 curve: Optional[CapCurve] = None, seed: int = 0):
        self.model = model or ResponseModel.prior()
        self.config = config or EnvConfig()
        self.curve = curve or load_curve()
        self.rng = np.random.default_rng(seed)
        self.t = 0
        self.ctx: Context = self.model.contexts[0]

    # ------------------------------------------------------------------ dinâmica
    def _sample(self) -> Context:
        return self.model.contexts[int(self.rng.integers(len(self.model.contexts)))]

    def action_mask(self, agent: int = 0) -> np.ndarray:
        return hold_mask(self.ctx.prb_incumbent)

    def observe(self, agent: int = 0) -> np.ndarray:
        return context_observation(self.ctx)

    def global_state(self) -> np.ndarray:
        phase = 2 * np.pi * (self.t / self.config.steps_per_episode)
        return np.concatenate([self.observe(), np.array([np.sin(phase), np.cos(phase)], dtype=np.float32)])

    def _cell_sat(self, cap: float, load: float) -> float:
        return float(min(1.0, self.curve.ratio(cap) / max(load, 1e-3)))

    def reset(self, seed: Optional[int] = None) -> List[np.ndarray]:
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.t = 0
        self.ctx = self._sample()
        return [self.observe()]

    def step(self, actions: List[int]) -> Tuple[List[np.ndarray], float, float, bool, StepInfo]:
        cfg, c = self.config, self.ctx
        action = int(actions[0])
        if self.action_mask()[action] < 0.5:
            action = KEEP_BOTH          # ação mascarada: vale a decisão da RDL-N1
        kept = HOLD_ACTIONS[action]
        ho, prb = 0 in kept, 1 in kept
        lost = bool(ho and self.rng.random() < self.model.p_loss(c.rsrp_gap_db))
        if ho:
            sat = self.model.sat_after_ho
            ue_sat = 0.0 if lost else (c.ue_sat if sat is None else float(sat[_load_bin(c.load_dst)]))
        else:
            ue_sat = c.ue_sat
        load = max(1e-3, c.load_src - (c.load_src / cfg.ues_per_cell if ho else 0.0))
        cell_sat = self._cell_sat(c.cap_new if prb else c.cap_src, load)
        if ho and prb:
            cell_sat = float(min(1.0, max(0.0, cell_sat + self.model.interaction)))
        reward = cfg.w_ue * ue_sat + cfg.w_cell * cell_sat - cfg.c_ho * ho - cfg.c_prb * prb
        cost = 1.0 if lost else 0.0
        info = StepInfo(action=action, ho_applied=ho, prb_applied=prb, lost=lost, ue_sat=ue_sat, cell_sat=cell_sat)
        self.t += 1
        done = self.t >= cfg.steps_per_episode
        if not done:
            self.ctx = self._sample()
        return [self.observe()], float(reward), cost, done, info


def contexts_from_transitions(transitions: Sequence[Dict]) -> Tuple[Context, ...]:
    """Contextos dos conflitos reais da família C (``transicoes.jsonl`` de ``extrair_transicoes.py``): para cada
    resolução da família C, o handover e o teto de PRB envolvidos e o KPM da janela da decisão."""
    out: List[Context] = []
    seen: Dict[str, Dict[str, Dict]] = {}     # propostas já vistas por execução (incumbentes)
    for rec in transitions:
        props = seen.setdefault(rec.get("run_id", ""), {})
        props.update({p["id"]: p for p in rec.get("proposals") or []})
        current = {p["id"] for p in rec.get("proposals") or []}
        cells = {c["gnb"]: c for c in rec.get("cells") or []}
        ues = {u["ue"]: u for u in rec.get("ues") or []}
        offered = {int(k): float(v) for k, v in (rec.get("ue_offered_mbps") or {}).items()}
        for r in rec.get("resolutions") or []:
            if r.get("family") != "C":
                continue
            inv = [props.get(i) for i in r.get("involved") or []]
            ho = next((p for p in inv if p and p.get("parameter") == "HANDOVER"), None)
            prb = next((p for p in inv if p and p.get("parameter") == "PRB_QUOTA"), None)
            if ho is None or prb is None or ho.get("ue") is None:
                continue
            src, dst = cells.get(ho["gnb"]), cells.get(int(round(float(ho["value"]))))
            ue = ues.get(int(ho["ue"]))
            if src is None or dst is None or ue is None:
                continue
            rsrp = ue.get("rsrp_dbm") or {}
            gap = rsrp.get(str(dst["cell_id"]), 0.0) - rsrp.get(str(src["cell_id"]), 0.0) if rsrp else 0.0
            sat = (ue.get("thp_mbps") or 0.0) / offered[int(ho["ue"])] if offered.get(int(ho["ue"])) else 0.5
            out.append(Context(load_src=float(src.get("prb_util") or 0.0), load_dst=float(dst.get("prb_util") or 0.0),
                               cap_src=float(src.get("prb_quota") or 100.0), cap_new=float(prb["value"]),
                               rsrp_gap_db=float(gap), sinr_db=float(ue.get("sinr_db") or 0.0),
                               ue_sat=float(min(1.0, sat)), prio_ho=int(ho.get("priority", 80)),
                               prio_prb=int(prb.get("priority", 70)), prb_incumbent=prb["id"] not in current))
    return tuple(dict.fromkeys(out))   # sem repetição (B3 e N12 da mesma semente dão o mesmo conflito)


# ---------------------------------------------------------------------- observação e ordem
def context_observation(c: Context) -> np.ndarray:
    return np.array([c.load_src, c.load_dst, c.cap_src / 100.0, (np.clip(c.rsrp_gap_db, -20, 20) + 20) / 40.0,
                     (np.clip(c.sinr_db, -10, 30) + 10) / 40.0, c.ue_sat, c.cap_new / 100.0, c.prio_ho / 100.0,
                     c.prio_prb / 100.0, 1.0, 0.0 if c.prb_incumbent else 1.0], dtype=np.float32)


def hold_mask(prb_incumbent: bool) -> np.ndarray:
    """Ações admissíveis: com o teto já em vigor, só manter as duas ou segurar o handover."""
    mask = np.ones(ACTION_DIM, dtype=np.float32)
    if prb_incumbent:
        mask[HOLD_SECOND] = mask[HOLD_BOTH] = 0.0
    return mask


def _prb_incumbent(reasoning, prb) -> bool:
    get_committed = getattr(getattr(reasoning, "memory", None), "get_committed_action", None)
    committed = get_committed(prb.node_id, "PRB_QUOTA") if callable(get_committed) else None
    return committed is not None and getattr(committed, "action_id", None) == prb.action_id


def mask_from_reasoning(reasoning, candidates: list) -> np.ndarray:
    """Máscara de um conflito real: o teto é incumbente quando é a ação confirmada na memória da Fase 1."""
    _, prb = order_candidates(candidates)[:2]
    return hold_mask(_prb_incumbent(reasoning, prb))


def order_candidates(candidates: list) -> list:
    """Ordem canônica da família C: handover primeiro, depois o teto de PRB."""
    return sorted(candidates, key=lambda a: 0 if a.parameter == "HANDOVER" else 1)


def observe_from_reasoning(reasoning, candidates: list) -> np.ndarray:
    """Observação de um conflito real a partir do que o raciocínio da Fase 1 recebe: teto confirmado na memória,
    valores e prioridades das candidatas. Carga das células, RSRP, SINR e satisfação do UE não chegam ao
    raciocínio pelo ``KPMReport`` atual e ficam no valor neutro (0,5), como na família A; levá-los até aqui é
    pré-requisito para usar a política na malha fechada."""
    ho, prb = order_candidates(candidates)[:2]
    committed = None
    get_committed = getattr(getattr(reasoning, "memory", None), "get_committed_action", None)
    if callable(get_committed):
        committed = get_committed(prb.node_id, "PRB_QUOTA")
    cap_src = float(committed.value) if committed is not None else 100.0
    c = Context(load_src=0.5, load_dst=0.5, cap_src=cap_src, cap_new=float(prb.value), rsrp_gap_db=0.0,
                sinr_db=10.0, ue_sat=0.5, prio_ho=int(ho.priority), prio_prb=int(prb.priority),
                prb_incumbent=_prb_incumbent(reasoning, prb))
    return context_observation(c)


# ---------------------------------------------------------------------- referências fixas
def fixed_policy(action: int):
    """Política constante (0 = RDL-N1/EEVS: manter as duas)."""
    return lambda env: [action]


REFERENCE_POLICIES = {"manter_as_duas": KEEP_BOTH, "segurar_ho": HOLD_FIRST, "segurar_prb": HOLD_SECOND,
                      "segurar_as_duas": HOLD_BOTH}
