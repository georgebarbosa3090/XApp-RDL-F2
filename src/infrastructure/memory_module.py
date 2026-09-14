import time
from typing import List, Dict, Any
from src.observability.logging import setup_logger

logger = setup_logger("MemoryModule")

class MemoryModule:
    """
    Módulo de armazenamento operacional em memória RAM para histórico local de eventos e ações,
    incorporando Grafo de Conhecimento Causal (Knowledge Graph) para detecção de conflitos indiretos.
    """
    def __init__(self):
        self._actions = []
        self._conflicts = []
        self._resolutions = []
        # Knowledge Graph: adjacency representation {source: set([(target, relation_type)])}
        self._causal_graph: Dict[str, List[Dict[str, str]]] = {}
        logger.info("MemoryModule (Causal Knowledge Graph) inicializado.")

    def add_causal_relation(self, source: str, relation: str, target: str):
        """
        Adiciona uma aresta ao grafo causal (ex: xApp_A -> MUTATES -> parameter_tx_power).
        """
        if source not in self._causal_graph:
            self._causal_graph[source] = []
        self._causal_graph[source].append({"target": target, "relation": relation})
        logger.debug(f"[MEMORY-KG] Relação Causal Registrada: ({source}) --[{relation}]--> ({target})")

    def find_indirect_conflict_path(self, node_a: str, node_b: str, max_depth: int = 4) -> List[List[str]]:
        """
        Busca caminhos no grafo causal que conectam node_a e node_b a um recurso/KPI em comum,
        identificando conflitos indiretos entre xApps via BFS.
        """
        if node_a not in self._causal_graph or node_b not in self._causal_graph:
            return []

        # Find all downstream targets reachable from node_a
        def get_reachable_paths(start_node: str) -> Dict[str, List[str]]:
            queue = [(start_node, [start_node])]
            reachable = {}
            visited = set()
            while queue:
                curr, path = queue.pop(0)
                if len(path) > max_depth:
                    continue
                if curr in visited:
                    continue
                visited.add(curr)
                reachable[curr] = path
                for edge in self._causal_graph.get(curr, []):
                    nxt = edge["target"]
                    queue.append((nxt, path + [nxt]))
            return reachable

        reachable_a = get_reachable_paths(node_a)
        reachable_b = get_reachable_paths(node_b)

        # Common target nodes excluding the start nodes
        common = (set(reachable_a.keys()) & set(reachable_b.keys())) - {node_a, node_b}
        
        conflict_paths = []
        for target in common:
            path_a = reachable_a[target]
            path_b = reachable_b[target]
            conflict_paths.append(path_a + list(reversed(path_b[:-1])))

        return conflict_paths

    def add_action(self, action):
        logger.debug(f"[MEMORY] Salvando Ação: {action.parameter}={action.value}")
        self._actions.append(action)
        # Register in Knowledge Graph if xapp_id / parameter available
        xapp_id = getattr(action, 'xapp_id', getattr(action, 'sender_id', 'unknown_xapp'))
        param = getattr(action, 'parameter', None)
        if param:
            self.add_causal_relation(str(xapp_id), "MUTATES", str(param))

    def add_conflict(self, conflict):
        logger.debug(f"[MEMORY] Registrando Conflito: {conflict.conflict_type.name}")
        self._conflicts.append(conflict)

    def add_resolution(self, resolution):
        logger.debug(f"[MEMORY] Registrando Resolução (Estratégia: {resolution.strategy_used.name})")
        self._resolutions.append(resolution)

    def get_similar_resolutions(self, conflict) -> list:
        # Retorna resoluções históricas registradas com o mesmo tipo de conflito
        c_type = getattr(conflict, 'conflict_type', None)
        if not c_type:
            return []
        matching = []
        for r in self._resolutions:
            r_conflict_type = getattr(getattr(r, 'conflict', None), 'conflict_type', getattr(r, 'conflict_type', None))
            if r_conflict_type is None and hasattr(r, 'conflict_id'):
                matched_c = next((c for c in self._conflicts if getattr(c, 'conflict_id', None) == r.conflict_id), None)
                if matched_c:
                    r_conflict_type = getattr(matched_c, 'conflict_type', None)
            if r_conflict_type == c_type:
                matching.append(r)
        return matching

    def get_recent_actions(self, n=50) -> list:
        return self._actions[-n:]

    def save_control_request(self, control_id: str, data: dict):
        logger.debug(f"[MEMORY] Salvando Control Request {control_id}: {data}")

    def update_control_result(self, control_id: str, result: str):
        logger.debug(f"[MEMORY] Atualizando Control Result {control_id} -> {result}")

    def record_rollback(self, control_id: str):
        logger.warning(f"[MEMORY] Registrando Rollback para {control_id}")


