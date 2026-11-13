"""
Treino do MAPPO da RDL-N2 no ambiente calibrado, com proveniência.

Uso:
    python -m cardl.marl.train --seeds 101 102 103 --episodes 400 --out experiments/training

Para cada semente grava em ``<out>/mappo_seed<semente>/``:
- ``actor_critic.pt``: checkpoint (carregado pelo motor RDL-N2 na inferência);
- ``convergence.csv``: recompensa, custo e λ por episódio;
- ``evaluation.json``: RDL-N2 contra B0–B3 em sementes de avaliação separadas;
- ``training_manifest.json``: commit, versão da Fase 1, sha256 da curva de calibração e do
  checkpoint, hiperparâmetros. ``publication_eligible`` é sempre ``false``: o ambiente é um
  substituto calibrado; a evidência vem da validação pré-registrada com E2 real no NORI.
"""

import argparse
import csv
import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

from cardl.marl.baselines import BASELINES
from cardl.marl.env import N_AGENTS, CalibratedSliceEnv, EnvConfig
from cardl.marl.mappo import MAPPO, MappoConfig

REPO = Path(__file__).resolve().parents[2]
EVAL_SEEDS = list(range(9001, 9021))


def _git_sha(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _git_dirty(path: Path) -> bool:
    """Árvore com alterações em código (cardl/, tests/, pyproject): o commit não descreve o que rodou."""
    try:
        out = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--", "cardl", "tests", "pyproject.toml"],
                                      text=True)
        return bool(out.strip())
    except Exception:
        return True


def _f1_version() -> Dict[str, str]:
    """Versão e commit do núcleo da Fase 1 em uso (sem caminhos locais, achado 40 da F1)."""
    try:
        import src as f1
        from importlib.metadata import version
        root = Path(f1.__file__).resolve().parents[1]
        info = {"package": "xapp-rdl-f1", "version": version("xapp-rdl-f1"), "git_sha": _git_sha(root)}
        try:
            dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--", "src"], text=True)
            info["git_dirty"] = bool(dirty.strip())
        except Exception:
            pass
        return info
    except Exception as exc:  # pragma: no cover
        return {"package": "xapp-rdl-f1", "error": type(exc).__name__}


def collect_episode(env: CalibratedSliceEnv, agent: MAPPO, seed: int) -> Dict[str, np.ndarray]:
    obs = env.reset(seed=seed)
    rec: Dict[str, List] = {k: [] for k in ("obs", "mask", "action", "logp", "state", "next_state", "reward", "cost", "done")}
    done = False
    while not done:
        masks = [env.action_mask(a) for a in range(N_AGENTS)]
        state = env.global_state()
        actions, logps = agent.act(obs, masks)
        next_obs, reward, cost, done, _ = env.step(actions)
        rec["obs"].append(np.stack(obs)); rec["mask"].append(np.stack(masks))
        rec["action"].append(actions); rec["logp"].append(logps)
        rec["state"].append(state); rec["next_state"].append(env.global_state())
        rec["reward"].append(reward); rec["cost"].append(cost); rec["done"].append(float(done))
        obs = next_obs
    return {k: np.asarray(v, dtype=np.float32 if k not in ("action",) else np.int64) for k, v in rec.items()}


def evaluate(policy: Callable[[CalibratedSliceEnv], List[int]], seeds: List[int], config: EnvConfig) -> Dict[str, float]:
    rewards, costs, energy, sat0, sat1, changes = [], [], [], [], [], []
    for seed in seeds:
        env = CalibratedSliceEnv(config, seed=seed)
        env.reset(seed=seed)
        done = False
        ep_r = 0.0
        while not done:
            prev = tuple(env.caps)
            _, r, c, done, info = env.step(policy(env))
            ep_r += r
            costs.append(c); energy.append(info.energy_ratio)
            sat0.append(info.satisfaction[0]); sat1.append(info.satisfaction[1])
            changes.append(sum(1 for a, b in zip(prev, info.caps) if a != b))
        rewards.append(ep_r)
    return {
        "episode_reward_mean": float(np.mean(rewards)), "episode_reward_sd": float(np.std(rewards, ddof=1)),
        "critical_sla_violation_rate": float(np.mean(costs)),
        "active_prb_ratio_mean": float(np.mean(energy)),
        "critical_satisfaction_mean": float(np.mean(sat0)), "embb_satisfaction_mean": float(np.mean(sat1)),
        "cap_changes_per_step": float(np.mean(changes)),
    }


def mappo_policy(agent: MAPPO) -> Callable[[CalibratedSliceEnv], List[int]]:
    def act(env: CalibratedSliceEnv) -> List[int]:
        obs = [env.observe(a) for a in range(N_AGENTS)]
        masks = [env.action_mask(a) for a in range(N_AGENTS)]
        return agent.act(obs, masks, greedy=True)[0]
    return act


def set_determinism(seed: int) -> None:
    """Treino reprodutível na CPU (docs/15 §3, item 4): sementes, um thread e algoritmos reprodutíveis."""
    import random
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True, warn_only=True)


def train_seed(seed: int, episodes: int, out: Path, env_cfg: EnvConfig, cfg: MappoConfig, episodes_per_update: int = 4) -> Dict:
    set_determinism(seed)
    run_dir = out / f"mappo_seed{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    env = CalibratedSliceEnv(env_cfg, seed=seed)
    agent = MAPPO(cfg, seed=seed)
    rng = np.random.default_rng(seed)
    t0 = time.time()
    rows = []
    for ep in range(0, episodes, episodes_per_update):
        batches = [collect_episode(env, agent, int(rng.integers(0, 2**31 - 1))) for _ in range(episodes_per_update)]
        batch = {k: np.concatenate([b[k] for b in batches]) for k in batches[0]}
        stats = agent.update(batch)
        rows.append({"episode": ep + episodes_per_update,
                     "reward_per_episode": float(batch["reward"].sum() / episodes_per_update),
                     "cost_rate": stats["mean_cost"], "lagrange": stats["lagrange"],
                     "entropy": stats["entropy"]})
    elapsed = time.time() - t0

    with (run_dir / "convergence.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    ckpt = run_dir / "actor_critic.pt"
    curve = env.curve
    agent.save(str(ckpt), {"calibration_sha256": curve.sha256, "seed": seed})
    ckpt_sha = hashlib.sha256(ckpt.read_bytes()).hexdigest()

    evaluation = {"eval_seeds": EVAL_SEEDS, "RDL-N2": evaluate(mappo_policy(agent), EVAL_SEEDS, env_cfg)}
    for name, policy in BASELINES.items():
        evaluation[name] = evaluate(policy, EVAL_SEEDS, env_cfg)
    (run_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    manifest = {
        "schema": "xapp-rdl-f2/mappo-training/v1",
        "environment": "CALIBRATED_SURROGATE",
        "publication_eligible": False,
        "eligibility_note": "Ambiente substituto calibrado com a curva NORI v5; a evidência exige a validação pré-registrada com E2 real (docs/preregistros).",
        "git_sha": _git_sha(REPO),
        "git_dirty": _git_dirty(REPO),
        "phase1": _f1_version(),
        "calibration": {"path": Path(curve.source).relative_to(REPO).as_posix() if Path(curve.source).is_relative_to(REPO) else curve.source,
                        "sha256": curve.sha256, "points": curve.points,
                        "base_throughput_mbps": curve.base_throughput_mbps,
                        "saturation_cap_pct": curve.saturation_cap_pct()},
        "seed": seed, "episodes": episodes, "training_time_s": round(elapsed, 1),
        "env_config": asdict(env_cfg), "mappo_config": asdict(cfg),
        "checkpoint": {"file": ckpt.name, "sha256": ckpt_sha},
        "final": rows[-1],
    }
    (run_dir / "training_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", nargs="+", type=int, default=[101, 102, 103])
    p.add_argument("--episodes", type=int, default=400)
    p.add_argument("--out", default=str(REPO / "experiments" / "training"))
    args = p.parse_args(argv)
    for seed in args.seeds:
        m = train_seed(seed, args.episodes, Path(args.out), EnvConfig(), MappoConfig())
        print(json.dumps({"seed": seed, "final": m["final"], "checkpoint": m["checkpoint"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
