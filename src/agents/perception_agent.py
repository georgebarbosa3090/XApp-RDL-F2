from typing import Dict, List, Optional, Set
from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity, KPMReport
import networkx as nx
import itertools

class PerceptionAgent:
    def __init__(self, memory=None, neighbor_nodes: Optional[Dict[str, List[str]]] = None):
        self.memory = memory
        # Grafo de dependências KPI multidimensional modelando relações lógicas, 5G-Adv e 6G
        # Parâmetro -> Afeta -> KPIs
        self.kpi_dependency_graph: Dict[str, List[str]] = {
            "PRB_QUOTA": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
            "SCHEDULER_WEIGHT": ["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
            "TX_POWER": ["L1M.DL-sinr", "DRB.UEThpDl", "Energy.PowerConsumption"],
            "BEAM_DOWNTILT": ["L1M.DL-sinr", "Beam.RSRP", "InterCell.Interference", "DRB.UEThpDl"],
            "A3_OFFSET": ["Mobility.HandoverRate", "Mobility.PingPongRate", "RRU.PrbUsedDl"],
            "ISAC_SENSING_RATIO": ["Radar.DetectionProb", "Radar.ResolutionRange", "DRB.UEThpDl"],
            "CARRIER_AGG_RATIO": ["SCell.PrbUsedDl", "DRB.UEThpDl"]
        }
        
        # Mapeamento de nós vizinhos com sobreposição de cobertura de rádio (Inter-Cell Topology)
        self.neighbor_nodes: Dict[str, List[str]] = neighbor_nodes or {}
        
        # Grafo NetworkX para análise topológica de caminhos causais
        self.graph = nx.DiGraph()
        self._build_topology_graph()
        
        # Registro das últimas ações: node_id -> parameter -> XAppAction
        self._action_registry: Dict[str, Dict[str, XAppAction]] = {}
        self.latest_kpm: Optional[KPMReport] = None

    def add_neighbor_relation(self, node_a: str, node_b: str):
        """Registra adjacência e potencial interferência co-canal entre duas gNodeBs vizinhas."""
        if node_a not in self.neighbor_nodes:
            self.neighbor_nodes[node_a] = []
        if node_b not in self.neighbor_nodes:
            self.neighbor_nodes[node_b] = []
        if node_b not in self.neighbor_nodes[node_a]:
            self.neighbor_nodes[node_a].append(node_b)
        if node_a not in self.neighbor_nodes[node_b]:
            self.neighbor_nodes[node_b].append(node_a)

    def _build_topology_graph(self):
        """Constrói o grafo direcionado de relacionamentos Parâmetro -> KPI -> QoS."""
        for param, kpis in self.kpi_dependency_graph.items():
            for kpi in kpis:
                self.graph.add_edge(param, kpi)
                if "Delay" in kpi or "sinr" in kpi or "Detection" in kpi:
                    self.graph.add_edge(kpi, "QoS.SLA")
                elif "Power" in kpi:
                    self.graph.add_edge(kpi, "EnergyEfficiency")

    def update_kpm_report(self, report: KPMReport):
        self.latest_kpm = report

    def get_active_xapps(self) -> Dict[str, List[XAppAction]]:
        active = {}
        for node, params in self._action_registry.items():
            for param, action in params.items():
                if action.xapp_id not in active:
                    active[action.xapp_id] = []
                active[action.xapp_id].append(action)
        return active

    def register_action_group(self, actions: List[XAppAction]) -> List[ConflictEvent]:
        conflicts = []
        
        # 1. Avalia combinações dentro do próprio grupo (Decision Window)
        for i in range(len(actions)):
            for j in range(i + 1, len(actions)):
                action_a = actions[i]
                action_b = actions[j]
                
                # Check Direct (Mesmo nó e mesmo parâmetro)
                if action_a.node_id == action_b.node_id and action_a.parameter == action_b.parameter and action_a.xapp_id != action_b.xapp_id:
                    conflicts.append(ConflictEvent(
                        conflict_type=ConflictType.DIRECT,
                        severity=ConflictSeverity.HIGH,
                        involved_xapps=[action_a, action_b],
                        affected_kpis=self.kpi_dependency_graph.get(action_a.parameter, []),
                        description=f"Direct conflict on parameter {action_a.parameter} at {action_a.node_id}"
                    ))
                
                # Check Indirect Intra-Cell (Mesmo nó, parâmetros distintos, KPIs compartilhados)
                elif action_a.node_id == action_b.node_id and action_a.xapp_id != action_b.xapp_id:
                    kpis_a = self.kpi_dependency_graph.get(action_a.parameter, [])
                    kpis_b = self.kpi_dependency_graph.get(action_b.parameter, [])
                    common_kpis = set(kpis_a).intersection(set(kpis_b))
                    if common_kpis:
                        conflicts.append(ConflictEvent(
                            conflict_type=ConflictType.INDIRECT,
                            severity=ConflictSeverity.MEDIUM,
                            involved_xapps=[action_a, action_b],
                            affected_kpis=list(common_kpis),
                            description=f"Indirect conflict on KPIs {common_kpis} via params {action_a.parameter} and {action_b.parameter}"
                        ))
                        
                # Check Indirect Inter-Cell (Nós vizinhos com acoplamento de interferência co-canal)
                elif action_a.node_id != action_b.node_id and action_a.xapp_id != action_b.xapp_id:
                    neighbors_a = self.neighbor_nodes.get(action_a.node_id, [])
                    if action_b.node_id in neighbors_a:
                        inter_params = {"TX_POWER", "BEAM_DOWNTILT", "PRB_QUOTA"}
                        if action_a.parameter in inter_params and action_b.parameter in inter_params:
                            conflicts.append(ConflictEvent(
                                conflict_type=ConflictType.INDIRECT,
                                severity=ConflictSeverity.MEDIUM,
                                involved_xapps=[action_a, action_b],
                                affected_kpis=["InterCell.Interference", "L1M.DL-sinr"],
                                description=f"Inter-Cell interference conflict between {action_a.node_id} ({action_a.parameter}) and {action_b.node_id} ({action_b.parameter})"
                            ))

        # 2. Avalia cada ação contra o registry (ações em vigor que não expiraram antes do lote)
        for action in actions:
            # Check Direct contra o histórico
            direct = self._detect_direct_conflict(action)
            if direct:
                conflicts.append(direct)
                
            # Check Indirect contra o histórico
            indirects = self._detect_indirect_conflict(action)
            conflicts.extend(indirects)
            
        # 3. Registra todas as novas ações após checagem
        for action in actions:
            if action.node_id not in self._action_registry:
                self._action_registry[action.node_id] = {}
            self._action_registry[action.node_id][action.parameter] = action
            
        return conflicts

    def _detect_direct_conflict(self, new_action: XAppAction) -> Optional[ConflictEvent]:
        if new_action.node_id in self._action_registry:
            if new_action.parameter in self._action_registry[new_action.node_id]:
                old_action = self._action_registry[new_action.node_id][new_action.parameter]
                if old_action.xapp_id != new_action.xapp_id:
                    return ConflictEvent(
                        conflict_type=ConflictType.DIRECT,
                        severity=ConflictSeverity.HIGH,
                        involved_xapps=[old_action, new_action],
                        affected_kpis=self.kpi_dependency_graph.get(new_action.parameter, []),
                        description=f"Direct conflict on parameter {new_action.parameter} against history"
                    )
        return None

    def _detect_indirect_conflict(self, new_action: XAppAction) -> List[ConflictEvent]:
        conflicts = []
        new_kpis = self.kpi_dependency_graph.get(new_action.parameter, [])
        
        if not new_kpis or new_action.node_id not in self._action_registry:
            return conflicts
            
        for param, old_action in self._action_registry[new_action.node_id].items():
            if param == new_action.parameter or old_action.xapp_id == new_action.xapp_id:
                continue
            
            old_kpis = self.kpi_dependency_graph.get(param, [])
            common_kpis = set(new_kpis).intersection(set(old_kpis))
            
            if common_kpis:
                conflicts.append(ConflictEvent(
                    conflict_type=ConflictType.INDIRECT,
                    severity=ConflictSeverity.MEDIUM,
                    involved_xapps=[old_action, new_action],
                    affected_kpis=list(common_kpis),
                    description=f"Indirect conflict on KPIs {common_kpis} via params {param} and {new_action.parameter} against history"
                ))
        return conflicts
