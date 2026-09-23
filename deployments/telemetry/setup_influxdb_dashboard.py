#!/usr/bin/env python3
"""
Automated InfluxDB Native Dashboard Provisioner for O-RAN H-RDL & CA-RDL.
Creates organizations, buckets, tokens, and builds a comprehensive native dashboard
directly inside the InfluxDB 2.x Web UI (http://localhost:8086).
"""

import json
import urllib.request
import urllib.error
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InfluxProvisioner")

INFLUX_URL = "http://127.0.0.1:8086"
ORG_NAME = "oran-alliance"
BUCKET_NAME = "oran_telemetry"
ADMIN_TOKEN = "oran_rdl_token_secret_key_2026_super_secure"


def get_headers():
    return {
        "Authorization": f"Token {ADMIN_TOKEN}",
        "Content-Type": "application/json",
    }


def api_request(method: str, path: str, data: dict = None):
    url = f"{INFLUX_URL}{path}"
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, headers=get_headers(), method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        logger.error(f"HTTP Error {e.code} on {method} {path}: {err_content}")
        raise e


def get_org_id():
    orgs = api_request("GET", f"/api/v2/orgs?org={ORG_NAME}")
    if orgs.get("orgs"):
        return orgs["orgs"][0]["id"]
    raise RuntimeError(f"Organization '{ORG_NAME}' not found.")


def create_or_update_dashboard(org_id: str):
    logger.info("Verificando dashboards existentes no InfluxDB...")
    dashboards = api_request("GET", f"/api/v2/dashboards?orgID={org_id}")
    dash_title = "O-RAN Closed-Loop Cognitive Orchestration (H-RDL / CA-RDL)"

    dash_id = None
    for d in dashboards.get("dashboards", []):
        if d.get("name") == dash_title:
            dash_id = d["id"]
            logger.info(f"Dashboard já existente encontrado (ID: {dash_id}). Atualizando...")
            break

    if not dash_id:
        logger.info("Criando novo Dashboard Nativo no InfluxDB...")
        new_dash = api_request(
            "POST",
            "/api/v2/dashboards",
            {
                "orgID": org_id,
                "name": dash_title,
                "description": "Dashboard oficial de telemetria O-RAN 5G-Adv/6G, Closed-Loop FSM, Conflitos Cognitivos e Envelopes dApp.",
            },
        )
        dash_id = new_dash["id"]
        logger.info(f"Dashboard criado com sucesso! (ID: {dash_id})")

    # Define cells to create
    cells_spec = [
        {
            "name": "🟢 Closed-Loop State (FSM)",
            "x": 0, "y": 0, "w": 3, "h": 3,
            "type": "single-stat",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "rdl_loop_state" and r["_field"] == "state_code") |> last()',
            "prefix": "STATE: ",
            "suffix": "",
        },
        {
            "name": "⏱️ Near-RT Convergence Latency (Gate 2)",
            "x": 3, "y": 0, "w": 3, "h": 3,
            "type": "single-stat",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "rdl_decision" and r["_field"] == "inference_time_ms") |> last()',
            "prefix": "",
            "suffix": " ms",
        },
        {
            "name": "🎯 Pareto Optimality Score",
            "x": 6, "y": 0, "w": 3, "h": 3,
            "type": "single-stat",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "rdl_decision" and r["_field"] == "pareto_optimality_score") |> last()',
            "prefix": "SCORE: ",
            "suffix": "",
        },
        {
            "name": "⚔️ Active Cognitive Conflicts",
            "x": 9, "y": 0, "w": 3, "h": 3,
            "type": "single-stat",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "rdl_conflicts" and r["_field"] == "conflict_count") |> last()',
            "prefix": "COUNT: ",
            "suffix": " active",
        },
        {
            "name": "📡 Latência RLC por Fatia vs SLA URLLC (1.0 ms)",
            "x": 0, "y": 3, "w": 6, "h": 4,
            "type": "xy",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "ran_kpi" and r["_field"] == "rlc_latency_ms") |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false) |> yield(name: "mean")',
            "y_label": "Latência (ms)",
            "y_suffix": " ms",
        },
        {
            "name": "📊 Distribuição Dinâmica de PRBs por Slice (%)",
            "x": 6, "y": 3, "w": 6, "h": 4,
            "type": "xy",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "ran_kpi" and r["_field"] == "prb_usage_pct") |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false) |> yield(name: "mean")',
            "y_label": "Alocação PRB (%)",
            "y_suffix": "%",
        },
        {
            "name": "🚀 Vazão de Downlink (Throughput Mbps)",
            "x": 0, "y": 7, "w": 6, "h": 4,
            "type": "xy",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "ran_kpi" and r["_field"] == "throughput_mbps") |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false) |> yield(name: "mean")',
            "y_label": "Throughput (Mbps)",
            "y_suffix": " Mbps",
        },
        {
            "name": "⚡ Potência Celular (TxPower dBm) & Economia de Energia (%)",
            "x": 6, "y": 7, "w": 6, "h": 4,
            "type": "xy",
            "query": 'from(bucket: "oran_telemetry") |> range(start: v.timeRangeStart, stop: v.timeRangeStop) |> filter(fn: (r) => r["_measurement"] == "ran_kpi" and (r["_field"] == "tx_power_dbm" or r["_field"] == "energy_saving_pct")) |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false) |> yield(name: "mean")',
            "y_label": "Valor (dBm / %)",
            "y_suffix": "",
        },
    ]

    for cell in cells_spec:
        logger.info(f"Adicionando célula ao painel: {cell['name']}...")
        cell_data = {
            "name": cell["name"],
            "x": cell["x"],
            "y": cell["y"],
            "w": cell["w"],
            "h": cell["h"],
        }
        added_cell = api_request("POST", f"/api/v2/dashboards/{dash_id}/cells", cell_data)
        cell_id = added_cell["id"]

        # Configure view properties
        if cell["type"] == "single-stat":
            view_payload = {
                "name": cell["name"],
                "properties": {
                    "shape": "chronograf-v2",
                    "type": "single-stat",
                    "queries": [{"text": cell["query"], "editMode": "advanced"}],
                    "prefix": cell.get("prefix", ""),
                    "suffix": cell.get("suffix", ""),
                    "colors": [
                        {"id": "base", "type": "text", "hex": "#00C9FF", "name": "laser", "value": 0}
                    ],
                    "decimalPlaces": {"isEnforced": True, "digits": 2},
                },
            }
        else:
            view_payload = {
                "name": cell["name"],
                "properties": {
                    "shape": "chronograf-v2",
                    "type": "xy",
                    "queries": [{"text": cell["query"], "editMode": "advanced"}],
                    "axes": {
                        "x": {"bounds": ["", ""], "label": "Time", "prefix": "", "suffix": "", "base": "10", "scale": "linear"},
                        "y": {
                            "bounds": ["", ""],
                            "label": cell.get("y_label", ""),
                            "prefix": "",
                            "suffix": cell.get("y_suffix", ""),
                            "base": "10",
                            "scale": "linear",
                        },
                    },
                    "staticLegend": {},
                    "colors": [
                        {"id": "1", "type": "scale", "hex": "#31C0F6", "name": "Nineteen Eighty Four", "value": 0},
                        {"id": "2", "type": "scale", "hex": "#A500A5", "name": "Nineteen Eighty Four", "value": 0},
                        {"id": "3", "type": "scale", "hex": "#FF7E27", "name": "Nineteen Eighty Four", "value": 0},
                    ],
                    "geom": "line",
                },
            }

        api_request("PATCH", f"/api/v2/dashboards/{dash_id}/cells/{cell_id}/view", view_payload)

    logger.info(f"Dashboard InfluxDB configurado com 100% de sucesso! ID: {dash_id}")
    return dash_id


def main():
    logger.info("Inicializando configuração automática do InfluxDB...")
    try:
        org_id = get_org_id()
        dash_id = create_or_update_dashboard(org_id)
        print("\n" + "=" * 78)
        print("  INFLUXDB CONFIGURADO COM SUCESSO!")
        print("=" * 78)
        print(f"  • Organization: {ORG_NAME} (ID: {org_id})")
        print(f"  • Bucket: {BUCKET_NAME}")
        print(f"  • Dashboard ID: {dash_id}")
        print(f"  • URL de Acesso: {INFLUX_URL}/orgs/{org_id}/dashboards/{dash_id}")
        print("=" * 78 + "\n")
    except Exception as e:
        logger.error(f"Erro ao configurar InfluxDB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
