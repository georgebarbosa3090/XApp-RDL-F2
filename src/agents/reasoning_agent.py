from typing import List, Tuple, Dict, Optional, Any
from src.conflict_types import ConflictEvent, ResolutionAction, ResolutionStrategy, XAppAction, ConflictType
from src.infrastructure.sdl_repository import SdlRepository
from src.agents.marl.mappo_agent import MAPPOCoordinator
import math
import itertools
import time

class ReasoningAgent:
    """
    Motor de Raciocínio Cognitivo Hierárquico Escalonado (xApp-RDL Fase 2 / Fase 3).
    Escalona a tomada de decisão entre 3 níveis de maturidade conforme a complexidade do conflito:
      Nível 1 (C(c, s) <= tau1): Heurística Rápida / Tabela de Prioridades (H-RDL) - < 1ms
      Nível 2A (tau1 < C(c, s) <= tau2): Utilidade Contextual / NDT Proativo (TVS/EEVS/COMIX)
      Nível 2B (C(c, s) > tau2): Coordenação Multiagente Aprendida (MAPPO com CTDE)
    """
    def __init__(self, memory: SdlRepository, config: Optional[dict] = None):
        self.memory = memory
        self.config = config or {}
        
        # Limiares de complexidade para escalonamento
        self.tau1 = float(self.config.get("tau1", 1.2))
        self.tau2 = float(self.config.get("tau2", 2.4))
        
        # Lockout cooling window (5 segundos anti-flapping estilo 6G-SMART MLO)
        self.cooling_window_s = float(self.config.get("cooling_window_s", 5.0))
        self.cooling_lockout: Dict[str, float] = {}
        
        # Coordenador MAPPO para resolução de Nível 2B
        self.mappo = MAPPOCoordinator(n_agents=2, obs_dim=10, action_dim=5, config=self.config)

    def estimate_complexity(self, conflict: ConflictEvent, kpm_state: Optional[Dict[str, float]] = None) -> float:
        """
        Calcula a métrica de complexidade C(c, s) para roteamento hierárquico escalonado.
        Fatores: tipo de conflito, número de xApps envolvidas, KPIs afetados e delta de prioridade.
        """
        type_factor = 0.5 if conflict.conflict_type == ConflictType.DIRECT else 1.2
        num_apps_factor = float(len(conflict.involved_xapps)) * 0.4
        kpis_factor = float(len(conflict.affected_kpis)) * 0.3
        
        prio_diff = 0.0
        if len(conflict.involved_xapps) >= 2:
            prio_diff = abs(conflict.involved_xapps[0].priority - conflict.involved_xapps[1].priority)
        prio_factor = max(0.0, 1.0 - (prio_diff / 50.0)) # Prioridades parecidas aumentam complexidade
        
        state_degradation = 0.0
        if kpm_state and kpm_state.get("QoS.FlowDelay", 0.0) > 20.0:
            state_degradation = 0.5
            
        c_score = type_factor + num_apps_factor + kpis_factor + prio_factor + state_degradation
        return float(c_score)

    def is_in_lockout(self, action: XAppAction, now_ts: float) -> bool:
        """Verifica se a ação da xApp está sob janela de resfriamento/lockout."""
        key = f"{action.xapp_id}_{action.node_id}_{action.parameter}"
        if key in self.cooling_lockout:
            if now_ts < self.cooling_lockout[key]:
                return True
            else:
                del self.cooling_lockout[key]
        return False

    def apply_lockout(self, rejected_actions: List[XAppAction], now_ts: float):
        """Aplica a janela de resfriamento de 5s para ações rejeitadas para evitar ping-pong."""
        for act in rejected_actions:
            key = f"{act.xapp_id}_{act.node_id}_{act.parameter}"
            self.cooling_lockout[key] = now_ts + self.cooling_window_s

    def resolve(self, conflict: ConflictEvent, kpm_state: Optional[Dict[str, float]] = None) -> ResolutionAction:
        """
        Ponto de entrada principal de resolução de conflitos com escalonamento hierárquico.
        """
        now = time.time()
        
        # 0. Filtragem de ações sob Lockout (Janela de Resfriamento)
        valid_actions = [act for act in conflict.involved_xapps if not self.is_in_lockout(act, now)]
        if not valid_actions:
            # Todas estavam em lockout, mantém fallback da ação mais segura ou primeira
            return ResolutionAction(
                conflict_id=conflict.conflict_id,
                strategy_used=ResolutionStrategy.PRIORITY_TABLE,
                winning_actions=[conflict.involved_xapps[0]] if conflict.involved_xapps else [],
                modified_value=conflict.involved_xapps[0].value if conflict.involved_xapps else None,
                confidence=0.7,
                validation_level=0
            )
        conflict.involved_xapps = valid_actions

        # 1. Busca no Histórico Semântico (Knowledge Graph / SDL)
        similar_resolutions = self.memory.get_similar_resolutions(conflict)
        if similar_resolutions:
            best_res = similar_resolutions[0]
            if best_res.confidence > 0.85:
                return self._resolve_by_history(conflict, similar_resolutions)

        # 2. Avaliação de Complexidade C(c, s) para Roteamento Escalonado
        complexity = self.estimate_complexity(conflict, kpm_state)

        # Camada 1: Heurística Rápida / Tabela de Prioridades (H-RDL)
        if complexity <= self.tau1 and conflict.conflict_type == ConflictType.DIRECT:
            return self._resolve_by_heuristic(conflict, now)

        # Camada 2A: Utilidade Contextual / NDT Proativo (COMIX / MLO)
        elif complexity <= self.tau2:
            return self._resolve_by_sla_utility(conflict, kpm_state, now, policy="TVS")

        # Camada 2B: Coordenação Multiagente Aprendida com MAPPO (CA-RDL)
        else:
            return self._resolve_by_marl(conflict, kpm_state, now)

    def _resolve_by_heuristic(self, conflict: ConflictEvent, now_ts: float) -> ResolutionAction:
        """
        Nível 1 (H-RDL): Resolução determinística baseada em prioridade e regras de negócio.
        Latência: < 1 ms.
        """
        sorted_actions = sorted(conflict.involved_xapps, key=lambda a: a.priority, reverse=True)
        winning_action = sorted_actions[0]
        rejected_actions = sorted_actions[1:]
        
        # Aplica lockout nas ações rejeitadas
        self.apply_lockout(rejected_actions, now_ts)
        
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.PRIORITY_TABLE,
            winning_actions=[winning_action],
            modified_value=winning_action.value,
            confidence=0.95,
            validation_level=0
        )

    def _resolve_by_sla_utility(
        self, 
        conflict: ConflictEvent, 
        kpm_state: Optional[Dict[str, float]], 
        now_ts: float, 
        policy: str = "TVS"
    ) -> ResolutionAction:
        """
        Nível 2A (CA-RDL Utilidade): Avaliação combinatória proativa do Power Set 2^N 
        com funções de utilidade normalizadas TVS/EEVS e regularização sigmoide de potência (COMIX).
        """
        actions = conflict.involved_xapps
        best_score = -float('inf')
        best_subset: List[XAppAction] = []
        best_policy_used = ResolutionStrategy.TVS if policy == "TVS" else ResolutionStrategy.EEVS

        # Geração do Power Set de ações válidas
        powerset = []
        for i in range(1, len(actions) + 1):
            powerset.extend(list(itertools.combinations(actions, i)))
            
        for subset in powerset:
            score = self._evaluate_subset_utility(list(subset), kpm_state, policy)
            if score > best_score:
                best_score = score
                best_subset = list(subset)
                
        # Identificar ações rejeitadas para lockout
        winning_ids = {f"{a.xapp_id}_{a.parameter}" for a in best_subset}
        rejected = [a for a in actions if f"{a.xapp_id}_{a.parameter}" not in winning_ids]
        self.apply_lockout(rejected, now_ts)
        
        modified_val = best_subset[0].value if len(best_subset) == 1 else None

        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_policy_used,
            winning_actions=best_subset,
            modified_value=modified_val,
            confidence=max(0.75, min(0.99, 0.85 + (best_score * 0.05))),
            validation_level=0
        )

    def _evaluate_subset_utility(self, subset: List[XAppAction], kpm_state: Optional[Dict[str, float]], policy: str) -> float:
        """
        Função de Utilidade Multi-Objetivo contextual com desempate suave por sigmoide de potência (COMIX Eq. 11/13).
        """
        # Checagem de consistência física
        param_targets = {}
        for act in subset:
            key = f"{act.node_id}_{act.parameter}"
            if key in param_targets and param_targets[key] != act.value:
                return -9999.0  # Inconsistência física
            param_targets[key] = act.value

        # Telemetria base real ou aproximada
        thp_base = kpm_state.get("DRB.UEThpDl", 50.0) if kpm_state else 50.0
        delay_base = kpm_state.get("QoS.FlowDelay", 10.0) if kpm_state else 10.0
        
        total_power = 0.0
        sla_violations = 0
        ee_violations = 0
        
        for act in subset:
            param_lower = act.parameter.lower()
            if "power" in param_lower or "tx_power" in param_lower:
                val = float(act.value) if isinstance(act.value, (int, float)) else 20.0
                total_power += val
                # Relação física de perda de pacote / SLA vs potência
                if val < 15.0:
                    sla_violations += 2
                elif val < 23.0:
                    sla_violations += 0
                else:
                    ee_violations += 3 # Potência excessiva degrada EE
            elif "prb" in param_lower:
                val = float(act.value) if isinstance(act.value, (int, float)) else 50.0
                if val < 20.0:
                    sla_violations += 1
            elif "downtilt" in param_lower or "beam" in param_lower:
                val = float(act.value) if isinstance(act.value, (int, float)) else 6.0
                if val > 12.0:
                    sla_violations += 1 # Downtilt excessivo reduz cobertura na borda
                elif val < 3.0:
                    ee_violations += 1 # Downtilt raso aumenta interferência intercelular
            elif "isac" in param_lower or "radar" in param_lower or "sensing" in param_lower:
                val = float(act.value) if isinstance(act.value, (int, float)) else 0.25
                if val > 0.40:
                    sla_violations += 1 # Excesso de símbolos dedicados a radar reduz vazão eMBB
            elif "offset" in param_lower or "a3" in param_lower:
                val = float(act.value) if isinstance(act.value, (int, float)) else 3.0
                if val < 1.0:
                    sla_violations += 1 # Margem de histerese muito baixa induz ping-pong
            else:
                total_power += 10.0

        # Termo sigmoide para desempate suave por consumo de potência
        sigmoid_power = 1.0 / (1.0 + math.exp(-max(0.01, total_power * 0.1)))

        if policy == "TVS":
            # COMIX TVS: Score = - SLA_Violations - Sigmoid(Power)
            score = -float(sla_violations) - sigmoid_power
            return score
        elif policy == "EEVS":
            # COMIX EEVS: Score = - EE_Violations - Sigmoid(Power)
            score = -float(ee_violations) - sigmoid_power
            return score

        return -float(sla_violations)

    def _resolve_by_marl(self, conflict: ConflictEvent, kpm_state: Optional[Dict[str, float]], now_ts: float) -> ResolutionAction:
        """
        Nível 2B (CA-RDL MAPPO): Coordenação Multiagente Cooperativa com CTDE.
        """
        winning_action, confidence = self.mappo.decide(conflict, kpm_state)
        
        if winning_action:
            rejected = [a for a in conflict.involved_xapps if a.xapp_id != winning_action.xapp_id]
            self.apply_lockout(rejected, now_ts)
            winning_list = [winning_action]
            mod_val = winning_action.value
        else:
            winning_list = [conflict.involved_xapps[0]] if conflict.involved_xapps else []
            mod_val = conflict.involved_xapps[0].value if conflict.involved_xapps else None
        
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=ResolutionStrategy.MARL_AGENT,
            winning_actions=winning_list,
            modified_value=mod_val,
            confidence=confidence,
            validation_level=0
        )

    def _resolve_by_history(self, conflict: ConflictEvent, similar: List[ResolutionAction]) -> ResolutionAction:
        """Resolução via memória semântica (Knowledge Graph)."""
        best_past_res = similar[0]
        return ResolutionAction(
            conflict_id=conflict.conflict_id,
            strategy_used=best_past_res.strategy_used,
            winning_actions=best_past_res.winning_actions,
            modified_value=best_past_res.modified_value,
            confidence=best_past_res.confidence,
            validation_level=0
        )
