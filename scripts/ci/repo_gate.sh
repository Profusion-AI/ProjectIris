#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "repo-gate: checking repository inventory"
git ls-files >/dev/null

echo "repo-gate: ensuring no tracked .env files"
if git ls-files | grep -Eq '(^|/)\.env(\.|$)'; then
  echo "repo-gate failed: tracked .env file detected"
  git ls-files | grep -E '(^|/)\.env(\.|$)'
  exit 1
fi

echo "repo-gate: ensuring benchmark API remains artifact-backed"
if git ls-files services/iris-server | grep -Eq '\.db$'; then
  echo "repo-gate failed: tracked database artifact detected under services/iris-server"
  git ls-files services/iris-server | grep -E '\.db$'
  exit 1
fi

echo "repo-gate: ok"
