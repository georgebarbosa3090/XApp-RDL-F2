"""Quantos conflitos de uma execução da Fase 1 em malha fechada a RDL-N2 mandaria ao MAPPO.

Lê as decisões do B3 (pipeline real da RDL-N1) em ``raw/closed_loop_log.jsonl`` de execuções do orquestrador
da Fase 1 (``scripts/closed_loop/orchestrator.py``) e aplica a cada conflito resolvido a regra de elegibilidade
do próprio motor (``CARDLReasoning._marl_ineligible``, ``cardl/engine.py``), como se houvesse checkpoint
carregado e o MARL estivesse ligado pela política A1 20002. Conflitos inelegíveis vão para a reserva (RDL-N1).
As recusas da proteção do ping-pong (``PINGPONG_GUARD``) são contadas à parte: a xApp RDL as decide antes da
arbitragem, e elas não chegam ao raciocínio (nem ao MAPPO).

Uso (Ubuntu do WSL, venv da Fase 1):
  python experiments/closed_loop/escopo_mappo.py ../XApp-RDL-F1/experiments/runs/<run_id> [...] [--f1 ../XApp-RDL-F1]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

F2 = Path(__file__).resolve().parents[2]


def elegibilidade(run: Path):
    from cardl.engine import CARDLReasoning

    motor = CARDLReasoning.__new__(CARDLReasoning)   # só a regra; sem memória, grafo nem checkpoint
    motor.policy = object()                           # como se houvesse checkpoint válido
    motor.marl_enabled = True
    linhas = [json.loads(l) for l in (run / "raw" / "closed_loop_log.jsonl").open(encoding="utf-8")]
    head = next(j for j in linhas if j.get("type") == "header")
    janelas = [j for j in linhas if j.get("type") == "window"]
    parametro = {p["id"]: p["parameter"] for j in janelas for p in (j.get("proposals") or [])}
    propostas = Counter(p["parameter"] for j in janelas for p in (j.get("proposals") or []))
    motivos, tipos, guarda = Counter(), Counter(), 0
    for j in janelas:
        for r in (j.get("decision") or {}).get("resolutions") or []:
            if r.get("strategy") == "PINGPONG_GUARD":
                guarda += 1                          # decidido antes da arbitragem (rdl_xapp): não chega ao raciocínio
                continue
            conflito = SimpleNamespace(
                conflict_type=SimpleNamespace(name=r["conflict_type"]),
                involved_xapps=[SimpleNamespace(parameter=parametro.get(i, "?")) for i in r["involved"]])
            tipos[(r["conflict_type"], "+".join(sorted({a.parameter for a in conflito.involved_xapps})))] += 1
            motivos[motor._marl_ineligible(conflito) or "MAPPO"] += 1
    return {"run": run.name, "baseline": head.get("baseline"), "propostas_por_parametro": dict(propostas),
            "recusas_pingpong_guard": guarda,
            "conflitos_arbitrados": sum(motivos.values()), "conflitos_por_tipo": {f"{t}/{p}": n for (t, p), n in tipos.items()},
            "destino": dict(motivos)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--f1", default=str(F2.parent / "XApp-RDL-F1"), help="raiz do repositório da Fase 1")
    a = ap.parse_args()
    for p in (str(F2), a.f1):
        if p not in sys.path:
            sys.path.insert(0, p)
    for r in a.runs:
        print(json.dumps(elegibilidade(Path(r)), ensure_ascii=False))


if __name__ == "__main__":
    main()
