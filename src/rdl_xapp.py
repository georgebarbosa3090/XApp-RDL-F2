from __future__ import annotations
import os
import json
import time
import threading
import uuid
from typing import Dict, Any, List, Optional, Tuple
try:
    from ricxappframe.xapp_frame import Xapp
    HAS_RICXAPPFRAME = True
except (ImportError, OSError, Exception):
    HAS_RICXAPPFRAME = False
    class Xapp:
        """Shim de compatibilidade do framework Xapp para testes e CI sem RMR nativo."""
        def __init__(self, entrypoint=None, rmr_port: int = 4560, use_fake_sdl: bool = True):
            self.entrypoint = entrypoint
            self.rmr_port = rmr_port
            self.use_fake_sdl = use_fake_sdl
            self._callbacks: Dict[int, Any] = {}
            self.is_mock_transport = True
            self.transport_name = "MOCK_TRANSPORT_SHIM"
        def register_callback(self, handler: Any, mtype: int):
            self._callbacks[mtype] = handler
        def run(self):
            if self.entrypoint:
                self.entrypoint(self)
        def stop(self):
            pass
        def rmr_send(self, payload: bytes, mtype: int) -> bool:
            return True
        def rmr_free(self, sbuf: Any):
            pass

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.sdl_repository import SdlRepository
from src.infrastructure.memory_module import MemoryModule
from src.infrastructure.ran_backend_factory import get_ran_backend_adapter
from src.infrastructure.ric_request_id_allocator import get_ric_request_id_allocator
from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
from src.e2.kpm_decoder import KpmDecoder
from src.e2.rc_encoder import RCEncoder
from src.observability.health import HealthServer, AppState
from src.observability.metrics import MetricsCollector
from src.observability.logging import setup_logger
from src.conflict_types import XAppAction, KPMReport, RDLDecision

logger = setup_logger("RDLxApp")

from src.e2.e2ap.constants import (
    RIC_SUBSCRIPTION_REQ,
    RIC_SUBSCRIPTION_RESP,
    RIC_SUBSCRIPTION_FAILURE,
    RIC_CONTROL_REQ,
    RIC_CONTROL_ACK,
    RIC_CONTROL_FAILURE,
    RIC_INDICATION,
    RDL_ACTION_PROPOSAL
)

def now_ts() -> float:
    return time.time()

class RDLxApp:
    def __init__(self, config_path: str = "configs/config-file.json"):
        self.config_mgr = ConfigManager(config_path)
        self.config = self.config_mgr.load_config()
        
        # Modo de Operacao (O_RAN_INTEROP / ORAN-STRICT | SIMULATION / OFFLINE_SIMULATION | STANDALONE)
        raw_mode = os.getenv("RDL_MODE", "OFFLINE_SIMULATION").upper()
        self.mode = "O_RAN_INTEROP" if raw_mode in ("O_RAN_INTEROP", "ORAN-STRICT", "ORAN_STRICT", "STRICT") else raw_mode
        self.oran_strict = (self.mode == "O_RAN_INTEROP")
        self.backend = get_ran_backend_adapter(os.getenv("RAN_BACKEND"))
        self.allocator = get_ric_request_id_allocator()
        
        # 1. Shared Data Layer
        sdl_host = os.environ.get("DBAAS_SERVICE_HOST", self.config.get("sdl_host", "localhost"))
        sdl_port = int(os.environ.get("DBAAS_SERVICE_PORT", self.config.get("sdl_port", 6379)))
        try:
            self.memory = SdlRepository(host=sdl_host, port=sdl_port)
        except Exception as exc:
            if getattr(self, "oran_strict", False) or getattr(self, "mode", "") in ("O_RAN_INTEROP", "ORAN-STRICT"):
                raise RuntimeError(
                    "SDL/DBaaS obrigatório no modo O_RAN_INTEROP; fallback local proibido."
                ) from exc
            logger.warning("SDL Redis indisponivel. Usando MemoryModule (Fallback Local).")
            self.memory = MemoryModule()
            
        # 2. Agentes Cognitivos & Decision Engine
        self.perception = PerceptionAgent(self.memory)
        self.reasoning = ReasoningAgent(self.memory, config=self.config)
        self.refinement = RefinementAgent(self.memory)
        
        # 3. Codecs E2 APER
        self.asn1_decoder = KpmDecoder()
        self.rc_encoder = RCEncoder()
        
        # 4. Observabilidade
        self.health = HealthServer(port=8080)
        self.metrics = MetricsCollector(port=8081)
        
        # 5. Buffer de Decisao em Lote (Decision Window) com Interrupção Dirigida por Eventos
        self.proposal_buffer: List[XAppAction] = []
        self.buffer_lock = threading.Lock()
        self.flush_event = threading.Event()
        self.WINDOW_DURATION_MS = self.config.get("decision_window_ms", 200)
        self.window_start = 0.0
        
        # 6. Rastreamento de Transacoes Assincronas E2 (Armazena timestamp e ação associada)
        self.pending_transactions: Dict[str, Dict[str, Any]] = {}
        
        self.running = False
             # 7. Framework Xapp e Modo de Transporte
        fake_sdl = os.environ.get("USE_FAKE_SDL", "True").lower() == "true"
        if self.oran_strict:
            self.require_operational_transport = True
            logger.info("🔒 Modo O_RAN_INTEROP estrito ativado: Transporte operacional real e SDL estrito exigidos (Fail-Closed).")
        else:
            self.require_operational_transport = (
                os.environ.get("REQUIRE_OPERATIONAL_TRANSPORT", "false").lower() == "true"
                or self.config.get("require_operational_transport", False)
            )

        self.xapp = Xapp(entrypoint=self._entrypoint, rmr_port=4560, use_fake_sdl=fake_sdl)
        self.is_mock_transport = getattr(self.xapp, "is_mock_transport", not HAS_RICXAPPFRAME)
        self.transport_mode = "MOCK_TRANSPORT_SHIM" if self.is_mock_transport else "RMR_E2_OPERATIONAL"
        self.is_operational_ready = not self.is_mock_transport
        
        if self.require_operational_transport and self.is_mock_transport:
            logger.error("❌ FALHA DE PRONTIDÃO OPERACIONAL: Transporte nativo RMR_E2_OPERATIONAL exigido, mas apenas MOCK_TRANSPORT_SHIM disponível.")
            raise RuntimeError(
                "TRANSPORTE O-RAN OPERACIONAL OBRIGATÓRIO NÃO DISPONÍVEL: "
                "O ambiente exige conexão nativa C RMR/E2, mas o socket nativo não foi carregado."
            )

        if self.is_mock_transport:
            logger.info("ℹ️ Transporte RMR inicializado em modo MOCK_TRANSPORT_SHIM (Ambiente local / CI de desenvolvimento)")
        else:
            logger.info("📡 Transporte RMR inicializado em modo RMR_E2_OPERATIONAL (Conexão nativa C O-RAN pronta)")
            
        self.xapp.register_callback(self._default_handler, 0)
        self.xapp.register_callback(self._kpm_indication_handler, RIC_INDICATION)
        self.xapp.register_callback(self._action_proposal_handler, RDL_ACTION_PROPOSAL)
        self.xapp.register_callback(self._control_ack_handler, RIC_CONTROL_ACK)
        self.xapp.register_callback(self._control_failure_handler, RIC_CONTROL_FAILURE)

    def start(self):
        self.running = True
        logger.info("Iniciando RDLxApp Engine", transport=self.transport_mode, backend=self.backend.metadata.backend_id)
        if not self.is_mock_transport and hasattr(self.xapp, "run"):
            self.xapp.run()
        else:
            self._entrypoint(None)

    def stop(self):
        self.running = False
        self.health.set_state(AppState.STOPPING)
        logger.info("Encerrando RDLxApp Engine")
        if self.xapp and hasattr(self.xapp, "stop"):
            self.xapp.stop()
        
    def _default_handler(self, xapp_instance, summary, sbuf):
        logger.debug("Mensagem RMR nao mapeada recebida", mtype=summary.get("mtype"))
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _entrypoint(self, xapp_instance):
        logger.info("xApp Framework Ready", transport=self.transport_mode)
        self.health.set_state(AppState.READY)
        threading.Thread(target=self._decision_loop, daemon=True).start()

    def _kpm_indication_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        self.metrics.record_kpm()
        payload = summary.get("payload")
        if payload:
            try:
                reports_data = self.backend.decode_kpm(payload)
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
            except Exception as e:
                logger.error("Erro ao decodificar telemetria KPM via backend", backend=self.backend.metadata.backend_id, error=str(e))
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
                action.t_arrival = time.perf_counter()
                action.arrival_monotonic = action.t_arrival
                with self.buffer_lock:
                    if not self.proposal_buffer:
                        self.window_start = time.perf_counter()
                    self.proposal_buffer.append(action)
                    logger.debug(f"Action buffered. Queue size: {len(self.proposal_buffer)}")
                    
                    # Janela de Decisão Adaptativa: Flush imediato para ações críticas URLLC (prioridade >= 80)
                    if action.priority >= 80:
                        logger.info("⚡ Fast-Flush disparado para ação URLLC de emergência", xapp=action.xapp_id, prio=action.priority)
                        self.window_start = 0.0 # Força expiração imediata
                        self.flush_event.set()
            except Exception as e:
                logger.error("Erro ao processar RDL_ACTION_PROPOSAL", error=str(e))
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _control_ack_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata confirmações de execução de controle emitidas pelo E2 Node / E2Term com suporte a APER e JSON."""
        t_ack_now = time.perf_counter()
        payload = summary.get("payload")
        if payload:
            tx_info = None
            tx_id = None
            try:
                # 1. Tenta correlação via backend APER e RicRequestIdAllocator
                ack_data = self.backend.correlate_ack(payload, allow_test_fallback=not self.oran_strict)
                req_id = ack_data.get("requestor_id")
                inst_id = ack_data.get("instance_id")
                node_id = ack_data.get("node_id", "gnb_01")
                ran_fn_id = ack_data.get("ran_function_id", 3)
                
                if req_id is not None and inst_id is not None:
                    ric_req_key = (node_id, ran_fn_id, req_id, inst_id)
                    tx_info = self.pending_transactions.pop(ric_req_key, None)
                    if not tx_info:
                        # Busca por iteração de chaves
                        for key, info in list(self.pending_transactions.items()):
                            if info.get("ric_req_key") == ric_req_key:
                                tx_info = self.pending_transactions.pop(key)
                                break
                                
                # 2. Fallback para decodificação JSON
                if not tx_info and isinstance(payload, bytes):
                    try:
                        data = json.loads(payload.decode('utf-8'))
                        tx_id = data.get("transaction_id")
                        if tx_id and tx_id in self.pending_transactions:
                            tx_info = self.pending_transactions.pop(tx_id)
                    except Exception:
                        pass
                        
                if tx_info:
                    t_start = tx_info["t_dispatch_start"]
                    act = tx_info.get("action")
                    if act:
                        act.t_ack = t_ack_now
                    rtt_ms = (t_ack_now - t_start) * 1000.0
                    logger.info("RIC_CONTROL_ACK recebido e confirmado", transaction_id=tx_id or "APER", rtt_ms=f"{rtt_ms:.3f}ms", action=act.parameter if act else None)
            except Exception as e:
                logger.debug(f"Erro ao decodificar RIC_CONTROL_ACK: {e}")
        logger.info("Recebido RIC_CONTROL_ACK", summary=summary)
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def _control_failure_handler(self, xapp_instance: Xapp, summary: Dict[str, Any], sbuf: Any):
        """Trata notificações de falha no E2 Node / E2Term."""
        payload = summary.get("payload")
        if payload:
            tx_info = None
            try:
                ack_data = self.backend.correlate_ack(payload, allow_test_fallback=not self.oran_strict)
                req_id = ack_data.get("requestor_id")
                inst_id = ack_data.get("instance_id")
                node_id = ack_data.get("node_id", "gnb_01")
                ran_fn_id = ack_data.get("ran_function_id", 3)
                
                if req_id is not None and inst_id is not None:
                    ric_req_key = (node_id, ran_fn_id, req_id, inst_id)
                    tx_info = self.pending_transactions.pop(ric_req_key, None)
                
                if not tx_info and isinstance(payload, bytes):
                    try:
                        data = json.loads(payload.decode('utf-8'))
                        tx_id = data.get("transaction_id")
                        if tx_id and tx_id in self.pending_transactions:
                            tx_info = self.pending_transactions.pop(tx_id)
                    except Exception:
                        pass
                        
                if tx_info:
                    logger.warning("RIC_CONTROL_FAILURE recebido para transação pendente", info=tx_info)
            except Exception as e:
                logger.debug(f"Erro ao processar RIC_CONTROL_FAILURE: {e}")
        logger.warning("Recebido RIC_CONTROL_FAILURE", summary=summary)
        if xapp_instance and sbuf:
            xapp_instance.rmr_free(sbuf)

    def inject_xapp_action(self, action: XAppAction):
        """API pública para injeção de ações simuladas (usada em testes)"""
        if not hasattr(action, 'arrival_monotonic') or action.arrival_monotonic is None:
            action.arrival_monotonic = time.perf_counter()
        with self.buffer_lock:
            if not self.proposal_buffer:
                self.window_start = time.perf_counter()
            self.proposal_buffer.append(action)
            if action.priority >= 80:
                self.window_start = 0.0
                self.flush_event.set()

    def _process_action_group(self, actions: List[XAppAction]):
        """
        Processa todas as ações acumuladas na Decision Window com instrumentação monotônica completa:
        1. Decompõe tempo de fila (T_queue) a partir do timestamp monotônico de chegada;
        2. Identifica conflitos (T_perception);
        3. Arbitra conflitos via ReasoningAgent (T_reasoning);
        4. Valida resoluções via RefinementAgent (T_refinement);
        5. Encodifica APER ASN.1 (T_e2_encode);
        6. Despacha via RMR (T_dispatch);
        7. Processa ações sem conflito (Pass-Through) com validação de segurança individual e métricas completas.
        """
        t0_perf = time.perf_counter()
        earliest_arrival = min((getattr(a, 'arrival_monotonic', t0_perf) for a in actions), default=t0_perf)
        t_queue_ms = (t0_perf - earliest_arrival) * 1000.0
        
        for act in actions:
            self.memory.add_action(act)
            
        t_perc_0 = time.perf_counter()
        conflicts = self.perception.register_action_group(actions)
        t_perc_ms = (time.perf_counter() - t_perc_0) * 1000.0
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
            
            # Telemetria com validação estrita de TTL por nó
            kpm_state = None
            context_available = True
            if conflict.involved_xapps:
                target_node = conflict.involved_xapps[0].node_id
                kpm_rep, is_valid_kpm = self.perception.get_kpm_report(target_node)
                if kpm_rep and is_valid_kpm:
                    kpm_state = {
                        "DRB.UEThpDl": kpm_rep.drb_thp_dl,
                        "DRB.UEThpUl": kpm_rep.drb_thp_ul,
                        "QoS.FlowDelay": kpm_rep.drb_delay_dl,
                        "RRU.PrbTotDl": float(kpm_rep.prb_used_dl)
                    }
                else:
                    context_available = False
                    logger.warning("Contexto KPM expirado ou indisponível (TTL > 1s). Encaminhamento conservador obrigatório para Heurística Segura.", node=target_node)
            
            t_reas_0 = time.perf_counter()
            if not context_available:
                resolution = self.reasoning._resolve_by_heuristic(conflict, time.time())
            else:
                resolution = self.reasoning.resolve(conflict, kpm_state=kpm_state)
            t_reas_ms = (time.perf_counter() - t_reas_0) * 1000.0
            
            t_ref_0 = time.perf_counter()
            is_valid, level, reason = self.refinement.validate(resolution, conflict)
            t_ref_ms = (time.perf_counter() - t_ref_0) * 1000.0
            
            t_proc_ms = t_perc_ms + t_reas_ms + t_ref_ms
            t_e2_encode_ms = 0.0
            t_e2_dispatch_ms = 0.0
            
            if is_valid and resolution.winning_actions:
                t_sel_now = time.perf_counter()
                for act in resolution.winning_actions:
                    act.t_selection = t_sel_now
                    logger.info("Conflito Resolvido", conflict=conflict.conflict_id, strategy=resolution.strategy_used.name, action=act.parameter)
                    _, enc_ms, disp_ms = self._send_control(act.node_id, act.parameter, act.value, action=act)
                    t_e2_encode_ms += enc_ms
                    t_e2_dispatch_ms += disp_ms
            elif not resolution.winning_actions:
                logger.info("ℹ️ Decisão No-Op / Deferida pelo MAPPO (nenhuma ação de controle despachada)")
            else:
                logger.warning("Resolução Rejeitada ou Lote Vazio / Quarentena", reason=reason)

            t_cycle_total_ms = t_queue_ms + t_proc_ms + t_e2_encode_ms + t_e2_dispatch_ms
            latency_total_s = t_cycle_total_ms / 1000.0
            
            logger.info(
                f"⏱️ Ciclo Total RDL Concluído em {t_cycle_total_ms:.2f}ms "
                f"(Espera Fila: {t_queue_ms:.2f}ms, Processamento: {t_proc_ms:.2f}ms [Percepção: {t_perc_ms:.2f}ms, Raciocínio: {t_reas_ms:.2f}ms, Refinamento: {t_ref_ms:.2f}ms], Codificação E2: {t_e2_encode_ms:.2f}ms, Despacho RMR: {t_e2_dispatch_ms:.2f}ms) [{self.transport_mode}]"
            )
            
            self.memory.add_resolution(resolution)
            self.metrics.record_resolution(resolution, latency_total_s)

        # 2. Despacho Contínuo de Ações Limpas (Conflict-Free Pass-Through Pipeline)
        clean_actions = [
            act for act in actions 
            if (act.node_id, act.parameter, act.xapp_id) not in conflicting_action_keys
        ]
        
        for clean_act in clean_actions:
            t_ref_clean_0 = time.perf_counter()
            clean_act.t_selection = t_ref_clean_0
            is_safe, level, reason = self.refinement.validate_single_action(clean_act)
            t_ref_clean_ms = (time.perf_counter() - t_ref_clean_0) * 1000.0
            
            if is_safe:
                logger.info("Ação Limpa Despachada (Pass-Through)", xapp=clean_act.xapp_id, param=clean_act.parameter, val=clean_act.value)
                _, enc_clean_ms, disp_clean_ms = self._send_control(clean_act.node_id, clean_act.parameter, clean_act.value, action=clean_act)
                t_clean_total_ms = t_queue_ms + t_ref_clean_ms + enc_clean_ms + disp_clean_ms
                logger.info(
                    f"⏱️ Ação Limpa (Pass-Through) Despachada em {t_clean_total_ms:.2f}ms "
                    f"(Espera Fila: {t_queue_ms:.2f}ms, Refinamento: {t_ref_clean_ms:.2f}ms, Codificação: {enc_clean_ms:.2f}ms, Despacho: {disp_clean_ms:.2f}ms)"
                )
            else:
                logger.warning("Ação Limpa Bloqueada pelo Safety Guard / Quarentena", reason=reason, param=clean_act.parameter)

    def _decision_loop(self):
        while self.running:
            # Espera reativa dirigida por eventos (fast-wake imediato para URLLC <= 0.5ms) ou timeout de 20ms
            self.flush_event.wait(timeout=0.02)
            self.flush_event.clear()
            
            with self.buffer_lock:
                if self.proposal_buffer:
                    elapsed_ms = (time.perf_counter() - self.window_start) * 1000 if self.window_start > 0 else 9999.0
                    if elapsed_ms >= self.WINDOW_DURATION_MS or self.window_start == 0.0:
                        # Flush Window
                        actions_to_process = list(self.proposal_buffer)
                        self.proposal_buffer.clear()
                        self.window_start = 0.0
                        logger.info(f"Decision Window Expired. Processing batch of {len(actions_to_process)} actions.")
                        
                        # Processa fora do lock para não travar RMR
                        threading.Thread(target=self._process_action_group, args=(actions_to_process,), daemon=True).start()

    def _send_control(self, node_id: str, parameter: str, value: float, action: Optional[XAppAction] = None, decision_id: Optional[str] = None) -> Tuple[bool, float, float]:
        """
        Codifica a PDU APER e despacha via RMR utilizando o RANBackendAdapter e RicRequestIdAllocator.
        Retorna: (success: bool, t_encode_ms: float, t_dispatch_ms: float)
        """
        t_enc_0 = time.perf_counter()
        if action:
            action.t_encode_start = t_enc_0
        
        ran_fn_id = 3
        req_id = self.allocator.allocate(
            node_id=node_id,
            ran_function_id=ran_fn_id,
            decision_id=decision_id,
            action_id=getattr(action, "action_id", None)
        )
        requestor_id = req_id.requestor_id
        instance_id = req_id.instance_id
        
        tx_id = str(uuid.uuid4())
        try:
            temp_action = action or XAppAction(xapp_id="cardl_core", node_id=node_id, parameter=parameter, value=value, priority=100)
            aper_bytes = self.backend.map_action_to_control_pdu(temp_action, requestor_id=requestor_id, instance_id=instance_id)
            
            payload_dict = {
                "transaction_id": tx_id,
                "decision_id": decision_id,
                "node_id": node_id,
                "parameter": parameter,
                "value": value,
                "requestor_id": requestor_id,
                "instance_id": instance_id,
                "ran_function_id": ran_fn_id,
                "header_aper_bytes": aper_bytes.hex() if isinstance(aper_bytes, bytes) else str(aper_bytes),
                "msg_aper_bytes": aper_bytes.hex() if isinstance(aper_bytes, bytes) else str(aper_bytes),
                "aper_bytes": aper_bytes.hex() if isinstance(aper_bytes, bytes) else str(aper_bytes),
                "transport_mode": self.transport_mode
            }
            payload_bytes = json.dumps(payload_dict).encode('utf-8')
            t_encode_ms = (time.perf_counter() - t_enc_0) * 1000.0
            
            t_disp_0 = time.perf_counter()
            if action:
                action.t_dispatch_start = t_disp_0
            # Verificação estrita de Dry-Run declarativo
            dry_run = self.config.get("control", {}).get("dry_run", False) or os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
            if dry_run:
                t_encode_ms = (time.perf_counter() - t_enc_0) * 1000.0
                logger.info("ℹ️ Dry-Run ativado: RIC_CONTROL_REQUEST simulado sem despacho via RMR socket", node_id=node_id, param=parameter, val=value, tx_id=tx_id)
                return True, t_encode_ms, 0.0

            ric_req_key = (node_id, ran_fn_id, requestor_id, instance_id)
            self.pending_transactions[tx_id] = {
                "t_dispatch_start": t_disp_0,
                "action": action,
                "node_id": node_id,
                "parameter": parameter,
                "value": value,
                "ric_req_key": ric_req_key
            }
            self.pending_transactions[ric_req_key] = self.pending_transactions[tx_id]

            # Seleciona formato do payload RMR (Octetos APER brutos no ambiente nativo O-RAN)
            if not self.is_mock_transport or os.getenv("RMR_RAW_PAYLOAD", "false").lower() in ("true", "1"):
                send_payload = aper_bytes
            else:
                send_payload = payload_bytes

            success = self.xapp.rmr_send(payload=send_payload, mtype=RIC_CONTROL_REQ)
            t_disp_end = time.perf_counter()
            t_dispatch_ms = (t_disp_end - t_disp_0) * 1000.0
            if action:
                action.t_dispatch_end = t_disp_end
        except Exception as e:
            logger.error(f"Falha ao gerar/despachar APER Control via backend {self.backend.metadata.backend_id}: {e}")
            t_encode_ms = (time.perf_counter() - t_enc_0) * 1000.0
            t_dispatch_ms = 0.0
            success = False
            if action:
                action.t_dispatch_end = time.perf_counter()
            
        if success:
            logger.info(
                "RIC_CONTROL_REQUEST despachado", 
                node_id=node_id, param=parameter, val=value, tx_id=tx_id,
                t_encode_ms=f"{t_encode_ms:.3f}ms", t_dispatch_ms=f"{t_dispatch_ms:.3f}ms",
                mode=self.transport_mode, backend=self.backend.metadata.backend_id
            )
        else:
            logger.error("Falha ao enviar RIC_CONTROL_REQUEST")
            
        return success, t_encode_ms, t_dispatch_ms

if __name__ == "__main__":
    app = RDLxApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.stop()
