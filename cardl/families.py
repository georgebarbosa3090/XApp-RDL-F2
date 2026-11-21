"""
Famílias de conflito da RDL-N2 (docs/17) e registro de políticas por família.

Cada conflito é classificado pelo tipo (Fase 1: DIRECT, INDIRECT, INTER_CELL) e pelos parâmetros das ações:

- ``A``: direto, só teto de PRB (o caso do ambiente calibrado do docs/15);
- ``B``: indireto, teto de PRB × potência de TX;
- ``C``: indireto, handover × teto de PRB;
- ``D``: indireto ou entre células, estado de célula ou potência × handover, ou estado de célula × potência;
- ``P``: entre células, só handovers (ping-pong; decidido pela proteção da Fase 1 antes do raciocínio).

Conflitos com uma xApp de teste de segurança (Rogue) ou com um evento agendado do cenário (``fault_injector``)
não pertencem a nenhuma família (comparativo das xApps originais e próprias, seção 4.7; docs/17 §1): ficam com a
RDL-N1 e fora das contagens e do dataset das famílias.

Nas famílias B, C e D a política escolhe que ações manter (``HOLD_ACTIONS``): manter todas, segurar uma ou
segurar todas. A RDL-N2 só decide uma família se houver política registrada para ela; sem política, o conflito
volta à RDL-N1 com o mesmo motivo de antes (o comportamento atual não muda).
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

A, B, C, D, P = "A", "B", "C", "D", "P"
FAMILIES = (A, B, C, D, P)
DESCRIPTION = {
    A: "direto, teto de PRB",
    B: "indireto, teto de PRB × potência",
    C: "indireto, handover × teto de PRB",
    D: "energia × mobilidade (estado de célula, potência, handover)",
    P: "ping-pong de handover entre células",
}

# Ações de "segurar" para conflitos de duas candidatas (índice -> candidatas mantidas)
KEEP_BOTH, HOLD_FIRST, HOLD_SECOND, HOLD_BOTH = 0, 1, 2, 3
HOLD_ACTIONS = {KEEP_BOTH: (0, 1), HOLD_FIRST: (1,), HOLD_SECOND: (0,), HOLD_BOTH: ()}

_ENERGY_MOBILITY = {"CELL_STATE", "TX_POWER", "HANDOVER"}

# xApp de teste de segurança e evento agendado do cenário: não são xApps legítimas em conflito
TEST_XAPPS = frozenset({"rogue_xapp", "fault_injector"})


def xapp_of_action_id(action_id: str) -> str:
    """``xapp_id`` de um id de proposta da malha fechada (``<xapp_id>-g<gnb>-<parâmetro>-<t>[-<seq>]``)."""
    return str(action_id or "").split("-", 1)[0]


def involves_test_xapp(xapp_ids: Iterable[str]) -> bool:
    return any(str(x) in TEST_XAPPS for x in xapp_ids)


def classify_params(conflict_type: str, parameters: Iterable[str], xapp_ids: Iterable[str] = ()) -> Optional[str]:
    """Família de um conflito pelo tipo (nome do ``ConflictType``) e pelos parâmetros das ações. Com uma xApp de
    teste ou evento entre as envolvidas (``xapp_ids``), nenhuma família."""
    if involves_test_xapp(xapp_ids):
        return None
    params = {str(p) for p in parameters if p}
    kind = str(conflict_type).upper()
    if not params:
        return None
    if kind == "DIRECT" and params == {"PRB_QUOTA"}:
        return A
    if kind == "INTER_CELL" and params == {"HANDOVER"}:
        return P
    if kind == "INDIRECT" and params == {"PRB_QUOTA", "TX_POWER"}:
        return B
    if kind == "INDIRECT" and params == {"HANDOVER", "PRB_QUOTA"}:
        return C
    if kind in ("INDIRECT", "INTER_CELL") and params <= _ENERGY_MOBILITY and (
            "CELL_STATE" in params or params == {"HANDOVER", "TX_POWER"}):
        return D
    return None


def classify(conflict: Any) -> Optional[str]:
    """Família de um ``ConflictEvent`` da Fase 1."""
    kind = getattr(getattr(conflict, "conflict_type", None), "name", "")
    actions = list(getattr(conflict, "involved_xapps", []) or [])
    return classify_params(kind, (a.parameter for a in actions), (getattr(a, "xapp_id", "") for a in actions))


@dataclass
class FamilyPolicy:
    """Política de uma família: modelo (``MAPPO``), sha256 conferido na carga, função de observação e número
    máximo de candidatas. ``observe(reasoning, candidates) -> np.ndarray`` monta a observação no formato do
    ambiente de treino da família."""
    family: str
    model: Any
    sha256: Optional[str]
    observe: Any
    max_candidates: int = 2
    order: Any = None     # ``order(candidates) -> list``: ordem canônica das candidatas (a de HOLD_ACTIONS)
    mask: Any = None      # ``mask(reasoning, candidates) -> np.ndarray``: ações admissíveis (padrão: todas)

    def ordered(self, candidates: list) -> list:
        return list(self.order(candidates)) if self.order is not None else list(candidates)


class FamilyRegistry:
    """Políticas registradas por família e famílias ligadas pela A1 20002 (``None``: todas as registradas)."""

    def __init__(self) -> None:
        self.policies: Dict[str, FamilyPolicy] = {}
        self.enabled: Optional[set] = None

    def register(self, policy: FamilyPolicy) -> None:
        if policy.family not in FAMILIES or policy.family in (A, P):
            raise ValueError(f"família {policy.family!r} não aceita política por registro (A usa o checkpoint "
                             "selecionado do docs/15; P fica com a proteção da Fase 1)")
        self.policies[policy.family] = policy

    def get(self, family: Optional[str]) -> Optional[FamilyPolicy]:
        if family is None or family not in self.policies:
            return None
        if self.enabled is not None and family not in self.enabled:
            return None
        return self.policies[family]

    def apply_model_policy(self, policy: Dict[str, Any]) -> None:
        """Campo opcional ``families`` da A1 20002: lista de famílias ligadas. Ausente, ficam todas as
        registradas. (O esquema da A1 20002 é definido na Fase 1; o campo precisa ser incluído lá.)"""
        if "families" in policy:
            fams = policy.get("families")
            self.enabled = None if fams is None else {str(f) for f in fams}
