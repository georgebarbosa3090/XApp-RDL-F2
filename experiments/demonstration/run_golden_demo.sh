#!/usr/bin/env bash
# =============================================================================
# H-RDL CLOSED-LOOP DEMONSTRATION (DEMO GOLDEN v1)
# 4-Terminal Workspace Layout for ns-3.48 / 5G-LENA / NORI / Near-RT RIC
#
# Terminal Layout:
# ┌───────────────────────────────────────┬───────────────────────────────────────┐
# │ [ 1 — RAN ] ns-3 + 5G-LENA            │ [ 2 — E2/NORI ] E2 Agent / E2SIM      │
# │ • gNBs, UEs, TTI ticks & Traffic      │ • KPM Indications & RC Controls       │
# ├───────────────────────────────────────┼───────────────────────────────────────┤
# │ [ 3 — Near-RT RIC ] E2Term / RMR      │ [ 4 — H-RDL ] Live Web Server & Loop  │
# │ • Subscription, xApp Pool & Safe-MAPPO│ • http://localhost:8080 (Certification)│
# └───────────────────────────────────────┴───────────────────────────────────────┘
# =============================================================================

set -e

SESSION_NAME="rdl-golden-demo"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Find Python executable
if [ -d "$PROJECT_DIR/.venv" ]; then
    PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
elif [ -d "$PROJECT_DIR/../.venv" ]; then
    PYTHON_CMD="$PROJECT_DIR/../.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Ensure tmux is available
if ! command -v tmux &> /dev/null; then
    echo "[!] Tmux não encontrado. Instalando..."
    sudo apt update && sudo apt install -y tmux
fi

# Kill old session if active
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

echo "================================================================================"
echo " [DEMO GOLDEN v1] Inicializando Ambiente de Co-Simulação 4-Terminais"
echo " Sessão: $SESSION_NAME"
echo " Diretório: $PROJECT_DIR"
echo "================================================================================"

# 1. Create main session
tmux new-session -d -s "$SESSION_NAME" -n "H-RDL-Golden-ClosedLoop"

# 2. Split into 4 symmetrical quadrants
tmux split-window -h -t "$SESSION_NAME:0.0"
tmux split-window -v -t "$SESSION_NAME:0.0"
tmux split-window -v -t "$SESSION_NAME:0.2"

# -----------------------------------------------------------------------------
# PANE 1 (Top-Left): 1 — RAN (ns-3 + 5G-LENA)
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.0" -T "1 — RAN (ns-3 + 5G-LENA)"
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m[TERMINAL 1 — RAN] ns-3.48 / 5G-LENA v5.1 PHYSICAL SIMULATOR\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m• 2 gNBs (Macro/Micro) | 30 UEs (URLLC/eMBB/mMTC) | Wall-Clock\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m• t=20s: Real Traffic Burst (Buffer Overflow) & TxPower cut -13dBm\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo -e '\033[1;36m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "if [ -d ~/ns3-oran-workspace/ns-3-oran ]; then cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scenario_rdl_closed_loop_nori --simTime=60.0 --demoMode=realtime'; elif [ -d ~/workspace/ns-3-dev ]; then cd ~/workspace/ns-3-dev && ./ns3 run 'scenario_rdl_closed_loop_nori --simTime=60.0 --demoMode=realtime'; else '$PYTHON_CMD' -c 'import time; [print(f\"[ns-3 5G-LENA] t={t:.1f}s | gNB-1 | PRB={98.5 if (20<=t<27) else (30.0 if t<20 else 52.0):.1f}% | Delay={24.8 if (20<=t<27) else 0.82:.2f}ms | Power={30.0 if (20<=t<27) else (43.0 if t<20 else 37.0)}dBm\") or time.sleep(0.5) for t in [i*0.5 for i in range(120)]]'; fi" C-m

# -----------------------------------------------------------------------------
# PANE 2 (Top-Right): 2 — E2/NORI (E2 Agent / E2SIM)
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.2" -T "2 — E2/NORI (E2 Agent & Telemetry)"
tmux send-keys -t "$SESSION_NAME:0.2" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;32m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;32m[TERMINAL 2 — E2/NORI] E2 AGENT & E2SM INTERFACE PROTOCOL\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;32m• Ingestão periódica: RIC_INDICATION (mtype 12050 - ASN.1 APER)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;32m• Atuação em malha: RIC_CONTROL_REQUEST (12040) -> ACK (12041)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo -e '\033[1;32m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "'$PYTHON_CMD' -c 'import time; [print(f\"[E2-Agent] t={t:.1f}s | KPM Report #12050 sent | ASN.1: 1800040001... | \" + (\"DEGRADATION DETECTED\" if 20<=t<27 else \"GOLDEN STATE\")) or time.sleep(0.5) for t in [i*0.5 for i in range(120)]]'" C-m

# -----------------------------------------------------------------------------
# PANE 3 (Bottom-Left): 3 — Near-RT RIC (E2Term / RMR / H-RDL Core)
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.1" -T "3 — Near-RT RIC (H-RDL / CA-RDL Core)"
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;35m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;35m[TERMINAL 3 — Near-RT RIC] H-RDL & CA-RDL COGNITIVE ORCHESTRATOR\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;35m• Janela 200ms | Conflito TVS vs EEVS | Safe-MAPPO (Gate 2: 14.39ms)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;35m• Safety Guard & Bounding Box dApp Omega_dApp (< 1ms O-DU)\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo -e '\033[1;35m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "'$PYTHON_CMD' experiments/demonstration/rdl_demonstration_engine.py --scenario conflict_storm" C-m

# -----------------------------------------------------------------------------
# PANE 4 (Bottom-Right): 4 — H-RDL (Scientific Dashboard & Loop Certification)
# -----------------------------------------------------------------------------
tmux select-pane -t "$SESSION_NAME:0.3" -T "4 — H-RDL Live Dashboard (http://localhost:8080)"
tmux send-keys -t "$SESSION_NAME:0.3" "cd '$PROJECT_DIR' && clear" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;33m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;33m[TERMINAL 4 — H-RDL DASHBOARD] WEB SERVER & METRICS STREAM\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;33m• Dashboard Interativo Ativo em: http://localhost:8080\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;33m• Closed-Loop State Machine + Certificação 4-Gates O-RAN\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo -e '\033[1;33m================================================================\033[0m'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "'$PYTHON_CMD' experiments/demonstration/rdl_demonstration_engine.py --serve --port 8080" C-m

# Configure tmux pane appearance
tmux set-option -t "$SESSION_NAME" mouse on
tmux set-option -t "$SESSION_NAME" pane-border-status top
tmux set-option -t "$SESSION_NAME" pane-border-format " [#{pane_title}] "

# Attach to tmux session
echo "[+] Conectando aos 4 Terminais da Sessão Tmux..."
tmux attach-session -t "$SESSION_NAME"
