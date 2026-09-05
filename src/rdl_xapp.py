import os
import json
import time
import threading
import uuid
from typing import Dict, Any, List, Optional
from ricxappframe.xapp_frame import Xapp

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.memory_module import MemoryModule
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.e2.asn1_decoder import ASN1Decoder
from src.e2.asn1_encoder import ASN1Encoder
from src.observability.health import HealthServer, AppState
from src.observability.metrics import MetricsCollector
from src.observability.logging import setup_logger
from src.conflict_types import XAppAction, KPMReport

logger = setup_logger("RDLxApp")

# RMR Message Types (O-RAN WG3 standard)
RIC_INDICATION = 12050
RIC_CONTROL_REQ = 12010
RIC_CONTROL_ACK = 12011
RIC_CONTROL_FAILURE = 12012
RDL_ACTION_PROPOSAL = 30000

def now_ts() -> float:
    return time.time()

class RDLxApp:
    def __init__(self, config_path: str = "configs/config-file.json"):
        self.config_mgr = ConfigManager(config_path)
        self.config = self.config_mgr.load_config()
        
        # 1. Shared Data Layer
        sdl_host = os.environ.get("DBAAS_SERVICE_HOST", self.config.get("sdl_host", "localhost"))
        sdl_port = int(os.environ.get("DBAAS_SERVICE_PORT", self.config.get("sdl_port", 6379)))
        try:
            self.memory = SdlRepository(host=sdl_host, port=sdl_port)
        except Exception:
            logger.warning("SDL Redis indisponivel. Usando MemoryModule (Fallback Local).")
            self.memory = MemoryModule()
            
        # 2. Agentes Cognitivos & Decision Engine
        self.perception = PerceptionAgent(self.memory)
        self.reasoning = ReasoningAgent(self.memory, config=self.config)
        self.refinement = RefinementAgent(self.memory)
        
        # 3. Codecs E2 APER
        self.asn1_decoder = ASN1Decoder()
        self.rc_encoder = ASN1Encoder()
        
        # 4. Observabilidade
        self.health = HealthServer(port=8080)
        self.metrics = MetricsCollector(port=8081)
        
        # 5. Buffer de Decisao em Lote (Decision Window)
        self.proposal_buffer: List[XAppAction] = []
        self.buffer_lock = threading.Lock()
        self.WINDOW_DURATION_MS = self.config.get("decision_window_ms", 200)
        self.window_start = 0.0
        
        # 6. Rastreamento de Transacoes Assincronas E2
        self.pending_transactions: Dict[str, float] = {}
        
        self.running = False
        
        # 7. Framework Xapp
        fake_sdl = os.environ.get("USE_FAKE_SDL", "True").lower() == "true"
        self.xapp = Xapp(entrypoint=self._entrypoint, rmr_port=4560, use_fake_sdl=fake_sdl)
        self.xapp.register_callback(self._default_handler, 0)
        self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
        self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
        self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
        self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)

    def start(self):
        logger.info("Iniciando xApp RDL (H-RDL / CA-RDL Fase 2)")
        self.health.run()
        self.metrics.start()
        self.running = True
        self.xapp.run()

    def stop(self):
        self.running = False
        self.health.set_state(AppState.STOPPED)
        self.xapp.stop()
        
    def _default_handler(self, xapp_instance, summary, sbuf):
        logger.debug("Mensagem RMR nao mapeada recebida", mtype=summary.get("mtype"))
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _entrypoint(self, xapp_instance):
        logger.info("xApp Framework Ready")
        self.health.set_state(AppState.READY)
        threading.Thread(target=self._decision_loop, daemon=True).start()

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            reports_data = self.asn1_decoder.decode_indication(payload)
            if reports_data:
                for data in reports_data:
                    report = KPMReport(
                        node_id=data.get("node_id", "gnb_01"),
                        ue_id=data.get("ue_id", "unknown"),
                        drb_thp_dl=data.get("drb_thp_dl", 0.0),
                        drb_thp_ul=data.get("drb_thp_ul", 0.0),
                        drb_delay_dl=data.get("drb_delay_dl", 0.0),
                        prb_used_dl=data.get("prb_used_dl", 0)
                    )
                    self.perception.update_kpm_report(report)
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _action_proposal_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Recebe acoes propostas por outras xApps via RMR e enfileira na janela temporal."""
        payload = summary.get("payload")
        if payload:
            try:
                data = json.loads(payload.decode('utf-8'))
                action = XAppAction(
                    xapp_id=data['xapp_id'],
                    node_id=data['node_id'],
                    parameter=data['parameter'],
                    value=data['value'],
                    priority=data.get('priority', 50)
                )
                with self.buffer_lock:
                    if not self.proposal_buffer:
                        self.window_start = now_ts()
                    self.proposal_buffer.append(action)
                    logger.debug(f"Action buffered. Queue size: {len(self.proposal_buffer)}")
                    
                    # Janela de Decisão Adaptativa: Flush imediato para ações críticas URLLC (prioridade >= 80)
                    if action.priority >= 80:
                        logger.info("⚡ Fast-Flush disparado para ação URLLC de emergência", xapp=action.xapp_id, prio=action.priority)
                        self.window_start = 0.0 # Força expiração imediata
            except Exception as e:
                logger.error("Erro ao processar RDL_ACTION_PROPOSAL", error=str(e))
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _control_ack_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata confirmações de execução de controle emitidas pelo E2 Node / E2Term."""
        payload = summary.get("payload")
        if payload:
            try:
                data = json.loads(payload.decode('utf-8'))
                tx_id = data.get("transaction_id")
                if tx_id and tx_id in self.pending_transactions:
                    rtt_ms = (now_ts() - self.pending_transactions.pop(tx_id)) * 1000.0
                    logger.info("RIC_CONTROL_ACK recebido", transaction_id=tx_id, rtt_ms=f"{rtt_ms:.2f}ms")
            except Exception:
                pass
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API pública para injeção de ações simuladas (usada em testes)"""
        with self.buffer_lock:
            if not self.proposal_buffer:
                self.window_start = now_ts()
            self.proposal_buffer.append(action)
            if action.priority >= 80:
                self.window_start = 0.0

    def _process_action_group(self, actions: List[XAppAction]):
        """
        Processa todas as ações acumuladas na Decision Window (Feature 2):
        1. Identifica conflitos diretos e indiretos;
        2. Arbitra conflitos via ReasoningAgent e valida via RefinementAgent;
        3. Executa Pass-Through de ações sem conflito validadas individualmente.
        """
        t0 = now_ts()
        for act in actions:
            self.memory.add_action(act)
            
        conflicts = self.perception.register_action_group(actions)
        self.metrics.update_active_xapps(len(self.perception.get_active_xapps()))
        
        # Mapeia ações em conflito para isolar as ações limpas
        conflicting_action_keys = set()
        for conflict in conflicts:
            for act in conflict.involved_xapps:
                conflicting_action_keys.add((act.node_id, act.parameter, act.xapp_id))
        
        # 1. Resolve conflitos do grupo
        for conflict in conflicts:
            logger.info("Conflito Detectado", conflict_id=conflict.conflict_id, type=conflict.conflict_type.name)
            self.memory.add_conflict(conflict)
            self.metrics.record_conflict(conflict)
            
            kpm_state = None
            if self.perception.latest_kpm:
                kpm_state = {
                    "DRB.UEThpDl": self.perception.latest_kpm.drb_thp_dl,
                    "DRB.UEThpUl": self.perception.latest_kpm.drb_thp_ul,
                    "QoS.FlowDelay": self.perception.latest_kpm.drb_delay_dl,
                    "RRU.PrbTotDl": float(self.perception.latest_kpm.prb_used_dl)
                }
            resolution = self.reasoning.resolve(conflict, kpm_state=kpm_state)
            is_valid, level, reason = self.refinement.validate(resolution, conflict)
            latency = now_ts() - t0
            
            self.memory.add_resolution(resolution)
            self.metrics.record_resolution(resolution, latency)
            
            if is_valid and resolution.winning_actions:
                for act in resolution.winning_actions:
                    logger.info("Conflito Resolvido", conflict=conflict.conflict_id, strategy=resolution.strategy_used.name, action=act.parameter)
                    self._send_control(act.node_id, act.parameter, act.value)
            else:
                logger.warning("Resolução Rejeitada ou Lote Vazio / Quarentena", reason=reason)

        # 2. Despacho Contínuo de Ações Limpas (Conflict-Free Pass-Through Pipeline)
        clean_actions = [
            act for act in actions 
            if (act.node_id, act.parameter, act.xapp_id) not in conflicting_action_keys
        ]
        
        for clean_act in clean_actions:
            is_safe, level, reason = self.refinement.validate_single_action(clean_act)
            if is_safe:
                logger.info("Ação Limpa Despachada (Pass-Through)", xapp=clean_act.xapp_id, param=clean_act.parameter, val=clean_act.value)
                self._send_control(clean_act.node_id, clean_act.parameter, clean_act.value)
            else:
                logger.warning("Ação Limpa Bloqueada pelo Safety Guard / Quarentena", reason=reason, param=clean_act.parameter)

    def _decision_loop(self):
        while self.running:
            time.sleep(0.02) # Verifica a cada 20ms para agilidade adaptativa
            
            with self.buffer_lock:
                if self.proposal_buffer:
                    elapsed_ms = (now_ts() - self.window_start) * 1000 if self.window_start > 0 else 9999.0
                    if elapsed_ms >= self.WINDOW_DURATION_MS or self.window_start == 0.0:
                        # Flush Window
                        actions_to_process = list(self.proposal_buffer)
                        self.proposal_buffer.clear()
                        self.window_start = 0.0
                        logger.info(f"Decision Window Expired. Processing batch of {len(actions_to_process)} actions.")
                        
                        # Processa fora do lock para não travar RMR
                        threading.Thread(target=self._process_action_group, args=(actions_to_process,), daemon=True).start()

    def _send_control(self, node_id: str, parameter: str, value: float):
        try:
            tx_id = str(uuid.uuid4())
            self.pending_transactions[tx_id] = now_ts()
            
            # Encodifica APER ASN.1 Nativo
            aper_payload = self.rc_encoder.encode_control_request(node_id, parameter, value)
            
            # Formata para o dispatcher RMR do E2 Term
            payload_dict = {
                "transaction_id": tx_id,
                "node_id": node_id,
                "parameter": parameter,
                "value": value,
                "aper_bytes": aper_payload.hex() if hasattr(aper_payload, "hex") else str(aper_payload)
            }
            payload_bytes = json.dumps(payload_dict).encode('utf-8')
            
            success = self.xapp.rmr_send(payload=payload_bytes, mtype=RIC_CONTROL_REQ)
        except Exception as e:
            logger.error(f"Falha ao gerar APER Control: {e}")
            success = False
        if success:
            logger.info("RIC_CONTROL_REQUEST enviado com sucesso", node_id=node_id, param=parameter, val=value, tx_id=tx_id)
        else:
            logger.error("Falha ao enviar RIC_CONTROL_REQUEST")

if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
