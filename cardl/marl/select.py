# Autor: George Barbosa
# Software próprio do projeto CA-RDL (Fase 2). Licença: Apache-2.0 (ver LICENSE).
"""
Seleção do modelo MAPPO por critério fixado antes de olhar os resultados (docs/15 §4).

Problema que resolve: das três sementes treinadas, uma não converge para uma política segura (34 % de
violações do SLA crítico). Sem critério de seleção, nada impede que esse checkpoint vá para a inferência.

Critério (fixado neste arquivo, antes da execução):

1. Cada checkpoint é avaliado nas sementes de **validação** 8001–8010, disjuntas das de treino e das de
   avaliação final (9001–9020), com a política gulosa.
2. É **elegível** se a taxa de violação do SLA crítico na validação for ≤ ``cost_limit`` do CMDP (5 %).
3. Entre os elegíveis, vence a maior recompensa média de validação; empate: menor violação; depois, a
   menor semente.
4. Sem elegível, nenhum modelo é selecionado e a CA-RDL opera só com a H-RDL (reserva).

Saída: ``experiments/training/selection.json`` (métricas de validação por semente, regra, escolha e sha256
do checkpoint escolhido). O motor usa esse arquivo com ``CARDL_SELECTION``.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from cardl.marl.env import EnvConfig
from cardl.marl.mappo import MAPPO, MappoConfig
from cardl.marl.train import REPO, evaluate, mappo_policy

VALIDATION_SEEDS = list(range(8001, 8011))


def select(training_dir: Path, seeds: List[int], validation_seeds: List[int] = VALIDATION_SEEDS,
           cost_limit: float = MappoConfig().cost_limit) -> Dict[str, Any]:
    env_cfg = EnvConfig()
    candidates = []
    for seed in seeds:
        ckpt = training_dir / f"mappo_seed{seed}" / "actor_critic.pt"
        if not ckpt.is_file():
            candidates.append({"seed": seed, "eligible": False, "reason": "checkpoint ausente"})
            continue
        metrics = evaluate(mappo_policy(MAPPO.load(str(ckpt))), validation_seeds, env_cfg)
        eligible = metrics["critical_sla_violation_rate"] <= cost_limit
        candidates.append({"seed": seed, "eligible": eligible,
                           "reason": "violação ≤ limite do CMDP" if eligible else "violação acima do limite do CMDP",
                           "checkpoint": ckpt.relative_to(REPO).as_posix() if ckpt.is_relative_to(REPO) else str(ckpt),
                           "sha256": hashlib.sha256(ckpt.read_bytes()).hexdigest(), "validation": metrics})
    eligible = [c for c in candidates if c["eligible"]]
    chosen = min(eligible, key=lambda c: (-c["validation"]["episode_reward_mean"],
                                          c["validation"]["critical_sla_violation_rate"], c["seed"])) if eligible else None
    return {
        "schema": "xapp-rdl-f2/model-selection/v1",
        "rule": ("validação nas sementes 8001–8010; elegível se violação do SLA crítico ≤ cost_limit; "
                 "maior recompensa entre os elegíveis; sem elegível, só H-RDL"),
        "cost_limit": cost_limit, "validation_seeds": validation_seeds,
        "candidates": candidates,
        "selected": None if chosen is None else {"seed": chosen["seed"], "checkpoint": chosen["checkpoint"],
                                                 "sha256": chosen["sha256"]},
        "publication_eligible": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--training-dir", default=str(REPO / "experiments" / "training"))
    p.add_argument("--seeds", nargs="+", type=int, default=[101, 102, 103])
    p.add_argument("--out", default=str(REPO / "experiments" / "training" / "selection.json"))
    args = p.parse_args(argv)
    result = select(Path(args.training_dir), args.seeds)
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"selected": result["selected"],
                      "candidates": [{k: c.get(k) for k in ("seed", "eligible", "reason")} for c in result["candidates"]]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
