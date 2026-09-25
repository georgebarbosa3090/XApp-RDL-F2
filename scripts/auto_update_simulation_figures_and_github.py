#!/usr/bin/env python3
"""
Pipeline Automático de Atualização de Figuras, Tabelas e Sincronização GitHub
Executado automaticamente ao final de cada rodada de simulação ns-3/NORI.
Autor: George Alexandro F. Barbosa / PPGC-UFPA
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent


def run_step(step_name, command, cwd=root_dir):
    print(f"\n--- {step_name} ---")
    try:
        res = subprocess.run(command, cwd=cwd, shell=True, check=False)
        if res.returncode == 0:
            print(f"[OK] {step_name} concluído com sucesso.")
        else:
            print(f"[AVISO] {step_name} retornou código {res.returncode}.")
    except Exception as e:
        print(f"[ERRO] Falha ao executar {step_name}: {e}")


def main():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 80)
    print(f" [AUTO-PIPELINE] Atualização Automática de Figuras, Tabelas e GitHub")
    print(f" Diretório: {root_dir}")
    print(f" Horário: {timestamp}")
    print("=" * 80)

    # 1. FlowMonitor Markdown Report
    report_script = root_dir / "scripts" / "generate_ns3_flowmonitor_markdown_report.py"
    if report_script.exists():
        run_step("1. Processar Traces FlowMonitor XML", f"{sys.executable} {report_script}")

    # 2. Exportar 16 Tabelas CSV de Síntese
    tables_script = root_dir / "analysis" / "export_tables.py"
    if tables_script.exists():
        run_step("2. Exportar 16 Tabelas CSV de Síntese", f"{sys.executable} {tables_script}")

    # 3. Reconciliar Matriz Canônica SSOT & Auditoria de Docs
    reconcile_script = root_dir / "scripts" / "reconcile_all_tables_and_docs.py"
    if reconcile_script.exists():
        run_step("3. Reconciliar Matriz Canônica SSOT & Auditoria de Docs", f"{sys.executable} {reconcile_script}")

    # 4. Gerar 25 Figuras Científicas Clássicas (300 DPI)
    plots_script = root_dir / "analysis" / "generate_plots.py"
    if plots_script.exists():
        run_step("4. Regenerar 25 Figuras Científicas (300 DPI)", f"{sys.executable} {plots_script}")

    # 5. Gerar Figuras Modulares Cross-Layer e Dashboard Mestre (Fig 19a-19e)
    crosslayer_script = root_dir / "analysis" / "generate_crosslayer_modular_plots.py"
    if crosslayer_script.exists():
        run_step("5. Gerar Dashboard Cross-Layer e Gráficos Fig 19a-19e", f"{sys.executable} {crosslayer_script}")

    # 6. Gerar Novos Gráficos da Demonstração Rica e Últimas Simulações (Fig 31-37)
    demo_plots_script = root_dir / "analysis" / "generate_demonstration_and_latest_sim_plots.py"
    if demo_plots_script.exists():
        run_step("6. Gerar Gráficos da Demonstração Rica & Simulações (Fig 31-37)", f"{sys.executable} {demo_plots_script}")

    # 7. Gerar Figuras Estendidas de Modelagem (Fig 26-30)
    extended_script = root_dir / "scripts" / "generate_extended_figures_and_tables.py"
    if extended_script.exists():
        run_step("7. Gerar Figuras Estendidas de Modelagem (Fig 26-30)", f"{sys.executable} {extended_script}")

    # 8. Gerar Figuras de Publicação
    pub_script = root_dir / "scripts" / "generate_publication_report_figures.py"
    if pub_script.exists():
        run_step("8. Gerar Figuras Científicas para Relatórios e Artigos", f"{sys.executable} {pub_script}")

    # 9. Sincronização Cruzada F1 <-> F2, GitHub e Google Drive
    cross_sync_script = root_dir / "scripts" / "sync_cross_repos.py"
    if cross_sync_script.exists():
        run_step("9. Sincronização Cruzada F1 <-> F2, GitHub e Google Drive", f"{sys.executable} {cross_sync_script}")
    else:
        # Fallback se sync_cross_repos não existir
        if (root_dir / ".git").exists():
            print("\n--- 9. Sincronização com o GitHub ---")
            subprocess.run("git add -A", cwd=root_dir, shell=True)
            commit_msg = f"results(sim): auto-update all figures, CSV tables and reports [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}]"
            subprocess.run(f'git commit -m "{commit_msg}"', cwd=root_dir, shell=True)
            subprocess.run("git pull --rebase origin main", cwd=root_dir, shell=True)
            subprocess.run("git push origin HEAD:main", cwd=root_dir, shell=True)

    print("\n" + "=" * 80)
    print(" [OK] Pipeline de simulação H-RDL e sincronização finalizado com sucesso!")
    print("=" * 80)


if __name__ == "__main__":
    main()

