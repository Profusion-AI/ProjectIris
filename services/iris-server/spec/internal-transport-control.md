# Internal Transport Control Contract (Draft)

This is an internal-only interface for `iris-server` to orchestrate `iris-transport-core`
through a process boundary during bootstrap.

## Security
- Require `Authorization: Bearer <signed-internal-token>`.
- Signed token format for bootstrap: `v1.<payload_b64url>.<hmac_sha256_sig_b64url>`.
- Reject unsigned or malformed tokens.
- Default bind for internal control listener: `127.0.0.1`.
- Command execution is allowlist-only: `iris-relay`, `iris-send`, `iris-recv`.

## Endpoints

### `POST /internal/transport/session/start`
- Purpose: start a transport scenario run.
- Request payload:
  - `stream_id` (u32)
  - `profile` (`real-time` or `buffered`)
  - `relay_addr` (`host:port`)
  - `frames` (u64)
  - `fps` (u64)
  - `payload_size` (usize)
  - `timeout_ms` (u64)
- Response payload:
  - `session_id`
  - `started_at_utc`
  - `correlation_id`
  - implied `artifact_path` namespace rooted under `docs/evidence/transport-sessions/<session_id>/`

### `POST /internal/transport/session/stop`
- Purpose: stop active transport run.
- Request payload:
  - `session_id`
  - `reason`
- Response payload:
  - `session_id`
  - `stopped_at_utc`
  - `status`

### `GET /internal/transport/session/{id}/metrics`
- Purpose: read normalized metrics linked to benchmark evidence.
- Response payload:
  - `session_id`
  - `profile`
  - `frames_sent`
  - `frames_received`
  - `frames_dropped`
  - `avg_latency_ms`
  - `artifact_path`
  - `correlation_id`
