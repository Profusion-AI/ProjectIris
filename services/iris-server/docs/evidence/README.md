# iris-server Evidence Artifacts

`iris-server` benchmark evidence is artifact-backed only for this phase.
Do not add SQLite or other local database dependencies for benchmark run storage.

## Layout
- `services/iris-server/docs/evidence/<run-id>/summary.json`

## `summary.json` Required Keys
- `run_id`
- `backend`
- `created_at_utc`
- `git_sha`
- `config`
  - `n`
  - `dtype`
  - `runs`
  - `warmup_runs`
  - `seed`
- `metrics`
  - `timings_ms`
  - `p50_ms`
  - `p95_ms`
  - `throughput_ops_s`
- `artifact_format`
