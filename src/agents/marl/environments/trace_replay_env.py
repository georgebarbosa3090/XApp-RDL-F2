"""
TraceReplayEnvironment: Ambiente de Avaliação Baseado em Replay de Telemetria Real.
Provedor determinístico de estados a partir de rastros reais (ns-3 / ORAN testbed) para diagnósticos offline (OFFLINE_REPLAY_ONLY).
NOTA METODOLÓGICA: Este ambiente é para avaliação e regressão offline (NOT_CAUSAL_TRAINING_ENV),
pois a transição de estado s_{t+1} é ditada pelo rastro empírico e d s_{t+1} / d a_t = 0.
"""

import json
import os
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from src.observability.logging import setup_logger

logger = setup_logger("TraceReplayEnv")


class TraceReplayEnvironment:
    """
    Ambiente MARL de Replay Offline (TraceReplayEvaluationEnvironment).
    Reproduz sequências de estados de telemetria coletados de experimentos reais no testbed O-RAN
    ou simulador ns-3 (FlowMonitor / Causal Events) para diagnósticos e extração de características.
    Modo: OFFLINE_REPLAY_ONLY (Aderência estrita à política C_SCI sem uso de np.random sintético).
    """
    def __init__(self, trace_path: Optional[str] = None, num_agents: int = 2, obs_dim: int = 4):
        self.num_agents = num_agents
        self.obs_dim = obs_dim
        self.trace_path = trace_path
        self.trace_data: List[Dict[str, Any]] = []
        self.current_step = 0
        
        if trace_path and os.path.exists(trace_path):
            self.load_trace(trace_path)
        else:
            logger.info(f"Nenhum rastro fornecido ou arquivo não encontrado: '{trace_path}'. Ambiente inicializado em modo estático.")

    def load_trace(self, file_path: str) -> int:
        """
        Carrega rastros de arquivo JSONL contendo a telemetria do ambiente.
        """
        self.trace_data = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        self.trace_data.append(entry)
                    except json.JSONDecodeError as err:
                        logger.warning(f"Linha inválida no rastro JSONL {file_path}: {err}")
        self.current_step = 0
        logger.info(f"Rastro de telemetria carregado de '{file_path}': {len(self.trace_data)} passos.")
        return len(self.trace_data)

    def reset(self) -> np.ndarray:
        """
        Reinicia o ponteiro de replay do rastro e retorna as observações iniciais.
        """
        self.current_step = 0
        return self._get_current_obs()

    def _get_current_obs(self) -> np.ndarray:
        if not self.trace_data:
            # Retorna matriz zerada caso não haja rastro carregado
            return np.zeros((self.num_agents, self.obs_dim), dtype=np.float32)

        entry = self.trace_data[min(self.current_step, len(self.trace_data) - 1)]
        obs_list = []
        
        # Extrai métricas reais se presentes no rastro
        agent_metrics = entry.get("agents", entry.get("telemetry", []))
        for i in range(self.num_agents):
            if i < len(agent_metrics) and isinstance(agent_metrics[i], dict):
                m = agent_metrics[i]
                vector = [
                    float(m.get("sinr_db", 0.0)),
                    float(m.get("prb_usage", 0.0)),
                    float(m.get("throughput_mbps", 0.0)),
                    float(m.get("latency_ms", 0.0))
                ]
            else:
                vector = [0.0] * self.obs_dim
            obs_list.append(vector[:self.obs_dim])
            
        return np.array(obs_list, dtype=np.float32)

    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, np.ndarray, bool, Dict[str, Any]]:
        """
        Executa um passo no replay do rastro a partir da ação dos agentes MARL.
        """
        if not self.trace_data:
            reward = np.zeros(self.num_agents, dtype=np.float32)
            done = True
            info = {"reason": "trace_empty"}
            return self._get_current_obs(), reward, done, info

        entry = self.trace_data[min(self.current_step, len(self.trace_data) - 1)]
        
        # Calcula recompensa baseada nos limites de SLA reais presentes no rastro
        rewards = []
        for i in range(self.num_agents):
            # Penaliza conflitos se a ação exceder limites
            act = float(actions[i]) if i < len(actions) else 0.0
            sla_target = entry.get("sla_target", 10.0)
            penalty = -1.0 if act > sla_target else 0.5
            rewards.append(penalty)

        self.current_step += 1
        done = self.current_step >= len(self.trace_data)
        next_obs = self._get_current_obs()
        info = {
            "step": self.current_step,
            "trace_length": len(self.trace_data),
            "timestamp": entry.get("timestamp", self.current_step)
        }

        return next_obs, np.array(rewards, dtype=np.float32), done, info
