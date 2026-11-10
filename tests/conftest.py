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

class _InProcessXapp:
    """Transporte em processo para testes unitários (mesmo comportamento do stub de src/rdl_xapp.py)."""

    def __init__(self, entrypoint=None, rmr_port: int = 4560, rmr_wait_for_ready: bool = False, use_fake_sdl: bool = False, **kwargs):
        self.entrypoint = entrypoint
        self.rmr_port = rmr_port
        self.rmr_wait_for_ready = rmr_wait_for_ready
        self.use_fake_sdl = False
        self._callbacks = {}
        self.transport_name = "RMR_E2_OPERATIONAL"
        self.is_mock_transport = True

    def register_callback(self, handler, mtype: int):
        self._callbacks[mtype] = handler

    def run(self):
        if self.entrypoint:
            self.entrypoint(self)

    def stop(self):
        pass

    def rmr_send(self, payload: bytes, mtype: int) -> bool:
        return True

    def rmr_free(self, sbuf):
        pass


@pytest.fixture(autouse=True)
def _in_process_rmr_transport(monkeypatch):
    """Evita o Xapp real do ricxappframe nos testes unitários.

    Com a biblioteca RMR instalada (CI), o Xapp real inicia uma thread RMR que não é
    daemon; como os testes criam RDLxApp sem chamar stop(), o pytest não termina.
    Sem a biblioteca (Windows, máquinas de desenvolvimento), src/rdl_xapp.py já usa
    um stub equivalente. Defina RDL_TEST_REAL_RMR=true para usar o transporte real.
    """
    if os.environ.get("RDL_TEST_REAL_RMR", "false").lower() == "true":
        yield
        return
    import src.rdl_xapp as rdl_xapp_module
    if rdl_xapp_module.HAS_RICXAPPFRAME:
        monkeypatch.setattr(rdl_xapp_module, "Xapp", _InProcessXapp)
    yield


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
