"""
Motor de decisão da CA-RDL: MAPPO sobre o núcleo H-RDL da Fase 1.

``CARDLReasoning`` estende ``src.core.reasoning.Reasoning`` (Fase 1). Para conflitos diretos de
``PRB_QUOTA`` com uma política carregada, consulta o MAPPO; nos demais casos, e sempre que o
MAPPO não decidir dentro do orçamento, usa a arbitragem TVS/EEVS da Fase 1 (reserva
determinística do contrato F1↔F2). O Refinement da Fase 1 continua validando a ação escolhida
no pipeline da ``RDLxApp``, qualquer que seja a origem.

Reserva para a H-RDL quando:
- não há checkpoint, ou o sha256 dele difere do esperado;
- o conflito não é de ``PRB_QUOTA`` (o MAPPO foi treinado só para tetos de PRB por fatia);
- a probabilidade da ação escolhida fica abaixo de ``min_confidence``;
- a inferência passa de ``time_budget_ms``;
- o MAPPO escolhe uma proposta que não está entre as candidatas, ou o no-op;
- a política A1 20002 desliga o MARL.

Cada decisão registra a origem e, na reserva, o motivo (``last_decision``).
"""

import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy, XAppAction
from src.core.reasoning import Reasoning

from cardl.marl.env import ACTION_DIM, OBS_DIM, SLOT_FEATURES, SLOTS


@dataclass
class DecisionRecord:
    source: str                      # "MAPPO" ou "H_RDL"
    reason: str = ""
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    probabilities: List[float] = field(default_factory=list)
    context: Dict[str, float] = field(default_factory=dict)   # grafo de conhecimento da Fase 1


class CARDLReasoning(Reasoning):
    def __init__(self, memory: Any, config: Optional[dict] = None, inter_cell_rules=None,
                 checkpoint_path: Optional[str] = None, expected_sha256: Optional[str] = None,
                 min_confidence: float = 0.5, time_budget_ms: float = 20.0,
                 base_throughput_mbps: float = 151.488):
        super().__init__(memory, config=config, inter_cell_rules=inter_cell_rules)
        self.min_confidence = float(min_confidence)
        self.time_budget_ms = float(time_budget_ms)
        self.base_throughput_mbps = float(base_throughput_mbps)
        self.marl_enabled = True
        self.policy = None
        self.policy_sha256: Optional[str] = None
        self.last_decision: Optional[DecisionRecord] = None
        # Grafo de conhecimento da Fase 1 (o mesmo da RDLxApp); fornece o contexto de cada decisão
        self.knowledge_graph = None
        if checkpoint_path:
            self.load_policy(checkpoint_path, expected_sha256)

    # ---------------------------------------------------------------- modelo
    def load_policy(self, path: str, expected_sha256: Optional[str]) -> None:
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if expected_sha256 and digest != expected_sha256:
            raise ValueError(f"checkpoint {path}: sha256 {digest} difere do esperado {expected_sha256}")
        from cardl.marl.mappo import MAPPO
        self.policy = MAPPO.load(path)
        self.policy_sha256 = digest
        # Aquecimento: a primeira inferência do PyTorch é bem mais lenta e estouraria o orçamento
        mask = np.ones(ACTION_DIM, dtype=np.float32)
        self.policy.probabilities(np.zeros(OBS_DIM, dtype=np.float32), mask)

    def apply_model_policy(self, policy: Dict[str, Any]) -> None:
        """Política A1 20002 (CARDL_Model_Policy): liga/desliga o MARL e ajusta a confiança mínima."""
        self.marl_enabled = bool(policy.get("marl_enabled", True))
        if "min_confidence" in policy:
            self.min_confidence = float(policy["min_confidence"])

    # ---------------------------------------------------------------- decisão
    def _context(self, conflict: ConflictEvent) -> Dict[str, float]:
        if self.knowledge_graph is None or not conflict.involved_xapps:
            return {}
        first = conflict.involved_xapps[0]
        try:
            return self.knowledge_graph.context_features(first.node_id, first.parameter)
        except Exception:
            return {}

    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        resolution = self._resolve(conflict)
        if self.last_decision is not None:
            self.last_decision.context = self._context(conflict)
        return resolution

    def _resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        reason = self._marl_ineligible(conflict)
        if reason is None:
            t0 = time.perf_counter()
            try:
                resolution, record = self._resolve_by_mappo(conflict)
            except Exception as exc:  # falha do modelo nunca derruba a decisão
                resolution, record = None, DecisionRecord("H_RDL", f"erro no MAPPO: {exc}")
            elapsed = (time.perf_counter() - t0) * 1000.0
            if resolution is not None and elapsed <= self.time_budget_ms:
                record.latency_ms = elapsed
                self.last_decision = record
                return resolution
            reason = record.reason if resolution is None else f"orçamento estourado ({elapsed:.1f} ms)"
        self.last_decision = DecisionRecord("H_RDL", reason)
        return super().resolve(conflict)

    def _marl_ineligible(self, conflict: ConflictEvent) -> Optional[str]:
        if self.policy is None:
            return "sem checkpoint"
        if not self.marl_enabled:
            return "MARL desligado por política A1"
        if conflict.conflict_type.name != "DIRECT":
            return f"conflito {conflict.conflict_type.name} fora do escopo do MAPPO"
        if any(a.parameter != "PRB_QUOTA" for a in conflict.involved_xapps):
            return "parâmetro fora do escopo do MAPPO"
        if len(conflict.involved_xapps) > SLOTS:
            return f"mais de {SLOTS} candidatas"
        return None

    def _observation(self, candidates: List[XAppAction]) -> np.ndarray:
        """Observação no formato do ambiente de treino, a partir do KPM e das candidatas."""
        critical = max(c.priority for c in candidates) >= 90
        agent = 0 if critical else 1
        obs = np.zeros(OBS_DIM, dtype=np.float32)
        obs[agent] = 1.0
        node = candidates[0].node_id
        report = self.kpm_by_node.get(node, self.latest_kpm)
        thp = getattr(report, "drb_thp_dl", None) if report is not None and report.node_id == node else None
        demand = min(1.0, float(thp) / self.base_throughput_mbps) if thp else 0.5
        committed = None
        get_committed = getattr(self.memory, "get_committed_action", None)
        if callable(get_committed):
            committed = get_committed(node, "PRB_QUOTA")
        cap = float(committed.value) if committed is not None else 50.0
        base = 2
        obs[base + 0] = demand
        obs[base + 1] = 0.5
        obs[base + 2] = cap / 100.0
        obs[base + 3] = 0.5
        obs[base + 4] = 1.0
        for k, c in enumerate(candidates[:SLOTS]):
            j = base + 5 + k * SLOT_FEATURES
            obs[j:j + SLOT_FEATURES] = (1.0, min(float(c.value), 150.0) / 100.0, c.priority / 100.0,
                                        float(c.xapp_id.casefold().startswith("energy")))
        return obs

    def _resolve_by_mappo(self, conflict: ConflictEvent):
        candidates = list(conflict.involved_xapps)
        obs = self._observation(candidates)
        mask = np.zeros(ACTION_DIM, dtype=np.float32)
        mask[:len(candidates)] = 1.0
        probs = self.policy.probabilities(obs, mask)
        choice = int(np.argmax(probs))
        confidence = float(probs[choice])
        record = DecisionRecord("MAPPO", confidence=confidence, probabilities=[float(p) for p in probs])
        if choice >= len(candidates):
            record.source, record.reason = "H_RDL", "MAPPO escolheu no-op"
            return None, record
        if confidence < self.min_confidence:
            record.source, record.reason = "H_RDL", f"confiança {confidence:.2f} < {self.min_confidence:.2f}"
            return None, record
        winner = candidates[choice]
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.MARL_AGENT,
            winning_actions=[winner],
            modified_value=winner.value,
            confidence=confidence,
            validation_level=0,
        ), record


def selected_checkpoint():
    """Checkpoint e sha256: de ``CARDL_SELECTION`` (seleção por critério, cardl/marl/select.py) ou de
    ``CARDL_CHECKPOINT``. Seleção sem modelo elegível: nenhum checkpoint (só H-RDL)."""
    selection = os.getenv("CARDL_SELECTION")
    if selection:
        import json
        from pathlib import Path
        data = json.loads(Path(selection).read_text(encoding="utf-8"))
        chosen = data.get("selected")
        if not chosen:
            return None, None
        path = Path(chosen["checkpoint"])
        if not path.is_absolute():
            path = Path(selection).resolve().parents[2] / path
        return str(path), chosen["sha256"]
    return os.getenv("CARDL_CHECKPOINT") or None, os.getenv("CARDL_CHECKPOINT_SHA256") or None


def build_cardl_xapp():
    """RDLxApp da Fase 1 com o raciocínio CA-RDL e a política A1 20002."""
    from src.rdl_xapp import RDLxApp

    app = RDLxApp()
    checkpoint, expected = selected_checkpoint()
    reasoning = CARDLReasoning(
        app.memory, config={}, inter_cell_rules=app.inter_cell_rules,
        checkpoint_path=checkpoint,
        expected_sha256=expected,
        min_confidence=float(os.getenv("CARDL_MIN_CONFIDENCE", "0.5")),
        time_budget_ms=float(os.getenv("CARDL_TIME_BUDGET_MS", "20")),
    )
    reasoning.knowledge_graph = app.knowledge_graph
    app.reasoning = reasoning
    # O tipo A1 20002 (CARDL_Model_Policy) é definido na Fase 1, fonte única dos esquemas
    previous = app._apply_a1_policy

    def apply(policy: Dict[str, Any]) -> None:
        previous(policy)
        reasoning.apply_model_policy(policy)

    app.a1_policies._listeners = [apply if cb == previous else cb for cb in app.a1_policies._listeners]
    apply(app.a1_policies.effective_policy())
    return app
