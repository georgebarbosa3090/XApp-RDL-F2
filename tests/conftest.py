import pytest
import uuid
import sys
import os

# Ensure root directory is always on sys.path for test discovery in all Python versions
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.conflict_types import XAppAction, ConflictEvent, ConflictType, ConflictSeverity
from src.infrastructure.memory_module import MemoryModule

@pytest.fixture
def test_memory():
    return MemoryModule()

@pytest.fixture
def mock_memory(test_memory):
    return test_memory

@pytest.fixture
def action_tx_power():
    return XAppAction(
        xapp_id="xapp_1",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=20.0,
        priority=60
    )

@pytest.fixture
def action_prb_quota():
    return XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="PRB_QUOTA",
        value=50.0,
        priority=80
    )

@pytest.fixture
def direct_conflict(action_tx_power):
    # Duas ações apontando para o mesmo parâmetro
    action2 = XAppAction(
        xapp_id="xapp_2",
        node_id="gnb_01",
        parameter="TX_POWER",
        value=15.0,
        priority=80
    )
    return ConflictEvent(
        conflict_id=str(uuid.uuid4()),
        conflict_type=ConflictType.DIRECT,
        severity=ConflictSeverity.HIGH,
        involved_xapps=[action_tx_power, action2],
        affected_kpis=["DRB.UEThpDl", "DRB.RlcSduDelayDl"],
        detected_at=0.0,
        description="Conflito direto em TX_POWER"
    )
