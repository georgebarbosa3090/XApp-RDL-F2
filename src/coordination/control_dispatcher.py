import time
import uuid
from typing import Dict, Optional, Any, List
from src.e2.rc_encoder import E2SMRCEncoder, ControlAction
from src.infrastructure.sdl_repository import SdlRepository
from src.conflict_types import RDLDecision as Decision, RDLDecision
from src.observability.logging import setup_logger

logger = setup_logger("ControlDispatcher")

class ControlDispatcher:
    def __init__(self, rmr_client, sdl_repo: Any, default_timeout_s: float = 5.0):
        self.rmr = rmr_client
        self.sdl = sdl_repo
        self.encoder = E2SMRCEncoder()
        self.default_timeout_s = default_timeout_s
        self.rollback_history: List[Dict[str, Any]] = []
        
    def dispatch_control(self, decision: Any) -> Optional[str]:
        safety_ok = getattr(decision, "safety_validation", True)
        if isinstance(decision, RDLDecision):
            safety_ok = decision.safety_result.get("is_safe", True) if decision.safety_result else True
            actions = decision.selected_actions
        else:
            act = getattr(decision, "selected_action", None)
            actions = [act] if act else getattr(decision, "selected_actions", [])

        if not safety_ok or not actions:
            logger.warning(f"Decisão {getattr(decision, 'decision_id', 'unknown')} ignorada por falha de safety guard ou sem ações.")
            return None

        control_request_id = str(uuid.uuid4())
        prev_val = getattr(decision, "previous_safe_value", 50.0)

        for act_obj in actions:
            target_node = getattr(decision, "affected_node", getattr(act_obj, "node_id", "gnb_01"))
            target_cell = getattr(decision, "affected_cell", "cell_01")
            
            control_action = ControlAction(act_obj, target_node, target_cell)
            payload = self.encoder.encode(control_action)
            
            tracking_info = {
                "control_request_id": control_request_id,
                "request_id": 1,
                "instance_id": 1,
                "ran_function_id": 3, # RC
                "meid": target_node,
                "decision_id": getattr(decision, "decision_id", control_request_id),
                "previous_safe_value": prev_val,
                "sent_at": time.time(),
                "timeout_at": time.time() + self.default_timeout_s,
                "status": "SENT"
            }
            self.sdl.save_control_request(control_request_id, tracking_info)
            logger.info(f"Enviando RIC_CONTROL_REQUEST {control_request_id} para MEID {target_node}")
            self.rmr.rmr_send(payload, 12010, target_node)

        return control_request_id

    def handle_ack(self, payload: bytes):
        """
        Trata o RIC_CONTROL_ACK (12011)
        Na prática, extraímos o request_id do payload.
        """
        req_id = "simulated_req_id"
        logger.info(f"Recebido RIC_CONTROL_ACK para req {req_id}")
        self.sdl.update_control_result(req_id, "ACKNOWLEDGED")

    def handle_failure(self, payload: bytes):
        """
        Trata o RIC_CONTROL_FAILURE (12012)
        """
        req_id = "simulated_req_id"
        logger.error(f"Recebido RIC_CONTROL_FAILURE para req {req_id}")
        self.sdl.update_control_result(req_id, "FAILED")
        self.trigger_rollback(req_id)
        
    def trigger_rollback(self, control_request_id: str, restored_value: float = 50.0):
        logger.warning(f"Executando Rollback para controle {control_request_id} -> valor restaurado: {restored_value}%")
        self.rollback_history.append({
            "request_id": control_request_id,
            "restored_value": restored_value,
            "timestamp": time.time()
        })
        if hasattr(self.sdl, "update_control_result"):
            self.sdl.update_control_result(control_request_id, "ROLLED_BACK")

    def check_timeouts(self, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Verifica requisições pendentes que ultrapassaram o deadline de ACK."""
        current_time = now if now is not None else time.time()
        timed_out = []
        if hasattr(self.sdl, "get_pending_requests"):
            pending = self.sdl.get_pending_requests()
        elif hasattr(self.sdl, "control_requests"):
            pending = [req for req in self.sdl.control_requests.values() if req.get("status") == "SENT"]
        else:
            pending = []

        for req in pending:
            if current_time >= req.get("timeout_at", 0):
                req["status"] = "TIMEOUT"
                timed_out.append(req)
                if hasattr(self.sdl, "update_control_result"):
                    self.sdl.update_control_result(req["control_request_id"], "TIMEOUT")
                self.trigger_rollback(req["control_request_id"], restored_value=req.get("previous_safe_value", 50.0))
        return timed_out

