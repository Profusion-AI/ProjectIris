#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="${ROOT_DIR}/docs/evidence/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT_DIR"

PORT="${PORT:-7445}"
RELAY_ADDR="127.0.0.1:${PORT}"
FPS="${FPS:-30}"
PAYLOAD_SIZE="${PAYLOAD_SIZE:-1024}"
CONTROL_TOKEN="${CONTROL_TOKEN:-}"

if [[ "${IRIS_BENCH_FAST:-0}" == "1" ]]; then
  : "${RT_TOTAL_FRAMES:=90}"
  : "${RT_RECV_MAX_FRAMES:=60}"
  : "${RT_STALE_PREFIX_FRAMES:=30}"
  : "${RT_STALE_OFFSET_MS:=350}"
  : "${BUF_TOTAL_FRAMES:=45}"
  : "${BUF_RECV_MAX_FRAMES:=45}"
else
  : "${RT_TOTAL_FRAMES:=180}"
  : "${RT_RECV_MAX_FRAMES:=120}"
  : "${RT_STALE_PREFIX_FRAMES:=60}"
  : "${RT_STALE_OFFSET_MS:=350}"
  : "${BUF_TOTAL_FRAMES:=120}"
  : "${BUF_RECV_MAX_FRAMES:=120}"
fi

RT_STREAM_ID="${RT_STREAM_ID:-777}"
BUF_STREAM_ID="${BUF_STREAM_ID:-778}"

relay_args=(--auto-cert --bind "${RELAY_ADDR}")
if [[ -n "${CONTROL_TOKEN}" ]]; then
  relay_args+=(--required-control-token "${CONTROL_TOKEN}")
fi

cargo run --quiet --bin iris-relay -- "${relay_args[@]}" >"${OUT_DIR}/relay.log" 2>&1 &
RELAY_PID=$!
trap 'kill ${RELAY_PID} >/dev/null 2>&1 || true' EXIT
sleep 1

echo "profile,stream_id,frames_sent,frames_target,frames_received,frames_dropped,drop_metric_source,avg_latency_ms,duration_ms,throughput_mbps,max_staleness_ms,playout_buffer_ms,stale_prefix_frames,stale_offset_ms" > "${OUT_DIR}/profiles.csv"

extract_field() {
  local pattern="$1"
  local file="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -o "${pattern}" "${file}" | tail -n 1 | cut -d= -f2
  else
    grep -Eo "${pattern}" "${file}" | tail -n 1 | cut -d= -f2
  fi
}

run_profile() {
  local profile="$1"
  local stream_id="$2"
  local frames_sent="$3"
  local frames_target="$4"
  local stale_prefix_frames="$5"
  local stale_offset_ms="$6"
  local max_staleness_ms="$7"
  local playout_buffer_ms="$8"

  recv_args=(
    --relay "${RELAY_ADDR}"
    --stream-id "${stream_id}"
    --profile "${profile}"
    --max-frames "${frames_target}"
    --output-file "${OUT_DIR}/${profile}.bin"
  )
  send_args=(
    --relay "${RELAY_ADDR}"
    --stream-id "${stream_id}"
    --profile "${profile}"
    --frames "${frames_sent}"
    --fps "${FPS}"
    --payload-size "${PAYLOAD_SIZE}"
    --stale-prefix-frames "${stale_prefix_frames}"
    --stale-offset-ms "${stale_offset_ms}"
  )
  if [[ -n "${CONTROL_TOKEN}" ]]; then
    recv_args+=(--control-token "${CONTROL_TOKEN}")
    send_args+=(--control-token "${CONTROL_TOKEN}")
  fi

  local start_ns
  start_ns="$(date +%s%N)"

  cargo run --quiet --bin iris-recv -- "${recv_args[@]}" >"${OUT_DIR}/${profile}-recv.log" 2>&1 &
  RECV_PID=$!

  sleep 0.4

  cargo run --quiet --bin iris-send -- "${send_args[@]}" >"${OUT_DIR}/${profile}-send.log" 2>&1

  wait ${RECV_PID}
  local end_ns duration_ms
  end_ns="$(date +%s%N)"
  duration_ms="$(( (end_ns - start_ns) / 1000000 ))"

  local received_frames avg_latency_ms relay_line dropped_frames drop_metric_source
  received_frames="$(extract_field 'received_frames=[0-9]+' "${OUT_DIR}/${profile}-recv.log")"
  avg_latency_ms="$(extract_field 'avg_latency_ms=[0-9]+(\.[0-9]+)?' "${OUT_DIR}/${profile}-recv.log")"
  if [[ -z "${received_frames:-}" || -z "${avg_latency_ms:-}" ]]; then
    echo "benchmark failed: missing receiver metrics for profile=${profile}" >&2
    echo "see ${OUT_DIR}/${profile}-recv.log" >&2
    exit 1
  fi

  if command -v rg >/dev/null 2>&1; then
    relay_line="$(rg "subscriber complete" "${OUT_DIR}/relay.log" | rg "profile=\"?${profile}\"?" | tail -n 1 || true)"
    dropped_frames="$(printf '%s' "${relay_line}" | rg -o 'local_frames_dropped=[0-9]+' | cut -d= -f2 || true)"
  else
    relay_line="$(grep -E "subscriber complete" "${OUT_DIR}/relay.log" | grep -E "profile=\"?${profile}\"?" | tail -n 1 || true)"
    dropped_frames="$(printf '%s' "${relay_line}" | grep -Eo 'local_frames_dropped=[0-9]+' | cut -d= -f2 || true)"
  fi

  if [[ -z "${dropped_frames:-}" ]]; then
    echo "benchmark failed: relay local drop counter missing for profile=${profile}" >&2
    echo "relay log tail:" >&2
    tail -n 80 "${OUT_DIR}/relay.log" >&2
    exit 1
  fi
  drop_metric_source="relay_local_counter"

  local throughput_mbps
  throughput_mbps="$(python3 - <<PY
received=${received_frames}
payload=${PAYLOAD_SIZE}
duration_ms=max(${duration_ms}, 1)
print(f"{(received * payload * 8.0) / (duration_ms / 1000.0) / 1_000_000.0:.6f}")
PY
)"

  echo "${profile},${stream_id},${frames_sent},${frames_target},${received_frames},${dropped_frames},${drop_metric_source},${avg_latency_ms},${duration_ms},${throughput_mbps},${max_staleness_ms},${playout_buffer_ms},${stale_prefix_frames},${stale_offset_ms}" >> "${OUT_DIR}/profiles.csv"
}

run_profile "real-time" "${RT_STREAM_ID}" "${RT_TOTAL_FRAMES}" "${RT_RECV_MAX_FRAMES}" "${RT_STALE_PREFIX_FRAMES}" "${RT_STALE_OFFSET_MS}" "200" "0"
run_profile "buffered" "${BUF_STREAM_ID}" "${BUF_TOTAL_FRAMES}" "${BUF_RECV_MAX_FRAMES}" "0" "0" "10000" "10000"

python3 - <<PY
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

out_dir = Path("${OUT_DIR}")
rows = list(csv.DictReader((out_dir / "profiles.csv").open("r", encoding="utf-8")))

summary = {
    "artifact_format": "iris-transport-bench-v2",
    "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_sha": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip(),
    "protocol": "quic/udp",
    "relay_addr": "${RELAY_ADDR}",
    "scenarios": {
        "real_time_drop_rule_ms": 200,
        "buffered_playout_target_ms": 10000,
    },
    "profiles": rows,
}

(out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\\n", encoding="utf-8")
PY

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "out_dir=${OUT_DIR}" >> "${GITHUB_OUTPUT}"
fi

echo "benchmark artifacts in ${OUT_DIR}"
