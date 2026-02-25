# Mojo Activation Gate

This document defines the activation path for replacing the bootstrap Python
control benchmark backend with runnable Mojo code in `iris-server`.

## Entry Criteria
- `services/iris-server/spec/openapi.yaml` contract is stable.
- CI smoke/evidence validation is green on `main`.
- Baseline evidence exists for Python control benchmark.

## Toolchain Requirements
- Mojo CLI installed and version pinned in CI.
- Reproducible environment bootstrap documented for local and CI runners.
- Deterministic benchmark command preserved across backends.

## Activation Checklist
1. Implement Mojo backend for `POST /bench/matmul` with the same request/response contract.
2. Emit benchmark evidence in the same artifact schema (`summary.json`).
3. Run side-by-side baseline vs Mojo benchmark runs with identical config/seed.
4. Enforce acceptance bar: at least one reproducible performance win versus Python baseline.
5. Publish residual risks and rollback procedure in release notes.

## MLIR Hardware Target Intent (Placeholder)
- Phase 1 target: CPU-only MLIR backend for deterministic CI and local validation.
- Phase 2 targets (planned placeholders):
  - GPU MLIR target
  - TPU v6e-class target
  - TPU v7/Ironwood-class target
- Requirement: preserve a single benchmark contract regardless of MLIR target.
