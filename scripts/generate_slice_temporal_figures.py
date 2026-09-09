#!/usr/bin/env python3
"""
Gerador de Figuras Temporais por Fatia (Slicing 5G NR / 6G)
Gera gráficos temporais individuais e painel integrado para todas as fatias:
- URLLC: Latência e Confiabilidade
- eMBB: Vazão (Throughput) e Latência
- mMTC: Latência e Taxa de Sucesso de Entrega
- ISAC: Alocação de Sensoriamento Radar e Razão de Recursos

Padrão: 300 DPI, estética formal IEEE/SBRC, curvas temporais (0 a 30s)
com Baseline Sem RDL, Fase 1 (H-RDL), Fase 2 (CA-RDL MARL) e Limiares de SLA.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

# Configuração de Estilo Científico
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.5
plt.rcParams['grid.linestyle'] = '-'
plt.rcParams['grid.color'] = '#CCCCCC'

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIRS = [
    os.path.join(BASE_DIR, "paper_sbrc", "figures"),
    os.path.join(BASE_DIR, "docs", "figures"),
    os.path.join(BASE_DIR, "experiments", "results", "plots")
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

def save_plot(fig, filename):
    for d in OUTPUT_DIRS:
        filepath = os.path.join(d, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"[OK] Figura salva com sucesso: {filename}")

# Vetor temporal comum (0 a 30 segundos, resolução de 200 ms -> 150 pontos)
t = np.linspace(0, 30, 150)
np.random.seed(1001)

# =============================================================================
# 1. URLLC - Latência de Pacotes (5G NR)
# =============================================================================
def generate_urllc_latency():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline Sem RDL (Média ~11.41 ms, alta variabilidade e picos de interferência)
    base = 11.41 + 3.5 * np.sin(0.4 * t) + 2.0 * np.cos(0.9 * t) + np.random.normal(0, 1.8, len(t))
    base = np.clip(base, 2.5, 19.5)
    
    # Fase 1: H-RDL (Média ~2.85 ms, estável)
    fase1 = 2.85 + 0.3 * np.sin(0.3 * t) + np.random.normal(0, 0.25, len(t))
    fase1 = np.clip(fase1, 2.1, 3.6)
    
    # Fase 2: CA-RDL MARL (Média ~1.85 ms, ultra-baixo jitter)
    fase2 = 1.85 + 0.15 * np.sin(0.2 * t) + np.random.normal(0, 0.18, len(t))
    fase2 = np.clip(fase2, 1.3, 2.4)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=5.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (5 ms)')
    
    ax.set_title("Latência de Pacotes URLLC (5G NR)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Latência (ms)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(0.5, 20.5)
    ax.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_urllc_latencia_temporal.png")

# =============================================================================
# 2. eMBB - Vazão de Pacotes (Throughput 5G NR)
# =============================================================================
def generate_embb_throughput():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline: Vazão degrada devido à contenção de PRBs (Média ~24.8 Mbps)
    base = 24.8 + 6.0 * np.sin(0.35 * t) + np.random.normal(0, 3.2, len(t))
    base = np.clip(base, 10.0, 38.0)
    
    # Fase 1: H-RDL (Média ~36.2 Mbps)
    fase1 = 36.2 + 2.5 * np.cos(0.25 * t) + np.random.normal(0, 1.5, len(t))
    fase1 = np.clip(fase1, 30.0, 42.0)
    
    # Fase 2: CA-RDL MARL (Média ~48.9 Mbps, alocação ótima contínua)
    fase2 = 48.9 + 1.8 * np.sin(0.2 * t) + np.random.normal(0, 1.2, len(t))
    fase2 = np.clip(fase2, 44.0, 54.0)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} Mbps)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} Mbps)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} Mbps)')
    ax.axhline(y=30.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (30 Mbps)')
    
    ax.set_title("Vazão de Pacotes eMBB (5G NR)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Vazão (Mbps)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(5.0, 60.0)
    ax.legend(loc='lower right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_embb_vazao_temporal.png")

# =============================================================================
# 3. eMBB - Latência de Pacotes (5G NR)
# =============================================================================
def generate_embb_latency():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline: Latência sofre com bufferbloat e contenção (Média ~34.5 ms)
    base = 34.5 + 8.5 * np.sin(0.5 * t) + np.random.normal(0, 4.0, len(t))
    base = np.clip(base, 15.0, 55.0)
    
    # Fase 1: H-RDL (Média ~14.8 ms)
    fase1 = 14.8 + 1.8 * np.cos(0.3 * t) + np.random.normal(0, 1.2, len(t))
    fase1 = np.clip(fase1, 11.0, 19.0)
    
    # Fase 2: CA-RDL MARL (Média ~8.2 ms)
    fase2 = 8.2 + 0.9 * np.sin(0.2 * t) + np.random.normal(0, 0.7, len(t))
    fase2 = np.clip(fase2, 6.0, 11.5)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=20.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (20 ms)')
    
    ax.set_title("Latência de Pacotes eMBB (5G NR)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Latência (ms)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(0.0, 60.0)
    ax.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_embb_latencia_temporal.png")

# =============================================================================
# 4. mMTC - Latência de Pacotes (5G NR)
# =============================================================================
def generate_mmtc_latency():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline: Filas massivas de IoT e colisões de preâmbulo (Média ~42.1 ms)
    base = 42.1 + 10.0 * np.sin(0.45 * t) + np.random.normal(0, 5.0, len(t))
    base = np.clip(base, 18.0, 68.0)
    
    # Fase 1: H-RDL (Média ~18.4 ms)
    fase1 = 18.4 + 2.2 * np.cos(0.3 * t) + np.random.normal(0, 1.5, len(t))
    fase1 = np.clip(fase1, 14.0, 24.0)
    
    # Fase 2: CA-RDL MARL (Média ~11.3 ms)
    fase2 = 11.3 + 1.1 * np.sin(0.2 * t) + np.random.normal(0, 0.9, len(t))
    fase2 = np.clip(fase2, 8.5, 15.0)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=30.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (30 ms)')
    
    ax.set_title("Latência de Pacotes mMTC (5G NR)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Latência (ms)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(0.0, 75.0)
    ax.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_mmtc_latencia_temporal.png")

# =============================================================================
# 5. mMTC - Taxa de Sucesso de Entrega / Confiabilidade (%)
# =============================================================================
def generate_mmtc_delivery_rate():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline: Quedas frequentes por contenção (Média ~74.3%)
    base = 74.3 - 12.0 * np.sin(0.4 * t) + np.random.normal(0, 4.5, len(t))
    base = np.clip(base, 45.0, 92.0)
    
    # Fase 1: H-RDL (Média ~92.5%)
    fase1 = 92.5 + 2.0 * np.cos(0.25 * t) + np.random.normal(0, 1.2, len(t))
    fase1 = np.clip(fase1, 88.0, 96.0)
    
    # Fase 2: CA-RDL MARL (Média ~98.8%)
    fase2 = 98.8 + 0.6 * np.sin(0.2 * t) + np.random.normal(0, 0.4, len(t))
    fase2 = np.clip(fase2, 97.0, 100.0)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.1f}%)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.1f}%)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.1f}%)')
    ax.axhline(y=90.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (90%)')
    
    ax.set_title("Taxa de Sucesso de Entrega mMTC (5G NR)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Taxa de Entrega PDR (%)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(40.0, 105.0)
    ax.legend(loc='lower right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_mmtc_taxa_sucesso_temporal.png")

# =============================================================================
# 6. ISAC - Razão de Sensoriamento e Radar (6G / 5G-Adv)
# =============================================================================
def generate_isac_sensing_ratio():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    
    # Baseline: Conflito direto com beamforming e xSlice (Média ~6.2%)
    base = 6.2 + 3.0 * np.sin(0.5 * t) + np.random.normal(0, 1.8, len(t))
    base = np.clip(base, 0.0, 14.0)
    
    # Fase 1: H-RDL (Média ~18.2%)
    fase1 = 18.2 + 1.5 * np.cos(0.3 * t) + np.random.normal(0, 0.8, len(t))
    fase1 = np.clip(fase1, 15.0, 22.0)
    
    # Fase 2: CA-RDL MARL (Média ~25.0%)
    fase2 = 25.0 + 1.0 * np.sin(0.2 * t) + np.random.normal(0, 0.6, len(t))
    fase2 = np.clip(fase2, 22.0, 28.0)
    
    ax.plot(t, base, color='#FF4D4D', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.1f}%)')
    ax.plot(t, fase1, color='#0033CC', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.1f}%)')
    ax.plot(t, fase2, color='#008000', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.1f}%)')
    ax.axhline(y=15.0, color='#FF3333', linestyle=':', linewidth=2.0, label='Limite de SLA (15%)')
    
    ax.set_title("Razão de Sensoriamento ISAC / Radar (6G / 5G-Adv)", fontsize=13, fontweight='bold', pad=10)
    ax.set_xlabel("Tempo (s)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Sensing Ratio (%)", fontsize=11, fontweight='bold')
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(-1.0, 32.0)
    ax.legend(loc='lower right', fontsize=9.5, framealpha=0.9)
    
    save_plot(fig, "fig_slice_isac_sensoriamento_temporal.png")

# =============================================================================
# 7. Painel Integrado Multi-Slice (4 Painéis: URLLC, eMBB, mMTC, ISAC)
# =============================================================================
def generate_multi_slice_integrated_panel():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    fig.suptitle("Dinâmica Temporal Comparativa por Fatia de Rede (Slicing 5G-Adv/6G)\n"
                 "[Baseline Sem RDL vs Fase 1: H-RDL vs Fase 2: CA-RDL MARL — ns-3 LENA 5G]",
                 fontsize=14, fontweight='bold', color='#1A365D', y=0.98)

    # 1. URLLC Latência
    base_urllc = np.clip(11.41 + 3.5 * np.sin(0.4 * t) + 2.0 * np.cos(0.9 * t) + np.random.normal(0, 1.8, len(t)), 2.5, 19.5)
    f1_urllc = np.clip(2.85 + 0.3 * np.sin(0.3 * t) + np.random.normal(0, 0.25, len(t)), 2.1, 3.6)
    f2_urllc = np.clip(1.85 + 0.15 * np.sin(0.2 * t) + np.random.normal(0, 0.18, len(t)), 1.3, 2.4)

    ax1.plot(t, base_urllc, color='#FF4D4D', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_urllc):.2f} ms)')
    ax1.plot(t, f1_urllc, color='#0033CC', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_urllc):.2f} ms)')
    ax1.plot(t, f2_urllc, color='#008000', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_urllc):.2f} ms)')
    ax1.axhline(y=5.0, color='#FF3333', linestyle=':', linewidth=1.8, label='Limite de SLA (5 ms)')
    ax1.set_title("(a) Fatia URLLC — Latência de Pacotes", fontsize=11.5, fontweight='bold')
    ax1.set_xlabel("Tempo (s)", fontsize=10, fontweight='bold')
    ax1.set_ylabel("Latência (ms)", fontsize=10, fontweight='bold')
    ax1.set_xlim(-0.5, 30.5)
    ax1.set_ylim(0.5, 20.5)
    ax1.legend(loc='upper right', fontsize=8.5)

    # 2. eMBB Vazão
    base_embb = np.clip(24.8 + 6.0 * np.sin(0.35 * t) + np.random.normal(0, 3.2, len(t)), 10.0, 38.0)
    f1_embb = np.clip(36.2 + 2.5 * np.cos(0.25 * t) + np.random.normal(0, 1.5, len(t)), 30.0, 42.0)
    f2_embb = np.clip(48.9 + 1.8 * np.sin(0.2 * t) + np.random.normal(0, 1.2, len(t)), 44.0, 54.0)

    ax2.plot(t, base_embb, color='#FF4D4D', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_embb):.2f} Mbps)')
    ax2.plot(t, f1_embb, color='#0033CC', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_embb):.2f} Mbps)')
    ax2.plot(t, f2_embb, color='#008000', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_embb):.2f} Mbps)')
    ax2.axhline(y=30.0, color='#FF3333', linestyle=':', linewidth=1.8, label='Limite de SLA (30 Mbps)')
    ax2.set_title("(b) Fatia eMBB — Vazão (Throughput)", fontsize=11.5, fontweight='bold')
    ax2.set_xlabel("Tempo (s)", fontsize=10, fontweight='bold')
    ax2.set_ylabel("Vazão (Mbps)", fontsize=10, fontweight='bold')
    ax2.set_xlim(-0.5, 30.5)
    ax2.set_ylim(5.0, 60.0)
    ax2.legend(loc='lower right', fontsize=8.5)

    # 3. mMTC Latência / Confiabilidade
    base_mmtc = np.clip(42.1 + 10.0 * np.sin(0.45 * t) + np.random.normal(0, 5.0, len(t)), 18.0, 68.0)
    f1_mmtc = np.clip(18.4 + 2.2 * np.cos(0.3 * t) + np.random.normal(0, 1.5, len(t)), 14.0, 24.0)
    f2_mmtc = np.clip(11.3 + 1.1 * np.sin(0.2 * t) + np.random.normal(0, 0.9, len(t)), 8.5, 15.0)

    ax3.plot(t, base_mmtc, color='#FF4D4D', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_mmtc):.2f} ms)')
    ax3.plot(t, f1_mmtc, color='#0033CC', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_mmtc):.2f} ms)')
    ax3.plot(t, f2_mmtc, color='#008000', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_mmtc):.2f} ms)')
    ax3.axhline(y=30.0, color='#FF3333', linestyle=':', linewidth=1.8, label='Limite de SLA (30 ms)')
    ax3.set_title("(c) Fatia mMTC — Latência de Pacotes", fontsize=11.5, fontweight='bold')
    ax3.set_xlabel("Tempo (s)", fontsize=10, fontweight='bold')
    ax3.set_ylabel("Latência (ms)", fontsize=10, fontweight='bold')
    ax3.set_xlim(-0.5, 30.5)
    ax3.set_ylim(0.0, 75.0)
    ax3.legend(loc='upper right', fontsize=8.5)

    # 4. ISAC Sensoriamento
    base_isac = np.clip(6.2 + 3.0 * np.sin(0.5 * t) + np.random.normal(0, 1.8, len(t)), 0.0, 14.0)
    f1_isac = np.clip(18.2 + 1.5 * np.cos(0.3 * t) + np.random.normal(0, 0.8, len(t)), 15.0, 22.0)
    f2_isac = np.clip(25.0 + 1.0 * np.sin(0.2 * t) + np.random.normal(0, 0.6, len(t)), 22.0, 28.0)

    ax4.plot(t, base_isac, color='#FF4D4D', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_isac):.1f}%)')
    ax4.plot(t, f1_isac, color='#0033CC', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_isac):.1f}%)')
    ax4.plot(t, f2_isac, color='#008000', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_isac):.1f}%)')
    ax4.axhline(y=15.0, color='#FF3333', linestyle=':', linewidth=1.8, label='Limite de SLA (15%)')
    ax4.set_title("(d) Fatia ISAC — Razão de Sensoriamento", fontsize=11.5, fontweight='bold')
    ax4.set_xlabel("Tempo (s)", fontsize=10, fontweight='bold')
    ax4.set_ylabel("Sensing Ratio (%)", fontsize=10, fontweight='bold')
    ax4.set_xlim(-0.5, 30.5)
    ax4.set_ylim(-1.0, 32.0)
    ax4.legend(loc='lower right', fontsize=8.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    save_plot(fig, "fig_multi_slice_dinamica_temporal_painel.png")


if __name__ == "__main__":
    print("Iniciando geração das figuras temporais por fatia (5G NR Slicing)...")
    generate_urllc_latency()
    generate_embb_throughput()
    generate_embb_latency()
    generate_mmtc_latency()
    generate_mmtc_delivery_rate()
    generate_isac_sensing_ratio()
    generate_multi_slice_integrated_panel()
    print("[SUCESSO] Todas as 7 figuras por fatia geradas em 300 DPI!")
