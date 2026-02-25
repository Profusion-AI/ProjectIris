from __future__ import annotations

from pathlib import Path


RELAY_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
bind=\"127.0.0.1:7443\"
while [[ $# -gt 0 ]]; do
  case \"$1\" in
    --bind)
      bind=\"$2\"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

echo \"relay listening on ${bind}\"
echo \"subscriber complete profile=\\\"${IRIS_SESSION_PROFILE:-real-time}\\\" local_frames_dropped=2\"
trap 'exit 0' TERM INT
while true; do
  sleep 0.1
done
"""

SEND_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
sleep 0.05
"""

RECV_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail
output=\"\"
max_frames=\"10\"
while [[ $# -gt 0 ]]; do
  case \"$1\" in
    --output-file)
      output=\"$2\"
      shift 2
      ;;
    --max-frames)
      max_frames=\"$2\"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z \"${output}\" ]]; then
  echo \"missing --output-file\" >&2
  exit 1
fi

python3 - \"${output}\" \"${max_frames}\" <<'PYEOF'
from pathlib import Path
import sys

out = Path(sys.argv[1])
count = int(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes((b\"IRIS\" * max(count, 1)))
PYEOF

echo \"received_frames=${max_frames}\"
echo \"avg_latency_ms=12.5\"
"""


def create_fake_transport_bin_dir(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    scripts = {
        "iris-relay": RELAY_SCRIPT,
        "iris-send": SEND_SCRIPT,
        "iris-recv": RECV_SCRIPT,
    }

    for name, content in scripts.items():
        path = bin_dir / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    return bin_dir
