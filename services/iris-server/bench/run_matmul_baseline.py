# SPDX-License-Identifier: AGPL-3.0-only
"""Deterministic vanilla-Python matrix benchmark for iris-server bootstrap."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkConfig:
    n: int
    dtype: str
    runs: int
    warmup_runs: int
    seed: int
    out_dir: Path
    run_id: str
    git_sha: str


def _timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (rank - lo)


def _gen_matrix(n: int, rng: random.Random) -> list[list[float]]:
    return [[rng.random() for _ in range(n)] for _ in range(n)]


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    n = len(a)
    out = [[0.0 for _ in range(n)] for _ in range(n)]
    bt = list(zip(*b))
    for i, row in enumerate(a):
        for j, col in enumerate(bt):
            s = 0.0
            for x, y in zip(row, col):
                s += x * y
            out[i][j] = s
    return out


def _build_summary(cfg: BenchmarkConfig, timings_ms: list[float]) -> dict[str, Any]:
    avg_ms = statistics.mean(timings_ms)
    seconds = avg_ms / 1000.0
    throughput_ops_s = 0.0 if seconds <= 0 else (2 * (cfg.n**3)) / seconds
    return {
        "run_id": cfg.run_id,
        "backend": "python-baseline",
        "created_at_utc": _timestamp_utc(),
        "git_sha": cfg.git_sha,
        "config": {
            "n": cfg.n,
            "dtype": cfg.dtype,
            "runs": cfg.runs,
            "warmup_runs": cfg.warmup_runs,
            "seed": cfg.seed,
        },
        "metrics": {
            "timings_ms": timings_ms,
            "p50_ms": _percentile(timings_ms, 0.50),
            "p95_ms": _percentile(timings_ms, 0.95),
            "throughput_ops_s": throughput_ops_s,
        },
        "artifact_format": "iris-server-bench-v1",
        "notes": {
            "intent": "vanilla Python control benchmark; intentionally unoptimized baseline",
            "storage": "artifact-backed only (no local database)",
        },
    }


def _parse_args() -> BenchmarkConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=64)
    parser.add_argument("--dtype", choices=["f32", "f64"], default="f64")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("services/iris-server/docs/evidence"),
    )
    parser.add_argument("--run-id", type=str, default=_default_run_id())
    parser.add_argument("--git-sha", type=str, default=os.getenv("GITHUB_SHA", "local-dev"))
    args = parser.parse_args()

    if args.n < 2:
        raise SystemExit("--n must be >= 2")
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.warmup_runs < 0:
        raise SystemExit("--warmup-runs must be >= 0")

    return BenchmarkConfig(
        n=args.n,
        dtype=args.dtype,
        runs=args.runs,
        warmup_runs=args.warmup_runs,
        seed=args.seed,
        out_dir=args.out_dir,
        run_id=args.run_id,
        git_sha=args.git_sha,
    )


def main() -> int:
    cfg = _parse_args()
    run_dir = cfg.out_dir / cfg.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(cfg.seed)
    a = _gen_matrix(cfg.n, rng)
    b = _gen_matrix(cfg.n, rng)

    for _ in range(cfg.warmup_runs):
        _ = _matmul(a, b)

    timings_ms: list[float] = []
    for _ in range(cfg.runs):
        start = time.perf_counter()
        _ = _matmul(a, b)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        timings_ms.append(elapsed_ms)

    summary = _build_summary(cfg, timings_ms)
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary_path={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
