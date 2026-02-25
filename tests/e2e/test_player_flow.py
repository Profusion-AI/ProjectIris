from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
IRIS_SERVER_ROOT = REPO_ROOT / "services" / "iris-server"
TESTS_ROOT = REPO_ROOT / "tests"
if str(IRIS_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(IRIS_SERVER_ROOT))
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from app.main import AppSettings, create_app  # noqa: E402
from helpers.fake_transport import create_fake_transport_bin_dir  # noqa: E402


@pytest.mark.parametrize("profile", ["real-time", "buffered"])
def test_player_session_bootstrap_stream_and_metrics(tmp_path: Path, profile: str) -> None:
    fake_bins = create_fake_transport_bin_dir(tmp_path)
    settings = AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=fake_bins,
        internal_control_secret="e2e-secret",
        server_version="test",
    )
    app = create_app(settings)
    client = TestClient(app)

    create_response = client.post(
        "/player/sessions",
        json={
            "profile": profile,
            "relay_addr": "127.0.0.1:7445",
            "stream_id": 777,
            "frames": 12,
            "fps": 60,
            "payload_size": 128,
            "timeout_ms": 4000,
        },
    )
    assert create_response.status_code == 200
    session = create_response.json()
    session_id = session["session_id"]
    session_token = session["session_token"]

    with client.websocket_connect(session["websocket_url"]) as unauthorized_ws:
        unauthorized_message = unauthorized_ws.receive_json()
        assert unauthorized_message["type"] == "error"

    frame_count = 0
    with client.websocket_connect(
        f"{session['websocket_url']}?session_token={session_token}"
    ) as websocket:
        while True:
            message = websocket.receive_json()
            if message["type"] == "frame":
                frame_count += 1
                assert message["correlation_id"] == session["correlation_id"]
                assert isinstance(message["payload_b64"], str)
            if message["type"] == "eos":
                break

    assert frame_count > 0

    deadline = time.time() + 5
    metrics_payload = None
    while time.time() < deadline:
        metrics_response = client.get(
            f"/player/sessions/{session_id}/metrics",
            headers={"X-Session-Token": session_token},
        )
        assert metrics_response.status_code == 200
        metrics_payload = metrics_response.json()
        if metrics_payload["status"] in {"completed", "failed", "stopped"}:
            break
        time.sleep(0.05)

    assert metrics_payload is not None
    assert metrics_payload["status"] == "completed"
    assert metrics_payload["profile"] == profile
    assert metrics_payload["frames_received"] == 12
    assert metrics_payload["correlation_id"] == session["correlation_id"]
    assert Path(metrics_payload["artifact_path"]).exists()

    unauthorized_response = client.get(f"/player/sessions/{session_id}/metrics")
    assert unauthorized_response.status_code == 401
