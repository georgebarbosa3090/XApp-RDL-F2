"""
RDL hierárquica: RDL-N1 e RDL-N2 juntas (decisão do autor de 2026-11-20).

Cada conflito passa por um roteador antes da arbitragem:

- **baixa complexidade → RDL-N1** (TVS/EEVS da Fase 1, sem passar pelo MAPPO);
- **alta complexidade → RDL-N2** (``CARDLReasoning``: MAPPO com restrições quando o conflito está no escopo do
  modelo; fora dele, ou sem checkpoint, confiança ou orçamento, a reserva é a própria RDL-N1, com o motivo).

Complexidade alta quando **qualquer** das condições vale:

1. índice C(c, s) da Fase 1 (``Reasoning.compute_complexity``) ≥ ``complexity_threshold`` (padrão 1,8: conflito
   indireto ou entre células, mais de um parâmetro, ou 5 ou mais propostas num conflito direto);
2. o grafo de conhecimento da Fase 1 registra pelo menos ``kg_recent_threshold`` conflito(s) anterior(es) no
   mesmo alvo (célula e parâmetro) nos últimos ``kg_lookback_s`` segundos (disputa recorrente, oscilação).

O tempo do critério 2 é o relógio do roteador (``clock``): na malha fechada, o relógio simulado do executor.
O roteador grava esse instante no nó do conflito (atributo ``t_route``) e só conta conflitos que já passaram
por ele, porque o ``detected_at`` da Fase 1 é tempo de parede.

Cada decisão deixa um traço (``trace_last()``): nível, C(c, s), conflitos recentes no grafo, motivo do
roteamento, origem da decisão (MAPPO ou RDL-N1) e, na reserva, o motivo.
"""

import os
import time
from typing import Any, Callable, Dict, Optional, Tuple

from src.conflict_types import ConflictEvent, ResolutionAction
from src.core.reasoning import Reasoning

from cardl.engine import CARDLReasoning, DecisionRecord, install_reasoning, selected_checkpoint

LOW, HIGH = "N1", "N2"


class HierarchicalReasoning(CARDLReasoning):
    def __init__(self, memory: Any, config: Optional[dict] = None, inter_cell_rules=None,
                 complexity_threshold: float = 1.8, kg_recent_threshold: int = 1, kg_lookback_s: float = 5.0,
                 clock: Optional[Callable[[], float]] = None, **cardl_kwargs):
        super().__init__(memory, config=config, inter_cell_rules=inter_cell_rules, **cardl_kwargs)
        self.complexity_threshold = float(complexity_threshold)
        self.kg_recent_threshold = int(kg_recent_threshold)
        self.kg_lookback_s = float(kg_lookback_s)
        self.clock: Callable[[], float] = clock or time.time
        self.route_counts: Dict[str, int] = {LOW: 0, HIGH: 0}
        self._last_trace: Dict[str, Any] = {}

    # ---------------------------------------------------------------- roteamento
    def _kg_recent(self, conflict: ConflictEvent, now: float) -> int:
        """Conflitos anteriores já roteados no mesmo alvo (célula e parâmetro) dentro da janela do grafo."""
        kg = self.knowledge_graph
        if kg is None or not conflict.involved_xapps:
            return 0
        own = f"conflict:{conflict.conflict_id}"
        found = set()
        for node, parameter in {(a.node_id, a.parameter) for a in conflict.involved_xapps}:
            try:
                ids = kg.conflicts_on(node, parameter)
            except Exception:
                continue
            for cid in ids:
                n = kg.node(cid)
                t = n.attrs.get("t_route") if n is not None else None
                if cid != own and t is not None and now - self.kg_lookback_s <= t <= now:
                    found.add(cid)
        return len(found)

    def route(self, conflict: ConflictEvent) -> Tuple[str, Dict[str, Any]]:
        now = float(self.clock())
        complexity = self.compute_complexity(conflict)
        recent = self._kg_recent(conflict, now)
        reasons = []
        if complexity >= self.complexity_threshold:
            reasons.append(f"C={complexity:.2f} >= {self.complexity_threshold:.2f}")
        if recent >= self.kg_recent_threshold:
            reasons.append(f"grafo: {recent} conflito(s) no alvo em {self.kg_lookback_s:g} s")
        level = HIGH if reasons else LOW
        if self.knowledge_graph is not None:
            try:   # marca o conflito com o instante do roteamento (relógio do roteador) e o nível
                self.knowledge_graph.add_node(f"conflict:{conflict.conflict_id}", "conflict",
                                              t_route=now, level=level, complexity=complexity)
            except Exception:
                pass
        return level, {"level": level, "complexity": complexity, "kg_recent_conflicts": recent,
                       "route_reason": "; ".join(reasons) or "baixa complexidade", "t_route": now}

    # ---------------------------------------------------------------- decisão
    def resolve(self, conflict: ConflictEvent) -> ResolutionAction:
        level, info = self.route(conflict)
        self.route_counts[level] += 1
        if level == LOW:
            resolution = Reasoning.resolve(self, conflict)
            self.last_decision = DecisionRecord("H_RDL", "baixa complexidade (RDL-N1)",
                                                context=self._context(conflict))
        else:
            resolution = CARDLReasoning.resolve(self, conflict)
        record = self.last_decision
        self._last_trace = {**info, "source": record.source if record else "H_RDL",
                            "fallback_reason": record.reason if record and level == HIGH and record.source != "MAPPO" else "",
                            "confidence": record.confidence if record else None,
                            "mappo_latency_ms": record.latency_ms if record else None}
        return resolution

    def trace_last(self) -> Dict[str, Any]:
        """Traço da última decisão (o executor da Fase 1 o junta ao registro da janela)."""
        return dict(self._last_trace)


def attach_hierarchical(app: Any, clock: Optional[Callable[[], float]] = None) -> HierarchicalReasoning:
    """Troca o raciocínio de uma ``RDLxApp`` da Fase 1 pelo hierárquico (N1 + N2) e liga a política A1 20002.

    Parâmetros por ambiente: ``CARDL_SELECTION`` ou ``CARDL_CHECKPOINT``/``CARDL_CHECKPOINT_SHA256`` (modelo),
    ``CARDL_MIN_CONFIDENCE``, ``CARDL_TIME_BUDGET_MS``, ``RDL_COMPLEXITY_THRESHOLD`` (1,8),
    ``RDL_KG_RECENT_THRESHOLD`` (1) e ``RDL_KG_LOOKBACK_S`` (5).
    """
    checkpoint, expected = selected_checkpoint()
    reasoning = HierarchicalReasoning(
        app.memory, config={}, inter_cell_rules=app.inter_cell_rules,
        complexity_threshold=float(os.getenv("RDL_COMPLEXITY_THRESHOLD", "1.8")),
        kg_recent_threshold=int(os.getenv("RDL_KG_RECENT_THRESHOLD", "1")),
        kg_lookback_s=float(os.getenv("RDL_KG_LOOKBACK_S", "5")),
        clock=clock,
        checkpoint_path=checkpoint, expected_sha256=expected,
        min_confidence=float(os.getenv("CARDL_MIN_CONFIDENCE", "0.5")),
        time_budget_ms=float(os.getenv("CARDL_TIME_BUDGET_MS", "20")),
    )
    install_reasoning(app, reasoning)
    return reasoning
