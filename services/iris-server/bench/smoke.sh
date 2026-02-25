#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

python3 services/iris-server/bench/run_matmul_baseline.py \
  --n 24 \
  --runs 2 \
  --warmup-runs 1 \
  --seed 11 \
  --out-dir "${TMP_DIR}" >/tmp/iris-server-bench.log

SUMMARY_PATH="$(awk -F= '/^summary_path=/{print $2}' /tmp/iris-server-bench.log)"
if [[ -z "${SUMMARY_PATH}" ]]; then
  echo "smoke failed: missing summary_path output"
  exit 1
fi

python3 services/iris-server/bench/validate_evidence.py "${SUMMARY_PATH}"
echo "iris-server smoke ok: ${SUMMARY_PATH}"
