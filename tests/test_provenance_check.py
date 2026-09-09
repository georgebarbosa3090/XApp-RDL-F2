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

def test_verify_raw_traces_rejects_synthetic_traces_in_experiment_mode(tmp_path, monkeypatch):
    """Valida o teste negativo de proveniência: traces sintéticos do modo demo DEVEM ser rejeitados no modo estrito."""
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    # 1. Gera traces em modo demo
    create_dummy_raw_traces_if_missing(["baseline"], range(1001, 1003))
    
    # 2. Execução em modo estrito/experimento deve detectar e rejeitar traces sintéticos
    with pytest.raises(ValueError, match="Rejeição de integridade experimental"):
        verify_raw_traces_exist(["baseline"], range(1001, 1003))

def test_verify_raw_traces_rejects_single_quotes_synthetic_and_empty_flows(tmp_path, monkeypatch):
    """Valida que atributos com aspas simples e XML sem fluxos são rejeitados via ElementTree."""
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    sc_dir = fake_raw_dir / "baseline"
    sc_dir.mkdir(parents=True)
    
    # 1. Teste com aspas simples: synthetic='true'
    file_single_quote = sc_dir / "flowmonitor_seed_1001.xml"
    file_single_quote.write_text("<FlowMonitor synthetic='true' mode='demo'><FlowStats/></FlowMonitor>", encoding="utf-8")
    
    with pytest.raises(ValueError, match="Rejeição de integridade experimental"):
        verify_raw_traces_exist(["baseline"], range(1001, 1002))
        
    # 2. Teste sem fluxos de telemetria
    file_single_quote.write_text("<FlowMonitor><FlowStats/></FlowMonitor>", encoding="utf-8")
    with pytest.raises(ValueError, match="não conformes"):
        verify_raw_traces_exist(["baseline"], range(1001, 1002))

def test_verify_raw_traces_accepts_valid_experimental_xml(tmp_path, monkeypatch):
    """Valida que arquivos XML com estrutura válida de FlowMonitor e contadores de pacotes são aceitos."""
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    sc_dir = fake_raw_dir / "baseline"
    sc_dir.mkdir(parents=True)
    
    valid_xml = sc_dir / "flowmonitor_seed_1001.xml"
    valid_xml.write_text(
        '<FlowMonitor execution_id="run_ns3_001">'
        '  <FlowStats>'
        '    <Flow flowId="1" txPackets="1000" rxPackets="998" delaySum="1.92" />'
        '  </FlowStats>'
        '</FlowMonitor>',
        encoding="utf-8"
    )
    
    # Não deve lançar exceção
    verify_raw_traces_exist(["baseline"], range(1001, 1002))

def test_verify_raw_traces_rejects_physical_invariant_violations(tmp_path, monkeypatch):
    """Valida que contadores físicos impossíveis (rx < 0 ou rx > tx) são rejeitados estritamente."""
    import scripts.package_and_sync_raw_results as pkg_module
    
    fake_raw_dir = tmp_path / "raw"
    monkeypatch.setattr(pkg_module, "RAW_DIR", str(fake_raw_dir))
    
    sc_dir = fake_raw_dir / "baseline"
    sc_dir.mkdir(parents=True)
    
    # 1. Caso rxPackets negativo: rxPackets="-5"
    bad_xml_1 = sc_dir / "flowmonitor_seed_1001.xml"
    bad_xml_1.write_text(
        '<FlowMonitor execution_id="run_ns3_001">'
        '  <FlowStats>'
        '    <Flow flowId="1" txPackets="10" rxPackets="-5" />'
        '  </FlowStats>'
        '</FlowMonitor>',
        encoding="utf-8"
    )
    with pytest.raises(ValueError, match="contadores negativos"):
        verify_raw_traces_exist(["baseline"], range(1001, 1002))
        
    # 2. Caso rxPackets > txPackets: tx="10" rx="999"
    bad_xml_1.write_text(
        '<FlowMonitor execution_id="run_ns3_001">'
        '  <FlowStats>'
        '    <Flow flowId="1" txPackets="10" rxPackets="999" />'
        '  </FlowStats>'
        '</FlowMonitor>',
        encoding="utf-8"
    )
    with pytest.raises(ValueError, match="violação física de conservação de pacotes rx > tx"):
        verify_raw_traces_exist(["baseline"], range(1001, 1002))



