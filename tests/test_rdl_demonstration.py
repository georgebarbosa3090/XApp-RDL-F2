#!/usr/bin/env python3
"""
Unit and Integration Tests for H-RDL and CA-RDL Demonstration Engine.

Validates:
  - 8-Stage Canonical Lifecycle execution;
  - Scenarios A (Conflict Storm), B (URLLC dApp), C (Temporal Flapping);
  - Gate 1: Real ASN.1 APER KPM Telemetry formatting;
  - Gate 2: Deterministic Decision Latency (< 50ms Near-RT SLA);
  - Gate 3: Real E2SM-RC Control Message Request and ACK confirmation;
  - Gate 4: Closed-Loop Physical Convergence in RAN state;
  - dApp Safety Envelopes compliance (nGRG-RR-2024-10).
"""

from __future__ import annotations

import json
import os
import pytest

from experiments.demonstration.demo_scenarios import (
    ALL_SCENARIOS,
    SCENARIO_A_CONFLICT_STORM,
    SCENARIO_B_URLLC_DAPP_ENVELOPES,
    SCENARIO_C_TEMPORAL_FLAPPING,
)
from experiments.demonstration.rdl_demonstration_engine import (
    DemonstrationEngine,
    DemonstrationStage,
    STAGE_NAMES,
)


def test_scenario_a_conflict_storm_full_run():
    engine = DemonstrationEngine(SCENARIO_A_CONFLICT_STORM)
    records = engine.run_all_stages()

    assert len(records) == 8
    assert engine.closed_loop_converged is True

    # Stage 1 validation
    s1 = records[0]
    assert s1.stage_id == 1
    assert s1.details["total_ues_registered"] == 3
    assert s1.details["e2_setup_status"] == "E2_CONNECTED_SUCCESSFUL"

    # Stage 2 validation (Gate 1)
    s2 = records[1]
    assert s2.stage_id == 2
    assert s2.details["kpm_indication"]["gate1_validation"] == "REAL_ASN1_APER_VALID"
    assert "Slice-URLLC" in s2.details["active_slices"]

    # Stage 3 validation
    s3 = records[2]
    assert s3.details["aggregation_window_ms"] == 200.0
    assert s3.details["proposals_count"] == 3

    # Stage 4 validation (Knowledge Graph)
    s4 = records[3]
    assert len(s4.details["nodes"]) >= 9
    assert len(s4.details["edges"]) >= 5

    # Stage 5 validation (Conflict Detection)
    s5 = records[4]
    assert s5.details["conflicts_detected_count"] >= 2
    assert s5.details["max_severity"] == "CRITICAL"

    # Stage 6 validation (CA-RDL Reasoning Tier 3)
    s6 = records[5]
    assert s6.details["tier_selected"] == 3
    assert s6.details["convergence_time_ms"] < 50.0  # Gate 2 Near-RT budget

    # Stage 7 validation (Safety Guard & dApp Envelopes)
    s7 = records[6]
    assert s7.details["safety_guard_all_passed"] is True
    assert "safety_envelope_omega" in s7.details["dapp_realtime_envelope"]

    # Stage 8 validation (Gate 3 & Gate 4)
    s8 = records[7]
    assert s8.details["gate1_kpm"] == "PASS"
    assert s8.details["gate3_e2sm_rc_ack"] == "PASS"
    assert s8.details["gate4_physical_response"].startswith("PASS")

    # Verify physical convergence
    ran_state = s8.details["final_ran_state"]
    assert ran_state["slice_kpis"]["Slice-URLLC"]["rlc_latency_ms"] < 1.0
    assert ran_state["tx_power_dbm"] == 37.0


def test_scenario_b_urllc_dapp_envelopes():
    engine = DemonstrationEngine(SCENARIO_B_URLLC_DAPP_ENVELOPES)
    records = engine.run_all_stages()

    assert len(records) == 8
    # Tier 2 optimization
    s6 = records[5]
    assert s6.details["tier_selected"] == 2

    # dApp envelope check
    s7 = records[6]
    envelope = s7.details["dapp_realtime_envelope"]
    assert envelope["target_node"] == "O-DU-gNB-1"
    assert envelope["execution_tier"] == "Tier 3 (< 1ms TTI)"


def test_scenario_c_temporal_flapping_lockout():
    engine = DemonstrationEngine(SCENARIO_C_TEMPORAL_FLAPPING)
    records = engine.run_all_stages()

    assert len(records) == 8
    s5 = records[4]
    assert any(c["type"] == "TEMPORAL_C3_PARAMETER_FLAPPING" for c in s5.details["conflicts"])

    s6 = records[5]
    assert s6.details["tier_selected"] == 1


def test_json_export(tmp_path):
    engine = DemonstrationEngine(SCENARIO_A_CONFLICT_STORM)
    engine.run_all_stages()
    out_file = tmp_path / "demo_output.json"
    engine.export_demonstration_json(str(out_file))

    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "scenario" in data
    assert "stages" in data
    assert len(data["stages"]) == 8
    assert data["gates_compliance"]["Gate_1_Real_KPM"] is True
    assert data["gates_compliance"]["Gate_4_Closed_Loop_Response"] is True
