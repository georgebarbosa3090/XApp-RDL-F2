#!/usr/bin/env python3
"""Fail-closed provenance validator for CA-RDL/MAPPO publication artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAINING_ROOT = ROOT / "experiments" / "training"

NON_PUBLICATION_ENVS = {
    "MAPPO_SMOKE_ENV",
    "SYNTHETIC",
    "MOCK",
    "DEMO",
    "TRACE_REPLAY_ONLY",
}

REQUIRED_PUBLICATION_FIELDS = {
    "git_sha",
    "environment",
    "publication_eligible",
    "seed",
    "episodes",
    "steps_per_episode",
    "n_agents",
    "obs_dim",
    "action_dim",
    "hyperparameters",
    "pytorch_version",
    "device",
    "observation_schema_hash",
    "action_schema_hash",
    "reward_definition_hash",
    "environment_manifest",
    "checkpoints",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_publication_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    environment = str(data.get("environment", "")).upper()
    eligible = bool(data.get("publication_eligible", False))

    if environment in NON_PUBLICATION_ENVS:
        if eligible:
            errors.append(f"{environment} não pode ser publication_eligible=true")
        return errors

    if not eligible:
        return errors

    missing = sorted(k for k in REQUIRED_PUBLICATION_FIELDS if data.get(k) in (None, "", {}))
    if missing:
        errors.append(f"campos obrigatórios ausentes: {missing}")

    checkpoints = data.get("checkpoints") or {}
    checkpoint_hashes = data.get("checkpoint_sha256") or {}
    for name, rel in checkpoints.items():
        ckpt = path.parent / rel
        if not ckpt.is_file():
            errors.append(f"checkpoint ausente: {rel}")
            continue
        expected = checkpoint_hashes.get(name)
        if not expected:
            errors.append(f"hash SHA256 ausente para checkpoint {name}")
        elif sha256(ckpt).lower() != str(expected).lower():
            errors.append(f"hash SHA256 divergente para checkpoint {name}")

    env_manifest = data.get("environment_manifest")
    if env_manifest:
        env_path = path.parent / env_manifest
        if not env_path.is_file():
            errors.append(f"environment_manifest ausente: {env_manifest}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-publication-data", action="store_true")
    args = parser.parse_args()

    manifests = sorted(TRAINING_ROOT.rglob("training_manifest.json")) if TRAINING_ROOT.exists() else []
    publication_manifests: list[Path] = []
    failed = False

    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("publication_eligible") is True:
            publication_manifests.append(manifest)
        errors = validate_publication_manifest(manifest)
        if errors:
            failed = True
            print(f"[ML PROVENANCE FAIL] {manifest.relative_to(ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[ML PROVENANCE OK] {manifest.relative_to(ROOT)}")

    if args.require_publication_data and not publication_manifests:
        print("[ML PROVENANCE FAIL] nenhum treinamento publication_eligible=true foi encontrado.")
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
