# Data Governance Baseline (MVP)

Date: 2026-02-26
Owner: Kyle
Support: Codex

## Scope
This baseline covers bootstrap `iris-server` and `player-web` session telemetry and artifacts.

## Data Handling Principles
- Minimize retained session data.
- Keep benchmark/session outputs artifact-backed and traceable.
- Treat streamed media payloads as sensitive operational data.

## Retention
- Benchmark/session artifacts under `services/iris-server/docs/evidence/**` are retained for engineering validation.
- Retention periods for staging/prod environments must be explicitly configured per deployment.
- Expired player session tokens are invalidated in-process and not persisted in this phase.

## Security Controls
- Internal control endpoints require signed bearer tokens.
- Player session access requires per-session token.
- Transport subprocess commands are allowlist-only.
- Correlation IDs propagate across orchestrated runs and logs.

## Encryption Expectations
- In transit: TLS/QUIC required for external-facing deployments.
- At rest: deployment environments must encrypt artifact storage where customer data may exist.

## Privacy and Compliance Readiness
- GDPR/CCPA posture is pre-production and documentation-first in this phase.
- Before onboarding external users:
  1. define data subject request handling,
  2. define retention/deletion SLAs,
  3. define audit logging and access control review.

## Known Limitation
- Session token revocation state is in-memory only and resets on process restart during straw-man phase.
