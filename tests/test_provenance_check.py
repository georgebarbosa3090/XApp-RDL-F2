import pytest
import os
import shutil
import tempfile
from scripts.package_and_sync_raw_results import (
    calculate_sha256,
    create_dummy_raw_traces_if_missing,
    verify_raw_traces_exist,
    package_scenario_raw_data
)

def test_calculate_sha256(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Open RAN RDL Provenance Test", encoding="utf-8")
    
    hash1 = calculate_sha256(str(test_file))
    assert len(hash1) == 64
    assert isinstance(hash1, str)
    
    # Deterministic check
    hash2 = calculate_sha256(str(test_file))
    assert hash1 == hash2

def test_verify_raw_traces_exist_raises_on_missing(tmp_path, monkeypatch):
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    # Directories do not exist -> should raise FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Modo estrito ativado"):
        verify_raw_traces_exist(["baseline"], range(1001, 1005))

def test_demo_mode_trace_generation_and_packaging(tmp_path, monkeypatch):
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    scenarios = ["baseline", "rdl_phase1"]
    seeds = range(1001, 1004)
    
    create_dummy_raw_traces_if_missing(scenarios, seeds)
    
    # Check that XML files were created
    for sc in scenarios:
        for seed in seeds:
            xml_file = fake_raw_dir / sc / f"flowmonitor_seed_{seed}.xml"
            assert xml_file.exists()
            assert "FlowMonitor" in xml_file.read_text(encoding="utf-8")
            
    # Package baseline
    pkg = package_scenario_raw_data("baseline", 1001, 1003)
    assert pkg["scenario"] == "baseline"
    assert pkg["file_count"] == 3
    assert len(pkg["sha256"]) == 64
    assert os.path.exists(pkg["filepath"])
