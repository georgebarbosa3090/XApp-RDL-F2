#!/usr/bin/env python3
"""
Scientific Demonstration Scenarios for H-RDL and CA-RDL Evaluation.

Defines 3 canonical demonstration scenarios:
  1. Scenario A (Conflict Storm): Concurrent conflict among QoS Slicing, Energy Saving, and Traffic Steering.
  2. Scenario B (URLLC Fast Preemption & Multi-Tier dApp Envelopes): Critical latency event requiring sub-1ms O-DU actuation within Near-RT safety bounds.
  3. Scenario C (Temporal Flapping Elimination): Cross-frequency oscillation between TS and CCO resolved via Knowledge Graph temporal lockout.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional


@dataclasses.dataclass(frozen=True)
class UERegistrationProfile:
    ue_id: str
    imsi: str
    rnti: int
    slice_id: str
    service_type: str  # eMBB, URLLC, mMTC
    initial_sinr_db: float
    initial_buffer_kb: float
    target_gnb: str


@dataclasses.dataclass(frozen=True)
class XAppProposal:
    xapp_id: str
    intent_type: str
    target_slice: Optional[str]
    target_cell: str
    proposed_rcp: str  # PRB_RATIO, TX_POWER, HO_A3_OFFSET, etc.
    proposed_value: float
    unit: str
    priority: int
    rationale: str


@dataclasses.dataclass(frozen=True)
class DemonstrationScenario:
    scenario_id: str
    title: str
    subtitle: str
    description: str
    ues: List[UERegistrationProfile]
    proposals: List[XAppProposal]
    initial_cell_power_dbm: float
    initial_prb_distribution: Dict[str, float]
    expected_conflict_types: List[str]
    expected_rdl_tier: int  # 1: Heuristic, 2: Utility/NDT, 3: Safe-MAPPO
    dapp_enabled: bool


SCENARIO_A_CONFLICT_STORM = DemonstrationScenario(
    scenario_id="scenario_a_conflict_storm",
    title="Cenário A: Tempestade de Conflitos (Conflict Storm - 6 xApps)",
    subtitle="Arbitragem Concorrente: QoS Slicing vs. Energy vs. TS vs. Beamformer vs. ISAC vs. Rogue xApp",
    description=(
        "Seis xApps de referência simultâneas solicitam modificações concorrentes no gNB-1: "
        "a xSlice demanda +35% de PRB para URLLC, a xEnergy demanda corte de 13 dBm na potência, "
        "a xTS força migração de UEs, a xBeamformer reorienta feixes verticais, a xISAC-Radar aloca "
        "40% de recursos para sensoriamento 6G, e a Rogue-xApp tenta injetar potência fora dos limites 3GPP. "
        "Demonstra a ativação do Knowledge Graph, isolamento Zero-Trust e a escalada até o Nível 3 (Safe-MAPPO)."
    ),
    ues=[
        UERegistrationProfile(
            ue_id="UE-101",
            imsi="001010123456001",
            rnti=101,
            slice_id="Slice-URLLC",
            service_type="URLLC",
            initial_sinr_db=18.5,
            initial_buffer_kb=450.0,
            target_gnb="gNB-1",
        ),
        UERegistrationProfile(
            ue_id="UE-102",
            imsi="001010123456002",
            rnti=102,
            slice_id="Slice-eMBB",
            service_type="eMBB",
            initial_sinr_db=22.0,
            initial_buffer_kb=1200.0,
            target_gnb="gNB-1",
        ),
        UERegistrationProfile(
            ue_id="UE-103",
            imsi="001010123456003",
            rnti=103,
            slice_id="Slice-mMTC",
            service_type="mMTC",
            initial_sinr_db=14.0,
            initial_buffer_kb=80.0,
            target_gnb="gNB-1",
        ),
        UERegistrationProfile(
            ue_id="UE-104",
            imsi="001010123456004",
            rnti=104,
            slice_id="Slice-ISAC",
            service_type="ISAC",
            initial_sinr_db=20.0,
            initial_buffer_kb=300.0,
            target_gnb="gNB-1",
        ),
        UERegistrationProfile(
            ue_id="UE-105",
            imsi="001010123456005",
            rnti=105,
            slice_id="Slice-V2X",
            service_type="V2X",
            initial_sinr_db=17.5,
            initial_buffer_kb=550.0,
            target_gnb="gNB-1",
        ),
    ],
    proposals=[
        XAppProposal(
            xapp_id="xApp-QoS-Slice",
            intent_type="SLA_PROTECTION_URLLC",
            target_slice="Slice-URLLC",
            target_cell="gNB-1",
            proposed_rcp="RRMPolicyRatio.PRB.Dedicated",
            proposed_value=65.0,
            unit="%",
            priority=1,
            rationale="Surto de tráfego crítico; buffer acumulado > 400KB requer elevação de PRBs dedicados de 30% para 65%.",
        ),
        XAppProposal(
            xapp_id="xApp-Energy-Saving",
            intent_type="GREEN_RAN_POWER_REDUCTION",
            target_slice="Slice-URLLC",
            target_cell="gNB-1",
            proposed_rcp="Cell.TxPower",
            proposed_value=30.0,
            unit="dBm",
            priority=3,
            rationale="Otimização de eficiência energética; redução de Tx Power de 43 dBm para 30 dBm para economia de 38% de consumo.",
        ),
        XAppProposal(
            xapp_id="xApp-Traffic-Steering",
            intent_type="LOAD_BALANCING_HANDOVER",
            target_slice="Slice-eMBB",
            target_cell="gNB-1",
            proposed_rcp="HO.A3Offset",
            proposed_value=-4.0,
            unit="dB",
            priority=2,
            rationale="Balanceamento de carga preventiva; forçar migração de UE-102 para gNB-2 para desobstruir célula local.",
        ),
        XAppProposal(
            xapp_id="xApp-Beamformer",
            intent_type="MIMO_BEAM_OPTIMIZATION",
            target_slice="Slice-eMBB",
            target_cell="gNB-1",
            proposed_rcp="BEAM_DOWNTILT",
            proposed_value=7.5,
            unit="deg",
            priority=4,
            rationale="Otimização angular de feixe vertical para UEs terrestres com redução de interferência inter-célula.",
        ),
        XAppProposal(
            xapp_id="xApp-ISAC-Radar",
            intent_type="SENSING_COMM_COEXISTENCE",
            target_slice="Slice-ISAC",
            target_cell="gNB-1",
            proposed_rcp="ISAC_SENSING_RATIO",
            proposed_value=0.4,
            unit="ratio",
            priority=2,
            rationale="Alocação de 40% dos subframes para varredura e rastreamento de alvos aéreos (UAV/Drones).",
        ),
        XAppProposal(
            xapp_id="xApp-Rogue-Stress",
            intent_type="ADVERSARIAL_POWER_OVERRIDE",
            target_slice="Slice-URLLC",
            target_cell="gNB-1",
            proposed_rcp="Cell.TxPower",
            proposed_value=55.0,
            unit="dBm",
            priority=1,
            rationale="Injeção não autorizada de 55 dBm extrapolando teto físico de hardware (Macro 43 dBm) - Teste Zero-Trust.",
        ),
    ],
    initial_cell_power_dbm=43.0,
    initial_prb_distribution={"Slice-URLLC": 30.0, "Slice-eMBB": 40.0, "Slice-mMTC": 10.0, "Slice-ISAC": 10.0, "Slice-V2X": 10.0},
    expected_conflict_types=[
        "DIRECT_C1_PRB_CONTENTION",
        "INDIRECT_C2_POWER_VS_QOS",
        "IMPLICIT_HO_INTERFERENCE",
        "SPATIAL_BEAM_INTERFERENCE",
        "ISAC_RADAR_SPECTRAL_CONTENTION",
        "ZERO_TRUST_BOUNDARY_VIOLATION"
    ],
    expected_rdl_tier=3,
    dapp_enabled=True,
)


SCENARIO_B_URLLC_DAPP_ENVELOPES = DemonstrationScenario(
    scenario_id="scenario_b_urllc_dapp",
    title="Cenário B: Preempção Rápida URLLC & Envelopes dApp Multi-Tier",
    subtitle="Controle em Tempo Real (< 1ms TTI) em O-DU sob Governança Near-RT (nGRG-RR-2024-10)",
    description=(
        "Demonstração do modelo Two-Tier AI e hierarquia de controle O-RAN: o Near-RT RIC (CA-RDL) "
        "projeta envelopes de segurança Omega_dApp para o O-DU, permitindo que a dApp execute preempção e "
        "ajuste de feixe em microsegundos durante o TTI sem violar a estabilidade macro da rede."
    ),
    ues=[
        UERegistrationProfile(
            ue_id="UE-201",
            imsi="001010123456201",
            rnti=201,
            slice_id="Slice-URLLC",
            service_type="URLLC",
            initial_sinr_db=16.0,
            initial_buffer_kb=850.0,
            target_gnb="gNB-1",
        ),
        UERegistrationProfile(
            ue_id="UE-202",
            imsi="001010123456202",
            rnti=202,
            slice_id="Slice-eMBB",
            service_type="eMBB",
            initial_sinr_db=25.0,
            initial_buffer_kb=3000.0,
            target_gnb="gNB-1",
        ),
    ],
    proposals=[
        XAppProposal(
            xapp_id="xApp-QoS-Slice",
            intent_type="FAST_URLLC_ENVELOPE",
            target_slice="Slice-URLLC",
            target_cell="gNB-1",
            proposed_rcp="RRMPolicyRatio.PRB.Dedicated",
            proposed_value=50.0,
            unit="%",
            priority=1,
            rationale="Estabelecimento de bounding box para dApp de escalonamento rápido no O-DU.",
        ),
        XAppProposal(
            xapp_id="xApp-Energy-Saving",
            intent_type="MODERATE_POWER_SAVING",
            target_slice=None,
            target_cell="gNB-1",
            proposed_rcp="Cell.TxPower",
            proposed_value=38.0,
            unit="dBm",
            priority=2,
            rationale="Redução conservadora de 5 dBm mantendo margem segura para canal URLLC.",
        ),
    ],
    initial_cell_power_dbm=43.0,
    initial_prb_distribution={"Slice-URLLC": 25.0, "Slice-eMBB": 75.0},
    expected_conflict_types=["MULTI_TIER_C5_CROSS_LAYER"],
    expected_rdl_tier=2,
    dapp_enabled=True,
)


SCENARIO_C_TEMPORAL_FLAPPING = DemonstrationScenario(
    scenario_id="scenario_c_temporal_flapping",
    title="Cenário C: Eliminação de Flapping Temporal (Ping-Pong Lockout)",
    subtitle="Convergência Causal e Janela de Resfriamento Temporal via Knowledge Graph",
    description=(
        "Duas xApps operando em taxas de amostragem discordantes (100ms vs 1s) produzem oscilações "
        "cíclicas nos offsets de handover e no tilt elétrico. O CA-RDL detecta o ciclo no grafo temporal "
        "e impõe janela de resfriamento (lockout) de 5s, restaurando o regime permanente."
    ),
    ues=[
        UERegistrationProfile(
            ue_id="UE-301",
            imsi="001010123456301",
            rnti=301,
            slice_id="Slice-eMBB",
            service_type="eMBB",
            initial_sinr_db=12.0,
            initial_buffer_kb=600.0,
            target_gnb="gNB-1",
        )
    ],
    proposals=[
        XAppProposal(
            xapp_id="xApp-Traffic-Steering",
            intent_type="FAST_HANDOVER_TRIGGER",
            target_slice="Slice-eMBB",
            target_cell="gNB-1",
            proposed_rcp="HO.A3Offset",
            proposed_value=-6.0,
            unit="dB",
            priority=1,
            rationale="Re-direcionamento agressivo para célula secundária.",
        ),
        XAppProposal(
            xapp_id="xApp-Coverage-Capacity",
            intent_type="CELL_EDGE_RECOVERY",
            target_slice=None,
            target_cell="gNB-1",
            proposed_rcp="Cell.TiltAngle",
            proposed_value=2.0,
            unit="deg",
            priority=2,
            rationale="Ajuste de tilt para expansão de cobertura contrária ao handover.",
        ),
    ],
    initial_cell_power_dbm=43.0,
    initial_prb_distribution={"Slice-eMBB": 100.0},
    expected_conflict_types=["TEMPORAL_C3_PARAMETER_FLAPPING"],
    expected_rdl_tier=1,
    dapp_enabled=False,
)

ALL_SCENARIOS = {
    "scenario_a_conflict_storm": SCENARIO_A_CONFLICT_STORM,
    "scenario_b_urllc_dapp": SCENARIO_B_URLLC_DAPP_ENVELOPES,
    "scenario_c_temporal_flapping": SCENARIO_C_TEMPORAL_FLAPPING,
}
