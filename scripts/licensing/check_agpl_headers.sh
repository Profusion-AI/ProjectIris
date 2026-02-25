#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

resolve_push_before() {
  if [[ -n "${GITHUB_EVENT_BEFORE:-}" ]]; then
    printf '%s\n' "${GITHUB_EVENT_BEFORE}"
    return
  fi

  if [[ -n "${GITHUB_EVENT_PATH:-}" && -f "${GITHUB_EVENT_PATH}" ]] && command -v python3 >/dev/null 2>&1; then
    python3 - "${GITHUB_EVENT_PATH}" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as file:
        payload = json.load(file)
except Exception:
    print("")
    raise SystemExit(0)

before = payload.get("before", "")
print(before if isinstance(before, str) else "")
PY
    return
  fi

  printf '\n'
}

resolve_range() {
  local base="${1:-}"
  local head="${2:-}"

  if [[ -n "${base}" && -n "${head}" ]]; then
    printf '%s...%s\n' "${base}" "${head}"
    return
  fi

  case "${GITHUB_EVENT_NAME:-}" in
    pull_request)
      if [[ -z "${GITHUB_BASE_REF:-}" ]]; then
        echo "missing GITHUB_BASE_REF for pull_request event" >&2
        exit 2
      fi
      git fetch --no-tags --prune origin "${GITHUB_BASE_REF}" >/dev/null 2>&1
      printf 'origin/%s...%s\n' "${GITHUB_BASE_REF}" "${GITHUB_SHA:-HEAD}"
      ;;
    push)
      local resolved_head before_sha
      if ! resolved_head="$(git rev-parse "${GITHUB_SHA:-HEAD}" 2>/dev/null)"; then
        echo "failed to resolve push head sha from GITHUB_SHA/HEAD" >&2
        exit 2
      fi

      before_sha="$(resolve_push_before)"
      if [[ -n "${before_sha}" ]]; then
        if [[ "${before_sha}" =~ ^0+$ ]]; then
          printf '%s\n' "${resolved_head}"
        else
          printf '%s...%s\n' "${before_sha}" "${resolved_head}"
        fi
        return
      fi

      if git rev-parse --verify --quiet "${resolved_head}^" >/dev/null; then
        printf '%s...%s\n' "$(git rev-parse "${resolved_head}^")" "${resolved_head}"
      else
        printf '%s\n' "${resolved_head}"
      fi
      ;;
    *)
      echo "usage: $0 [BASE_SHA HEAD_SHA]" >&2
      echo "or run in GitHub Actions pull_request/push context." >&2
      exit 2
      ;;
  esac
}

RANGE="$(resolve_range "${1:-}" "${2:-}")"

if [[ "${RANGE}" == *"..."* ]]; then
  new_file_cmd=(git diff --name-only --diff-filter=A "${RANGE}")
else
  new_file_cmd=(git show --pretty='' --name-only --diff-filter=A "${RANGE}")
fi

if command -v rg >/dev/null 2>&1; then
  filter_cmd=(rg '^services/(iris-server|transport-core)/.*\.(mojo|rs|py|ts|tsx|js)$')
else
  filter_cmd=(grep -E '^services/(iris-server|transport-core)/.*\.(mojo|rs|py|ts|tsx|js)$')
fi

mapfile -t candidate_files < <(
  "${new_file_cmd[@]}" \
    | "${filter_cmd[@]}" || true
)

if [[ "${#candidate_files[@]}" -eq 0 ]]; then
  echo "AGPL header check: no new core source files in scope."
  exit 0
fi

missing=()
for file in "${candidate_files[@]}"; do
  if [[ ! -f "${file}" ]]; then
    continue
  fi

  if command -v rg >/dev/null 2>&1; then
    if ! head -n 5 "${file}" | rg -q 'SPDX-License-Identifier:\s*AGPL-3\.0-only'; then
      missing+=("${file}")
    fi
  elif ! head -n 5 "${file}" | grep -Eq 'SPDX-License-Identifier:[[:space:]]*AGPL-3\.0-only'; then
    missing+=("${file}")
  fi
done

if [[ "${#missing[@]}" -gt 0 ]]; then
  echo "AGPL header check failed. Missing SPDX header in:"
  printf '  - %s\n' "${missing[@]}"
  echo
  echo "Use one of:"
  echo "  $(cat scripts/licensing/agpl-3.0-header.hash.txt)"
  echo "  $(cat scripts/licensing/agpl-3.0-header.slash.txt)"
  exit 1
fi

echo "AGPL header check: ok (${#candidate_files[@]} new source file(s) validated)."
