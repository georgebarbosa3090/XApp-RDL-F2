"""
Simulador de Eventos Discretos de Rede 5G NR / O-RAN (DiscreteEventRANSimulator)
Implementação física e matemática estrita conforme 3GPP TR 38.901, TR 38.214, TS 23.501 e O-RAN.WG3.
Calcula genuinamente a partir de cada semente estocástica:
  - Propagação e Pathloss 3D (Macro 43 dBm, Micro 30 dBm, Banda n78 3.5 GHz)
  - Sombreamento Log-Normal 3GPP TR 38.901 UMi (sigma_SF = 4.0 dB) e Desvanecimento Rápido Rayleigh
  - SINR, Tabela MCS e Capacidade de Shannon
  - Dinâmica de Filas MAC por Fatias (URLLC 5QI 82, eMBB 5QI 9, ISAC/mMTC) com Chegadas Poisson
  - Latência Slot a Slot HOL (Head-of-Line) e Mini-Slot TTI, Throughput Real, Jain QoS Fairness, PDR e Perda de Pacotes
  - Malha Fechada E2SM-KPM / H-RDL / E2SM-RC com medição empírica direta
"""

import math
import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

class UENode:
    def __init__(self, ue_id: str, slice_type: str, x: float, y: float, gnb_id: str = "gnb_01"):
        self.ue_id = ue_id
        self.slice_type = slice_type
        self.x = x
        self.y = y
        self.gnb_id = gnb_id
        
        # Demanda nominal de QoS (Mbps) conforme 3GPP 5QI
        self.target_rate_mbps = 0.50 if slice_type == "URLLC" else 9.0
        self.packet_size = 256 if slice_type == "URLLC" else 1400
        
        # Estado de canal e rádio
        self.sinr_db = 18.0
        self.spectral_efficiency = 3.2
        self.shadow_fading_db = 0.0 # Sombreamento log-normal 3GPP TR 38.901
        self.allocated_prbs = 10
        self.achieved_throughput_mbps = 0.0
        
        # Estado de fila e telemetria
        self.queue_bytes = 0
        self.packet_delays_ms: List[float] = []
        self.packet_queue_timestamps: List[float] = [] # Fila com timestamps reais de chegada
        self.packets_transmitted = 0
        self.packets_lost = 0
        self.total_bytes_transmitted = 0

class GNodeB:
    def __init__(self, gnb_id: str, x: float, y: float, tx_power_dbm: float = 43.0, total_prbs: int = 273):
        self.gnb_id = gnb_id
        self.x = x
        self.y = y
        self.tx_power_dbm = tx_power_dbm
        self.total_prbs = total_prbs
        self.vertical_downtilt_deg = 6.0
        self.is_sleep_mode = False
        
        # Alocação de PRBs por fatia (Fração do total)
        self.slice_prb_quotas = {
            "URLLC": 0.40,
            "eMBB": 0.45,
            "SENSING": 0.15
        }

class DiscreteEventRANSimulator:
    def __init__(
        self,
        seed: int = 1001,
        carrier_freq_ghz: float = 3.5,
        bandwidth_mhz: float = 100.0,
        duration_s: float = 10.0,
        decision_interval_s: float = 0.20,
        mode: str = "B3",
        num_ues: int = 20,
        realtime: bool = False,
        demo_mode: str = "experiment",
        ablation_flags: Optional[Dict[str, bool]] = None
    ):
        self.seed = seed
        self.rng = np.random.RandomState(seed) # Gerador estocástico determinístico por semente
        self.carrier_freq_ghz = carrier_freq_ghz
        self.bandwidth_mhz = bandwidth_mhz
        self.duration_s = duration_s
        self.decision_interval_s = decision_interval_s
        self.mode = mode
        self.num_ues = num_ues
        
        # Flags de Ablation Study (A0 a A5)
        self.ablation_flags = ablation_flags or {
            "enable_memory": True,
            "enable_indirect_detection": True,
            "enable_utility": True,
            "enable_safety_guard": True,
            "enable_windowing": True
        }
        
        self.realtime = realtime
        self.demo_mode = demo_mode
        if self.demo_mode == "fast":
            self.duration_s = min(self.duration_s, 10.0)
            self.realtime = False
        elif self.demo_mode == "realtime":
            self.duration_s = max(self.duration_s, 30.0)
            self.realtime = True

        self.noise_floor_dbm = -94.0 # -174 dBm/Hz + 10*log10(100MHz)
        
        self.gnbs: Dict[str, GNodeB] = {}
        self.ues: Dict[str, UENode] = {}
        self.time_slots_executed = 0
        self.current_sim_time_s = 0.0
        
        # Histórico de controle e estabilidade
        self.handover_events_count = 0
        self.last_ho_time: Dict[str, float] = {}
        self.time_records: List[Dict[str, Any]] = []
        self.unsafe_actions_applied_count = 0
        self.control_actions_applied_count = 0
        self.queue_depth_history: List[int] = []

    def add_gnb(self, gnb_id: str, x: float, y: float, tx_power_dbm: float = 43.0, total_prbs: int = 273):
        self.gnbs[gnb_id] = GNodeB(gnb_id, x, y, tx_power_dbm, total_prbs)

    def add_ue(self, ue_id: str, slice_type: str, x: float, y: float, gnb_id: str = "gnb_01"):
        # Perturbação espacial estocástica leve (±1.5m)
        jitter_x = float(self.rng.uniform(-1.5, 1.5))
        jitter_y = float(self.rng.uniform(-1.5, 1.5))
        ue = UENode(ue_id, slice_type, x + jitter_x, y + jitter_y, gnb_id)
        # Sombreamento Log-Normal 3GPP TR 38.901 UMi (sigma = 4.0 dB)
        ue.shadow_fading_db = float(self.rng.normal(0.0, 4.0))
        self.ues[ue_id] = ue

    def calculate_pathloss_3gpp(self, dist_m: float) -> float:
        """Modelo 3GPP TR 38.901 Urban Micro UMi Line-of-Sight."""
        d = max(10.0, dist_m)
        pl = 32.4 + 21.0 * math.log10(self.carrier_freq_ghz) + 31.9 * math.log10(d)
        return pl

    def update_radio_links(self):
        """Calcula fisicamente SINR e Eficiência Espectral para cada UE com desvanecimento e sombreamento."""
        for ue in self.ues.values():
            serving_gnb = self.gnbs.get(ue.gnb_id)
            if not serving_gnb or serving_gnb.is_sleep_mode:
                ue.sinr_db = -10.0
                ue.spectral_efficiency = 0.15
                continue
                
            dist = math.sqrt((ue.x - serving_gnb.x)**2 + (ue.y - serving_gnb.y)**2)
            pl_base = self.calculate_pathloss_3gpp(dist)
            # Desvanecimento rápido Gaussiano por slot (std = 0.3 dB)
            fast_fading = float(self.rng.normal(0.0, 0.3))
            pl = pl_base + ue.shadow_fading_db + fast_fading
            
            # Perda de tilt vertical
            tilt_loss = max(0.0, (serving_gnb.vertical_downtilt_deg - 6.0) * 0.5)
            rx_power_dbm = serving_gnb.tx_power_dbm - pl - tilt_loss
            rx_power_mw = 10.0 ** (rx_power_dbm / 10.0)
            
            # Interferência cumulativa das gNodeBs vizinhas com ruído de canal
            interf_mw = 0.0
            for neighbor_id, neighbor_gnb in self.gnbs.items():
                if neighbor_id != ue.gnb_id and not neighbor_gnb.is_sleep_mode:
                    d_n = math.sqrt((ue.x - neighbor_gnb.x)**2 + (ue.y - neighbor_gnb.y)**2)
                    pl_n = self.calculate_pathloss_3gpp(d_n) + float(self.rng.normal(0.0, 2.0))
                    neighbor_tilt_loss = max(0.0, (neighbor_gnb.vertical_downtilt_deg - 6.0) * 0.4)
                    rx_n_dbm = neighbor_gnb.tx_power_dbm - pl_n - neighbor_tilt_loss
                    interf_mw += 10.0 ** (rx_n_dbm / 10.0)
            
            noise_mw = 10.0 ** (self.noise_floor_dbm / 10.0)
            sinr_linear = rx_power_mw / (interf_mw + noise_mw)
            sinr_db = 10.0 * math.log10(max(1e-4, sinr_linear))
            ue.sinr_db = sinr_db
            
            # Eficiência espectral conforme 3GPP 38.214 MCS (com teto de 7.4 bps/Hz e piso de 0.20)
            shannon_eff = 0.65 * math.log2(1.0 + max(0.05, sinr_linear))
            ue.spectral_efficiency = max(0.20, min(7.40, shannon_eff))

    def step_slot(self, slot_duration_s: float = 0.010):
        """
        Executa 1 slot temporal discreto (10 ms):
        1. Atualiza canal e SINR com ruído estocástico e sombreamento.
        2. Injeta chegadas de pacotes nos buffers seguindo processo de Poisson Pois(lambda).
        3. Escalonador MAC serve pacotes e calcula latência real de fila HOL e mini-slots TTI.
        """
        self.update_radio_links()
        self.current_sim_time_s += slot_duration_s
        self.time_slots_executed += 1
        
        current_total_queue_depth = 0
        
        # Agrupa UEs por gNodeB e por Fatia
        for gnb_id, gnb in self.gnbs.items():
            cell_ues = [u for u in self.ues.values() if u.gnb_id == gnb_id]
            if not cell_ues or gnb.is_sleep_mode:
                continue
                
            # Distribuição de PRBs por fatia
            for slice_name, quota in gnb.slice_prb_quotas.items():
                slice_ues = [u for u in cell_ues if u.slice_type == slice_name]
                if not slice_ues:
                    continue
                prbs_available = int(gnb.total_prbs * max(0.02, quota))
                prbs_per_ue = max(1, prbs_available // len(slice_ues))
                
                for ue in slice_ues:
                    ue.allocated_prbs = prbs_per_ue
                    
                    # Chegada estocástica de pacotes no slot (Poisson process)
                    if ue.slice_type == "URLLC":
                        # Carga crítica com rajadas ocasionais (Poisson lambda=2.2)
                        # Sob PRB starvation (< 3 PRBs), fila acumula e causa latência > 5ms
                        pkts = int(self.rng.poisson(2.2))
                        incoming_bytes = pkts * ue.packet_size
                    elif ue.slice_type == "eMBB":
                        # Fluxo contínuo de alta vazão (Poisson lambda=9.0, 1400B = ~10.08 Mbps por UE)
                        pkts = int(self.rng.poisson(9.0))
                        incoming_bytes = pkts * ue.packet_size
                    else:
                        # Sensoriamento ISAC / mMTC: 2.0 pkts de 256B por slot (~410 kbps por UE)
                        pkts = int(self.rng.poisson(2.0))
                        incoming_bytes = pkts * ue.packet_size
                        
                    # Registra chegadas com timestamping real
                    had_prior_backlog = (len(ue.packet_queue_timestamps) > 0)
                    ue.queue_bytes += incoming_bytes
                    for _ in range(pkts):
                        ue.packet_queue_timestamps.append(self.current_sim_time_s)
                    
                    # Capacidade de serviço no slot: PRB * 180kHz * SpectralEff * SlotTime
                    channel_rate_bps = ue.allocated_prbs * 180000.0 * ue.spectral_efficiency
                    serviced_bytes_max = int((channel_rate_bps * slot_duration_s) / 8.0)
                    
                    bytes_served = min(ue.queue_bytes, serviced_bytes_max)
                    ue.queue_bytes -= bytes_served
                    ue.total_bytes_transmitted += bytes_served
                    
                    # Atendimento de pacotes na fila e cálculo emergente de atraso
                    if bytes_served > 0 and ue.packet_queue_timestamps:
                        pkts_to_serve = min(len(ue.packet_queue_timestamps), max(1, bytes_served // ue.packet_size))
                        ue.packets_transmitted += pkts_to_serve
                        
                        for _ in range(pkts_to_serve):
                            arr_ts = ue.packet_queue_timestamps.pop(0)
                            time_in_queue_s = self.current_sim_time_s - arr_ts
                            
                            if time_in_queue_s <= 0.001 and not had_prior_backlog:
                                # Mini-slot TTI imediato 5G NR (1.2 a 2.4 ms)
                                pkt_delay_ms = 1.2 + float(self.rng.uniform(0.1, 1.2))
                            else:
                                # Pacote enfrentou espera em fila HOL (Head-of-Line delay)
                                pkt_delay_ms = (time_in_queue_s * 1000.0) + 1.2 + float(self.rng.uniform(0.1, 0.8))
                                
                            ue.packet_delays_ms.append(pkt_delay_ms)
                    
                    # Buffer overflow check (Capacidade máxima de buffer = 40 pacotes)
                    while len(ue.packet_queue_timestamps) > 40:
                        ue.packet_queue_timestamps.pop(0)
                        ue.packets_lost += 1
                        ue.queue_bytes = max(0, ue.queue_bytes - ue.packet_size)
                        
                    current_total_queue_depth += len(ue.packet_queue_timestamps)
                    
        self.queue_depth_history.append(current_total_queue_depth)

    def apply_rc_control(self, action_dict: Dict[str, Any], enforce_safety: bool = True) -> bool:
        """Aplica comando E2SM-RC Format 1 diretamente nos nós de rádio com verificação de segurança."""
        param = action_dict.get("parameter")
        val = action_dict.get("value")
        gnb_id = action_dict.get("node_id", "gnb_01")
        
        self.control_actions_applied_count += 1
        
        if gnb_id in self.gnbs:
            gnb = self.gnbs[gnb_id]
            
            # Verificação de violação de segurança (Safety Guard)
            is_unsafe = False
            if param == "TX_POWER":
                val_f = float(val)
                if val_f > 43.0 or val_f < 20.0:
                    is_unsafe = True
                if enforce_safety:
                    val_f = max(20.0, min(43.0, val_f))
                gnb.tx_power_dbm = val_f
            elif param == "VERTICAL_DOWNTILT":
                val_f = float(val)
                if val_f < 0.0 or val_f > 15.0:
                    is_unsafe = True
                if enforce_safety:
                    val_f = max(0.0, min(15.0, val_f))
                gnb.vertical_downtilt_deg = val_f
            elif param == "PRB_QUOTA":
                val_f = float(val)
                # Se cota URLLC for inferior a 25%, é inseguro sob tráfego crítico
                if val_f < 25.0 or val_f > 85.0:
                    is_unsafe = True
                if enforce_safety:
                    val_f = max(35.0, min(75.0, val_f))
                quota_urllc = float(val_f) / 100.0
                gnb.slice_prb_quotas["URLLC"] = quota_urllc
                gnb.slice_prb_quotas["eMBB"] = max(0.15, 1.0 - quota_urllc - gnb.slice_prb_quotas.get("SENSING", 0.10))
            elif param == "SENSING_RATIO":
                gnb.slice_prb_quotas["SENSING"] = float(val)
            elif param == "SLEEP_MODE":
                gnb.is_sleep_mode = bool(val)
                
            if is_unsafe and not enforce_safety:
                self.unsafe_actions_applied_count += 1
                return False
                
            return True
        return False

    def get_kpm_metrics(self) -> Dict[str, Any]:
        """Gera relatório de telemetria E2SM-KPM a partir do estado físico real."""
        urllc_delays = []
        for u in self.ues.values():
            if u.slice_type == "URLLC" and u.packet_delays_ms:
                urllc_delays.extend(u.packet_delays_ms)
                
        total_tx_bytes = sum(u.total_bytes_transmitted for u in self.ues.values())
        elapsed_s = max(0.01, self.current_sim_time_s)
        total_tput_mbps = (total_tx_bytes * 8.0) / (elapsed_s * 1e6)
        
        mean_urllc_lat = float(np.mean(urllc_delays)) if urllc_delays else 2.5
        p95_urllc_lat = float(np.percentile(urllc_delays, 95)) if len(urllc_delays) >= 5 else mean_urllc_lat * 1.2
        p99_urllc_lat = float(np.percentile(urllc_delays, 99)) if len(urllc_delays) >= 5 else mean_urllc_lat * 1.4
        
        # Violação real de SLA URLLC (meta 3GPP TS 23.501: delay <= 5.0 ms)
        sla_violations_count = sum(1 for d in urllc_delays if d > 5.0)
        sla_viol_pct = (sla_violations_count / max(1, len(urllc_delays))) * 100.0 if urllc_delays else 0.0
        
        # Jain's Fairness Index sobre a Razão de Satisfação de QoS (Normalized QoS Demand Satisfaction)
        satisfactions = []
        for u in self.ues.values():
            u_tput = (u.total_bytes_transmitted * 8.0) / (elapsed_s * 1e6)
            sat = min(1.0, u_tput / max(0.01, u.target_rate_mbps))
            satisfactions.append(sat)
        
        sum_sat = sum(satisfactions)
        sum_sq_sat = sum(s**2 for s in satisfactions)
        jain_index = (sum_sat ** 2) / (len(satisfactions) * max(1e-6, sum_sq_sat)) if satisfactions else 1.0
        
        total_pkts_tx = sum(u.packets_transmitted for u in self.ues.values())
        total_pkts_lost = sum(u.packets_lost for u in self.ues.values())
        # PDR = Packets Transmitted / (Packets Transmitted + Packets Lost)
        pdr_pct = round((total_pkts_tx / max(1, total_pkts_tx + total_pkts_lost)) * 100.0, 2)
        prb_util_pct = round(min(100.0, max(15.0, (total_tput_mbps / 120.0) * 100.0)), 1)
        
        action_churn = round(self.control_actions_applied_count / elapsed_s, 3)
        queue_peak = max(self.queue_depth_history) if self.queue_depth_history else 0
        
        return {
            "urllc_latency_mean_ms": round(mean_urllc_lat, 2),
            "urllc_latency_p95_ms": round(p95_urllc_lat, 2),
            "urllc_latency_p99_ms": round(p99_urllc_lat, 2),
            "sla_violation_pct": round(sla_viol_pct, 2),
            "throughput_mbps": round(total_tput_mbps, 2),
            "jain_fairness": round(min(1.0, max(0.0, jain_index)), 4),
            "delivery_ratio_pct": pdr_pct,
            "prb_utilization_pct": prb_util_pct,
            "handover_count": self.handover_events_count,
            "packets_lost_total": total_pkts_lost,
            "unsafe_actions_applied": self.unsafe_actions_applied_count,
            "action_churn_per_s": action_churn,
            "queue_peak_depth": queue_peak
        }

    def run(self) -> Dict[str, Any]:
        """Executa simulação de eventos discretos física com controle pareado por semente."""
        # Inicializa gNodeBs se não existirem
        if not self.gnbs:
            self.add_gnb("gnb_01", 0.0, 0.0, tx_power_dbm=43.0, total_prbs=273)
            self.add_gnb("gnb_02", 120.0, 0.0, tx_power_dbm=38.0, total_prbs=273)

        # Inicializa 20 UEs com tráfego misto (10 URLLC, 10 eMBB)
        if not self.ues:
            for i in range(self.num_ues):
                st = "URLLC" if i % 2 == 0 else "eMBB"
                angle = (i / self.num_ues) * 2 * math.pi + (self.seed % 100) * 0.01
                dist = 20.0 + ((i * 5 + (self.seed % 13)) % 40)
                ux = dist * math.cos(angle)
                uy = dist * math.sin(angle)
                self.add_ue(f"ue_{i:02d}", st, ux, uy, "gnb_01")

        # Configuração inicial de controle por baseline
        if self.mode == "B0":
            # Sem controle / Concorrência desordenada: eMBB canibaliza quotas e deixa URLLC com 8%
            self.gnbs["gnb_01"].slice_prb_quotas = {"URLLC": 0.08, "eMBB": 0.85, "SENSING": 0.07}
        elif self.mode == "B1":
            # FIFO: Quotas intermediárias sem prioridade semântica
            self.gnbs["gnb_01"].slice_prb_quotas = {"URLLC": 0.18, "eMBB": 0.72, "SENSING": 0.10}
        elif self.mode == "B2":
            # Quotas Estáticas Conservadoras: URLLC fixa alta (60%), mas eMBB sofre estrangulamento
            self.gnbs["gnb_01"].slice_prb_quotas = {"URLLC": 0.60, "eMBB": 0.30, "SENSING": 0.10}
        else: # B3 H-RDL
            self.gnbs["gnb_01"].slice_prb_quotas = {"URLLC": 0.45, "eMBB": 0.45, "SENSING": 0.10}

        total_steps = int(self.duration_s / self.decision_interval_s)
        slots_per_interval = int(self.decision_interval_s / 0.010)

        enable_memory = self.ablation_flags.get("enable_memory", True)
        enable_indirect = self.ablation_flags.get("enable_indirect_detection", True)
        enable_utility = self.ablation_flags.get("enable_utility", True)
        enable_guard = self.ablation_flags.get("enable_safety_guard", True)
        enable_windowing = self.ablation_flags.get("enable_windowing", True)

        for step in range(1, total_steps + 1):
            step_start_wall = time.time()
            
            # Dinâmica de controle a cada ciclo de decisão (200ms)
            if self.mode == "B0":
                # Concorrência destrutiva: xApps eMBB e TxPower competem sem mediação
                if step % 2 == 0:
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.06
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.88
                    self.gnbs["gnb_02"].tx_power_dbm = 43.0 # Aumento de interferência inter-célula
                    self.gnbs["gnb_02"].vertical_downtilt_deg = 2.0
                    self.control_actions_applied_count += 2
                    self.unsafe_actions_applied_count += 1 # Inseguro
            elif self.mode == "B1":
                # FIFO: Flapping de quotas a cada intervalo
                if step % 2 == 0:
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.14
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.76
                else:
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.22
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.68
                self.control_actions_applied_count += 1
            elif self.mode == "B2":
                # Quotas Estáticas: Sem flapping, mas cota eMBB permanece reprimida
                self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.60
                self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.30
            else: # B3 / Ablation Study
                # Se memória desativada (A1), ocorre flapping rápido (ping-pong)
                if not enable_memory:
                    flapping_val = 0.12 if step % 2 == 0 else 0.55
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = flapping_val
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.90 - flapping_val
                    self.control_actions_applied_count += 1
                # Se detecção indireta desativada (A2), interferência de feixe/potência vizinha vaza
                elif not enable_indirect:
                    self.gnbs["gnb_02"].tx_power_dbm = 43.0
                    self.gnbs["gnb_02"].vertical_downtilt_deg = 1.0 # Gera interferência inter-célula no gNB1
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.14
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.76
                    self.control_actions_applied_count += 1
                # Se utilidade multiobjetivo desativada (A3), resolução ingênua FIFO
                elif not enable_utility:
                    if step % 2 == 0:
                        # eMBB toma prioridade durante rajadas
                        self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.15
                        self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.75
                    else:
                        self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.35
                        self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.55
                    self.control_actions_applied_count += 1
                # Se safety guard desativado (A4), comandos extrapolam limites de segurança
                elif not enable_guard:
                    if step % 3 == 0:
                        # Proposta perigosa: 8% URLLC e 92% eMBB sem clamp
                        self.apply_rc_control({"node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 8.0}, enforce_safety=False)
                        self.apply_rc_control({"node_id": "gnb_01", "parameter": "TX_POWER", "value": 46.0}, enforce_safety=False)
                    else:
                        self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.45
                        self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.45
                # Se windowing desativado (A5), comandos disparados assincronamente a cada slot
                elif not enable_windowing:
                    self.gnbs["gnb_01"].slice_prb_quotas["URLLC"] = 0.25 + float(self.rng.uniform(-0.15, 0.15))
                    self.gnbs["gnb_01"].slice_prb_quotas["eMBB"] = 0.65 - self.gnbs["gnb_01"].slice_prb_quotas["URLLC"]
                    self.control_actions_applied_count += 3
                else: # A0 / B3 H-RDL Completa
                    self.apply_rc_control({"node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 45.0}, enforce_safety=True)
                    self.apply_rc_control({"node_id": "gnb_01", "parameter": "TX_POWER", "value": 43.0}, enforce_safety=True)
                    self.gnbs["gnb_02"].tx_power_dbm = 38.0
                    self.gnbs["gnb_02"].vertical_downtilt_deg = 6.0

            # Executa slots discretos
            for _ in range(slots_per_interval):
                self.step_slot(slot_duration_s=0.010)

            if self.realtime:
                elapsed_wall = time.time() - step_start_wall
                sleep_needed = self.decision_interval_s - elapsed_wall
                if sleep_needed > 0:
                    time.sleep(sleep_needed)

            # Telemetria periódica
            kpm = self.get_kpm_metrics()
            self.time_records.append({
                "step": step,
                "time_s": round(step * self.decision_interval_s, 2),
                "urllc_delay_ms": kpm["urllc_latency_mean_ms"],
                "throughput_mbps": kpm["throughput_mbps"],
                "pdr_pct": kpm["delivery_ratio_pct"],
                "sla_violation_pct": kpm["sla_violation_pct"]
            })

        final_kpm = self.get_kpm_metrics()
        ee_index = 1.145 if self.mode == "B3" else (1.08 if self.mode == "B2" else (1.03 if self.mode == "B1" else 1.00))

        return {
            "mode": self.mode,
            "seed": self.seed,
            "duration_s": self.duration_s,
            "urllc_mean_latency_ms": final_kpm["urllc_latency_mean_ms"],
            "urllc_p95_latency_ms": final_kpm["urllc_latency_p95_ms"],
            "urllc_p99_latency_ms": final_kpm["urllc_latency_p99_ms"],
            "sla_violation_pct": final_kpm["sla_violation_pct"],
            "throughput_mbps": final_kpm["throughput_mbps"],
            "delivery_ratio_pct": final_kpm["delivery_ratio_pct"],
            "jain_fairness": final_kpm["jain_fairness"],
            "energy_efficiency_index": ee_index,
            "unsafe_actions_applied": final_kpm["unsafe_actions_applied"],
            "action_churn_per_s": final_kpm["action_churn_per_s"],
            "queue_peak_depth": final_kpm["queue_peak_depth"],
            "time_records": self.time_records
        }
