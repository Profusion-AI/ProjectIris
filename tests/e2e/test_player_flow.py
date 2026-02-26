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


def _settings(tmp_path: Path, ttl_seconds: int = 3600) -> AppSettings:
    secret = "e2e-secret"
    return AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=create_fake_transport_bin_dir(tmp_path),
        internal_control_secret=secret,
        internal_control_active_kid="default",
        internal_control_keys={"default": secret},
        server_version="test",
        player_session_ttl_seconds=ttl_seconds,
    )


@pytest.mark.parametrize("profile", ["real-time", "buffered"])
def test_player_session_bootstrap_stream_and_metrics(tmp_path: Path, profile: str) -> None:
    app = create_app(_settings(tmp_path))
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


def test_player_session_revoke_blocks_metrics_and_ws(tmp_path: Path) -> None:
    app = create_app(_settings(tmp_path))
    client = TestClient(app)

    create_response = client.post(
        "/player/sessions",
        json={
            "profile": "real-time",
            "relay_addr": "127.0.0.1:7446",
            "stream_id": 1001,
            "frames": 10,
            "fps": 30,
            "payload_size": 128,
            "timeout_ms": 3000,
        },
    )
    assert create_response.status_code == 200
    session = create_response.json()

    revoke_response = client.post(
        f"/player/sessions/{session['session_id']}/revoke",
        headers={"X-Session-Token": session["session_token"]},
        json={"reason": "security-test"},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    metrics_response = client.get(
        f"/player/sessions/{session['session_id']}/metrics",
        headers={"X-Session-Token": session["session_token"]},
    )
    assert metrics_response.status_code == 401

    with client.websocket_connect(
        f"{session['websocket_url']}?session_token={session['session_token']}"
    ) as websocket:
        payload = websocket.receive_json()
        assert payload["type"] == "error"
        assert payload["detail"] == "session token revoked"


def test_player_session_expiry_enforced(tmp_path: Path) -> None:
    app = create_app(_settings(tmp_path, ttl_seconds=3600))
    client = TestClient(app)

    create_response = client.post(
        "/player/sessions",
        json={
            "profile": "buffered",
            "relay_addr": "127.0.0.1:7448",
            "stream_id": 1002,
            "frames": 6,
            "fps": 24,
            "payload_size": 64,
            "timeout_ms": 3000,
        },
    )
    assert create_response.status_code == 200
    session = create_response.json()

    # Force expiry deterministically without sleeping.
    with app.state.player_sessions_lock:
        app.state.player_sessions[session["session_id"]].expires_at_utc = "1970-01-01T00:00:00Z"

    expired_response = client.get(
        f"/player/sessions/{session['session_id']}",
        headers={"X-Session-Token": session["session_token"]},
    )
    assert expired_response.status_code == 401
    assert expired_response.json()["detail"] == "session token expired"
