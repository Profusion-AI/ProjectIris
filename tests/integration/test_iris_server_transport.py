from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
IRIS_SERVER_ROOT = REPO_ROOT / "services" / "iris-server"
TESTS_ROOT = REPO_ROOT / "tests"
if str(IRIS_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(IRIS_SERVER_ROOT))
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from app.main import AppSettings, create_app, mint_internal_token  # noqa: E402
from helpers.fake_transport import create_fake_transport_bin_dir  # noqa: E402


def _poll_metrics(client: TestClient, session_id: str, token: str, timeout_sec: float = 5.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        response = client.get(
            f"/internal/transport/session/{session_id}/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed", "stopped"}:
            return payload
        time.sleep(0.05)
    raise AssertionError("timed out waiting for session completion")


def test_internal_transport_session_start_and_metrics(tmp_path: Path) -> None:
    secret = "integration-secret"
    fake_bins = create_fake_transport_bin_dir(tmp_path)
    settings = AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=fake_bins,
        internal_control_secret=secret,
        server_version="test",
    )
    app = create_app(settings)
    client = TestClient(app)

    token = mint_internal_token(secret)
    start_response = client.post(
        "/internal/transport/session/start",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "stream_id": 100,
            "profile": "real-time",
            "relay_addr": "127.0.0.1:7443",
            "frames": 20,
            "fps": 30,
            "payload_size": 512,
            "timeout_ms": 3000,
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()

    metrics = _poll_metrics(client, start_payload["session_id"], token)
    assert metrics["status"] == "completed"
    assert metrics["frames_sent"] == 20
    assert metrics["frames_received"] == 20
    assert metrics["frames_dropped"] == 2
    assert metrics["avg_latency_ms"] == 12.5
    assert metrics["correlation_id"] == start_payload["correlation_id"]
    assert metrics["artifact_path"] is not None
    assert Path(metrics["artifact_path"]).exists()


def test_internal_auth_rejects_unsigned_token(tmp_path: Path) -> None:
    fake_bins = create_fake_transport_bin_dir(tmp_path)
    settings = AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=fake_bins,
        internal_control_secret="another-secret",
        server_version="test",
    )
    app = create_app(settings)
    client = TestClient(app)

    response = client.post(
        "/internal/transport/session/start",
        headers={"Authorization": "Bearer invalid-token"},
        json={
            "stream_id": 101,
            "profile": "buffered",
            "relay_addr": "127.0.0.1:7444",
            "frames": 10,
            "fps": 24,
            "payload_size": 256,
            "timeout_ms": 2000,
        },
    )
    assert response.status_code == 401
