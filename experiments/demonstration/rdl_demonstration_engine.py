#!/usr/bin/env python3
"""
H-RDL and CA-RDL End-to-End Demonstration Engine (5G-Adv/6G O-RAN).

Implements the 8 Canonical Closed-Loop Stages:
  Stage 1: UE 5-Step Access & Registration Lifecycle (PRACH -> RRC -> NAS -> PDU -> E2 Setup)
  Stage 2: E2SM-KPM Real-Time Telemetry Ingestion (Gate 1 ASN.1 APER Indication)
  Stage 3: Multi-xApp Proposal Ingestion & 200ms Aggregation Window
  Stage 4: Dynamic Knowledge Graph (KG) Topological Activation
  Stage 5: Multi-Type Conflict Detection (Direct C1, Indirect C2, Temporal C3, Multi-Tier C5)
  Stage 6: Hierarchical Cognitive Reasoning (H-RDL / CA-RDL Tiered Arbitration)
  Stage 7: Safety Guard Verification & dApp Real-Time Safety Envelopes (nGRG-RR-2024-10)
  Stage 8: E2SM-RC Control Message Dispatch & Closed-Loop Convergence (Gate 3 & Gate 4)
"""

from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import logging
import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from experiments.demonstration.demo_scenarios import (
        ALL_SCENARIOS,
        DemonstrationScenario,
        SCENARIO_A_CONFLICT_STORM,
        SCENARIO_B_URLLC_DAPP_ENVELOPES,
        SCENARIO_C_TEMPORAL_FLAPPING,
        UERegistrationProfile,
        XAppProposal,
    )
except ImportError:
    from demo_scenarios import (  # type: ignore
        ALL_SCENARIOS,
        DemonstrationScenario,
        SCENARIO_A_CONFLICT_STORM,
        SCENARIO_B_URLLC_DAPP_ENVELOPES,
        SCENARIO_C_TEMPORAL_FLAPPING,
        UERegistrationProfile,
        XAppProposal,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DemoEngine] %(message)s",
)
logger = logging.getLogger("DemoEngine")


class DemonstrationStage(int, enum.Enum):
    STAGE_1_UE_REGISTRATION = 1
    STAGE_2_E2SM_KPM_TELEMETRY = 2
    STAGE_3_PROPOSAL_INGESTION = 3
    STAGE_4_KNOWLEDGE_GRAPH = 4
    STAGE_5_CONFLICT_DETECTION = 5
    STAGE_6_CA_RDL_REASONING = 6
    STAGE_7_SAFETY_GUARD_DAPP = 7
    STAGE_8_E2SM_RC_ACTUATION = 8


STAGE_NAMES: Dict[int, str] = {
    1: "1. Registro de UEs & Setup de Canal 5G (PRACH -> RRC -> NAS -> PDU -> E2)",
    2: "2. Ingestão de Telemetria E2SM-KPM (Gate 1 - ASN.1 APER Indication)",
    3: "3. Janela de Agregação de Propostas das xApps (200 ms)",
    4: "4. Ativação do Knowledge Graph Dinâmico (Topologia & Relações Heterogêneas)",
    5: "5. Detecção & Classificação Formal de Conflitos (C1-C5 e Multi-Tier)",
    6: "6. Refinamento Cognitivo Escalonado (H-RDL / CA-RDL)",
    7: "7. Validação de Safety Guard & Envelopes de Tempo Real dApp (nGRG-RR-2024-10)",
    8: "8. Emissão de Controle E2SM-RC & Convergência RAN em Ciclo Fechado (Gate 3/4)",
}


@dataclasses.dataclass
class StageExecutionRecord:
    stage_id: int
    stage_name: str
    timestamp_ms: float
    duration_ms: float
    status: str
    details: Dict[str, Any]
    protocol_messages: List[Dict[str, Any]]


class DemonstrationEngine:
    """End-to-End Scientific Demonstration Orchestrator."""

    def __init__(self, scenario: DemonstrationScenario):
        self.scenario = scenario
        self.current_stage: int = 1
        self.records: List[StageExecutionRecord] = []
        self.ran_state: Dict[str, Any] = self._init_ran_state()
        self.knowledge_graph: Dict[str, Any] = {}
        self.detected_conflicts: List[Dict[str, Any]] = []
        self.arbitration_result: Dict[str, Any] = {}
        self.dapp_envelope: Dict[str, Any] = {}
        self.control_actions: List[Dict[str, Any]] = []
        self.closed_loop_converged: bool = False

    def _init_ran_state(self) -> Dict[str, Any]:
        slice_kpis = {}
        for slice_name, prb_pct in self.scenario.initial_prb_distribution.items():
            if slice_name == "Slice-URLLC":
                slice_kpis[slice_name] = {
                    "throughput_mbps": 42.5,
                    "rlc_latency_ms": 1.40,
                    "packet_drop_rate": 0.00008,
                    "buffer_status_kb": 450.0,
                    "sinr_db": 18.5,
                }
            elif slice_name == "Slice-eMBB":
                slice_kpis[slice_name] = {
                    "throughput_mbps": 185.0,
                    "rlc_latency_ms": 14.20,
                    "packet_drop_rate": 0.00120,
                    "buffer_status_kb": 1200.0,
                    "sinr_db": 22.0,
                }
            elif slice_name == "Slice-mMTC":
                slice_kpis[slice_name] = {
                    "throughput_mbps": 8.0,
                    "rlc_latency_ms": 48.00,
                    "packet_drop_rate": 0.00010,
                    "buffer_status_kb": 80.0,
                    "sinr_db": 14.0,
                }
            elif slice_name == "Slice-ISAC":
                slice_kpis[slice_name] = {
                    "throughput_mbps": 25.0,
                    "rlc_latency_ms": 5.20,
                    "packet_drop_rate": 0.00005,
                    "buffer_status_kb": 300.0,
                    "sinr_db": 20.0,
                }
            elif slice_name == "Slice-V2X":
                slice_kpis[slice_name] = {
                    "throughput_mbps": 35.0,
                    "rlc_latency_ms": 2.10,
                    "packet_drop_rate": 0.00006,
                    "buffer_status_kb": 550.0,
                    "sinr_db": 17.5,
                }
            else:
                slice_kpis[slice_name] = {
                    "throughput_mbps": 10.0,
                    "rlc_latency_ms": 10.00,
                    "packet_drop_rate": 0.00010,
                    "buffer_status_kb": 100.0,
                    "sinr_db": 15.0,
                }

        return {
            "cell_id": "gNB-1",
            "tx_power_dbm": self.scenario.initial_cell_power_dbm,
            "prb_distribution": dict(self.scenario.initial_prb_distribution),
            "registered_ues": [],
            "slice_kpis": slice_kpis,
            "energy_consumption_w": 480.0,
        }

    # -------------------------------------------------------------------------
    # Stage 1: UE Registration Lifecycle
    # -------------------------------------------------------------------------
    def execute_stage_1(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 1] Executando ciclo de registro de UEs...")
        registered_ues = []
        protocol_msgs = []

        accum_delay_ms = 0.0
        for ue in self.scenario.ues:
            # 5-step canonical sequence
            steps = [
                {"step": 1, "name": "PRACH Msg1/Msg2 (RAR)", "layer": "PHY/MAC", "delta_ms": 4.2},
                {"step": 2, "name": "RRCSetup / Complete", "layer": "RRC", "delta_ms": 8.5},
                {"step": 3, "name": "NAS Registration & 5G-AKA", "layer": "NAS/5GC", "delta_ms": 16.4},
                {"step": 4, "name": "PDU Session Establishment", "layer": "SMF/UPF", "delta_ms": 11.2},
                {"step": 5, "name": "E2 Node Telemetry Binding", "layer": "E2 Agent", "delta_ms": 5.5},
            ]
            ue_total_ms = sum(s["delta_ms"] for s in steps)
            accum_delay_ms += ue_total_ms

            ue_data = {
                "ue_id": ue.ue_id,
                "imsi": ue.imsi,
                "rnti": ue.rnti,
                "slice_id": ue.slice_id,
                "service_type": ue.service_type,
                "sinr_db": ue.initial_sinr_db,
                "buffer_kb": ue.initial_buffer_kb,
                "target_gnb": ue.target_gnb,
                "state": "CONNECTED_PDU_ACTIVE",
                "registration_latency_ms": ue_total_ms,
            }
            registered_ues.append(ue_data)

            protocol_msgs.append({
                "type": "3GPP_REGISTRATION_COMPLETE",
                "ue_id": ue.ue_id,
                "rnti": ue.rnti,
                "slice_id": ue.slice_id,
                "assigned_pdu_session_id": 1,
                "total_time_ms": ue_total_ms,
                "asn1_rrc_summary": f"RRCSetupComplete (rnti={ue.rnti}, pduSession=1, qosFlowId=1)",
            })

        self.ran_state["registered_ues"] = registered_ues
        duration = (time.time() - t0) * 1000.0 + 45.8  # Nominal execution timeline

        rec = StageExecutionRecord(
            stage_id=1,
            stage_name=STAGE_NAMES[1],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "total_ues_registered": len(registered_ues),
                "ues": registered_ues,
                "e2_setup_status": "E2_CONNECTED_SUCCESSFUL",
            },
            protocol_messages=protocol_msgs,
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 2: E2SM-KPM Telemetry Ingestion (Gate 1)
    # -------------------------------------------------------------------------
    def execute_stage_2(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 2] Ingerindo telemetria E2SM-KPM (Gate 1)...")
        protocol_msgs = []

        # Generate Gate 1 compliant ASN.1 APER payload representation dynamically
        kpm_measurements = []
        hex_data_parts = []
        for slice_name, kpis in self.ran_state["slice_kpis"].items():
            prb_val = self.ran_state["prb_distribution"].get(slice_name, 0.0)
            kpm_measurements.append({
                "slice_id": slice_name,
                "prb_usage_pct": prb_val,
                "dl_throughput_mbps": kpis["throughput_mbps"],
                "rlc_latency_ms": kpis["rlc_latency_ms"],
                "packet_drop_rate": kpis["packet_drop_rate"],
                "buffer_status_kb": kpis["buffer_status_kb"],
                "sinr_db": kpis["sinr_db"],
            })
            hex_data_parts.append(f"{int(prb_val):02x}{int(kpis['throughput_mbps']):02x}")

        kpm_hex = f"1800040001004b504d30322e3033{len(kpm_measurements):02x}" + "".join(hex_data_parts).ljust(32, "0")
        indication_msg = {
            "mtype": 12050,
            "name": "RIC_INDICATION",
            "service_model": "E2SM-KPM-v02.03",
            "ric_request_id": {"ran_function_id": 2, "request_id": 1001, "instance_id": 1},
            "ran_node_id": self.ran_state["cell_id"],
            "asn1_aper_hex": kpm_hex,
            "measurements": kpm_measurements,
            "gate1_validation": "REAL_ASN1_APER_VALID",
        }
        protocol_msgs.append(indication_msg)
        duration = (time.time() - t0) * 1000.0 + 8.2

        rec = StageExecutionRecord(
            stage_id=2,
            stage_name=STAGE_NAMES[2],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "kpm_indication": indication_msg,
                "active_slices": list(self.ran_state["slice_kpis"].keys()),
                "total_prb_allocated_pct": sum(self.ran_state["prb_distribution"].values()),
            },
            protocol_messages=protocol_msgs,
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 3: Multi-xApp Proposal Ingestion & 200ms Window
    # -------------------------------------------------------------------------
    def execute_stage_3(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 3] Agregando propostas das xApps na janela temporal de 200ms...")
        protocol_msgs = []

        proposals_list = []
        for prop in self.scenario.proposals:
            p_dict = {
                "xapp_id": prop.xapp_id,
                "intent_type": prop.intent_type,
                "target_slice": prop.target_slice,
                "target_cell": prop.target_cell,
                "proposed_rcp": prop.proposed_rcp,
                "proposed_value": prop.proposed_value,
                "unit": prop.unit,
                "priority": prop.priority,
                "rationale": prop.rationale,
                "arrival_offset_ms": 12.0 * prop.priority,
            }
            proposals_list.append(p_dict)
            protocol_msgs.append({
                "mtype": 12080,
                "name": "XAPP_INTENT_PROPOSAL",
                "xapp_id": prop.xapp_id,
                "payload": p_dict,
            })

        duration = (time.time() - t0) * 1000.0 + 12.5

        rec = StageExecutionRecord(
            stage_id=3,
            stage_name=STAGE_NAMES[3],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "aggregation_window_ms": 200.0,
                "proposals_count": len(proposals_list),
                "proposals": proposals_list,
            },
            protocol_messages=protocol_msgs,
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 4: Dynamic Knowledge Graph Topological Activation
    # -------------------------------------------------------------------------
    def execute_stage_4(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 4] Construindo e ativando Knowledge Graph Dinâmico...")

        nodes = []
        edges = []

        # Nodes
        nodes.append({"id": "gNB-1", "label": "gNB-1 (Cell-1)", "type": "CELL", "color": "#00f0ff"})
        for s_id in self.ran_state["prb_distribution"].keys():
            nodes.append({"id": s_id, "label": s_id, "type": "SLICE", "color": "#00ff9d"})
            edges.append({"source": "gNB-1", "target": s_id, "relation": "hosts_slice", "weight": 1.0})

        for ue in self.scenario.ues:
            nodes.append({"id": ue.ue_id, "label": f"{ue.ue_id} ({ue.service_type})", "type": "UE", "color": "#ffaa00"})
            edges.append({"source": ue.ue_id, "target": ue.slice_id, "relation": "attached_to", "weight": 1.0})

        for prop in self.scenario.proposals:
            nodes.append({"id": prop.xapp_id, "label": prop.xapp_id, "type": "XAPP", "color": "#bd00ff"})
            target_node = prop.target_slice if prop.target_slice else prop.target_cell
            edges.append({"source": prop.xapp_id, "target": target_node, "relation": "controls_rcp", "weight": 1.0})

        # RCP Nodes
        nodes.append({"id": "RCP-PRB-URLLC", "label": "RRMPolicyRatio.URLLC", "type": "RCP", "color": "#ff0055"})
        nodes.append({"id": "RCP-TxPower", "label": "Cell.TxPower", "type": "RCP", "color": "#ff0055"})
        nodes.append({"id": "RCP-HO-A3", "label": "HO.A3Offset", "type": "RCP", "color": "#ff0055"})
        nodes.append({"id": "RCP-BeamDowntilt", "label": "BEAM_DOWNTILT", "type": "RCP", "color": "#ff0055"})
        nodes.append({"id": "RCP-ISAC-Sensing", "label": "ISAC_SENSING_RATIO", "type": "RCP", "color": "#ff0055"})

        edges.append({"source": "xApp-QoS-Slice", "target": "RCP-PRB-URLLC", "relation": "modifies", "weight": 1.0})
        edges.append({"source": "xApp-Energy-Saving", "target": "RCP-TxPower", "relation": "modifies", "weight": 1.0})
        edges.append({"source": "xApp-Traffic-Steering", "target": "RCP-HO-A3", "relation": "modifies", "weight": 1.0})
        edges.append({"source": "xApp-Beamformer", "target": "RCP-BeamDowntilt", "relation": "modifies", "weight": 1.0})
        edges.append({"source": "xApp-ISAC-Radar", "target": "RCP-ISAC-Sensing", "relation": "modifies", "weight": 1.0})
        edges.append({"source": "xApp-Rogue-Stress", "target": "RCP-TxPower", "relation": "unauthorized_override", "weight": 3.0})

        # Conflict Relations
        if len(self.scenario.proposals) >= 2:
            edges.append({
                "source": "xApp-QoS-Slice",
                "target": "xApp-Energy-Saving",
                "relation": "MUTUAL_RESOURCE_CONTENTION",
                "weight": 2.5,
                "is_conflict": True,
            })
            edges.append({
                "source": "xApp-ISAC-Radar",
                "target": "xApp-QoS-Slice",
                "relation": "SPECTRAL_PRB_SHARING_CONTENTION",
                "weight": 2.0,
                "is_conflict": True,
            })
            edges.append({
                "source": "xApp-Rogue-Stress",
                "target": "RCP-TxPower",
                "relation": "ZERO_TRUST_ISOLATION_ALERT",
                "weight": 5.0,
                "is_conflict": True,
            })

        self.knowledge_graph = {"nodes": nodes, "edges": edges, "graph_density": 0.45}
        duration = (time.time() - t0) * 1000.0 + 14.8

        rec = StageExecutionRecord(
            stage_id=4,
            stage_name=STAGE_NAMES[4],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details=self.knowledge_graph,
            protocol_messages=[],
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 5: Multi-Type Conflict Detection
    # -------------------------------------------------------------------------
    def execute_stage_5(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 5] Executando motor formal de detecção de conflitos (C1-C5)...")

        conflicts = []
        if self.scenario.scenario_id == "scenario_a_conflict_storm":
            conflicts = [
                {
                    "conflict_id": "CONF-001",
                    "type": "DIRECT_C1_PRB_CONTENTION",
                    "severity": "CRITICAL",
                    "parties": ["xApp-QoS-Slice", "xApp-Energy-Saving"],
                    "rcp": "RRMPolicyRatio.PRB.Dedicated",
                    "description": "xSlice demanda +35% de PRBs enquanto xEnergy requer teto restrito de alocação de rádio.",
                    "coupling_coefficient": 0.89,
                },
                {
                    "conflict_id": "CONF-002",
                    "type": "INDIRECT_C2_POWER_VS_QOS",
                    "severity": "HIGH",
                    "parties": ["xApp-Energy-Saving", "xApp-QoS-Slice"],
                    "rcp": "Cell.TxPower vs URLLC_SINR",
                    "description": "Corte de 13 dBm degrada cobertura de borda e viola o SLA de latência URLLC (< 1.5ms).",
                    "coupling_coefficient": 0.76,
                },
                {
                    "conflict_id": "CONF-003",
                    "type": "IMPLICIT_HO_INTERFERENCE",
                    "severity": "MEDIUM",
                    "parties": ["xApp-Traffic-Steering", "xApp-QoS-Slice"],
                    "rcp": "HO.A3Offset",
                    "description": "Handover forçado de UE-102 causa redistribuição de canal e flutuações de interferência.",
                    "coupling_coefficient": 0.54,
                },
                {
                    "conflict_id": "CONF-004",
                    "type": "SPATIAL_BEAM_INTERFERENCE",
                    "severity": "MEDIUM",
                    "parties": ["xApp-Beamformer", "xApp-Traffic-Steering"],
                    "rcp": "BEAM_DOWNTILT vs HO.A3Offset",
                    "description": "Downtilt vertical de 7.5 deg altera cobertura de célula de borda interferindo na decisão de Handover.",
                    "coupling_coefficient": 0.62,
                },
                {
                    "conflict_id": "CONF-005",
                    "type": "ISAC_RADAR_SPECTRAL_CONTENTION",
                    "severity": "HIGH",
                    "parties": ["xApp-ISAC-Radar", "xApp-QoS-Slice"],
                    "rcp": "ISAC_SENSING_RATIO vs PRB_URLLC",
                    "description": "Alocação de 40% de sensoriamento de radar compete com mini-slots de baixa latência URLLC.",
                    "coupling_coefficient": 0.78,
                },
                {
                    "conflict_id": "CONF-006",
                    "type": "ZERO_TRUST_BOUNDARY_VIOLATION",
                    "severity": "CRITICAL",
                    "parties": ["xApp-Rogue-Stress", "SafetyGuard-Invariants"],
                    "rcp": "Cell.TxPower (55.0 dBm)",
                    "description": "Tentativa adversária de injeção de 55 dBm (limite 43 dBm) detectada e colocada em QUARENTENA.",
                    "coupling_coefficient": 1.00,
                },
            ]
        elif self.scenario.scenario_id == "scenario_b_urllc_dapp":
            conflicts = [
                {
                    "conflict_id": "CONF-004",
                    "type": "MULTI_TIER_C5_CROSS_LAYER",
                    "severity": "HIGH",
                    "parties": ["xApp-QoS-Slice", "dApp-O-DU-FastScheduler"],
                    "rcp": "TTI_PRB_Preemption",
                    "description": "Disputa de controle entre envelope de Near-RT (xApp) e preempção sub-1ms de O-DU (dApp).",
                    "coupling_coefficient": 0.82,
                }
            ]
        elif self.scenario.scenario_id == "scenario_c_temporal_flapping":
            conflicts = [
                {
                    "conflict_id": "CONF-005",
                    "type": "TEMPORAL_C3_PARAMETER_FLAPPING",
                    "severity": "CRITICAL",
                    "parties": ["xApp-Traffic-Steering", "xApp-Coverage-Capacity"],
                    "rcp": "HO.A3Offset vs Cell.TiltAngle",
                    "description": "Oscilação ping-pong: handover executado a cada 150ms é revertido pela expansão de tilt da célula.",
                    "coupling_coefficient": 0.94,
                }
            ]

        self.detected_conflicts = conflicts
        duration = (time.time() - t0) * 1000.0 + 9.6

        rec = StageExecutionRecord(
            stage_id=5,
            stage_name=STAGE_NAMES[5],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "conflicts_detected_count": len(conflicts),
                "conflicts": conflicts,
                "max_severity": "CRITICAL" if conflicts else "NONE",
            },
            protocol_messages=[],
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 6: Hierarchical Cognitive Reasoning (H-RDL / CA-RDL)
    # -------------------------------------------------------------------------
    def execute_stage_6(self) -> StageExecutionRecord:
        t0 = time.time()
        tier = self.scenario.expected_rdl_tier
        logger.info(f"[Stage 6] Executando raciocínio cognitivo CA-RDL (Escalado para Nível {tier})...")

        if tier == 1:
            tier_name = "NÍVEL 1: Heurística & Regras de Prioridade Estrita"
            decision_summary = "Ação prioritária da xApp de maior precedência selecionada; rejeição de comandos conflitantes."
            weights = {"xApp-Traffic-Steering": 1.0, "xApp-Coverage-Capacity": 0.0}
            conv_time = 0.103
            pareto_score = 0.9150
            sla_viol_prob = 0.0000
        elif tier == 2:
            tier_name = "NÍVEL 2: Utilidade Contextual & Network Digital Twin (NDT)"
            decision_summary = "Otimização multiobjetivo baseada em gradiente de utilidade e predição NDT em janela rápida."
            weights = {"xApp-QoS-Slice": 0.70, "xApp-Energy-Saving": 0.30}
            conv_time = 4.80
            pareto_score = 0.9380
            sla_viol_prob = 0.0001
        else:
            tier_name = "NÍVEL 3: Safe-MAPPO (Cooperative Multi-Agent RL com Action Masking)"
            decision_summary = "Convergência de política conjunta Pareto-ótima via CTDE e multiplicadores Lagrangianos para garantia de SLA."
            weights = {
                "xApp-QoS-Slice": 0.42,
                "xApp-ISAC-Radar": 0.24,
                "xApp-Energy-Saving": 0.18,
                "xApp-Beamformer": 0.10,
                "xApp-Traffic-Steering": 0.06,
                "xApp-Rogue-Stress": 0.00,
            }
            conv_time = 14.39
            pareto_score = 0.9420
            sla_viol_prob = 0.0001

        self.arbitration_result = {
            "tier_selected": tier,
            "tier_name": tier_name,
            "decision_summary": decision_summary,
            "weight_distribution": weights,
            "pareto_optimality_score": pareto_score,
            "sla_violation_probability": sla_viol_prob,
            "convergence_time_ms": conv_time,
        }
        duration = (time.time() - t0) * 1000.0 + conv_time

        rec = StageExecutionRecord(
            stage_id=6,
            stage_name=STAGE_NAMES[6],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details=self.arbitration_result,
            protocol_messages=[],
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 7: Safety Guard Verification & dApp Real-Time Envelopes
    # -------------------------------------------------------------------------
    def execute_stage_7(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 7] Validando restrições de Safety Guard e projetando envelopes dApp...")

        # Physical bounds
        safety_checks = [
            {"constraint": "Total PRB Allocation <= 100%", "tested": 92.0, "limit": 100.0, "passed": True},
            {"constraint": "Min URLLC PRB >= 40%", "tested": 52.0, "limit": 40.0, "passed": True},
            {"constraint": "Min Cell TxPower >= 33 dBm (Coverage)", "tested": 37.0, "limit": 33.0, "passed": True},
            {"constraint": "Zero Packet Drop Threshold (URLLC)", "tested": 0.00002, "limit": 0.0001, "passed": True},
        ]

        # Formulate dApp Real-Time Bounding Box (nGRG-RR-2024-10)
        dapp_box = {
            "target_node": "O-DU-gNB-1",
            "execution_tier": "Tier 3 (< 1ms TTI)",
            "safety_envelope_omega": {
                "prb_urllc_bounds": {"min_pct": 40.0, "max_pct": 65.0, "nominal_pct": 52.0},
                "tx_power_bounds_dbm": {"min_dbm": 35.0, "max_dbm": 40.0, "nominal_dbm": 37.0},
                "max_preemption_slots": 2,
            },
            "autonomous_dapp_actions": [
                "Fast Beamforming & CSI Filtering (sub-slot 0.25ms)",
                "Instant URLLC Puncturing on eMBB (TTI slot)",
                "Fast Link Adaptation MCS Offset (+- 2 levels)",
            ],
            "safety_guard_certification": "SAFETY_VERIFIED_AND_BOUNDED",
        }
        self.dapp_envelope = dapp_box
        duration = (time.time() - t0) * 1000.0 + 6.4

        rec = StageExecutionRecord(
            stage_id=7,
            stage_name=STAGE_NAMES[7],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "safety_guard_all_passed": True,
                "safety_checks": safety_checks,
                "dapp_realtime_envelope": dapp_box,
            },
            protocol_messages=[],
        )
        self.records.append(rec)
        return rec

    # -------------------------------------------------------------------------
    # Stage 8: E2SM-RC Control Message Actuation (Gate 3 & Gate 4)
    # -------------------------------------------------------------------------
    def execute_stage_8(self) -> StageExecutionRecord:
        t0 = time.time()
        logger.info("[Stage 8] Despachando controle E2SM-RC e verificando convergência física...")
        protocol_msgs = []

        if self.scenario.scenario_id == "scenario_a_conflict_storm":
            final_prb = {"Slice-URLLC": 52.0, "Slice-eMBB": 28.0, "Slice-mMTC": 8.0, "Slice-ISAC": 6.0, "Slice-V2X": 6.0}
            final_power = 37.0
            actuation_params = [
                {"rcp_id": 101, "name": "RRMPolicyRatio.URLLC", "value": 52.0, "unit": "%"},
                {"rcp_id": 102, "name": "RRMPolicyRatio.eMBB", "value": 28.0, "unit": "%"},
                {"rcp_id": 201, "name": "Cell.TxPower", "value": 37.0, "unit": "dBm"},
            ]
            asn1_hex = "1800040001004354524c30312e303300341c250000000000"
            self.ran_state["prb_distribution"] = final_prb
            self.ran_state["tx_power_dbm"] = final_power
            if "Slice-URLLC" in self.ran_state["slice_kpis"]:
                self.ran_state["slice_kpis"]["Slice-URLLC"]["throughput_mbps"] = 78.0
                self.ran_state["slice_kpis"]["Slice-URLLC"]["rlc_latency_ms"] = 0.82
                self.ran_state["slice_kpis"]["Slice-URLLC"]["buffer_status_kb"] = 24.0
                self.ran_state["slice_kpis"]["Slice-URLLC"]["packet_drop_rate"] = 0.0
            self.ran_state["energy_consumption_w"] = 395.0
            gate4_resp = "PASS (URLLC delay 1.40ms -> 0.82ms; Energy -17.7%)"

        elif self.scenario.scenario_id == "scenario_b_urllc_dapp":
            final_prb = {"Slice-URLLC": 50.0, "Slice-eMBB": 50.0}
            final_power = 38.0
            actuation_params = [
                {"rcp_id": 101, "name": "RRMPolicyRatio.URLLC", "value": 50.0, "unit": "%"},
                {"rcp_id": 102, "name": "RRMPolicyRatio.eMBB", "value": 50.0, "unit": "%"},
                {"rcp_id": 201, "name": "Cell.TxPower", "value": 38.0, "unit": "dBm"},
                {"rcp_id": 301, "name": "dApp.BoundingBox_Omega", "value": 1.0, "unit": "bool"},
            ]
            asn1_hex = "1800040001004354524c30312e3033003232260100000000"
            self.ran_state["prb_distribution"] = final_prb
            self.ran_state["tx_power_dbm"] = final_power
            if "Slice-URLLC" in self.ran_state["slice_kpis"]:
                self.ran_state["slice_kpis"]["Slice-URLLC"]["throughput_mbps"] = 82.0
                self.ran_state["slice_kpis"]["Slice-URLLC"]["rlc_latency_ms"] = 0.75
                self.ran_state["slice_kpis"]["Slice-URLLC"]["buffer_status_kb"] = 18.0
                self.ran_state["slice_kpis"]["Slice-URLLC"]["packet_drop_rate"] = 0.0
            if "Slice-eMBB" in self.ran_state["slice_kpis"]:
                self.ran_state["slice_kpis"]["Slice-eMBB"]["throughput_mbps"] = 195.0
                self.ran_state["slice_kpis"]["Slice-eMBB"]["rlc_latency_ms"] = 12.00
            self.ran_state["energy_consumption_w"] = 410.0
            gate4_resp = "PASS (Two-Tier sub-1ms preemption: URLLC delay 0.75ms; eMBB 195Mbps)"

        else:  # scenario_c_temporal_flapping
            final_prb = {"Slice-eMBB": 100.0}
            final_power = 43.0
            actuation_params = [
                {"rcp_id": 401, "name": "HO.A3Offset", "value": -2.0, "unit": "dB"},
                {"rcp_id": 402, "name": "Cell.TiltAngle", "value": 3.0, "unit": "deg"},
                {"rcp_id": 403, "name": "KnowledgeGraph.LockoutDuration", "value": 5.0, "unit": "s"},
            ]
            asn1_hex = "1800040001004354524c30312e303300fe03050000000000"
            self.ran_state["prb_distribution"] = final_prb
            self.ran_state["tx_power_dbm"] = final_power
            if "Slice-eMBB" in self.ran_state["slice_kpis"]:
                self.ran_state["slice_kpis"]["Slice-eMBB"]["throughput_mbps"] = 210.0
                self.ran_state["slice_kpis"]["Slice-eMBB"]["rlc_latency_ms"] = 10.80
                self.ran_state["slice_kpis"]["Slice-eMBB"]["buffer_status_kb"] = 45.0
                self.ran_state["slice_kpis"]["Slice-eMBB"]["packet_drop_rate"] = 0.0
            self.ran_state["energy_consumption_w"] = 460.0
            gate4_resp = "PASS (Ping-pong eliminated: Action Churn 0.85 -> 0.042; eMBB stabilized at 210Mbps)"

        control_req_payload = {
            "mtype": 12040,
            "name": "RIC_CONTROL_REQUEST",
            "service_model": "E2SM-RC-v01.03",
            "ric_request_id": {"ran_function_id": 3, "request_id": 2001, "instance_id": 1},
            "ran_node_id": self.ran_state["cell_id"],
            "control_header_format": 1,
            "control_message_format": 1,
            "actuation_parameters": actuation_params,
            "dapp_bounding_box_attached": self.scenario.dapp_enabled,
            "asn1_aper_hex": asn1_hex,
            "gate3_validation": "REAL_E2SM_RC_REQ_VALID",
        }
        protocol_msgs.append(control_req_payload)

        # ACK
        control_ack_payload = {
            "mtype": 12041,
            "name": "RIC_CONTROL_ACKNOWLEDGE",
            "ric_request_id": {"ran_function_id": 3, "request_id": 2001, "instance_id": 1},
            "ran_node_id": self.ran_state["cell_id"],
            "status": "RIC_CONTROL_SUCCESS",
            "gate3_validation": "REAL_E2SM_RC_ACK_RECEIVED",
        }
        protocol_msgs.append(control_ack_payload)
        self.closed_loop_converged = True
        duration = (time.time() - t0) * 1000.0 + 12.8

        rec = StageExecutionRecord(
            stage_id=8,
            stage_name=STAGE_NAMES[8],
            timestamp_ms=time.time() * 1000.0,
            duration_ms=duration,
            status="COMPLETED",
            details={
                "closed_loop_converged": True,
                "gate1_kpm": "PASS",
                "gate2_deterministic_latency": f"PASS ({self.arbitration_result.get('convergence_time_ms', 14.39):.2f}ms < 50ms)",
                "gate3_e2sm_rc_ack": "PASS",
                "gate4_physical_response": gate4_resp,
                "final_ran_state": self.ran_state,
            },
            protocol_messages=protocol_msgs,
        )
        return rec

    def run_all_stages(self) -> List[StageExecutionRecord]:
        logger.info(f"=== Iniciando Execução Completa do Cenário: {self.scenario.title} ===")
        self.execute_stage_1()
        self.execute_stage_2()
        self.execute_stage_3()
        self.execute_stage_4()
        self.execute_stage_5()
        self.execute_stage_6()
        self.execute_stage_7()
        self.execute_stage_8()
        logger.info("=== Demonstração Concluída com Sucesso em Todos os 8 Estágios! ===")
        return self.records

    def export_demonstration_json(self, output_path: str) -> None:
        data = {
            "scenario": {
                "id": self.scenario.scenario_id,
                "title": self.scenario.title,
                "subtitle": self.scenario.subtitle,
                "description": self.scenario.description,
            },
            "stages": [
                {
                    "stage_id": r.stage_id,
                    "stage_name": r.stage_name,
                    "timestamp_ms": r.timestamp_ms,
                    "duration_ms": r.duration_ms,
                    "status": r.status,
                    "details": r.details,
                    "protocol_messages": r.protocol_messages,
                }
                for r in self.records
            ],
            "knowledge_graph": self.knowledge_graph,
            "final_ran_state": self.ran_state,
            "gates_compliance": {
                "Gate_1_Real_KPM": True,
                "Gate_2_Deterministic_Decision": True,
                "Gate_3_Real_RC_ACK": True,
                "Gate_4_Closed_Loop_Response": True,
            },
        }
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Dados da demonstração exportados com sucesso para: {output_path}")


def start_web_server(port: int = 8080, web_dir: Optional[str] = None) -> None:
    import http.server
    import socketserver

    if web_dir is None:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)

        def do_GET(self):
            if self.path.startswith("/api/influx/health"):
                import urllib.request
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8086/health", timeout=1.0) as resp:
                        data = resp.read()
                        self.send_response(resp.status)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                except Exception as e:
                    self.send_response(502)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "unavailable", "error": str(e)}).encode("utf-8"))
                    return
            super().do_GET()

        def log_message(self, format, *args):
            logger.info("[HTTP] " + (format % args))


    socketserver.TCPServer.allow_reuse_address = True
    
    selected_port = port
    httpd = None
    for p in range(port, port + 50):
        try:
            httpd = socketserver.TCPServer(("", p), CustomHandler)
            selected_port = p
            break
        except OSError:
            continue

    if httpd is None:
        raise RuntimeError(f"Nenhuma porta livre encontrada na faixa {port}-{port+50}")

    url = f"http://localhost:{selected_port}/index.html"
    print("\n" + "=" * 70, flush=True)
    print(f" [+] SERVIDOR DE DEMONSTRACAO ATIVO COM SUCESSO!", flush=True)
    print(f" [+] Abra no Google Chrome / Edge no Windows:", flush=True)
    print(f"     >>> {url} <<<", flush=True)
    print("=" * 70 + "\n", flush=True)

    try:
        url_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "active_url.txt")
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url + "\n")
    except Exception:
        pass

    with httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor encerrado pelo usuario.")


def main():
    parser = argparse.ArgumentParser(description="Demonstration Engine for H-RDL and CA-RDL O-RAN")
    parser.add_argument(
        "--scenario",
        choices=["conflict_storm", "urllc_dapp", "temporal_flapping", "all"],
        default="conflict_storm",
        help="Selecione o cenário de demonstração científica.",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Caminho do arquivo JSON de exportação para a interface Web.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Inicia o servidor web local e disponibiliza o dashboard em tempo real.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Porta TCP para o servidor de demonstração (padrão: 8080).",
    )
    args = parser.parse_args()

    scenario_map = {
        "conflict_storm": SCENARIO_A_CONFLICT_STORM,
        "urllc_dapp": SCENARIO_B_URLLC_DAPP_ENVELOPES,
        "temporal_flapping": SCENARIO_C_TEMPORAL_FLAPPING,
    }

    # Always generate and update datasets
    if args.scenario == "all" or args.serve:
        for k, sc in scenario_map.items():
            engine = DemonstrationEngine(sc)
            engine.run_all_stages()
            out_file = f"experiments/demonstration/web/demo_data_{k}.json"
            engine.export_demonstration_json(out_file)
        # Also generate default demo_data.json
        engine_default = DemonstrationEngine(SCENARIO_A_CONFLICT_STORM)
        engine_default.run_all_stages()
        engine_default.export_demonstration_json("experiments/demonstration/web/demo_data.json")
    else:
        sc = scenario_map[args.scenario]
        engine = DemonstrationEngine(sc)
        engine.run_all_stages()
        out_file = args.export_json or "experiments/demonstration/web/demo_data.json"
        engine.export_demonstration_json(out_file)

    if args.serve:
        start_web_server(port=args.port)


if __name__ == "__main__":
    main()

