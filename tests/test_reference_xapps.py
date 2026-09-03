import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "reference-xapps" / "qos-xslice"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "energy-saving"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "traffic-steering"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "beamformer"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "isac-radar"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "rogue-xapp"))

from xslice_xapp import XSliceXApp
from energy_saving_xapp import EnergySavingXApp
from traffic_steering_xapp import TrafficSteeringXApp
from beamformer_xapp import BeamformerXApp
from isac_radar_xapp import ISACRadarXApp
from rogue_xapp import RogueXApp

from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import XAppAction, ConflictType, ResolutionStrategy

def test_xslice_proposal_generation():
    app = XSliceXApp(http_port=18082, metrics_port=18083)
    prop = app.generate_action_proposal(node_id="gnb_01", prb_quota=85.0)
    assert prop["xapp_id"] == "xslice_oran"
    assert prop["parameter"] == "PRB_QUOTA"
    assert prop["value"] == 85.0
    assert prop["priority"] == 90
    assert prop["slice_type"] == "URLLC"

def test_energy_saving_proposal_generation():
    app = EnergySavingXApp(http_port=18084, metrics_port=18085)
    prop = app.generate_action_proposal(node_id="gnb_01", tx_power=15.0)
    assert prop["xapp_id"] == "energy_saving_orange"
    assert prop["parameter"] == "TX_POWER"
    assert prop["value"] == 15.0
    assert prop["priority"] == 65

def test_traffic_steering_proposal_generation():
    app = TrafficSteeringXApp(http_port=18086, metrics_port=18087)
    prop = app.generate_action_proposal(source_node="gnb_01", target_node="gnb_02", target_ue="UE-09")
    assert prop["xapp_id"] == "traffic_steering_oransc"
    assert prop["parameter"] == "HANDOVER"
    assert prop["target_node"] == "gnb_02"
    assert prop["target_ue"] == "UE-09"
    assert prop["priority"] == 80

def test_beamformer_proposal_generation():
    app = BeamformerXApp(http_port=18088, metrics_port=18089)
    prop = app.generate_action_proposal(node_id="gnb_01", downtilt=7.5)
    assert prop["xapp_id"] == "beamformer_mimo_5ga"
    assert prop["parameter"] == "VERTICAL_DOWNTILT"
    assert prop["value"] == 7.5
    assert prop["priority"] == 75

def test_isac_radar_proposal_generation():
    app = ISACRadarXApp(http_port=18090, metrics_port=18091)
    prop = app.generate_action_proposal(node_id="gnb_01", sensing_ratio=0.4)
    assert prop["xapp_id"] == "isac_radar_sensing_6g"
    assert prop["parameter"] == "SENSING_RATIO"
    assert prop["value"] == 0.4
    assert prop["priority"] == 85
    assert prop["slice_type"] == "SENSING"

def test_rogue_xapp_proposal_generation():
    app = RogueXApp(http_port=18092, metrics_port=18093)
    prop1 = app.generate_action_proposal(node_id="gnb_01")
    prop2 = app.generate_action_proposal(node_id="gnb_01")
    assert prop1["xapp_id"] == "rogue_vendor_stress_6g"
    assert prop1["parameter"] == "TX_POWER"
    assert prop1["value"] != prop2["value"] # Parameter flipping verificado

def test_multi_xapp_conflict_triad_detection_and_resolution():
    """Valida arbitragem de conflito entre fatiamento e economia de energia."""
    xslice = XSliceXApp()
    es = EnergySavingXApp()

    p1 = xslice.generate_action_proposal(node_id="gnb_01", prb_quota=80.0)
    p2 = es.generate_action_proposal(node_id="gnb_01", tx_power=15.0)

    action_xslice = XAppAction(
        xapp_id=p1["xapp_id"],
        node_id=p1["node_id"],
        parameter=p1["parameter"],
        value=p1["value"],
        priority=p1["priority"]
    )
    action_es = XAppAction(
        xapp_id=p2["xapp_id"],
        node_id=p2["node_id"],
        parameter=p2["parameter"],
        value=p2["value"],
        priority=p2["priority"]
    )

    perception = PerceptionAgent()
    conflicts = perception.register_action_group([action_xslice, action_es])

    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT
    assert len(conflicts[0].involved_xapps) == 2

    memory = MemoryModule()
    reasoning = ReasoningAgent(memory=memory, config={})
    resolution = reasoning.resolve(conflicts[0])

    assert resolution is not None
    assert resolution.winning_actions[0].xapp_id == "xslice_oran"
    assert resolution.strategy_used in (ResolutionStrategy.PRIORITY_TABLE, ResolutionStrategy.TVS, ResolutionStrategy.EEVS, ResolutionStrategy.MARL_AGENT)
