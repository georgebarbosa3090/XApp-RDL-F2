#!/usr/bin/env python3
"""
Dataset offline da RDL-N2 a partir das execuções em malha fechada da Fase 1 (docs/17, §3 e §4).

Lê ``raw/closed_loop_log.jsonl`` e ``execution_manifest.json`` de cada execução e grava:

- ``transicoes.jsonl``: uma linha por janela com propostas: KPM da janela (células e UEs), propostas, decisão
  (selecionadas e resoluções com família, nível e origem), ações aplicadas, KPM da janela seguinte (+0,2 s) e
  células 1 s depois;
- ``handovers.jsonl``: um evento por handover aplicado com UE: diferença de RSRP destino − origem, carga do
  destino, satisfação do UE antes (1 s) e depois (1 s), perda de conexão em até 3 s; entrada de
  ``cardl.marl.env_handover_prb.fit_response``;
- ``manifesto.json``: execuções lidas (commit, estado da árvore, status, sha256 do log), contagens e sha256 das
  saídas.

Só execuções com ``run_status: SUCCESS`` entram. Uso:

    python experiments/closed_loop/extrair_transicoes.py <saida> <execução ou padrão glob> [...]
"""

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from cardl.families import classify_params  # noqa: E402

PARAM_RE = re.compile(r"-g\d+-([A-Z_]+)-\d")
UE_KEYS = ("ue", "cell_id", "connected", "thp_mbps", "delay_ms", "sinr_db", "rsrp_dbm")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def param_of(action_id: str) -> Optional[str]:
    m = PARAM_RE.search(action_id or "")
    return m.group(1) if m else None


def _ues(window: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{k: u.get(k) for k in UE_KEYS} for u in window["kpm"].get("ues", [])]


def _resolutions(window: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for r in (window.get("decision") or {}).get("resolutions") or []:
        params = [param_of(i) for i in r.get("involved") or []]
        out.append({"conflict_type": r.get("conflict_type"), "family": classify_params(r.get("conflict_type", ""), params),
                    "strategy": r.get("strategy"), "involved": r.get("involved"), "winners": r.get("winners"),
                    **{k: r.get(k) for k in ("level", "complexity", "route_reason", "source", "fallback_reason")
                       if k in r}})
    return out


def read_run(run: Path):
    manifest = json.loads((run / "execution_manifest.json").read_text(encoding="utf-8"))
    header, windows = None, {}
    with open(run / "raw" / "closed_loop_log.jsonl", encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            if j.get("type") == "header":
                header = j
            elif j.get("type") == "window":
                windows[round(float(j["t"]), 1)] = j
    return manifest, header or {}, windows


def handover_events(run_id: str, header: Dict, windows: Dict[float, Dict]) -> Iterable[Dict[str, Any]]:
    cell_of = {g["gnb"]: g["cell_id"] for g in (header.get("hello") or {}).get("gnbs", [])}
    offered = {int(k): float(v) for k, v in ((header.get("hello") or {}).get("ue_offered_mbps") or {}).items()}
    ts = sorted(windows)

    def ue_at(t, ue):
        w = windows.get(round(t, 1))
        return next((u for u in w["kpm"]["ues"] if u.get("ue") == ue), None) if w else None

    def mean_sat(ue, t0, t1):
        vals = [u["thp_mbps"] for t in ts if t0 < t <= t1 for u in [ue_at(t, ue)] if u and u.get("thp_mbps") is not None]
        return (sum(vals) / len(vals) / offered[ue]) if vals and offered.get(ue) else None

    for t in ts:
        for a in windows[t].get("actions") or []:
            if a.get("parameter") != "HANDOVER" or a.get("ue") is None or int(a["ue"]) < 0:
                continue
            ue, src, dst = int(a["ue"]), cell_of.get(a["gnb"]), cell_of.get(int(round(float(a["value"]))))
            u = ue_at(t, ue)
            if u is None or src is None or dst is None:
                continue
            rsrp = u.get("rsrp_dbm") or {}
            gap = (rsrp[str(dst)] - rsrp[str(src)]) if str(dst) in rsrp and str(src) in rsrp else None
            dst_cell = next((c for c in windows[t]["kpm"]["cells"] if c.get("cell_id") == dst), None)
            lost = any(not (ue_at(tt, ue) or {}).get("connected", True) for tt in ts if t < tt <= t + 3.0)
            yield {"run_id": run_id, "t": t, "ue": ue, "xapp_id": a.get("xapp_id"), "src_cell": src, "dst_cell": dst,
                   "rsrp_gap_db": gap, "sinr_db": u.get("sinr_db"),
                   "load_dst": dst_cell.get("prb_util") if dst_cell else None,
                   "sat_before": mean_sat(ue, t - 1.0, t), "sat_after": mean_sat(ue, t + 0.2, t + 1.2), "lost": lost}


def transitions(run_id: str, manifest: Dict, header: Dict, windows: Dict[float, Dict]) -> Iterable[Dict[str, Any]]:
    for t in sorted(windows):
        w = windows[t]
        if not w.get("proposals"):
            continue
        nxt, later = windows.get(round(t + 0.2, 1)), windows.get(round(t + 1.0, 1))
        yield {"run_id": run_id, "scenario": header.get("scenario"), "baseline": header.get("baseline"),
               "seed": header.get("seed"), "repo_git_sha": manifest.get("repo_git_sha"), "t": t,
               "ue_offered_mbps": (header.get("hello") or {}).get("ue_offered_mbps"),
               "cells": w["kpm"].get("cells"), "ues": _ues(w), "a1": w.get("a1"),
               "proposals": w.get("proposals"), "selected": (w.get("decision") or {}).get("selected"),
               "rule": (w.get("decision") or {}).get("rule"), "resolutions": _resolutions(w),
               "actions": [a.get("id") for a in w.get("actions") or []],
               "next": {"t": nxt["t"], "cells": nxt["kpm"].get("cells"), "ues": _ues(nxt)} if nxt else None,
               "cells_1s": later["kpm"].get("cells") if later else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("saida", type=Path)
    ap.add_argument("execucoes", nargs="+")
    args = ap.parse_args(argv)
    runs = sorted({Path(p) for pat in args.execucoes for p in (glob.glob(pat) or [pat])})
    args.saida.mkdir(parents=True, exist_ok=True)
    tr_path, ho_path = args.saida / "transicoes.jsonl", args.saida / "handovers.jsonl"
    lidas, puladas, n_tr, n_ho, familias = [], [], 0, 0, {}
    with open(tr_path, "w", encoding="utf-8", newline="\n") as ftr, open(ho_path, "w", encoding="utf-8", newline="\n") as fho:
        for run in runs:
            log = run / "raw" / "closed_loop_log.jsonl"
            if not log.exists() or not (run / "execution_manifest.json").exists():
                puladas.append({"run_id": run.name, "motivo": "sem log ou manifesto"})
                continue
            manifest, header, windows = read_run(run)
            if manifest.get("run_status") != "SUCCESS":
                puladas.append({"run_id": run.name, "motivo": f"run_status {manifest.get('run_status')}"})
                continue
            for rec in transitions(run.name, manifest, header, windows):
                ftr.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_tr += 1
                for r in rec["resolutions"]:
                    familias[str(r["family"])] = familias.get(str(r["family"]), 0) + 1
            for ev in handover_events(run.name, header, windows):
                fho.write(json.dumps(ev, ensure_ascii=False) + "\n")
                n_ho += 1
            lidas.append({"run_id": run.name, "scenario": header.get("scenario"), "baseline": header.get("baseline"),
                          "seed": header.get("seed"), "repo_git_sha": manifest.get("repo_git_sha"),
                          "repo_dirty": manifest.get("repo_dirty"), "log_sha256": sha256_file(log)})
    out = {"execucoes": lidas, "puladas": puladas, "transicoes": n_tr, "handovers": n_ho,
           "resolucoes_por_familia": familias,
           "saidas": {p.name: sha256_file(p) for p in (tr_path, ho_path)}}
    (args.saida / "manifesto.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("transicoes", "handovers", "resolucoes_por_familia")}, ensure_ascii=False),
          f"| execuções: {len(lidas)} lidas, {len(puladas)} puladas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
