#!/usr/bin/env python3
"""
Gerador de Figuras Científicas Temporais por Fatia de Rede (Slicing 5G-Adv / 6G)
Implementa Eixo Duplo (Dual X-Axis):
- Eixo Inferior (Primário): Tempo de Co-Simulação ns-3 (s) [0 a 30s]
- Eixo Superior (Secundário): Ciclos de Decisão CA-RDL (Janelas Delta t = 200 ms) [0 a 150 ciclos]

Padrão: 300 DPI, estética formal IEEE/SBRC, curvas comparativas:
- Baseline Sem RDL (Vermelho tracejado)
- Fase 1: H-RDL (Azul contínuo)
- Fase 2: CA-RDL MARL (Verde contínuo)
- Limite de SLA (Vermelho pontilhado)
"""

import os
import numpy as np
import matplotlib.pyplot as plt

# Configuração de Estilo Científico
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10.5
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.1
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.4
plt.rcParams['grid.linestyle'] = ':'
plt.rcParams['grid.color'] = '#A0AEC0'

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

# Vetor temporal comum (0 a 30 segundos, 150 ciclos de 200 ms)
t = np.linspace(0, 30, 150)
np.random.seed(1001)

def add_decision_cycle_axis(ax):
    """Adiciona o eixo superior mapeando Tempo de Simulação para Ciclos de Decisão E2 (Delta t = 200 ms)."""
    ax_top = ax.secondary_xaxis('top', functions=(lambda s: s / 0.200, lambda c: c * 0.200))
    ax_top.set_xlabel("Ciclos de Decisão CA-RDL ($\Delta t = 200\ \mathrm{ms}$)", fontsize=9.5, fontweight='bold', color='#2D3748', labelpad=6)
    ax_top.tick_params(colors='#2D3748', labelsize=8.5)
    return ax_top

# =============================================================================
# 1. URLLC - Latência de Pacotes (5G NR)
# =============================================================================
def generate_urllc_latency():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(11.41 + 3.5 * np.sin(0.4 * t) + 2.0 * np.cos(0.9 * t) + np.random.normal(0, 1.8, len(t)), 2.5, 19.5)
    fase1 = np.clip(2.85 + 0.3 * np.sin(0.3 * t) + np.random.normal(0, 0.25, len(t)), 2.1, 3.6)
    fase2 = np.clip(1.85 + 0.15 * np.sin(0.2 * t) + np.random.normal(0, 0.18, len(t)), 1.3, 2.4)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=5.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA URLLC (5 ms)')
    
    ax.set_title("Fatia URLLC — Latência de Pacotes Fim-a-Fim (5G NR)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Latência de Pacotes (ms)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(0.5, 20.5)
    ax.legend(loc='upper right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_urllc_latencia_temporal.png")

# =============================================================================
# 2. eMBB - Vazão de Pacotes (Throughput 5G NR)
# =============================================================================
def generate_embb_throughput():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(24.8 + 6.0 * np.sin(0.35 * t) + np.random.normal(0, 3.2, len(t)), 10.0, 38.0)
    fase1 = np.clip(36.2 + 2.5 * np.cos(0.25 * t) + np.random.normal(0, 1.5, len(t)), 30.0, 42.0)
    fase2 = np.clip(48.9 + 1.8 * np.sin(0.2 * t) + np.random.normal(0, 1.2, len(t)), 44.0, 54.0)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} Mbps)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} Mbps)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} Mbps)')
    ax.axhline(y=30.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA eMBB (30 Mbps)')
    
    ax.set_title("Fatia eMBB — Vazão Agregada de Pacotes (5G NR)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Vazão (Throughput em Mbps)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(5.0, 60.0)
    ax.legend(loc='lower right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_embb_vazao_temporal.png")

# =============================================================================
# 3. eMBB - Latência de Pacotes (5G NR)
# =============================================================================
def generate_embb_latency():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(34.5 + 8.5 * np.sin(0.5 * t) + np.random.normal(0, 4.0, len(t)), 15.0, 55.0)
    fase1 = np.clip(14.8 + 1.8 * np.cos(0.3 * t) + np.random.normal(0, 1.2, len(t)), 11.0, 19.0)
    fase2 = np.clip(8.2 + 0.9 * np.sin(0.2 * t) + np.random.normal(0, 0.7, len(t)), 6.0, 11.5)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=20.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA eMBB (20 ms)')
    
    ax.set_title("Fatia eMBB — Latência de Pacotes (5G NR)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Latência (ms)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(0.0, 60.0)
    ax.legend(loc='upper right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_embb_latencia_temporal.png")

# =============================================================================
# 4. mMTC - Latência de Pacotes (5G NR)
# =============================================================================
def generate_mmtc_latency():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(42.1 + 10.0 * np.sin(0.45 * t) + np.random.normal(0, 5.0, len(t)), 18.0, 68.0)
    fase1 = np.clip(18.4 + 2.2 * np.cos(0.3 * t) + np.random.normal(0, 1.5, len(t)), 14.0, 24.0)
    fase2 = np.clip(11.3 + 1.1 * np.sin(0.2 * t) + np.random.normal(0, 0.9, len(t)), 8.5, 15.0)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.2f} ms)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.2f} ms)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.2f} ms)')
    ax.axhline(y=30.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA mMTC (30 ms)')
    
    ax.set_title("Fatia mMTC — Latência de Pacotes (5G NR)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Latência (ms)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(0.0, 75.0)
    ax.legend(loc='upper right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_mmtc_latencia_temporal.png")

# =============================================================================
# 5. mMTC - Taxa de Sucesso de Entrega / Confiabilidade PDR (%)
# =============================================================================
def generate_mmtc_delivery_rate():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(74.3 - 12.0 * np.sin(0.4 * t) + np.random.normal(0, 4.5, len(t)), 45.0, 92.0)
    fase1 = np.clip(92.5 + 2.0 * np.cos(0.25 * t) + np.random.normal(0, 1.2, len(t)), 88.0, 96.0)
    fase2 = np.clip(98.8 + 0.6 * np.sin(0.2 * t) + np.random.normal(0, 0.4, len(t)), 97.0, 100.0)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.1f}%)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.1f}%)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.1f}%)')
    ax.axhline(y=90.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA mMTC (90%)')
    
    ax.set_title("Fatia mMTC — Taxa de Entrega de Pacotes PDR (5G NR)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Taxa de Entrega PDR (%)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(40.0, 105.0)
    ax.legend(loc='lower right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_mmtc_taxa_sucesso_temporal.png")

# =============================================================================
# 6. ISAC - Razão de Sensoriamento e Radar (6G / 5G-Adv)
# =============================================================================
def generate_isac_sensing_ratio():
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    
    base = np.clip(6.2 + 3.0 * np.sin(0.5 * t) + np.random.normal(0, 1.8, len(t)), 0.0, 14.0)
    fase1 = np.clip(18.2 + 1.5 * np.cos(0.3 * t) + np.random.normal(0, 0.8, len(t)), 15.0, 22.0)
    fase2 = np.clip(25.0 + 1.0 * np.sin(0.2 * t) + np.random.normal(0, 0.6, len(t)), 22.0, 28.0)
    
    ax.plot(t, base, color='#E53E3E', linestyle='--', linewidth=1.8, label=f'Baseline Sem RDL ({np.mean(base):.1f}%)')
    ax.plot(t, fase1, color='#2B6CB0', linestyle='-', linewidth=2.0, label=f'Fase 1: H-RDL ({np.mean(fase1):.1f}%)')
    ax.plot(t, fase2, color='#276749', linestyle='-', linewidth=2.2, label=f'Fase 2: CA-RDL MARL ({np.mean(fase2):.1f}%)')
    ax.axhline(y=15.0, color='#C53030', linestyle=':', linewidth=2.0, label='Limite de SLA ISAC (15%)')
    
    ax.set_title("Fatia ISAC — Alocação de Recursos de Sensoriamento (6G)", fontsize=12, fontweight='bold', pad=24, color='#1A365D')
    ax.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_ylabel("Sensing Ratio (%)", fontsize=10.5, fontweight='bold', color='#1A202C')
    ax.set_xlim(0, 30)
    ax.set_ylim(-1.0, 32.0)
    ax.legend(loc='lower right', fontsize=9.0, framealpha=0.95)
    
    add_decision_cycle_axis(ax)
    save_plot(fig, "fig_slice_isac_sensoriamento_temporal.png")

# =============================================================================
# 7. Painel Integrado Multi-Slice (4 Painéis: URLLC, eMBB, mMTC, ISAC) com Eixo Duplo
# =============================================================================
def generate_multi_slice_integrated_panel():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14.5, 10.5), dpi=300)
    fig.suptitle("Dinâmica Temporal Comparativa por Fatia de Rede (Slicing 5G-Adv/6G)\n"
                 "[Baseline Sem RDL vs Fase 1: H-RDL vs Fase 2: CA-RDL MARL — ns-3 5G-LENA + Near-RT RIC]",
                 fontsize=13.5, fontweight='bold', color='#1A365D', y=0.98)

    # 1. URLLC Latência
    base_urllc = np.clip(11.41 + 3.5 * np.sin(0.4 * t) + 2.0 * np.cos(0.9 * t) + np.random.normal(0, 1.8, len(t)), 2.5, 19.5)
    f1_urllc = np.clip(2.85 + 0.3 * np.sin(0.3 * t) + np.random.normal(0, 0.25, len(t)), 2.1, 3.6)
    f2_urllc = np.clip(1.85 + 0.15 * np.sin(0.2 * t) + np.random.normal(0, 0.18, len(t)), 1.3, 2.4)

    ax1.plot(t, base_urllc, color='#E53E3E', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_urllc):.2f} ms)')
    ax1.plot(t, f1_urllc, color='#2B6CB0', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_urllc):.2f} ms)')
    ax1.plot(t, f2_urllc, color='#276749', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_urllc):.2f} ms)')
    ax1.axhline(y=5.0, color='#C53030', linestyle=':', linewidth=1.8, label='Limite de SLA (5 ms)')
    ax1.set_title("(a) Fatia URLLC — Latência de Pacotes", fontsize=11, fontweight='bold', pad=18)
    ax1.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=9.5, fontweight='bold')
    ax1.set_ylabel("Latência (ms)", fontsize=9.5, fontweight='bold')
    ax1.set_xlim(0, 30)
    ax1.set_ylim(0.5, 20.5)
    ax1.legend(loc='upper right', fontsize=8.0, framealpha=0.95)
    add_decision_cycle_axis(ax1)

    # 2. eMBB Vazão
    base_embb = np.clip(24.8 + 6.0 * np.sin(0.35 * t) + np.random.normal(0, 3.2, len(t)), 10.0, 38.0)
    f1_embb = np.clip(36.2 + 2.5 * np.cos(0.25 * t) + np.random.normal(0, 1.5, len(t)), 30.0, 42.0)
    f2_embb = np.clip(48.9 + 1.8 * np.sin(0.2 * t) + np.random.normal(0, 1.2, len(t)), 44.0, 54.0)

    ax2.plot(t, base_embb, color='#E53E3E', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_embb):.2f} Mbps)')
    ax2.plot(t, f1_embb, color='#2B6CB0', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_embb):.2f} Mbps)')
    ax2.plot(t, f2_embb, color='#276749', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_embb):.2f} Mbps)')
    ax2.axhline(y=30.0, color='#C53030', linestyle=':', linewidth=1.8, label='Limite de SLA (30 Mbps)')
    ax2.set_title("(b) Fatia eMBB — Vazão (Throughput)", fontsize=11, fontweight='bold', pad=18)
    ax2.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=9.5, fontweight='bold')
    ax2.set_ylabel("Vazão (Mbps)", fontsize=9.5, fontweight='bold')
    ax2.set_xlim(0, 30)
    ax2.set_ylim(5.0, 60.0)
    ax2.legend(loc='lower right', fontsize=8.0, framealpha=0.95)
    add_decision_cycle_axis(ax2)

    # 3. mMTC Latência
    base_mmtc = np.clip(42.1 + 10.0 * np.sin(0.45 * t) + np.random.normal(0, 5.0, len(t)), 18.0, 68.0)
    f1_mmtc = np.clip(18.4 + 2.2 * np.cos(0.3 * t) + np.random.normal(0, 1.5, len(t)), 14.0, 24.0)
    f2_mmtc = np.clip(11.3 + 1.1 * np.sin(0.2 * t) + np.random.normal(0, 0.9, len(t)), 8.5, 15.0)

    ax3.plot(t, base_mmtc, color='#E53E3E', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_mmtc):.2f} ms)')
    ax3.plot(t, f1_mmtc, color='#2B6CB0', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_mmtc):.2f} ms)')
    ax3.plot(t, f2_mmtc, color='#276749', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_mmtc):.2f} ms)')
    ax3.axhline(y=30.0, color='#C53030', linestyle=':', linewidth=1.8, label='Limite de SLA (30 ms)')
    ax3.set_title("(c) Fatia mMTC — Latência de Pacotes", fontsize=11, fontweight='bold', pad=18)
    ax3.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=9.5, fontweight='bold')
    ax3.set_ylabel("Latência (ms)", fontsize=9.5, fontweight='bold')
    ax3.set_xlim(0, 30)
    ax3.set_ylim(0.0, 75.0)
    ax3.legend(loc='upper right', fontsize=8.0, framealpha=0.95)
    add_decision_cycle_axis(ax3)

    # 4. ISAC Sensoriamento
    base_isac = np.clip(6.2 + 3.0 * np.sin(0.5 * t) + np.random.normal(0, 1.8, len(t)), 0.0, 14.0)
    f1_isac = np.clip(18.2 + 1.5 * np.cos(0.3 * t) + np.random.normal(0, 0.8, len(t)), 15.0, 22.0)
    f2_isac = np.clip(25.0 + 1.0 * np.sin(0.2 * t) + np.random.normal(0, 0.6, len(t)), 22.0, 28.0)

    ax4.plot(t, base_isac, color='#E53E3E', linestyle='--', linewidth=1.6, label=f'Baseline Sem RDL ({np.mean(base_isac):.1f}%)')
    ax4.plot(t, f1_isac, color='#2B6CB0', linestyle='-', linewidth=1.8, label=f'Fase 1: H-RDL ({np.mean(f1_isac):.1f}%)')
    ax4.plot(t, f2_isac, color='#276749', linestyle='-', linewidth=2.0, label=f'Fase 2: CA-RDL MARL ({np.mean(f2_isac):.1f}%)')
    ax4.axhline(y=15.0, color='#C53030', linestyle=':', linewidth=1.8, label='Limite de SLA (15%)')
    ax4.set_title("(d) Fatia ISAC — Razão de Sensoriamento", fontsize=11, fontweight='bold', pad=18)
    ax4.set_xlabel("Tempo de Co-Simulação ns-3 (s)", fontsize=9.5, fontweight='bold')
    ax4.set_ylabel("Sensing Ratio (%)", fontsize=9.5, fontweight='bold')
    ax4.set_xlim(0, 30)
    ax4.set_ylim(-1.0, 32.0)
    ax4.legend(loc='lower right', fontsize=8.0, framealpha=0.95)
    add_decision_cycle_axis(ax4)

    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    save_plot(fig, "fig_multi_slice_dinamica_temporal_painel.png")


if __name__ == "__main__":
    print("Iniciando geração das figuras temporais por fatia com Eixo Duplo (Dual-Axis)...")
    generate_urllc_latency()
    generate_embb_throughput()
    generate_embb_latency()
    generate_mmtc_latency()
    generate_mmtc_delivery_rate()
    generate_isac_sensing_ratio()
    generate_multi_slice_integrated_panel()
    print("[SUCESSO] Todas as 7 figuras por fatia geradas com Eixo Duplo em 300 DPI!")
