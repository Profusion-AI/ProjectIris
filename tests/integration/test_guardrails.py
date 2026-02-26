# SPDX-License-Identifier: AGPL-3.0-only
"""Integration tests: env-var guardrails enforce configured limits at non-default values.

Covers:
  - IRIS_MAX_ACTIVE_SESSIONS   — session count cap
  - IRIS_MAX_ACTIVE_SUBPROCESSES — subprocess slot cap
  - IRIS_PLAYER_SESSION_TTL_SECONDS — player session expiry window
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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


def _make_settings(tmp_path: Path, **overrides) -> AppSettings:
    """Build minimal AppSettings for guardrail tests."""
    secret = "guardrail-test-secret"
    return AppSettings(
        evidence_root=tmp_path / "evidence",
        transport_manifest=REPO_ROOT / "services" / "transport-core" / "Cargo.toml",
        transport_bin_dir=create_fake_transport_bin_dir(tmp_path),
        internal_control_secret=secret,
        internal_control_active_kid="default",
        internal_control_keys={"default": secret},
        server_version="test",
        **overrides,
    )


_DEFAULT_SESSION_BODY = {
    "profile": "real-time",
    "relay_addr": "127.0.0.1:7443",
    "stream_id": 1,
    "frames": 20,
    "fps": 30,
    "payload_size": 512,
    "timeout_ms": 5000,
}


def test_session_cap_enforced(tmp_path: Path) -> None:
    """Third session start is rejected with 503 when IRIS_MAX_ACTIVE_SESSIONS=2."""
    settings = _make_settings(tmp_path, max_active_sessions=2)
    client = TestClient(create_app(settings), raise_server_exceptions=False)

    r1 = client.post("/player/sessions", json={**_DEFAULT_SESSION_BODY, "stream_id": 1})
    assert r1.status_code == 200, f"session 1 should succeed: {r1.text}"

    r2 = client.post("/player/sessions", json={**_DEFAULT_SESSION_BODY, "stream_id": 2})
    assert r2.status_code == 200, f"session 2 should succeed: {r2.text}"

    r3 = client.post("/player/sessions", json={**_DEFAULT_SESSION_BODY, "stream_id": 3})
    assert r3.status_code == 503, (
        f"third session should be rejected with 503 (got {r3.status_code}): {r3.text}"
    )
    assert "session" in r3.json().get("detail", "").lower()


def test_subprocess_cap_enforced(tmp_path: Path) -> None:
    """Second session start is rejected with 503 when IRIS_MAX_ACTIVE_SUBPROCESSES=3.

    The first session reserves all 3 slots (projected = 0 + 0 + 3 = 3, not > 3).
    The second session's projection (current_reserved=3, needs 3 more) exceeds the cap.
    """
    settings = _make_settings(tmp_path, max_active_subprocesses=3)
    client = TestClient(create_app(settings), raise_server_exceptions=False)

    r1 = client.post("/player/sessions", json={**_DEFAULT_SESSION_BODY, "stream_id": 1})
    assert r1.status_code == 200, f"first session should succeed: {r1.text}"

    r2 = client.post("/player/sessions", json={**_DEFAULT_SESSION_BODY, "stream_id": 2})
    assert r2.status_code == 503, (
        f"second session should be rejected with 503 (got {r2.status_code}): {r2.text}"
    )
    assert "subprocess" in r2.json().get("detail", "").lower()


def test_ttl_applied(tmp_path: Path) -> None:
    """Player session expires_at_utc reflects IRIS_PLAYER_SESSION_TTL_SECONDS=5."""
    ttl = 5
    settings = _make_settings(tmp_path, player_session_ttl_seconds=ttl)
    client = TestClient(create_app(settings), raise_server_exceptions=False)

    before = int(time.time())
    resp = client.post("/player/sessions", json=_DEFAULT_SESSION_BODY)
    assert resp.status_code == 200, f"session creation should succeed: {resp.text}"

    expires_str = resp.json()["expires_at_utc"]
    expires_ts = datetime.strptime(expires_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    expires_epoch = int(expires_ts.timestamp())

    # expires_at_utc must be approximately before + ttl (within ±2 s for clock granularity)
    assert expires_epoch <= before + ttl + 2, (
        f"expires_at_utc {expires_str!r} is further than {ttl + 2}s from issue time"
    )
    assert expires_epoch >= before + ttl - 2, (
        f"expires_at_utc {expires_str!r} is less than {ttl - 2}s from issue time"
    )
