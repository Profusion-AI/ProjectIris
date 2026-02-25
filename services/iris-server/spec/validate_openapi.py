# SPDX-License-Identifier: AGPL-3.0-only
"""Validate the iris-server OpenAPI schema."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from openapi_spec_validator import validate_spec


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_openapi.py <openapi.yaml>", file=sys.stderr)
        return 1

    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"spec not found: {spec_path}", file=sys.stderr)
        return 1

    with spec_path.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    validate_spec(spec)
    print(f"openapi validation ok: {spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
