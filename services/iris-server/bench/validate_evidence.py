# SPDX-License-Identifier: AGPL-3.0-only
"""Validate iris-server benchmark evidence summary schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = {
    "run_id",
    "backend",
    "created_at_utc",
    "git_sha",
    "config",
    "metrics",
    "artifact_format",
}

REQUIRED_METRICS = {"timings_ms", "p50_ms", "p95_ms", "throughput_ops_s"}
REQUIRED_CONFIG = {"n", "dtype", "runs", "warmup_runs", "seed"}


def _fail(msg: str) -> int:
    print(f"evidence validation failed: {msg}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return _fail("usage: validate_evidence.py <summary.json>")

    path = Path(sys.argv[1])
    if not path.exists():
        return _fail(f"file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))

    missing = REQUIRED_TOP_LEVEL.difference(payload.keys())
    if missing:
        return _fail(f"missing top-level keys: {sorted(missing)}")

    config = payload["config"]
    if not isinstance(config, dict):
        return _fail("config must be an object")
    missing_config = REQUIRED_CONFIG.difference(config.keys())
    if missing_config:
        return _fail(f"missing config keys: {sorted(missing_config)}")

    metrics = payload["metrics"]
    if not isinstance(metrics, dict):
        return _fail("metrics must be an object")
    missing_metrics = REQUIRED_METRICS.difference(metrics.keys())
    if missing_metrics:
        return _fail(f"missing metrics keys: {sorted(missing_metrics)}")

    if not isinstance(metrics["timings_ms"], list) or not metrics["timings_ms"]:
        return _fail("metrics.timings_ms must be a non-empty array")

    print(f"evidence validation ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
