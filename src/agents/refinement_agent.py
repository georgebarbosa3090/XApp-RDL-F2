from typing import Tuple, Dict, Any, List
import time
from src.conflict_types import ConflictEvent, ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("RefinementAgent")

from enum import Enum

class XAppLifecycleState(Enum):
    ACTIVE = "ACTIVE"
    SUSPECT = "SUSPECT"
    QUARANTINE = "QUARANTINE"
    PROBATION = "PROBATION"

class RefinementAgent:
    """
    Agente de Refinamento, Blindagem Invariante e Segurança Zero-Trust (Safety Guards).
    Executa verificação determinística pós-inferência, validação de limites físicos de hardware
    diferenciados por perfil de célula (Macro vs Small Cell), barreira temporal e FSM de quarentena.
    """
    def __init__(self, memory=None, node_profiles: Optional[Dict[str, str]] = None):
        self.memory = memory
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
            "max_violations_before_quarantine": 3,
            "violation_window_ms": 10000,
            "quarantine_duration_ms": 30000,
            "probation_duration_ms": 10000
        }
        # Perfis de potência por tipo de célula (Macro: 43 dBm, Small Cell: 23 dBm)
        self.node_profiles = node_profiles or {
            "gnb_01": "macro",
            "gnb_02": "macro",
            "gnb_03": "small_cell"
        }
        self.last_control_time: Dict[str, float] = {}
        # Zero-Trust FSM Tracking: xapp_id -> {state, violations: [], state_change_ts}
        self.app_states: Dict[str, Dict[str, Any]] = {}

    def _get_app_state(self, xapp_id: str, now_ms: float) -> XAppLifecycleState:
        if xapp_id not in self.app_states:
            self.app_states[xapp_id] = {
                "state": XAppLifecycleState.ACTIVE,
                "violations": [],
                "state_change_ts": now_ms
            }
            return XAppLifecycleState.ACTIVE
            
        data = self.app_states[xapp_id]
        curr_state = data["state"]
        elapsed = now_ms - data["state_change_ts"]
        
        # Transições automáticas de tempo na FSM
        if curr_state == XAppLifecycleState.QUARANTINE:
            if elapsed >= self.config["quarantine_duration_ms"]:
                data["state"] = XAppLifecycleState.PROBATION
                data["state_change_ts"] = now_ms
                logger.info(f"🔄 xApp '{xapp_id}' passou de QUARANTINE para PROBATION.")
                return XAppLifecycleState.PROBATION
        elif curr_state == XAppLifecycleState.PROBATION:
            if elapsed >= self.config["probation_duration_ms"]:
                data["state"] = XAppLifecycleState.ACTIVE
                data["violations"].clear()
                data["state_change_ts"] = now_ms
                logger.info(f"✅ xApp '{xapp_id}' reabilitada: PROBATION -> ACTIVE.")
                return XAppLifecycleState.ACTIVE
                
        return curr_state

    def _check_quarantine(self, xapp_id: str, now_ms: float) -> Tuple[bool, str]:
        """Verifica se a xApp está sob quarentena Zero-Trust."""
        state = self._get_app_state(xapp_id, now_ms)
        if state == XAppLifecycleState.QUARANTINE:
            elapsed = now_ms - self.app_states[xapp_id]["state_change_ts"]
            remaining_s = (self.config["quarantine_duration_ms"] - elapsed) / 1000.0
            return True, f"xApp '{xapp_id}' is in Zero-Trust QUARANTINE (remaining: {remaining_s:.1f}s)"
        return False, ""

    def _record_violation(self, xapp_id: str, now_ms: float, reason: str):
        """Registra infração comportamental e atualiza a FSM de segurança."""
        if not xapp_id:
            return
        state = self._get_app_state(xapp_id, now_ms)
        data = self.app_states[xapp_id]
        
        # Em estado de PROBATION, 1 violação retorna imediatamente para QUARANTINE
        if state == XAppLifecycleState.PROBATION:
            data["state"] = XAppLifecycleState.QUARANTINE
            data["state_change_ts"] = now_ms
            logger.warning(f"🚨 PROBATION FAILURE: xApp '{xapp_id}' retornou para QUARANTINE. Motivo: {reason}")
            return
            
        # Manter violações dentro da janela
        window = self.config.get("violation_window_ms", 10000)
        data["violations"] = [t for t in data["violations"] if (now_ms - t) <= window]
        data["violations"].append(now_ms)
        
        limit = self.config.get("max_violations_before_quarantine", 3)
        if len(data["violations"]) >= limit:
            data["state"] = XAppLifecycleState.QUARANTINE
            data["state_change_ts"] = now_ms
            logger.warning(f"🚨 ZERO-TRUST ISOLATION: xApp '{xapp_id}' colocada em QUARANTINE por 30s. Motivo: {reason}")
        elif len(data["violations"]) == 1:
            data["state"] = XAppLifecycleState.SUSPECT
            logger.warning(f"⚠️ xApp '{xapp_id}' em estado SUSPECT (1 violação). Motivo: {reason}")

    def _validate_parameter_bounds(self, parameter: str, value: Any, node_id: str = "gnb_01") -> Tuple[bool, str]:
        """Validação estrita de limites físicos de rádio com perfil de célula (Macro vs Small Cell)."""
        param_upper = parameter.upper()
        if not isinstance(value, (int, float)):
            return False, f"Invalid non-numeric value for parameter {parameter}"
            
        val = float(value)
        cell_profile = self.node_profiles.get(node_id, "macro")
        max_power_dbm = 43.0 if cell_profile == "macro" else 23.0 # Teto Macro (20W) vs Small Cell (200mW)
        
        if param_upper == "PRB_QUOTA":
            if val < 0.0 or val > 100.0:
                return False, f"PRB value {val} out of bounds (0-100%)"
        elif param_upper == "TX_POWER":
            if val < -10.0 or val > max_power_dbm:
                return False, f"TX Power {val} dBm out of bounds (-10 to {max_power_dbm} dBm for profile {cell_profile})"
        elif "DOWNTILT" in param_upper:
            if val < 0.0 or val > 15.0:
                return False, f"Beam Downtilt {val}° out of bounds (0-15°)"
        elif "ISAC" in param_upper or "SENSING" in param_upper:
            if val < 0.0 or val > 0.5:
                return False, f"ISAC Sensing Ratio {val} out of bounds (0.0-0.5)"
        elif "OFFSET" in param_upper or "A3" in param_upper:
            if val < -10.0 or val > 10.0:
                return False, f"A3 Offset {val} dB out of bounds (-10 to 10 dB)"
        elif "SCHEDULER" in param_upper or "WEIGHT" in param_upper:
            if val <= 0.0 or val > 10.0:
                return False, f"Scheduler Weight {val} out of bounds (0.1-10.0)"
                
        return True, ""

    def validate(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, int, str]:
        """
        Safety Guard que valida se o lote de controle proposto é seguro e compatível com as regras invariantes.
        Retorna (is_valid, validation_level, reason)
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"
            
        actions = resolution.winning_actions
        if not actions:
            return False, 1, "No actions selected"

        now = time.time() * 1000
        
        for action in actions:
            # 0. Checagem de Quarentena Zero-Trust
            is_quarantined, q_reason = self._check_quarantine(action.xapp_id, now)
            if is_quarantined:
                return False, 1, q_reason

            if not action.node_id:
                self._record_violation(action.xapp_id, now, "Unknown target node")
                return False, 1, "Unknown target node"

            target_key = f"{action.node_id}_{action.parameter}"
            
            # 1. Validade temporal (frequência máxima de controle no mesmo parâmetro/nó)
            last_time = self.last_control_time.get(target_key, 0)
            if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
                self._record_violation(action.xapp_id, now, f"Control frequency exceeded for {target_key}")
                return False, 1, f"Control frequency exceeded for {target_key}"
                
            # 2. Limites físicos de parâmetros de rádio
            valid_bounds, bounds_reason = self._validate_parameter_bounds(action.parameter, action.value)
            if not valid_bounds:
                self._record_violation(action.xapp_id, now, bounds_reason)
                return False, 1, bounds_reason

            # Atualiza tempo
            self.last_control_time[target_key] = now

        return True, 2, "Passed safety checks"

    def validate_single_action(self, action: XAppAction) -> Tuple[bool, int, str]:
        """
        Valida uma ação individual não conflitante (Pass-Through) antes do envio direto.
        Garante que mesmo ações limpas respeitem os limites físicos, temporais e Zero-Trust.
        """
        if not self.config.get("enabled", True):
            return True, 1, "Safety guard disabled"
            
        now = time.time() * 1000
        
        # 0. Checagem de Quarentena Zero-Trust
        is_quarantined, q_reason = self._check_quarantine(action.xapp_id, now)
        if is_quarantined:
            return False, 1, q_reason

        if not action.node_id:
            self._record_violation(action.xapp_id, now, "Unknown target node")
            return False, 1, "Unknown target node"

        target_key = f"{action.node_id}_{action.parameter}"
        
        # 1. Validade temporal (frequência máxima de controle no mesmo parâmetro/nó)
        last_time = self.last_control_time.get(target_key, 0)
        if (now - last_time) < self.config.get("minimum_control_interval_ms", 1000):
            self._record_violation(action.xapp_id, now, f"Control frequency exceeded for {target_key}")
            return False, 1, f"Control frequency exceeded for {target_key}"
            
        # 2. Limites físicos de parâmetros de rádio
        valid_bounds, bounds_reason = self._validate_parameter_bounds(action.parameter, action.value)
        if not valid_bounds:
            self._record_violation(action.xapp_id, now, bounds_reason)
            return False, 1, bounds_reason

        self.last_control_time[target_key] = now
        return True, 2, "Passed safety checks"
