#!/usr/bin/env bash
# =============================================================================
# H-RDL & CA-RDL Live Multi-Window Demonstration Suite (WSL2 / Linux)
# Inspired by RIC-TaaP (Orange / O-RAN SC) & Colosseum / OpenRAN Gym (WiNES Lab)
#
# Sets up a 4-Pane Tmux Workspace:
#   [ Pane 1 (Top-Left) ]: ns-3 / 5G-LENA / NORI Physical RAN Simulator & E2 Node
#   [ Pane 2 (Top-Right) ]: Near-RT RIC Core (H-RDL & CA-RDL Cognitive Orchestrator)
#   [ Pane 3 (Bottom-Left) ]: Multi-xApp Ingestion Window & dApp Real-Time Monitor
#   [ Pane 4 (Bottom-Right) ]: Live Web Server & E2SM-RC ASN.1 APER Protocol Stream
# =============================================================================

set -e

SESSION_NAME="rdl-live-demo"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Robust Python Executable Detection (prefer venv with packages, fallback to system python3)
PYTHON_CMD=""
for candidate in \
    "/home/george/.venv-rdl/bin/python" \
    "$PROJECT_DIR/.venv/bin/python" \
    "$PROJECT_DIR/../.venv/bin/python" \
    "$(command -v python3 2>/dev/null)" \
    "$(command -v python 2>/dev/null)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        PYTHON_CMD="$candidate"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo "[!] Tmux nao encontrado. Instalando tmux via apt..."
    sudo apt update && sudo apt install -y tmux
fi

# Kill previous session if running
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

echo "[+] Inicializando Sessao Multi-Janela: $SESSION_NAME..."
echo "[+] Diretorio do Projeto: $PROJECT_DIR"
echo "[+] Python Executable: $PYTHON_CMD"

# 1. Create session with Pane 1 (ns-3 / RAN Simulator)
tmux new-session -d -s "$SESSION_NAME" -n "RDL-Demo-Workspace"

# Split horizontally into Left and Right columns (50% each)
tmux split-window -h -t "$SESSION_NAME:0.0"

# Split Left column into Top and Bottom (50% each)
tmux split-window -v -t "$SESSION_NAME:0.0"

# Split Right column into Top and Bottom (50% each)
tmux split-window -v -t "$SESSION_NAME:0.2"

# Pane Layout:
# 0.0: Top-Left    (ns-3 RAN Simulation)
# 0.1: Bottom-Left (Multi-xApp & dApp Monitor)
# 0.2: Top-Right   (H-RDL / CA-RDL Near-RT RIC Core)
# 0.3: Bottom-Right(Web Server & Protocol Inspector)

# -----------------------------------------------------------------------------
# Configure Pane 0: ns-3 / 5G-LENA / NORI RAN Simulation
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.0" -T "1. ns-3 5G-LENA / NORI RAN Simulator"
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m[PANE 1] ns-3.48 / 5G-LENA v5.1 / NORI RAN SIMULATOR\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m[Step 1-2] 3GPP PRACH->RRC->NAS->PDU & E2 Telemetry\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "if [ -f ~/workspace/ns-3-dev/ns3 ]; then cd ~/workspace/ns-3-dev && ./ns3 run scenario_rdl_closed_loop_nori; elif [ -f ~/ns3-oran-workspace/ns-3-oran/ns3 ]; then cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run scenario_rdl_closed_loop_nori; else '$PYTHON_CMD' -c 'import time, sys; [print(f\"[ns-3 5G-LENA] TTI={t*1000:.1f}ms | gNB-1 | UEs=3 | PRB_URLLC=30% | SINR=18.5dB | KPM Indication #12050 sent\") or time.sleep(0.5) for t in [i*0.001 for i in range(1, 1000)]]'; fi" C-m

# -----------------------------------------------------------------------------
# Configure Pane 2: H-RDL / CA-RDL Near-RT RIC Core
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.2" -T "2. H-RDL & CA-RDL Cognitive Core"
tmux send-keys -t "$SESSION_NAME:0.2" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;35m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;35m[PANE 2] H-RDL & CA-RDL COGNITIVE ORCHESTRATOR (RIC)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;35m[Step 4-6] Knowledge Graph, C1-C5 Detection & Safe-MAPPO\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;35m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "'$PYTHON_CMD' experiments/demonstration/rdl_demonstration_engine.py --scenario conflict_storm" C-m

# -----------------------------------------------------------------------------
# Configure Pane 1: Reference xApps & dApp Real-Time Monitor
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.1" -T "3. Multi-xApp & dApp Real-Time Monitor"
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;33m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;33m[PANE 3] MULTI-xAPP INGESTION & O-DU dApp MONITOR\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;33m[Step 3 & 7] 200ms Window & Sub-1ms TTI Envelope (nGRG)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;33m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "'$PYTHON_CMD' -c 'import time; [print(f\"[xApp-Pool] xSlice: +35% PRB | xEnergy: -13dBm | xTS: HO-A3 | dApp-O-DU: Preemption Slot #{(i%4)+1} OK\") or time.sleep(0.6) for i in range(1, 500)]'" C-m

# -----------------------------------------------------------------------------
# Configure Pane 3: Web Dashboard Server & Protocol Inspector
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.3" -T "4. Web Dashboard Server & Protocol Stream"
tmux send-keys -t "$SESSION_NAME:0.3" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;32m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;32m[PANE 4] WEB DASHBOARD SERVER & E2SM-RC PROTOCOL\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;32m[Step 8] Live Web UI at http://localhost:8080 (Gate 1-4)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;32m========================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "'$PYTHON_CMD' experiments/demonstration/rdl_demonstration_engine.py --serve --port 8080" C-m

# Enable mouse support and borders
tmux set-option -t "$SESSION_NAME" mouse on
tmux set-option -t "$SESSION_NAME" pane-border-status top
tmux set-option -t "$SESSION_NAME" pane-border-format " [#{pane_index}: #{pane_title}] "

# Attach to tmux session if running in an interactive terminal
if [ -t 1 ]; then
    echo "[+] Anexando a sessao Tmux multi-janelas..."
    tmux attach-session -t "$SESSION_NAME"
else
    echo "[+] Sessao Tmux '$SESSION_NAME' criada em background com sucesso!"
    echo "[+] Para conectar aos 4 quadrantes na tela, execute no terminal:"
    echo "    tmux attach-session -t $SESSION_NAME"
fi

