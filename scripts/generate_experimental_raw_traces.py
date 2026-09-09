#!/usr/bin/env python3
"""
Gerador Demonstrativo de Traces Calibrados do ns-3 FlowMonitor (XML)
Projeto: xApp RDL (Resource and Decision Layer) - Fase 2 (CA-RDL)

Classificação Formal de Auditoria:
Este script é uma ferramenta demonstrativa e de teste de integração que gera
observações estocasticamente calibradas para validação de pipeline e testes unitários.
Todos os traces gerados contêm explicitamente o atributo synthetic="true" e mode="demo"
para garantir rastreabilidade estrita e impedir sua aceitação espúria como medição de rede.
"""

import os
import argparse
import numpy as np
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "experiments", "results")

def generate_calibrated_flowmonitor_traces(output_dir=None, n_seeds=30, mode="demo"):
    if output_dir is None:
        output_dir = os.path.join(RESULTS_DIR, mode, "raw")
        
    scenarios = ["baseline", "rdl_phase1", "rdl_phase2"]
    seeds = [1000 + i for i in range(1, n_seeds + 1)]
    
    for sc in scenarios:
        sc_dir = os.path.join(output_dir, sc)
        os.makedirs(sc_dir, exist_ok=True)
        
        for s in seeds:
            rng = np.random.RandomState(s)
            seed_file = os.path.join(sc_dir, f"flowmonitor_seed_{s}.xml")
            iso_now = datetime.now(timezone.utc).isoformat()
            
            with open(seed_file, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" ?>\n')
                f.write(
                    f'<FlowMonitor scenario="{sc}" seed="{s}" '
                    f'execution_id="demo_calibrated_{sc}_{s}" mode="demo" synthetic="true" '
                    f'generator="stochastic_calibrated_demo" timestamp="{iso_now}">\n'
                )
                f.write('  <FlowStats>\n')
                
                for flow_id in range(1, 31):
                    slice_type = "URLLC" if flow_id % 3 == 1 else ("eMBB" if flow_id % 3 == 2 else "mMTC")
                    tx_pkts = 1000
                    
                    if sc == "baseline":
                        pdr = max(0.20, min(0.60, rng.normal(0.3928, 0.065)))
                        rx_pkts = int(tx_pkts * pdr)
                        delay_mean = rng.normal(11.79, 1.85)
                    elif sc == "rdl_phase1":
                        pdr = max(0.98, min(0.999, rng.normal(0.9953, 0.0035)))
                        rx_pkts = int(tx_pkts * pdr)
                        delay_mean = rng.normal(2.85, 0.22)
                    else: # rdl_phase2
                        pdr = max(0.995, min(1.0, rng.normal(0.9988, 0.0008)))
                        rx_pkts = int(tx_pkts * pdr)
                        delay_mean = rng.normal(2.12, 0.15)
                    
                    # Invariante estrito físico: 0 <= rx_pkts <= tx_pkts e n_lost = n_tx - n_rx
                    rx_pkts = max(0, min(tx_pkts, rx_pkts))
                    lost_pkts = tx_pkts - rx_pkts
                    delay_sum = round(delay_mean * rx_pkts / 1000.0, 4)
                    jitter_sum = round(delay_mean * 0.1 * rx_pkts / 1000.0, 4)
                    
                    f.write(
                        f'    <Flow flowId="{flow_id}" slice="{slice_type}" '
                        f'txPackets="{tx_pkts}" rxPackets="{rx_pkts}" lostPackets="{lost_pkts}" '
                        f'delaySum="{delay_sum}" jitterSum="{jitter_sum}" />\n'
                    )
                
                f.write('  </FlowStats>\n')
                f.write('</FlowMonitor>\n')
                
    print(f"[OK] Traces demonstrativos calibrados gerados em: {output_dir} ({len(scenarios) * len(seeds)} arquivos XML com synthetic='true')")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador Demonstrativo de Traces Calibrados")
    parser.add_argument("--n-seeds", type=int, default=30)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--mode", type=str, default="demo")
    args = parser.parse_args()
    
    generate_calibrated_flowmonitor_traces(output_dir=args.output_dir, n_seeds=args.n_seeds, mode=args.mode)
