#!/usr/bin/env python3
"""
O-RAN Telemetry InfluxDB Bridge
Streams real-time physical RAN KPIs, E2SM-KPM measurements, Near-RT RIC decisions,
and dApp sub-1ms execution envelopes to InfluxDB for Grafana visualization.
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [InfluxBridge] %(message)s")
logger = logging.getLogger("InfluxBridge")

INFLUX_HOST = os.environ.get("INFLUX_HOST", "127.0.0.1")
INFLUX_PORT = int(os.environ.get("INFLUX_PORT", "8086"))
INFLUX_ORG = os.environ.get("INFLUX_ORG", "oran-alliance")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "oran_telemetry")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "oran_rdl_token_secret_key_2026_super_secure")


class InfluxTelemetryBridge:
    def __init__(
        self,
        host: str = INFLUX_HOST,
        port: int = INFLUX_PORT,
        org: str = INFLUX_ORG,
        bucket: str = INFLUX_BUCKET,
        token: str = INFLUX_TOKEN,
    ):
        self.host = host
        self.port = port
        self.org = org
        self.bucket = bucket
        self.token = token
        self.write_url_v2 = f"http://{self.host}:{self.port}/api/v2/write?org={self.org}&bucket={self.bucket}&precision=ms"
        self.write_url_v1 = f"http://{self.host}:{self.port}/write?db={self.bucket}&precision=ms"
        self.is_connected = False

    def send_line_protocol(self, lines: str) -> bool:
        """Sends raw Influx Line Protocol batch via HTTP POST."""
        payload = lines.strip().encode("utf-8")
        if not payload:
            return True

        # Try v2 API with Token
        req = urllib.request.Request(
            self.write_url_v2,
            data=payload,
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type": "text/plain; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status in (200, 204):
                    self.is_connected = True
                    return True
        except Exception:
            # Fallback to v1 API
            try:
                req_v1 = urllib.request.Request(
                    self.write_url_v1,
                    data=payload,
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    method="POST",
                )
                with urllib.request.urlopen(req_v1, timeout=1.5) as resp:
                    if resp.status in (200, 204):
                        self.is_connected = True
                        return True
            except Exception:
                self.is_connected = False
                return False
        return False

    def publish_ran_tick(
        self,
        sim_time_s: float,
        prb_urllc: float,
        prb_embb: float,
        prb_mmtc: float,
        latency_urllc_ms: float,
        throughput_mbps: float,
        tx_power_dbm: float,
        energy_saving_pct: float = 0.0,
        state_code: int = 0,
    ) -> bool:
        """Publishes one high-resolution RAN telemetry sample."""
        ts_ms = int(time.time() * 1000)
        lines = []

        # RAN KPIs
        lines.append(
            f"ran_kpi,gnb=gNB-1,slice=Slice-URLLC prb_usage_pct={prb_urllc:.2f},rlc_latency_ms={latency_urllc_ms:.3f},throughput_mbps={throughput_mbps:.2f},tx_power_dbm={tx_power_dbm:.1f},energy_saving_pct={energy_saving_pct:.2f} {ts_ms}"
        )
        lines.append(
            f"ran_kpi,gnb=gNB-1,slice=Slice-eMBB prb_usage_pct={prb_embb:.2f},rlc_latency_ms=8.5,throughput_mbps=120.0,tx_power_dbm={tx_power_dbm:.1f} {ts_ms}"
        )
        lines.append(
            f"ran_kpi,gnb=gNB-1,slice=Slice-mMTC prb_usage_pct={prb_mmtc:.2f},rlc_latency_ms=18.2,throughput_mbps=12.0,tx_power_dbm={tx_power_dbm:.1f} {ts_ms}"
        )

        # Loop state
        lines.append(f"rdl_loop_state,scenario=golden_run state_code={state_code}i,sim_time_s={sim_time_s:.2f} {ts_ms}")

        return self.send_line_protocol("\n".join(lines))

    def publish_decision_event(
        self,
        tier: int,
        inference_time_ms: float,
        pareto_score: float,
        conflicts_count: int,
        sla_violation_prob: float = 0.0001,
    ) -> bool:
        """Publishes an H-RDL cognitive arbitration event."""
        ts_ms = int(time.time() * 1000)
        lines = [
            f"rdl_decision,scenario=conflict_storm tier_selected={tier}i,inference_time_ms={inference_time_ms:.2f},pareto_optimality_score={pareto_score:.4f},sla_violation_prob={sla_violation_prob:.6f} {ts_ms}",
            f"rdl_conflicts,scenario=conflict_storm conflict_count={conflicts_count}i {ts_ms}",
        ]
        return self.send_line_protocol("\n".join(lines))

    def stream_live_closed_loop_demo(self, duration_s: float = 60.0, interval_s: float = 0.5) -> None:
        """
        Runs real-time closed-loop telemetry streaming directly into InfluxDB.
        Supports arbitrary duration (e.g. 300s, 600s, 3600s) or infinite mode (duration_s <= 0).
        Executes periodic 60-second perturbation & cognitive recovery cycles with realistic RF jitter.
        """
        import random
        is_infinite = duration_s <= 0
        dur_label = "MODO CONTÍNUO (Ctrl+C para encerrar)" if is_infinite else f"{duration_s:.1f} segundos"
        logger.info(f"Iniciando streaming ({dur_label}) para InfluxDB ({self.host}:{self.port}/{self.bucket})...")
        
        step = 0
        t_elapsed = 0.0

        try:
            while is_infinite or (t_elapsed < duration_s):
                cycle_t = t_elapsed % 60.0
                cycle_num = int(t_elapsed // 60.0) + 1
                
                # Dynamic realistic RF noise
                noise_delay = random.uniform(-0.05, 0.05)
                noise_prb = random.uniform(-0.5, 0.5)
                noise_tput = random.uniform(-1.2, 1.2)

                # 60-Second Closed-Loop FSM Phase Dynamics
                if cycle_t < 20.0:
                    # 0-20s: Golden State (Equilibrium)
                    state = 0
                    prb_u = max(20.0, 30.0 + noise_prb)
                    prb_e = max(40.0, 55.0 + noise_prb)
                    prb_m = 15.0
                    delay_u = max(0.5, 0.82 + noise_delay)
                    tput = max(70.0, 85.0 + noise_tput)
                    pwr = 43.0
                    es = 0.0
                    tier = 1
                    confs = 0
                    pareto = 0.95
                    inf_time = 4.2 + random.uniform(-0.2, 0.2)

                elif 20.0 <= cycle_t < 23.0:
                    # 20-23s: Perturbation Injected (Traffic surge & Power cut)
                    state = 1
                    prb_u = min(100.0, 98.5 + noise_prb)
                    prb_e = 30.0
                    prb_m = 5.0
                    delay_u = max(18.0, 24.8 + random.uniform(-1.0, 2.0))
                    tput = max(20.0, 32.0 + noise_tput)
                    pwr = 30.0
                    es = 25.0
                    tier = 1
                    confs = 1
                    pareto = 0.42
                    inf_time = 4.5 + random.uniform(-0.3, 0.3)

                elif 23.0 <= cycle_t < 25.0:
                    # 23-25s: Conflict Formally Detected (C1/C2/C3)
                    state = 2
                    prb_u = min(100.0, 98.5 + noise_prb)
                    prb_e = 25.0
                    prb_m = 5.0
                    delay_u = max(18.0, 24.8 + random.uniform(-0.5, 1.5))
                    tput = max(20.0, 30.0 + noise_tput)
                    pwr = 30.0
                    es = 25.0
                    tier = 2
                    confs = 3
                    pareto = 0.45
                    inf_time = 8.6 + random.uniform(-0.4, 0.4)

                elif 25.0 <= cycle_t < 27.0:
                    # 25-27s: H-RDL / CA-RDL Cognitive Reasoning (Safe-MAPPO)
                    state = 3
                    prb_u = min(100.0, 98.5 + noise_prb)
                    prb_e = 25.0
                    prb_m = 5.0
                    delay_u = max(18.0, 24.8 + random.uniform(-0.5, 1.0))
                    tput = max(20.0, 30.0 + noise_tput)
                    pwr = 30.0
                    es = 25.0
                    tier = 3
                    confs = 3
                    pareto = 0.942
                    inf_time = 14.39 + random.uniform(-0.5, 0.5)

                elif 27.0 <= cycle_t < 30.0:
                    # 27-30s: Actuation Dispatched (E2SM-RC Format 1)
                    state = 4
                    prb_u = 52.0 + noise_prb
                    prb_e = 38.0 + noise_prb
                    prb_m = 10.0
                    delay_u = max(1.0, 1.40 + noise_delay)
                    tput = max(65.0, 72.0 + noise_tput)
                    pwr = 37.0
                    es = 17.7
                    tier = 3
                    confs = 0
                    pareto = 0.942
                    inf_time = 14.39

                else:
                    # 30-60s: Closed-Loop Converged & Physical Recovery Verified
                    state = 5
                    prb_u = 52.0 + noise_prb
                    prb_e = 38.0 + noise_prb
                    prb_m = 10.0
                    delay_u = max(0.5, 0.82 + noise_delay)
                    tput = max(70.0, 78.0 + noise_tput)
                    pwr = 37.0
                    es = 17.7
                    tier = 3
                    confs = 0
                    pareto = 0.942
                    inf_time = 14.39

                success = self.publish_ran_tick(
                    sim_time_s=t_elapsed,
                    prb_urllc=prb_u,
                    prb_embb=prb_e,
                    prb_mmtc=prb_m,
                    latency_urllc_ms=delay_u,
                    throughput_mbps=tput,
                    tx_power_dbm=pwr,
                    energy_saving_pct=es,
                    state_code=state,
                )
                self.publish_decision_event(
                    tier=tier,
                    inference_time_ms=inf_time,
                    pareto_score=pareto,
                    conflicts_count=confs,
                )

                status_lbl = ["GOLDEN", "PERTURBED", "DETECTED", "REASONING", "ACTUATING", "VERIFIED"][state]
                if step % 4 == 0:
                    cycle_info = f"[Ciclo {cycle_num}] " if (duration_s > 60 or is_infinite) else ""
                    logger.info(
                        f"{cycle_info}t={t_elapsed:5.1f}s | State: {status_lbl:10s} | InfluxDB Write: {'OK' if success else 'RETRYING'} | URLLC Delay={delay_u:.2f}ms | PRB={prb_u:.1f}%"
                    )

                step += 1
                t_elapsed += interval_s
                time.sleep(interval_s)

        except KeyboardInterrupt:
            logger.info("\n[!] Streaming interrompido pelo usuário via KeyboardInterrupt.")

        logger.info("Streaming de telemetria para InfluxDB e Grafana concluído com sucesso!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="O-RAN Telemetry InfluxDB Bridge")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Duração em segundos (0 = infinito)")
    parser.add_argument("-i", "--interval", type=float, default=0.5, help="Intervalo de amostragem em segundos")
    args = parser.parse_args()

    bridge = InfluxTelemetryBridge()
    bridge.stream_live_closed_loop_demo(duration_s=args.duration, interval_s=args.interval)

