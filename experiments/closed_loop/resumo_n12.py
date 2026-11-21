"""Roteamento da RDL hierárquica (N1 + N2) numa execução da Fase 1 em malha fechada (baseline N12).

Lê ``raw/closed_loop_log.jsonl`` do orquestrador da Fase 1 e conta, por execução:

- conflitos arbitrados por nível (RDL-N1, baixa complexidade; RDL-N2, alta) e o motivo do roteamento
  (C(c, s) acima do limiar, disputa recorrente no grafo de conhecimento, ou os dois);
- na RDL-N2, quantas decisões vieram do MAPPO e quantas foram para a reserva (RDL-N1), por motivo;
- recusas da proteção do ping-pong (decididas antes da arbitragem) e a proveniência gravada no cabeçalho
  (commit da Fase 2, checkpoint e sha256, limiares) e as políticas A1 entregues pelo Non-RT RIC simulado.

Uso: python experiments/closed_loop/resumo_n12.py ../XApp-RDL-F1/experiments/runs/<run_id> [...]
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def resumir(run: Path) -> dict:
    linhas = [json.loads(l) for l in (run / "raw" / "closed_loop_log.jsonl").open(encoding="utf-8")]
    head = next(j for j in linhas if j.get("type") == "header")
    janelas = [j for j in linhas if j.get("type") == "window"]
    nivel, motivo_rota, origem_n2, reserva, guarda = Counter(), Counter(), Counter(), Counter(), 0
    complexidade = []
    for j in janelas:
        for r in (j.get("decision") or {}).get("resolutions") or []:
            if r.get("strategy") == "PINGPONG_GUARD":
                guarda += 1
                continue
            if "level" not in r:
                nivel["sem traço"] += 1
                continue
            nivel[r["level"]] += 1
            complexidade.append(r["complexity"])
            if r["level"] == "N2":
                rr = r.get("route_reason", "")
                motivo_rota[("C" if "C=" in rr else "") + ("+grafo" if "grafo" in rr else "")] += 1
                origem_n2[r.get("source")] += 1
                if r.get("source") != "MAPPO":
                    reserva[r.get("fallback_reason") or "?"] += 1
    entregas = Counter(d for j in janelas for d in ((j.get("a1") or {}).get("delivered") or []))
    gov = [g for j in janelas for g in [((j.get("a1") or {}).get("governanca") or {})] if g.get("20000")]
    n2 = head.get("rdl_n2") or {}
    return {"run": run.name, "baseline": head.get("baseline"), "governanca": head.get("governanca"),
            "f2_git_sha": n2.get("f2_git_sha"), "f2_git_dirty": n2.get("f2_git_dirty"),
            "checkpoint_sha256": n2.get("policy_loaded_sha256"),
            "limiares": {k: n2.get(k) for k in ("complexity_threshold", "kg_recent_threshold", "kg_lookback_s")},
            "recusas_pingpong_guard": guarda, "conflitos_por_nivel": dict(nivel),
            "rota_n2": dict(motivo_rota), "origem_n2": dict(origem_n2), "reserva_n2": dict(reserva),
            "complexidade_max": max(complexidade) if complexidade else None,
            "a1_entregues": dict(entregas), "publicacoes_20000": len(gov)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args()
    for r in a.runs:
        print(json.dumps(resumir(Path(r)), ensure_ascii=False))


if __name__ == "__main__":
    main()
