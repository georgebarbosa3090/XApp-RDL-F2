#!/usr/bin/env bash
# =============================================================================
# O-RAN TELEMETRY STACK LAUNCHER (InfluxDB v2 + Grafana 10 + Realtime Bridge)
# =============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/deployments/telemetry/docker-compose.telemetry.yml"

echo "================================================================================"
echo " [TELEMETRY STACK] Inicializando InfluxDB v2 + Grafana 10 + H-RDL Bridge"
echo " Diretorio: $PROJECT_DIR"
echo "================================================================================"

# Check Docker
if ! command -v docker &>/dev/null; then
    echo "[!] Docker nao encontrado. Por favor, instale o Docker no WSL."
    exit 1
fi

# Detect compose command
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "[!] Docker Compose nao encontrado."
    exit 1
fi

echo "[+] Subindo containers InfluxDB e Grafana..."
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d

echo "[+] Aguardando inicializacao dos servicos (5s)..."
sleep 5

# Detect python
PYTHON_CMD=""
for candidate in \
    "/home/george/.venv-rdl/bin/python" \
    "$PROJECT_DIR/.venv/bin/python" \
    "$PROJECT_DIR/../.venv/bin/python" \
    "$(command -v python3 2>/dev/null)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        PYTHON_CMD="$candidate"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

echo "================================================================================"
echo " [✓] TELEMETRY STACK PRONTA E OPERACIONAL!"
echo "================================================================================"
echo ""
echo " 📊 GRAFANA DASHBOARD (Pre-Configurado):"
echo "    URL: http://localhost:3000/d/oran-rdl-closed-loop"
echo "    Login: admin / admin (ou acesso anonimo automatico)"
echo ""
echo " 🗄️ INFLUXDB DATA EXPLORER & FLUX QUERY:"
echo "    URL: http://localhost:8086"
echo "    Org: oran-alliance | Bucket: oran_telemetry"
echo ""
echo " 🌐 H-RDL DASHBOARD CIENTIFICO LIVE:"
echo "    URL: http://localhost:8082"
echo ""
echo "================================================================================"
echo "[+] Iniciando Streaming de Telemetria E2SM-KPM / Safe-MAPPO para InfluxDB..."
echo "================================================================================"

"$PYTHON_CMD" "$PROJECT_DIR/deployments/telemetry/telemetry_influx_bridge.py"
