from typing import Tuple, Dict, Any, List
import time
from src.conflict_types import ConflictEvent, ResolutionAction, XAppAction
from src.observability.logging import setup_logger

logger = setup_logger("RefinementAgent")

class RefinementAgent:
    """
    Agente de Refinamento, Blindagem Invariante e Segurança Zero-Trust (Safety Guards).
    Executa verificação determinística pós-inferência, validação de limites físicos de hardware,
    barreira de frequência temporal e quarentena comportamental contra Rogue xApps.
    """
    def __init__(self, memory=None):
        self.memory = memory
        self.config = {
            "enabled": True,
            "minimum_control_interval_ms": 1000,
            "max_violations_before_quarantine": 3,
            "violation_window_ms": 10000,
            "quarantine_duration_ms": 30000
        }
        self.last_control_time: Dict[str, float] = {}
        # Zero-Trust Tracking: xapp_id -> [violation_timestamp_ms, ...]
        self.violations: Dict[str, List[float]] = {}
        # Quarentena ativa: xapp_id -> quarantine_expiration_ms
        self.quarantine: Dict[str, float] = {}

    def _check_quarantine(self, xapp_id: str, now_ms: float) -> Tuple[bool, str]:
        """Verifica se a xApp está sob quarentena Zero-Trust."""
        if xapp_id in self.quarantine:
            if now_ms < self.quarantine[xapp_id]:
                remaining_s = (self.quarantine[xapp_id] - now_ms) / 1000.0
                return True, f"xApp '{xapp_id}' is in Zero-Trust QUARANTINE (remaining: {remaining_s:.1f}s)"
            else:
                del self.quarantine[xapp_id]
        return False, ""

    def _record_violation(self, xapp_id: str, now_ms: float, reason: str):
        """Registra infração comportamental e aciona quarentena se ultrapassar o limiar."""
        if not xapp_id:
            return
        if xapp_id not in self.violations:
            self.violations[xapp_id] = []
        
        # Manter apenas violações dentro da janela
        window = self.config.get("violation_window_ms", 10000)
        self.violations[xapp_id] = [t for t in self.violations[xapp_id] if (now_ms - t) <= window]
        self.violations[xapp_id].append(now_ms)
        
        limit = self.config.get("max_violations_before_quarantine", 3)
        if len(self.violations[xapp_id]) >= limit:
            quarantine_dur = self.config.get("quarantine_duration_ms", 30000)
            self.quarantine[xapp_id] = now_ms + quarantine_dur
            logger.warning(
                f"🚨 ZERO-TRUST ISOLATION: xApp '{xapp_id}' placed in QUARANTINE for {quarantine_dur/1000:.0f}s. Reason: {reason}"
            )

    def _validate_parameter_bounds(self, parameter: str, value: Any) -> Tuple[bool, str]:
        """Validação estrita de limites físicos de rádio (3GPP / O-RAN WG3)."""
        param_upper = parameter.upper()
        if not isinstance(value, (int, float)):
            return False, f"Invalid non-numeric value for parameter {parameter}"
            
        val = float(value)
        if param_upper == "PRB_QUOTA":
            if val < 0.0 or val > 100.0:
                return False, f"PRB value {val} out of bounds (0-100%)"
        elif param_upper == "TX_POWER":
            if val < -10.0 or val > 43.0:
                return False, f"TX Power {val} dBm out of bounds (-10 to 43 dBm)"
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
