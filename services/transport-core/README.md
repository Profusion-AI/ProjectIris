# iris-transport-core

Rust-based MoQ-like QUIC transport proof-of-concept for Project Iris.

## Scope
- QUIC relay with publisher/subscriber CLI tools.
- Tunable latency profiles: `real-time` and `buffered`.
- Deterministic inputs: synthetic frames and file chunk streaming.

This is a **MoQ-like** framing prototype for transport validation and is not a full MoQ spec implementation.

## Binaries
- `iris-relay`
- `iris-send`
- `iris-recv`

## Quickstart

```bash
cd services/transport-core
cargo build

# 1) Start relay (auto-generates local self-signed certs)
cargo run --bin iris-relay -- --auto-cert --bind 127.0.0.1:7443
```

```bash
# 2) Start receiver (new terminal)
cd services/transport-core
cargo run --bin iris-recv -- \
  --relay 127.0.0.1:7443 \
  --stream-id 100 \
  --profile real-time \
  --max-frames 120 \
  --output-file /tmp/iris.out
```

```bash
# 3) Start sender (new terminal)
cd services/transport-core
cargo run --bin iris-send -- \
  --relay 127.0.0.1:7443 \
  --stream-id 100 \
  --profile real-time \
  --frames 120 \
  --fps 30 \
  --payload-size 1024
```

## Profiles
- `real-time`: drops stale frames (>250ms) for lower latency.
- `buffered`: adds initial playout buffer (~2000ms) for continuity.

## CI validation

```bash
cd services/transport-core
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test
bash scripts/smoke.sh
```

## Evidence capture
Use `scripts/benchmark.sh` to run local reproducible profile captures and save artifacts to `docs/evidence/`.

## v0.1.x TODOs
- Webcam sender mode scaffolded for v0.2.0 requirement.
- CI benchmark gate planned for v0.2.1.
- MoQ draft alignment and interoperability coverage beyond v0.1.x.
