from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
IRIS_SERVER_ROOT = REPO_ROOT / "services" / "iris-server"
if str(IRIS_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(IRIS_SERVER_ROOT))

from app.main import AppSettings, create_app, mint_internal_token  # noqa: E402


@pytest.mark.skipif(
    os.getenv("IRIS_RUN_REAL_TRANSPORT_TEST") != "1",
    reason="set IRIS_RUN_REAL_TRANSPORT_TEST=1 to run real transport orchestration coverage",
)
def test_real_transport_session_completes(tmp_path: Path) -> None:
    if shutil.which("cargo") is None:
        pytest.skip("cargo is required for real transport integration coverage")

    secret = "real-transport-secret"
    settings = AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=None,
        internal_control_secret=secret,
        server_version="test-real",
        relay_startup_timeout_sec=25,
        recv_startup_delay_sec=0.4,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        token = mint_internal_token(secret, ttl_seconds=600)
        start_response = client.post(
            "/internal/transport/session/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "stream_id": 9201,
                "profile": "real-time",
                "relay_addr": "127.0.0.1:7447",
                "frames": 20,
                "fps": 30,
                "payload_size": 128,
                "timeout_ms": 60000,
            },
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        deadline = time.time() + 90
        metrics_payload: dict[str, object] | None = None
        while time.time() < deadline:
            metrics_response = client.get(
                f"/internal/transport/session/{session_id}/metrics",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert metrics_response.status_code == 200
            metrics_payload = metrics_response.json()
            if metrics_payload["status"] in {"completed", "failed", "stopped"}:
                break
            time.sleep(0.25)

        assert metrics_payload is not None
        assert metrics_payload["status"] == "completed"
        assert isinstance(metrics_payload["frames_received"], int)
        assert metrics_payload["frames_received"] > 0
        assert isinstance(metrics_payload["artifact_path"], str)
        assert Path(metrics_payload["artifact_path"]).exists()
