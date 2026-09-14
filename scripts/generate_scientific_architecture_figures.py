"""
Scientific Architecture & Figure Generator (5G/5GA/6G, NTN, SAGIN, O-RAN, RIS)
Gera figuras vetoriais de altíssima qualidade (300 DPI) para publicações científicas e relatórios técnicos.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np

def generate_sagin_architecture_diagram(output_path="docs/figures/diagram_sagin_6g_ntn_architecture.png"):
    """Gera diagrama 3D estratificado de Space-Air-Ground Integrated Networks (SAGIN) com RIS."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(14, 9), dpi=300)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # 1. Planos de Fundo das Camadas Espaciais
    ax.axhspan(68, 100, color="#0b132b", alpha=0.95) # Spaceborne Layer (Escuro / Cosmos)
    ax.axhspan(36, 68, color="#1c2541", alpha=0.90)  # Air / Stratospheric Layer (Azul petróleo)
    ax.axhspan(0, 36, color="#0b192c", alpha=0.98)   # Terrestrial Ground Layer (Profundo)

    # Linhas de Demarcação de Estrato (Tracejadas)
    ax.axhline(68, color="#48cae4", linestyle="--", linewidth=1.5, alpha=0.7)
    ax.axhline(36, color="#00b4d8", linestyle="--", linewidth=1.5, alpha=0.7)

    # 2. Rótulos Laterais de Camada
    ax.text(3, 93, "SPACEBORNE NETWORKS\n• GEO: 35,786 km\n• MEO: 7,000 - 25,000 km\n• LEO: 300 - 1,500 km", 
            color="#90e0ef", fontsize=9, weight="bold", linespacing=1.4)
    ax.text(3, 58, "UAS / HAPS NETWORKS\n• HAPS: 18 - 27 km (20 km)\n• Aerial / UAVs: 9 - 11.5 km\n• Tactical Drones: < 1 km", 
            color="#00b4d8", fontsize=9, weight="bold", linespacing=1.4)
    ax.text(3, 24, "TERRESTRIAL NETWORKS\n• Urban / Rural / Remote\n• 5G/6G gNodeBs & 5G Core\n• Reconfigurable Surfaces (RIS)", 
            color="#caf0f8", fontsize=9, weight="bold", linespacing=1.4)

    # 3. Desenho de Satélites (GEO e LEO)
    # Satélite GEO
    geo_x, geo_y = 115, 88
    ax.scatter([geo_x], [geo_y], color="#f8f9fa", s=320, marker="s", edgecolors="#ffd166", linewidth=2.5, zorder=6)
    ax.text(geo_x, geo_y + 4.5, "GEO Satellite\n(35,786 km)", color="#ffd166", fontsize=8, weight="bold", ha="center")

    # Constelação LEO (2 nós)
    leo1_x, leo1_y = 45, 78
    leo2_x, leo2_y = 85, 80
    ax.scatter([leo1_x, leo2_x], [leo1_y, leo2_y], color="#e0fbfc", s=220, marker="s", edgecolors="#00b4d8", linewidth=2, zorder=6)
    ax.text(leo1_x, leo1_y + 4.0, "LEO-1 (500 km)\n[RIS Payload]", color="#00b4d8", fontsize=8, weight="bold", ha="center")
    ax.text(leo2_x, leo2_y + 4.0, "LEO-2 (600 km)\n[ISAC Radar]", color="#00b4d8", fontsize=8, weight="bold", ha="center")

    # Inter-Satellite Link (ISL)
    ax.annotate("", xy=(leo2_x - 3, leo2_y), xytext=(leo1_x + 3, leo1_y),
                arrowprops=dict(arrowstyle="<->", color="#ffd166", lw=2.2, linestyle="-", shrinkA=0, shrinkB=0))
    ax.text((leo1_x + leo2_x)/2, leo1_y + 2.5, "Inter-Satellite Link (ISL FSO)", color="#ffd166", fontsize=8, weight="bold", ha="center")

    # 4. Desenho de HAPS e UAVs
    haps_x, haps_y = 65, 52
    ax.scatter([haps_x], [haps_y], color="#90e0ef", s=380, marker="o", edgecolors="#0077b6", linewidth=2.5, zorder=6)
    ax.text(haps_x, haps_y + 4.5, "HAPS / Airship (20 km)\n[Multi-Beam Slicing]", color="#90e0ef", fontsize=8, weight="bold", ha="center")

    uav_x, uav_y = 100, 44
    ax.scatter([uav_x], [uav_y], color="#48cae4", s=180, marker="^", edgecolors="#03045e", linewidth=2, zorder=6)
    ax.text(uav_x, uav_y + 4.0, "UAV Relay\n(10 km)", color="#48cae4", fontsize=8, weight="bold", ha="center")

    # 5. Camada Terrestre: Gateway, 5GC, Setores
    gw_x, gw_y = 25, 12
    ax.scatter([gw_x], [gw_y], color="#f97316", s=280, marker="p", edgecolors="#ea580c", linewidth=2.5, zorder=6)
    ax.text(gw_x, gw_y - 5.5, "NTN Gateway & 5G Core\n(O-Cloud / Near-RT RIC)", color="#f97316", fontsize=8, weight="bold", ha="center")

    # Setor Urbano
    urb_x, urb_y = 65, 12
    ax.scatter([urb_x], [urb_y], color="#38bdf8", s=260, marker="h", edgecolors="#0284c7", linewidth=2, zorder=6)
    ax.text(urb_x, urb_y - 5.5, "Urban Macro gNB\n(Connected V2X / UEs)", color="#38bdf8", fontsize=8, weight="bold", ha="center")

    # RIS Predial
    ris_x, ris_y = 80, 20
    ax.scatter([ris_x], [ris_y], color="#f43f5e", s=200, marker="D", edgecolors="#be123c", linewidth=2.2, zorder=6)
    ax.text(ris_x, ris_y + 3.5, "Building RIS Panel\n(Blockage Bypass)", color="#f43f5e", fontsize=8, weight="bold", ha="center")

    # Setor Rural / Remoto
    rur_x, rur_y = 115, 12
    ax.scatter([rur_x], [rur_y], color="#4ade80", s=240, marker="h", edgecolors="#16a34a", linewidth=2, zorder=6)
    ax.text(rur_x, rur_y - 5.5, "Rural & Remote Node\n(Agriculture IoT / Vessel)", color="#4ade80", fontsize=8, weight="bold", ha="center")

    # 6. Feixes de Comunicação e Conexões
    # Feeder Link: Gateway -> GEO & LEO
    ax.annotate("", xy=(leo1_x, leo1_y - 2), xytext=(gw_x, gw_y + 2),
                arrowprops=dict(arrowstyle="<->", color="#f97316", lw=2.2, linestyle="-"))
    ax.text(31, 46, "Feeder Link (Ka/Q/V)", color="#f97316", fontsize=8, weight="bold", rotation=58)

    # Service Links: LEO -> Urbano & Rural
    ax.annotate("", xy=(urb_x - 3, urb_y + 3), xytext=(leo1_x, leo1_y - 2),
                arrowprops=dict(arrowstyle="->", color="#22c55e", lw=2.0, linestyle="-"))
    ax.text(58, 40, "Service Link (Ku/S)", color="#22c55e", fontsize=8, weight="bold", rotation=-68)

    # Feixe HAPS -> UEs
    ax.annotate("", xy=(urb_x, urb_y + 3), xytext=(haps_x, haps_y - 2),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.8, linestyle="--"))
    ax.annotate("", xy=(rur_x, rur_y + 3), xytext=(haps_x, haps_y - 2),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.8, linestyle="--"))

    # Feixe Bloqueado e Bypass via RIS
    ax.annotate("", xy=(ris_x, ris_y), xytext=(urb_x, urb_y),
                arrowprops=dict(arrowstyle="->", color="#fb7185", lw=2.0, linestyle=":"))
    ax.annotate("", xy=(95, 10), xytext=(ris_x, ris_y),
                arrowprops=dict(arrowstyle="->", color="#f43f5e", lw=2.2, linestyle="-"))
    ax.text(88, 14, "Reflected Beam", color="#f43f5e", fontsize=7.5, weight="bold", rotation=-24)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[✓] Figura científica SAGIN gerada com sucesso em: {output_path}")

if __name__ == "__main__":
    generate_sagin_architecture_diagram()
