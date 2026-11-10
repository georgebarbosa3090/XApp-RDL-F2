"""Políticas de referência no ambiente calibrado: B0–B2 e a H-RDL da Fase 1 (B3)."""

from typing import Callable, List

from cardl.marl.env import SLOTS, CalibratedSliceEnv

Policy = Callable[[CalibratedSliceEnv], List[int]]


def _valid(env: CalibratedSliceEnv, agent: int) -> List[int]:
    mask = env.action_mask(agent)
    return [k for k in range(SLOTS) if k < len(env.proposals[agent]) and mask[k] > 0]


def b0_last_arrival(env: CalibratedSliceEnv) -> List[int]:
    """Sem coordenação: vale a última proposta que chega (ordem de geração)."""
    out = []
    for a in range(len(env.proposals)):
        valid = _valid(env, a)
        out.append(valid[-1] if valid else SLOTS)
    return out


def b1_fifo(env: CalibratedSliceEnv) -> List[int]:
    out = []
    for a in range(len(env.proposals)):
        valid = _valid(env, a)
        out.append(valid[0] if valid else SLOTS)
    return out


def b2_priority(env: CalibratedSliceEnv) -> List[int]:
    out = []
    for a in range(len(env.proposals)):
        valid = _valid(env, a)
        out.append(max(valid, key=lambda k: env.proposals[a][k].priority) if valid else SLOTS)
    return out


def b3_hrdl(env: CalibratedSliceEnv) -> List[int]:
    """H-RDL: TVS da Fase 1 (``Reasoning.resolve``) sobre o conflito direto de cada alvo."""
    from src.conflict_types import ConflictEvent, ConflictSeverity, ConflictType, XAppAction
    from src.core.reasoning import Reasoning
    from src.infrastructure.memory_module import MemoryModule

    reasoning = getattr(b3_hrdl, "_reasoning", None)
    if reasoning is None:
        reasoning = Reasoning(MemoryModule())
        b3_hrdl._reasoning = reasoning  # type: ignore[attr-defined]
    out = []
    for a in range(len(env.proposals)):
        valid = _valid(env, a)
        if not valid:
            out.append(SLOTS)
            continue
        if len(valid) == 1:
            out.append(valid[0])
            continue
        actions = [XAppAction(xapp_id=env.proposals[a][k].xapp_id, node_id=f"slice_{a}", parameter="PRB_QUOTA",
                              value=float(env.proposals[a][k].value), priority=int(env.proposals[a][k].priority),
                              action_id=str(k)) for k in valid]
        resolution = reasoning.resolve(ConflictEvent(ConflictType.DIRECT, ConflictSeverity.HIGH, actions))
        out.append(int(resolution.winning_actions[0].action_id) if resolution.winning_actions else SLOTS)
    return out


BASELINES = {"B0": b0_last_arrival, "B1": b1_fifo, "B2": b2_priority, "B3": b3_hrdl}
