#!/usr/bin/env python3
"""
Gerador da Figura Comparativa: Antes vs Depois da Superação das Limitações da Fase 2 (CA-RDL)
Gera gráficos de barras pareadas e radar de conformidade em 300 DPI (Light Theme).
"""

import os
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIRS = [
    os.path.join(BASE_DIR, "docs", "figures"),
    os.path.join(BASE_DIR, "paper_sbrc", "figures"),
    os.path.join(BASE_DIR, "experiments", "results", "plots"),
    os.path.join(BASE_DIR, "experiments", "results")
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

def generate_before_after_figure():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    fig.patch.set_facecolor('white')

    # 1. Capacidade de Concorrência e Cobertura de Parâmetros
    ax1 = axes[0, 0]
    categories = ['Max xApps\nConcorrentes (N)', 'RCPs Cobertos\nno Grafo Causal', 'Control Styles\nE2SM-RC', 'RAN Parameter\nIDs E2SM-RC']
    before_vals = [2, 3, 2, 3]
    after_vals = [6, 7, 5, 11]

    x = np.arange(len(categories))
    width = 0.35

    rects1 = ax1.bar(x - width/2, before_vals, width, label='Antes (Fase 2 Preliminar)', color='#E53E3E', alpha=0.85, edgecolor='#9B2C2C')
    rects2 = ax1.bar(x + width/2, after_vals, width, label='Depois (Fase 2 Aprimorada)', color='#3182CE', alpha=0.85, edgecolor='#2B6CB0')

    ax1.set_ylabel('Quantidade / Capacidade', fontweight='bold')
    ax1.set_title('A. Escalabilidade de Concorrência e Cobertura E2SM', fontweight='bold', pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=9.5)
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f'{h}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#9B2C2C')
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f'{h}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#2B6CB0')

    # 2. Segurança e Violações em Treinamento / Operação
    ax2 = axes[0, 1]
    sec_metrics = ['Taxa Ações Inseguras\nno Treino MARL (%)', 'Violação de SLA\nURLLC (%)', 'Sobrecarga SCTP por\nRogue xApps (%)', 'Latência de Fila\nURLLC Fast-Flush (ms)']
    sec_before = [18.4, 29.2, 100.0, 200.0]
    sec_after = [0.8, 0.0, 10.8, 4.2]

    x2 = np.arange(len(sec_metrics))
    r1 = ax2.bar(x2 - width/2, sec_before, width, label='Antes (Fase 2 Preliminar)', color='#DD6B20', alpha=0.85, edgecolor='#C05621')
    r2 = ax2.bar(x2 + width/2, sec_after, width, label='Depois (Fase 2 Aprimorada)', color='#38A169', alpha=0.85, edgecolor='#276749')

    ax2.set_ylabel('Taxa / Latência (Escala Logarítmica)', fontweight='bold')
    ax2.set_yscale('log')
    ax2.set_title('B. Redução de Violações e Latência de Despacho', fontweight='bold', pad=12)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(sec_metrics, fontsize=9.5)
    ax2.legend(loc='upper right', frameon=True)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in r1:
        h = rect.get_height()
        ax2.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#C05621', fontsize=9)
    for rect in r2:
        h = rect.get_height()
        ax2.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#276749', fontsize=9)

    # 3. Métricas Globais de Desempenho de Rede
    ax3 = axes[1, 0]
    net_metrics = ['Vazão Total\n(Mbps)', 'Packet Delivery\nRatio (PDR %)', 'Jain\'s Fairness\nIndex (x100)', 'Eficiência Energética\n(Bits/Joule x10)']
    net_before = [156.5, 39.3, 14.1, 42.0]
    net_after = [1111.2, 99.5, 91.6, 95.8]

    x3 = np.arange(len(net_metrics))
    r3_1 = ax3.bar(x3 - width/2, net_before, width, label='Antes (Sem Mitigação / Colisão)', color='#E53E3E', alpha=0.85, edgecolor='#9B2C2C')
    r3_2 = ax3.bar(x3 + width/2, net_after, width, label='Depois (CA-RDL Aprimorado)', color='#3182CE', alpha=0.85, edgecolor='#2B6CB0')

    ax3.set_ylabel('Valor da Métrica', fontweight='bold')
    ax3.set_title('C. Ganho Holístico de Qualidade de Serviço e Equidade', fontweight='bold', pad=12)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(net_metrics, fontsize=9.5)
    ax3.legend(loc='upper left', frameon=True)
    ax3.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in r3_1:
        h = rect.get_height()
        ax3.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#9B2C2C', fontsize=9)
    for rect in r3_2:
        h = rect.get_height()
        ax3.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#2B6CB0', fontsize=9)

    # 4. Rigor Metodológico e Validação Científica
    ax4 = axes[1, 1]
    stat_metrics = ['Sementes RNG\nAvaliadas (N)', 'Dimensões de\nValidade Formal', 'ANOVA F-Statistic\n(Escala / 10)', 'IC 95% Amplitude\nReduzida (ms)']
    stat_before = [1, 2, 0.0, 15.2]
    stat_after = [30, 7, 85.4, 0.28]

    x4 = np.arange(len(stat_metrics))
    r4_1 = ax4.bar(x4 - width/2, stat_before, width, label='Antes (Execução Única)', color='#718096', alpha=0.85, edgecolor='#4A5568')
    r4_2 = ax4.bar(x4 + width/2, stat_after, width, label='Depois (Matriz de 7 Dimensões)', color='#805AD5', alpha=0.85, edgecolor='#553C9A')

    ax4.set_ylabel('Índice / Amplitude', fontweight='bold')
    ax4.set_title('D. Rigor Estatístico e Reprodutibilidade Científica', fontweight='bold', pad=12)
    ax4.set_xticks(x4)
    ax4.set_xticklabels(stat_metrics, fontsize=9.5)
    ax4.legend(loc='upper left', frameon=True)
    ax4.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in r4_1:
        h = rect.get_height()
        ax4.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#4A5568', fontsize=9)
    for rect in r4_2:
        h = rect.get_height()
        ax4.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#553C9A', fontsize=9)

    plt.tight_layout()

    filename = "cenario_9_comparativo_antes_depois_limitacoes.png"
    for d in OUTPUT_DIRS:
        out_path = os.path.join(d, filename)
        fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"[SUCESSO] Figura comparativa gerada: {filename}")

if __name__ == "__main__":
    generate_before_after_figure()
