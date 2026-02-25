#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CERT_DIR="${ROOT_DIR}/certs"
mkdir -p "$CERT_DIR"

PORT="7444"
STREAM_ID="9001"

cargo run --quiet --bin iris-relay -- --auto-cert --bind "127.0.0.1:${PORT}" > /tmp/iris-relay.log 2>&1 &
RELAY_PID=$!
trap 'kill ${RELAY_PID} >/dev/null 2>&1 || true' EXIT

sleep 1

cargo run --quiet --bin iris-recv -- \
  --relay "127.0.0.1:${PORT}" \
  --stream-id "$STREAM_ID" \
  --profile real-time \
  --max-frames 30 \
  --output-file /tmp/iris-smoke.out > /tmp/iris-recv.log 2>&1 &
RECV_PID=$!

sleep 0.5

cargo run --quiet --bin iris-send -- \
  --relay "127.0.0.1:${PORT}" \
  --stream-id "$STREAM_ID" \
  --profile real-time \
  --frames 30 \
  --fps 30 \
  --payload-size 128 > /tmp/iris-send.log 2>&1

wait ${RECV_PID}

SIZE=$(wc -c < /tmp/iris-smoke.out)
if [[ "$SIZE" -le 0 ]]; then
  echo "smoke failed: no output written"
  exit 1
fi

echo "smoke ok: wrote ${SIZE} bytes"
