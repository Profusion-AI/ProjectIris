#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="${ROOT_DIR}/docs/evidence/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT_DIR"

PORT="7445"
STREAM_ID="777"

cargo run --quiet --bin iris-relay -- --auto-cert --bind "127.0.0.1:${PORT}" >"${OUT_DIR}/relay.log" 2>&1 &
RELAY_PID=$!
trap 'kill ${RELAY_PID} >/dev/null 2>&1 || true' EXIT
sleep 1

for PROFILE in real-time buffered; do
  cargo run --quiet --bin iris-recv -- \
    --relay "127.0.0.1:${PORT}" \
    --stream-id "$STREAM_ID" \
    --profile "$PROFILE" \
    --max-frames 120 \
    --output-file "${OUT_DIR}/${PROFILE}.bin" >"${OUT_DIR}/${PROFILE}-recv.log" 2>&1 &
  RECV_PID=$!

  sleep 0.4

  cargo run --quiet --bin iris-send -- \
    --relay "127.0.0.1:${PORT}" \
    --stream-id "$STREAM_ID" \
    --profile "$PROFILE" \
    --frames 120 \
    --fps 30 \
    --payload-size 1024 >"${OUT_DIR}/${PROFILE}-send.log" 2>&1

  wait ${RECV_PID}
done

echo "benchmark artifacts in ${OUT_DIR}"
