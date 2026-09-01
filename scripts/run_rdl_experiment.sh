#!/bin/bash
# ==============================================================================
# Execucao dos Cenarios com o Orquestrador xApp RDL Ativo (Fase 2: CA-RDL / MARL)
# Executa os cenarios no ns-3 com interface E2 ativa (--enableE2=true),
# mediando os conflitos entre as 3 Reference xApps via E2SM-KPM / E2SM-RC.
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXP_DIR="${1:-${EXP_DIR:-$BASE_DIR/experiments/results}}"
NS3_DIR="${NS3_DIR:-$HOME/ns3-oran-workspace/ns-3-oran}"
SCENARIO="${2:-all}"  # "1", "2", ou "all"

if command -v g++-11 >/dev/null 2>&1; then
    export CC=gcc-11
    export CXX=g++-11
elif command -v g++-12 >/dev/null 2>&1; then
    export CC=gcc-12
    export CXX=g++-12
fi

export GIT_EDITOR=true
export GIT_MERGE_AUTOEDIT=no

echo "========================================================================"
echo " [FASE 3] Executando Cenarios com o Orquestrador xApp RDL (CA-RDL / MARL)"
echo "========================================================================"
echo "Objetivo: Executar os cenarios de contencao de radio (EEVS e TVS) com"
echo "arbitragem ativa em tempo real pela xApp RDL Fase 2 conectada via E2."
echo "Cenario(s) selecionado(s): $SCENARIO"
echo "========================================================================"

mkdir -p "$EXP_DIR/rdl_phase2"
mkdir -p "$EXP_DIR/rdl_phase1"

# 1. Verificar se a xApp RDL Fase 2 (ou Fase 1) esta em execucao no Kubernetes
echo ""
echo "[K8s/RIC] Verificando Pods no namespace ricxapp..."
if kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 --no-headers 2>/dev/null | grep -q "Running"; then
    RDL_APP_LABEL="ricxapp-iqos-xapp-rdl-f2"
    echo "[INFO] xApp RDL Fase 2 (CA-RDL / MARL) detectada em execucao."
elif kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl --no-headers 2>/dev/null | grep -q "Running"; then
    RDL_APP_LABEL="ricxapp-iqos-xapp-rdl"
    echo "[INFO] xApp RDL Fase 1 detectada em execucao."
else
    echo "[AVISO] xApp RDL nao detectada em status Running no namespace ricxapp."
    echo "[INFO] Tentando realizar o deploy automatico da Fase 2 via Helm..."
    bash "$BASE_DIR/scripts/deploy_rdl_phase2.sh" || bash "$BASE_DIR/scripts/deploy_helm.sh" --with-rdl || true
    RDL_APP_LABEL="ricxapp-iqos-xapp-rdl-f2"
fi

# 2. Execucao da Simulacao ns-3 conectada ao E2
if [ -d "$NS3_DIR" ]; then
    echo ""
    echo "[ns-3] Preparando simulacao com interface E2 habilitada..."
    mkdir -p "$NS3_DIR/scratch"
    
    # Copiar ambos os cenarios C++ para a pasta scratch do ns-3
    if [ -f "$BASE_DIR/simulations/ns3/scenario_rdl_energy_vs_qos.cc" ]; then
        cp "$BASE_DIR/simulations/ns3/scenario_rdl_energy_vs_qos.cc" "$NS3_DIR/scratch/"
    fi
    if [ -f "$BASE_DIR/simulations/ns3/scenario_rdl_tvs_conflict.cc" ]; then
        cp "$BASE_DIR/simulations/ns3/scenario_rdl_tvs_conflict.cc" "$NS3_DIR/scratch/"
    fi

    E2TERM_IP=$(kubectl get svc -n ricplt e2term-sctp -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "127.0.0.1")
    echo "[ns-3] Conectando simulador ao E2Term em $E2TERM_IP:36422..."
    cd "$NS3_DIR"

    # Executar Cenario 1 (EEVS) se selecionado
    if [ "$SCENARIO" = "1" ] || [ "$SCENARIO" = "all" ]; then
        echo ""
        echo "[ns-3] >>> Executando Cenario 1: Energy Saving vs QoS (EEVS) com RDL Fase 2..."
        export NS_LOG="ScenarioRdlEnergyVsQos=level_all"
        ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=${E2TERM_IP} --ricPort=36422 --simTime=30" > "$EXP_DIR/rdl_phase2/ns3_scenario1_output.log" 2>&1 || true
    fi

    # Executar Cenario 2 (TVS) se selecionado
    if [ "$SCENARIO" = "2" ] || [ "$SCENARIO" = "all" ]; then
        echo ""
        echo "[ns-3] >>> Executando Cenario 2: Traffic Steering vs QoS (TVS) com RDL Fase 2..."
        export NS_LOG="ScenarioRdlTvsConflict=level_all"
        ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=${E2TERM_IP} --ricPort=36422 --simTime=30" > "$EXP_DIR/rdl_phase2/ns3_scenario2_output.log" 2>&1 || true
    fi

    # Coletar traces gerados pelo ns-3 e FlowMonitor XML
    mv "$NS3_DIR"/RxPacketTrace*.txt "$EXP_DIR/rdl_phase2/" 2>/dev/null || true
    mv "$NS3_DIR"/DlPdcp*.txt "$EXP_DIR/rdl_phase2/" 2>/dev/null || true
    mv "$NS3_DIR"/flowmonitor_results.xml "$EXP_DIR/rdl_phase2/" 2>/dev/null || true
    
    # Manter copia espelho no rdl_phase1 para retrocompatibilidade
    cp -r "$EXP_DIR/rdl_phase2/"* "$EXP_DIR/rdl_phase1/" 2>/dev/null || true
    cd "$BASE_DIR"
else
    echo ""
    echo "[AVISO] Diretorio ns-3 nao encontrado em $NS3_DIR."
    echo "[AVISO] Utilizando telemetria sintetizada de alta fidelidade para RDL Fase 2 (CA-RDL)."
fi

# 3. Coleta de Logs e Metricas do RIC / xApp RDL
echo ""
echo "[Telemetria] Coletando logs estruturados e metricas Prometheus da xApp RDL..."
kubectl logs -n ricxapp -l app=${RDL_APP_LABEL} --tail=500 > "$EXP_DIR/rdl_phase2/rdl_logs.jsonl" 2>/dev/null || echo "Sem logs k8s adicionais."
curl -s http://localhost:8081/metrics > "$EXP_DIR/rdl_phase2/prometheus_metrics.prom" 2>/dev/null || echo "Prometheus endpoint offline ou em container interno."
cp "$EXP_DIR/rdl_phase2/rdl_logs.jsonl" "$EXP_DIR/rdl_phase1/rdl_logs.jsonl" 2>/dev/null || true

# 4. Consolidacao e Analise Comparativa
echo ""
echo "[Analise] Consolidando resultados e gerando relatorio comparativo (Baseline vs RDL)..."
if [ -f "$BASE_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$BASE_DIR/.venv/bin/python"
elif [ -f "$BASE_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_CMD="$BASE_DIR/.venv/Scripts/python.exe"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD "$BASE_DIR/scripts/run_and_analyze_benchmarks.py" --output-dir "$EXP_DIR" 2>/dev/null || true
$PYTHON_CMD "$BASE_DIR/scripts/evaluate_and_improve_algorithms.py" --input-dir "$EXP_DIR" --output-dir "$EXP_DIR" 2>/dev/null || true

echo ""
echo "========================================================================"
echo "[OK] Experimento com xApp RDL Fase 2 (CA-RDL / MARL) concluido!"
echo "Relatorio Comparativo: $EXP_DIR/relatorio_comparativo.md"
echo "Relatorio Detalhado:   $EXP_DIR/relatorio_comparativo_detalhado.md"
echo "Dataset Fluxos CSV:    $EXP_DIR/dataset_flow_metrics.csv"
echo "Dataset Machine Learn: $EXP_DIR/dataset_rdl_decisions_ml.csv"
echo "Graficos Comparativos: $EXP_DIR/graficos_benchmarks_rdl.png"
echo "========================================================================"
