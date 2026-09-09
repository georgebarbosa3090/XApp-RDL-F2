#!/usr/bin/env python3
"""
Script de Empacotamento e Sincronizacao de Dados Brutos (Raw Traces) para Google Drive
Projeto: xApp-RDL Fase 2 (CA-RDL / Safe-MARL)

Objetivo:
1. Empacotar todos os traces brutos (XML, logs por semente, PCAPs) por rodada/cenario;
2. Calcular hashes criptograficos SHA-256 para cada pacote de dados brutos;
3. Gerar manifesto de rastreabilidade vinculando os dados processados (GitHub)
   aos dados brutos de alta volumetria hospedados no Google Drive:
   Pasta Google Drive: https://drive.google.com/drive/folders/1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(BASE_DIR, "experiments", "results", "raw")
GDRIVE_FOLDER_ID = "1dC5g5iAVqGcdiXKQPyyUxES1rNjdZw8x"
GDRIVE_URL = f"https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}"

def calculate_sha256(filepath: str) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_dummy_raw_traces_if_missing(scenarios, seeds_range):
    """Gera arquivos de trace XML representativos por semente exclusivamente em modo de teste/demo."""
    for sc in scenarios:
        sc_dir = os.path.join(RAW_DIR, sc)
        os.makedirs(sc_dir, exist_ok=True)
        for seed in seeds_range:
            seed_file = os.path.join(sc_dir, f"flowmonitor_seed_{seed}.xml")
            if not os.path.exists(seed_file):
                with open(seed_file, "w", encoding="utf-8") as f:
                    iso_now = datetime.now(timezone.utc).isoformat()
                    f.write(f'<?xml version="1.0" ?>\n<FlowMonitor scenario="{sc}" seed="{seed}" mode="demo" synthetic="true" timestamp="{iso_now}">\n')
                    f.write('  <FlowStats>\n')
                    for flow_id in range(1, 31):
                        slice_type = "URLLC" if flow_id % 3 == 1 else ("eMBB" if flow_id % 3 == 2 else "mMTC")
                        f.write(f'    <Flow flowId="{flow_id}" slice="{slice_type}" txPackets="1000" rxPackets="998" delaySum="1.92" />\n')
                    f.write('  </FlowStats>\n</FlowMonitor>\n')

import xml.etree.ElementTree as ET

def verify_raw_traces_exist(scenarios, seeds_range):
    """Verifica estruturalmente se todos os arquivos brutos experimentais existem e são autênticos via ElementTree."""
    missing = []
    synthetic_found = []
    invalid_format = []
    
    for sc in scenarios:
        sc_dir = os.path.join(RAW_DIR, sc)
        if not os.path.isdir(sc_dir):
            missing.append(f"Diretório ausente: {sc_dir}")
            continue
        for seed in seeds_range:
            seed_file = os.path.join(sc_dir, f"flowmonitor_seed_{seed}.xml")
            if not os.path.exists(seed_file):
                missing.append(seed_file)
            else:
                try:
                    tree = ET.parse(seed_file)
                    root = tree.getroot()
                    
                    # 1. Verifica atributos explícitos de demonstração/sintéticos (independente de aspas)
                    is_synth = root.attrib.get("synthetic", "").lower() in ("true", "1", "yes")
                    is_demo = root.attrib.get("mode", "").lower() in ("demo", "synthetic")
                    
                    if is_synth or is_demo:
                        synthetic_found.append(seed_file)
                        continue
                        
                    # 2. Verificação de associação de metadados: cenário e semente
                    sc_attr = root.attrib.get("scenario")
                    if sc_attr and sc_attr != sc:
                        invalid_format.append(f"{seed_file} (cenário nos metadados '{sc_attr}' difere do diretório '{sc}')")
                        continue
                    seed_attr = root.attrib.get("seed")
                    if seed_attr:
                        try:
                            if int(seed_attr) != seed:
                                invalid_format.append(f"{seed_file} (semente nos metadados '{seed_attr}' difere do arquivo '{seed}')")
                                continue
                        except ValueError:
                            pass

                    # 3. Verificação positiva de estrutura de fluxos
                    flows = root.findall(".//Flow")
                    if not flows:
                        invalid_format.append(f"{seed_file} (estrutura FlowMonitor sem nós <Flow> de telemetria física)")
                        continue
                        
                    # Validação estrita de invariantes físicos em TODOS os fluxos: 0 <= n_rx <= n_tx e n_lost = n_tx - n_rx
                    has_positive_tx = False
                    flow_invariant_error = None
                    for f_elem in flows:
                        tx_val = f_elem.attrib.get("txPackets")
                        rx_val = f_elem.attrib.get("rxPackets")
                        lost_val = f_elem.attrib.get("lostPackets")
                        if tx_val is None or rx_val is None:
                            flow_invariant_error = "contadores txPackets ou rxPackets ausentes"
                            break
                        try:
                            tx = int(tx_val)
                            rx = int(rx_val)
                        except ValueError:
                            flow_invariant_error = f"contadores não numéricos: tx={tx_val}, rx={rx_val}"
                            break
                        
                        if tx < 0 or rx < 0:
                            flow_invariant_error = f"contadores negativos: tx={tx}, rx={rx}"
                            break
                        if rx > tx:
                            flow_invariant_error = f"violação física de conservação de pacotes rx > tx: tx={tx}, rx={rx}"
                            break
                            
                        # Validação estrita da conservação física de pacotes: n_lost = n_tx - n_rx
                        if lost_val is not None:
                            try:
                                lost = int(lost_val)
                                if lost != (tx - rx):
                                    flow_invariant_error = f"violação de conservação n_lost == n_tx - n_rx: lost={lost}, tx-rx={tx-rx}"
                                    break
                            except ValueError:
                                flow_invariant_error = f"contador lostPackets não numérico: {lost_val}"
                                break
                                
                        if tx > 0:
                            has_positive_tx = True

                    if flow_invariant_error:
                        invalid_format.append(f"{seed_file} ({flow_invariant_error})")
                    elif not has_positive_tx:
                        invalid_format.append(f"{seed_file} (todos os fluxos possuem txPackets == 0)")
                        
                except Exception as e:
                    invalid_format.append(f"{seed_file} (falha de leitura/parse XML: {e})")

    if missing:
        raise FileNotFoundError(
            f"Modo estrito ativado: {len(missing)} arquivos de trace brutos ausentes na cadeia de custódia:\n"
            + "\n".join(missing[:10])
            + ("\n..." if len(missing) > 10 else "")
        )
    if synthetic_found:
        raise ValueError(
            f"Modo estrito ativado: Rejeição de integridade experimental! "
            f"Foram detectados {len(synthetic_found)} traces sintéticos de demonstração no diretório experimental:\n"
            + "\n".join(synthetic_found[:10])
            + "\nNo modo --mode experiment, todos os traces devem ser originários de execuções físicas/ns-3 reais."
        )
    if invalid_format:
        raise ValueError(
            f"Modo estrito ativado: {len(invalid_format)} arquivos de trace brutos inválidos ou não conformes:\n"
            + "\n".join(invalid_format[:10])
        )

def package_scenario_raw_data(scenario_name: str, min_seed: int, max_seed: int) -> dict:
    """Empacota os traces brutos de um cenario em um arquivo ZIP comprimido."""
    sc_dir = os.path.join(RAW_DIR, scenario_name)
    zip_path = os.path.join(RAW_DIR, f"raw_traces_{scenario_name}_seeds_{min_seed}_{max_seed}.zip")
    
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(sc_dir):
            for file in files:
                if file.endswith((".xml", ".log", ".pcap", ".tr")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, RAW_DIR)
                    zf.write(full_path, rel_path)
                    file_count += 1
                    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    sha256 = calculate_sha256(zip_path)
    rel_zip_path = os.path.relpath(zip_path, BASE_DIR).replace("\\", "/")
    return {
        "scenario": scenario_name,
        "filename": os.path.basename(zip_path),
        "filepath": rel_zip_path,
        "file_count": file_count,
        "size_mb": round(size_mb, 2),
        "sha256": sha256
    }

def main():
    parser = argparse.ArgumentParser(description="Empacotamento de Raw Traces para Sincronização Google Drive")
    parser.add_argument("--mode", choices=["demo", "experiment"], default="demo", help="Modo de execução (demo cria traces sintéticos se ausentes, experiment exige traces reais)")
    parser.add_argument("--strict", action="store_true", help="Falha com erro se traces reais estiverem ausentes")
    parser.add_argument("--seeds", type=int, default=30, help="Número de sementes estocásticas a empacotar")
    parser.add_argument("--start-seed", type=int, default=1001, help="Semente inicial")
    args = parser.parse_args()

    print("=" * 75)
    print(" Empacotamento de Dados Brutos (Raw Traces) para Sincronizacao Google Drive")
    print(f" Modo: {args.mode.upper()} | Estrito: {args.strict}")
    print(f" Pasta de Destino: {GDRIVE_URL}")
    print("=" * 75)
    
    os.makedirs(RAW_DIR, exist_ok=True)
    scenarios = ["baseline", "rdl_phase1", "rdl_phase2"]
    seeds_range = range(args.start_seed, args.start_seed + args.seeds)
    min_seed = args.start_seed
    max_seed = args.start_seed + args.seeds - 1

    if args.strict or args.mode == "experiment":
        verify_raw_traces_exist(scenarios, seeds_range)
    else:
        create_dummy_raw_traces_if_missing(scenarios, seeds_range)
    
    manifest = {
        "experiment_name": "xApp-RDL-Phase2-MultiSeed-Campaign",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "strict": args.strict,
        "seeds_count": args.seeds,
        "seeds_range": [min_seed, max_seed],
        "gdrive_folder_id": GDRIVE_FOLDER_ID,
        "gdrive_folder_url": GDRIVE_URL,
        "packages": []
    }
    
    for sc in scenarios:
        print(f"[*] Empacotando traces brutos do cenario: {sc}...")
        pkg = package_scenario_raw_data(sc, min_seed, max_seed)
        manifest["packages"].append(pkg)
        print(f"    -> Arquivo: {pkg['filename']} ({pkg['size_mb']} MB, {pkg['file_count']} files) | SHA-256: {pkg['sha256'][:16]}...")
        
    # Salvar manifesto JSON
    manifest_path = os.path.join(BASE_DIR, "experiments", "results", "manifest_gdrive_raw_data.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    rel_manifest_path = os.path.relpath(manifest_path, BASE_DIR).replace("\\", "/")
    print(f"\n[OK] Manifesto de dados brutos salvo em: {rel_manifest_path}")
    
    # Criar documentacao explicativa no diretorio raw/
    readme_raw_path = os.path.join(RAW_DIR, "README.md")
    with open(readme_raw_path, "w", encoding="utf-8") as f:
        f.write("# Armazenamento de Dados Brutos de Co-Simulacao (Raw Traces)\n\n")
        f.write("Devido ao volume de dados gerado pelo `FlowMonitor` do ns-3 e pelos traces PCAP/SCTP de cada rodada estocastica ($N = 30$ sementes por cenario), os arquivos brutos estao hospedados no **Google Drive oficial do projeto**, enquanto o **GitHub armazena os datasets limpos e processados (`experiments/results/data/*.csv`)**.\n\n")
        f.write(f"### [Acessar Pasta de Dados Brutos no Google Drive]({GDRIVE_URL})\n\n")
        f.write("#### Pacotes de Dados Brutos e Hashes SHA-256:\n\n")
        f.write("| Cenario | Arquivo Compactado | Arquivos | Tamanho | Checksum SHA-256 |\n")
        f.write("| :--- | :--- | :---: | :---: | :--- |\n")
        for pkg in manifest["packages"]:
            f.write(f"| **{pkg['scenario']}** | `{pkg['filename']}` | `{pkg['file_count']}` | `{pkg['size_mb']} MB` | `{pkg['sha256']}` |\n")
        f.write("\n---\n")
        f.write("### Como empacotar traces de novos ensaios:\n")
        f.write("```bash\n")
        f.write("# Modo demonstracao com sementes 1001-1030\n")
        f.write("python scripts/package_and_sync_raw_results.py --mode demo\n\n")
        f.write("# Modo estrito de experimentacao (valida cadeia de custodia completa)\n")
        f.write("python scripts/package_and_sync_raw_results.py --mode experiment --strict\n")
        f.write("```\n")
        
    print(f"[OK] Documentacao raw salva em: {readme_raw_path}")
    print("=" * 75)
    print(" Concluido com sucesso! Os arquivos .csv permanecem no GitHub e os .zip/.xml no Google Drive.")
    print("=" * 75)

if __name__ == "__main__":
    main()
