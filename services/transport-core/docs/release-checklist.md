# v0.1.0 Release Checklist

## Required
- [ ] `cargo fmt --all -- --check`
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] `cargo test --all-targets`
- [ ] `bash scripts/smoke.sh`
- [ ] Repro run captured with `bash scripts/benchmark.sh`
  - includes `docs/evidence/<timestamp>/summary.json`
  - reports QUIC/UDP transport metadata + real-time (200ms stale-drop) and buffered (10s playout) scenarios

## Release Notes Must Include
- [ ] What changed.
- [ ] What was verified (commands/tests/benchmark capture path).
- [ ] Rollback plan.
- [ ] Residual risks.
- [ ] Statement that framing is MoQ-like and not spec-complete.

## Deferred Track
- [ ] v0.2.0: webcam sender required.
- [ ] v0.2.1: CI benchmark gate required.
- [ ] Enhanced and hardening gates documented for roadmap continuity.
