# Integration Tests

Service-to-service and data boundary tests live here.

## Current Coverage
- `test_iris_server_transport.py`
  - Internal transport session start/metrics lifecycle.
  - Signed internal-token enforcement on control endpoints.
- `test_iris_server_transport_real.py`
  - Real `transport-core` subprocess orchestration path (gated with `IRIS_RUN_REAL_TRANSPORT_TEST=1`).
  - Executed via nightly/manual workflow `iris-server-real-transport-nightly`.
