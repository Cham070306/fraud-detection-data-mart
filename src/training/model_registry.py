"""Versioned local model registry with integrity checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_model(model_path, metadata_path, registry_path="models/registry.json"):
    model_path, metadata_path, registry_path = map(Path, (model_path, metadata_path, registry_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    version = str(metadata["version"])
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"models": {}}
    entry = {
        "model_name": metadata["model_name"], "version": version,
        "model_path": str(model_path), "metadata_path": str(metadata_path),
        "sha256": sha256_file(model_path), "threshold": metadata["threshold"],
        "created_at": metadata["created_at"], "status": "active",
    }
    for item in registry["models"].values():
        item["status"] = "archived"
    registry["models"][version] = entry
    registry["active_version"] = version
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return entry


def resolve_model(version=None, registry_path="models/registry.json"):
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    version = str(version or registry["active_version"])
    entry = registry["models"][version]
    if sha256_file(entry["model_path"]) != entry["sha256"]:
        raise ValueError(f"Model integrity check failed for version {version}")
    return entry

