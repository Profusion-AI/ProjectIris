# iris-server

Mojo-oriented service track for backend API experiments and compute-heavy
benchmark paths.

## Bootstrap Status
- API and benchmark contracts are defined under `spec/`.
- Control benchmark backend is currently vanilla Python by design.
- Mojo runtime implementation is gated by `docs/mojo-activation-gate.md`.
- Runtime bootstrap is now FastAPI-based as a temporary sprint implementation.

## Contracts
- Public API: `spec/openapi.yaml`
  - `GET /metrics` (Prometheus text metrics)
  - `GET /healthz`
  - `POST /bench/matmul`
  - `GET /bench/runs/{run_id}`
  - `POST /player/sessions`
  - `POST /player/sessions/{session_id}/revoke` (requires `X-Session-Token`)
  - `GET /player/sessions/{session_id}` (requires `X-Session-Token`)
  - `GET /player/sessions/{session_id}/metrics` (requires `X-Session-Token`)
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

## Runtime Commands
Install runtime/test dependencies:
```bash
cd /home/kyle/ProjectIris
python3 -m pip install -r services/iris-server/requirements.txt
```

Start server:
```bash
cd /home/kyle/ProjectIris
uvicorn app.main:app --app-dir services/iris-server --host 127.0.0.1 --port 8080
```

Generate a signed internal control token:
```bash
cd /home/kyle/ProjectIris
python3 - <<'PY'
import os
import sys
sys.path.insert(0, "services/iris-server")
from app.main import mint_internal_token, mint_internal_token_v2

secret = os.getenv("IRIS_INTERNAL_CONTROL_SECRET", "iris-dev-internal-secret")
print(mint_internal_token(secret, ttl_seconds=3600))

active_kid = os.getenv("IRIS_INTERNAL_CONTROL_ACTIVE_KID", "default")
keys = {active_kid: secret}
print(mint_internal_token_v2(keys, active_kid=active_kid, ttl_seconds=3600))
PY
```

## Runtime Controls
- Internal token rotation:
  - `IRIS_INTERNAL_CONTROL_ACTIVE_KID`
  - `IRIS_INTERNAL_CONTROL_KEYS_JSON`
- Player session token lifecycle:
  - `IRIS_PLAYER_SESSION_TTL_SECONDS`
- Concurrency guardrails:
  - `IRIS_MAX_ACTIVE_SESSIONS`
  - `IRIS_MAX_ACTIVE_SUBPROCESSES`

## Evidence Policy
- Benchmark runs are artifact-backed (`docs/evidence/**`) only.
- No local DB state (for example SQLite) is allowed in this bootstrap phase.
