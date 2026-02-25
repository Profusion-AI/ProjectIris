# iris-server

Mojo-oriented service track for backend API experiments and compute-heavy
benchmark paths.

## Bootstrap Status
- API and benchmark contracts are defined under `spec/`.
- Control benchmark backend is currently vanilla Python by design.
- Mojo runtime implementation is gated by `docs/mojo-activation-gate.md`.

## Contracts
- Public API: `spec/openapi.yaml`
  - `GET /healthz`
  - `POST /bench/matmul`
  - `GET /bench/runs/{run_id}`
- Internal transport control draft: `spec/internal-transport-control.md`

## Benchmark Commands
```bash
cd /home/kyle/ProjectIris
bash services/iris-server/bench/smoke.sh
```

```bash
cd /home/kyle/ProjectIris
python3 services/iris-server/bench/run_matmul_baseline.py \
  --n 64 \
  --runs 5 \
  --warmup-runs 1 \
  --seed 7 \
  --out-dir services/iris-server/docs/evidence
```

## Evidence Policy
- Benchmark runs are artifact-backed (`docs/evidence/**`) only.
- No local DB state (for example SQLite) is allowed in this bootstrap phase.
