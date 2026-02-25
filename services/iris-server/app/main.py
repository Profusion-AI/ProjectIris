# SPDX-License-Identifier: AGPL-3.0-only
"""FastAPI runtime for iris-server bootstrap and transport orchestration."""

from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
import hashlib
import hmac
import json
import os
import random
import re
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVIDENCE_ROOT = PROJECT_ROOT / "services" / "iris-server" / "docs" / "evidence"
DEFAULT_TRANSPORT_MANIFEST = PROJECT_ROOT / "services" / "transport-core" / "Cargo.toml"

RE_RELAY_READY = re.compile(r"relay listening on")
RE_RECEIVED_FRAMES = re.compile(r"received_frames=(\d+)")
RE_AVG_LATENCY = re.compile(r"avg_latency_ms=([0-9]+(?:\.[0-9]+)?)")
RE_DROPPED_FRAMES = re.compile(r"local_frames_dropped=(\d+)")


class MatmulRequest(BaseModel):
    n: int = Field(ge=2, le=2048)
    dtype: str = Field(pattern=r"^(f32|f64)$")
    runs: int = Field(ge=1, le=200)
    warmup_runs: int = Field(ge=0, le=50)
    seed: int = Field(ge=0)


class StartTransportSessionRequest(BaseModel):
    stream_id: int = Field(ge=1, le=2**32 - 1)
    profile: str = Field(pattern=r"^(real-time|buffered)$")
    relay_addr: str = Field(min_length=3, max_length=128)
    frames: int = Field(ge=1, le=100_000)
    fps: int = Field(ge=1, le=240)
    payload_size: int = Field(ge=1, le=4 * 1024 * 1024)
    timeout_ms: int = Field(ge=500, le=120_000)


class StopTransportSessionRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    reason: str = Field(min_length=1, max_length=256)


class PlayerSessionRequest(BaseModel):
    profile: str = Field(default="real-time", pattern=r"^(real-time|buffered)$")
    relay_addr: str = Field(default="127.0.0.1:7443", min_length=3, max_length=128)
    stream_id: int = Field(default=777, ge=1, le=2**32 - 1)
    frames: int = Field(default=120, ge=1, le=100_000)
    fps: int = Field(default=30, ge=1, le=240)
    payload_size: int = Field(default=1024, ge=1, le=4 * 1024 * 1024)
    timeout_ms: int = Field(default=20_000, ge=500, le=120_000)


@dataclass(slots=True)
class AppSettings:
    evidence_root: Path
    transport_manifest: Path
    transport_bin_dir: Path | None
    internal_control_secret: str
    default_bench_backend: str = "python-baseline"
    relay_startup_timeout_sec: int = 25
    recv_startup_delay_sec: float = 0.4
    server_version: str = "0.1.0"


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    correlation_id: str
    profile: str
    stream_id: int
    relay_addr: str
    frames: int
    fps: int
    payload_size: int
    timeout_ms: int
    started_at_utc: str
    artifact_dir: Path
    status: str = "starting"
    stopped_at_utc: str | None = None
    error: str | None = None
    frames_sent: int | None = None
    frames_received: int | None = None
    frames_dropped: int | None = None
    avg_latency_ms: float | None = None
    artifact_path: str | None = None
    drop_metric_source: str = "relay_local_counter"
    relay_proc: subprocess.Popen[str] | None = None
    recv_proc: subprocess.Popen[str] | None = None
    send_proc: subprocess.Popen[str] | None = None


@dataclass(slots=True)
class PlayerSessionRecord:
    session_id: str
    session_token: str
    correlation_id: str
    profile: str
    stream_id: int
    relay_url: str
    metrics_url: str
    websocket_url: str
    created_at_utc: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_settings() -> AppSettings:
    bin_dir = os.getenv("IRIS_TRANSPORT_BIN_DIR")
    return AppSettings(
        evidence_root=Path(os.getenv("IRIS_EVIDENCE_ROOT", str(DEFAULT_EVIDENCE_ROOT))),
        transport_manifest=Path(
            os.getenv("IRIS_TRANSPORT_MANIFEST_PATH", str(DEFAULT_TRANSPORT_MANIFEST))
        ),
        transport_bin_dir=Path(bin_dir) if bin_dir else None,
        internal_control_secret=os.getenv(
            "IRIS_INTERNAL_CONTROL_SECRET", "iris-dev-internal-secret"
        ),
        server_version=os.getenv("IRIS_SERVER_VERSION", "0.1.0-strawman"),
    )


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def mint_internal_token(secret: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "scope": "internal-control",
        "exp": int(time.time()) + ttl_seconds,
        "iat": int(time.time()),
        "jti": uuid.uuid4().hex,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"v1.{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def verify_internal_token(token: str, secret: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise ValueError("invalid token format")

    payload_raw = _b64url_decode(parts[1])
    signature = _b64url_decode(parts[2])
    expected = hmac.new(secret.encode("utf-8"), payload_raw, hashlib.sha256).digest()

    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid token signature")

    payload = json.loads(payload_raw.decode("utf-8"))
    if payload.get("scope") != "internal-control":
        raise ValueError("invalid token scope")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expired")
    return payload


class TransportOrchestrator:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._sessions: dict[str, SessionRecord] = {}

    def start_session(self, request: StartTransportSessionRequest) -> SessionRecord:
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        correlation_id = f"corr-{uuid.uuid4().hex[:12]}"
        artifact_dir = self._settings.evidence_root / "transport-sessions" / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        record = SessionRecord(
            session_id=session_id,
            correlation_id=correlation_id,
            profile=request.profile,
            stream_id=request.stream_id,
            relay_addr=request.relay_addr,
            frames=request.frames,
            fps=request.fps,
            payload_size=request.payload_size,
            timeout_ms=request.timeout_ms,
            started_at_utc=_utc_now(),
            artifact_dir=artifact_dir,
        )
        with self._lock:
            self._sessions[session_id] = record

        worker = threading.Thread(target=self._run_session, args=(session_id,), daemon=True)
        worker.start()
        return record

    def stop_session(self, session_id: str, reason: str) -> SessionRecord:
        del reason
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                raise KeyError(session_id)
            self._terminate_processes(record)
            if record.status not in {"completed", "failed", "stopped"}:
                record.status = "stopped"
                record.stopped_at_utc = _utc_now()
        return record

    def get_session(self, session_id: str) -> SessionRecord:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                raise KeyError(session_id)
            return record

    def shutdown(self) -> None:
        with self._lock:
            for record in self._sessions.values():
                self._terminate_processes(record)

    def _run_session(self, session_id: str) -> None:
        with self._lock:
            record = self._sessions[session_id]
            record.status = "running"

        relay_log = record.artifact_dir / "relay.log"
        recv_log = record.artifact_dir / f"{record.profile}-recv.log"
        send_log = record.artifact_dir / f"{record.profile}-send.log"
        output_file = record.artifact_dir / f"{record.profile}.bin"

        try:
            relay_args = ["--auto-cert", "--bind", record.relay_addr]
            record.relay_proc = self._spawn("iris-relay", relay_args, relay_log, record)
            self._wait_for_relay_ready(record, relay_log)

            recv_args = [
                "--relay",
                record.relay_addr,
                "--stream-id",
                str(record.stream_id),
                "--profile",
                record.profile,
                "--max-frames",
                str(record.frames),
                "--output-file",
                str(output_file),
            ]
            record.recv_proc = self._spawn("iris-recv", recv_args, recv_log, record)
            time.sleep(self._settings.recv_startup_delay_sec)

            send_args = [
                "--relay",
                record.relay_addr,
                "--stream-id",
                str(record.stream_id),
                "--profile",
                record.profile,
                "--frames",
                str(record.frames),
                "--fps",
                str(record.fps),
                "--payload-size",
                str(record.payload_size),
            ]
            record.send_proc = self._spawn("iris-send", send_args, send_log, record)

            send_timeout = max(record.timeout_ms / 1000.0, 1.0)
            recv_timeout = max(record.timeout_ms / 1000.0, 1.0)
            record.send_proc.wait(timeout=send_timeout)
            record.recv_proc.wait(timeout=recv_timeout)

            self._terminate_process(record.relay_proc)
            record.relay_proc = None

            record.frames_sent = record.frames
            record.frames_received = self._extract_int(RE_RECEIVED_FRAMES, recv_log)
            record.avg_latency_ms = self._extract_float(RE_AVG_LATENCY, recv_log)
            dropped = self._extract_int(RE_DROPPED_FRAMES, relay_log, default=0)
            record.frames_dropped = dropped
            if dropped == 0:
                record.drop_metric_source = "relay_local_counter_defaulted"
            record.artifact_path = str(record.artifact_dir / "summary.json")

            with self._lock:
                if record.status not in {"stopped", "failed"}:
                    record.status = "completed"
                    record.stopped_at_utc = _utc_now()
            self._write_session_summary(record)
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._terminate_processes(record)
                record.status = "failed"
                record.stopped_at_utc = _utc_now()
                record.error = str(exc)
            self._write_session_summary(record)

    def _wait_for_relay_ready(self, record: SessionRecord, relay_log: Path) -> None:
        timeout_sec = min(
            max(record.timeout_ms / 1000.0, self._settings.relay_startup_timeout_sec),
            120.0,
        )
        started = time.monotonic()
        while True:
            if relay_log.exists():
                text = relay_log.read_text(encoding="utf-8", errors="replace")
                if RE_RELAY_READY.search(text):
                    return

            if record.relay_proc is None or record.relay_proc.poll() is not None:
                raise RuntimeError("relay exited before readiness")

            if time.monotonic() - started >= timeout_sec:
                raise TimeoutError(
                    f"relay did not report readiness within {timeout_sec:.1f}s"
                )
            time.sleep(0.1)

    def _spawn(
        self,
        logical_name: str,
        args: list[str],
        log_file: Path,
        record: SessionRecord,
    ) -> subprocess.Popen[str]:
        command = self._resolve_command(logical_name, args)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handle_fd = os.open(log_file, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        env = os.environ.copy()
        env["IRIS_CORRELATION_ID"] = record.correlation_id
        env["IRIS_SESSION_ID"] = record.session_id
        env["IRIS_SESSION_PROFILE"] = record.profile
        env["IRIS_ARTIFACT_DIR"] = str(record.artifact_dir)
        env["RUST_LOG"] = env.get("RUST_LOG", "info")
        try:
            return subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=handle_fd,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
        finally:
            os.close(handle_fd)

    def _resolve_command(self, logical_name: str, args: list[str]) -> list[str]:
        allowed = {"iris-relay", "iris-send", "iris-recv"}
        if logical_name not in allowed:
            raise ValueError(f"command not allowlisted: {logical_name}")

        if self._settings.transport_bin_dir is not None:
            candidate = self._settings.transport_bin_dir / logical_name
            if candidate.exists() and candidate.is_file():
                return [str(candidate), *args]

        return [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(self._settings.transport_manifest),
            "--bin",
            logical_name,
            "--",
            *args,
        ]

    def _terminate_processes(self, record: SessionRecord) -> None:
        self._terminate_process(record.send_proc)
        self._terminate_process(record.recv_proc)
        self._terminate_process(record.relay_proc)
        record.send_proc = None
        record.recv_proc = None
        record.relay_proc = None

    @staticmethod
    def _terminate_process(proc: subprocess.Popen[str] | None) -> None:
        if proc is None:
            return
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=2)
            return
        except subprocess.TimeoutExpired:
            pass
        proc.send_signal(signal.SIGKILL)

    @staticmethod
    def _extract_int(pattern: re.Pattern[str], path: Path, default: int | None = None) -> int:
        if not path.exists():
            if default is not None:
                return default
            raise RuntimeError(f"missing metrics log: {path}")

        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(pattern.finditer(text))
        if not matches:
            if default is not None:
                return default
            raise RuntimeError(f"missing integer field {pattern.pattern} in {path}")
        return int(matches[-1].group(1))

    @staticmethod
    def _extract_float(
        pattern: re.Pattern[str], path: Path, default: float | None = None
    ) -> float:
        if not path.exists():
            if default is not None:
                return default
            raise RuntimeError(f"missing metrics log: {path}")

        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(pattern.finditer(text))
        if not matches:
            if default is not None:
                return default
            raise RuntimeError(f"missing float field {pattern.pattern} in {path}")
        return float(matches[-1].group(1))

    @staticmethod
    def _write_session_summary(record: SessionRecord) -> None:
        payload = {
            "artifact_format": "iris-transport-session-v1",
            "session_id": record.session_id,
            "correlation_id": record.correlation_id,
            "profile": record.profile,
            "stream_id": record.stream_id,
            "relay_addr": record.relay_addr,
            "status": record.status,
            "started_at_utc": record.started_at_utc,
            "stopped_at_utc": record.stopped_at_utc or _utc_now(),
            "metrics": {
                "frames_sent": record.frames_sent,
                "frames_received": record.frames_received,
                "frames_dropped": record.frames_dropped,
                "avg_latency_ms": record.avg_latency_ms,
                "drop_metric_source": record.drop_metric_source,
            },
        }
        summary_path = record.artifact_dir / "summary.json"
        summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_matmul_benchmark(settings: AppSettings, req: MatmulRequest) -> dict[str, Any]:
    script = PROJECT_ROOT / "services" / "iris-server" / "bench" / "run_matmul_baseline.py"
    run_id = datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S-%f")
    cmd = [
        "python3",
        str(script),
        "--n",
        str(req.n),
        "--dtype",
        req.dtype,
        "--runs",
        str(req.runs),
        "--warmup-runs",
        str(req.warmup_runs),
        "--seed",
        str(req.seed),
        "--run-id",
        run_id,
        "--out-dir",
        str(settings.evidence_root),
    ]

    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"benchmark execution failed: {proc.stderr.strip()}")

    summary_path = ""
    for line in proc.stdout.splitlines():
        if line.startswith("summary_path="):
            summary_path = line.split("=", 1)[1].strip()
    if not summary_path:
        raise RuntimeError("benchmark output missing summary_path")

    summary_file = Path(summary_path)
    if not summary_file.exists():
        raise RuntimeError(f"benchmark summary missing at {summary_file}")

    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    return {
        "run_id": payload["run_id"],
        "backend": payload["backend"],
        "p50_ms": metrics["p50_ms"],
        "p95_ms": metrics["p95_ms"],
        "throughput_ops_s": metrics["throughput_ops_s"],
        "artifact_path": str(summary_file),
    }


def create_app(settings: AppSettings | None = None) -> FastAPI:
    resolved_settings = settings or _default_settings()
    resolved_settings.evidence_root.mkdir(parents=True, exist_ok=True)
    orchestrator = TransportOrchestrator(resolved_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            orchestrator.shutdown()

    app = FastAPI(
        title="iris-server",
        version=resolved_settings.server_version,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.orchestrator = orchestrator
    app.state.player_sessions: dict[str, PlayerSessionRecord] = {}
    app.state.player_sessions_lock = threading.Lock()

    def require_internal_auth(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        token = authorization[7:]
        try:
            return verify_internal_token(token, resolved_settings.internal_control_secret)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    def require_player_session_token(
        session_id: str,
        session_token: str | None,
    ) -> PlayerSessionRecord:
        if not session_token:
            raise HTTPException(status_code=401, detail="missing session token")

        with app.state.player_sessions_lock:
            record = app.state.player_sessions.get(session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="session not found")
        if not hmac.compare_digest(session_token, record.session_token):
            raise HTTPException(status_code=401, detail="invalid session token")
        return record

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        git_sha = os.getenv("GITHUB_SHA") or os.getenv("IRIS_GIT_SHA", "local-dev")
        return {
            "status": "ok",
            "version": resolved_settings.server_version,
            "git_sha": git_sha,
        }

    @app.post("/bench/matmul")
    def run_matmul(req: MatmulRequest) -> dict[str, Any]:
        try:
            return _run_matmul_benchmark(resolved_settings, req)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/bench/runs/{run_id}")
    def get_benchmark_run(run_id: str) -> dict[str, Any]:
        summary = resolved_settings.evidence_root / run_id / "summary.json"
        if not summary.exists():
            raise HTTPException(status_code=404, detail="run not found")
        return json.loads(summary.read_text(encoding="utf-8"))

    @app.post("/internal/transport/session/start")
    def start_transport_session(
        req: StartTransportSessionRequest,
        _: dict[str, Any] = Depends(require_internal_auth),
    ) -> dict[str, str]:
        record = orchestrator.start_session(req)
        return {
            "session_id": record.session_id,
            "started_at_utc": record.started_at_utc,
            "correlation_id": record.correlation_id,
        }

    @app.post("/internal/transport/session/stop")
    def stop_transport_session(
        req: StopTransportSessionRequest,
        _: dict[str, Any] = Depends(require_internal_auth),
    ) -> dict[str, str]:
        try:
            record = orchestrator.stop_session(req.session_id, req.reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc

        return {
            "session_id": record.session_id,
            "stopped_at_utc": record.stopped_at_utc or _utc_now(),
            "status": record.status,
        }

    @app.get("/internal/transport/session/{session_id}/metrics")
    def get_transport_metrics(
        session_id: str,
        _: dict[str, Any] = Depends(require_internal_auth),
    ) -> dict[str, Any]:
        try:
            record = orchestrator.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc

        return {
            "session_id": record.session_id,
            "profile": record.profile,
            "frames_sent": record.frames_sent,
            "frames_received": record.frames_received,
            "frames_dropped": record.frames_dropped,
            "avg_latency_ms": record.avg_latency_ms,
            "artifact_path": record.artifact_path,
            "correlation_id": record.correlation_id,
            "status": record.status,
            "error": record.error,
        }

    @app.post("/player/sessions")
    def create_player_session(req: PlayerSessionRequest) -> dict[str, Any]:
        session_req = StartTransportSessionRequest(
            stream_id=req.stream_id,
            profile=req.profile,
            relay_addr=req.relay_addr,
            frames=req.frames,
            fps=req.fps,
            payload_size=req.payload_size,
            timeout_ms=req.timeout_ms,
        )
        transport = orchestrator.start_session(session_req)
        session_token = f"pst-{uuid.uuid4().hex}"
        record = PlayerSessionRecord(
            session_id=transport.session_id,
            session_token=session_token,
            correlation_id=transport.correlation_id,
            profile=req.profile,
            stream_id=req.stream_id,
            relay_url=f"quic://{req.relay_addr}",
            metrics_url=f"/player/sessions/{transport.session_id}/metrics",
            websocket_url=f"/player/sessions/{transport.session_id}/ws",
            created_at_utc=_utc_now(),
        )
        with app.state.player_sessions_lock:
            app.state.player_sessions[record.session_id] = record

        return {
            "session_id": record.session_id,
            "session_token": record.session_token,
            "relay_url": record.relay_url,
            "stream_id": record.stream_id,
            "profile": record.profile,
            "metrics_url": record.metrics_url,
            "websocket_url": record.websocket_url,
            "correlation_id": record.correlation_id,
        }

    @app.get("/player/sessions/{session_id}")
    def get_player_session(
        session_id: str,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict[str, Any]:
        record = require_player_session_token(session_id, x_session_token)

        transport = orchestrator.get_session(session_id)
        return {
            "session_id": record.session_id,
            "session_token": record.session_token,
            "relay_url": record.relay_url,
            "stream_id": record.stream_id,
            "profile": record.profile,
            "metrics_url": record.metrics_url,
            "websocket_url": record.websocket_url,
            "correlation_id": record.correlation_id,
            "status": transport.status,
            "error": transport.error,
        }

    @app.get("/player/sessions/{session_id}/metrics")
    def get_player_metrics(
        session_id: str,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict[str, Any]:
        record = require_player_session_token(session_id, x_session_token)

        transport = orchestrator.get_session(session_id)
        return {
            "session_id": transport.session_id,
            "correlation_id": transport.correlation_id,
            "profile": transport.profile,
            "frames_sent": transport.frames_sent,
            "frames_received": transport.frames_received,
            "frames_dropped": transport.frames_dropped,
            "avg_latency_ms": transport.avg_latency_ms,
            "artifact_path": transport.artifact_path,
            "status": transport.status,
            "error": transport.error,
            "metrics_url": record.metrics_url,
        }

    @app.websocket("/player/sessions/{session_id}/ws")
    async def player_session_ws(
        websocket: WebSocket,
        session_id: str,
        session_token: str | None = None,
    ) -> None:
        await websocket.accept()
        try:
            require_player_session_token(session_id, session_token)
            transport = orchestrator.get_session(session_id)
        except HTTPException as exc:
            await websocket.send_json({"type": "error", "detail": exc.detail})
            await websocket.close(code=4401 if exc.status_code == 401 else 4404)
            return
        except KeyError:
            await websocket.send_json({"type": "error", "detail": "session not found"})
            await websocket.close(code=4404)
            return

        timeout_at = time.monotonic() + min(max(transport.timeout_ms / 1000.0, 2.0), 30.0)
        out_file = transport.artifact_dir / f"{transport.profile}.bin"
        while not out_file.exists() and transport.status in {"starting", "running"}:
            if time.monotonic() > timeout_at:
                break
            await asyncio.sleep(0.1)
            transport = orchestrator.get_session(session_id)

        payloads = _build_frame_payloads(transport, out_file)
        frame_interval = max(1.0 / max(transport.fps, 1), 0.005)

        try:
            for frame_index, payload in enumerate(payloads):
                await websocket.send_json(
                    {
                        "type": "frame",
                        "frame_index": frame_index,
                        "correlation_id": transport.correlation_id,
                        "payload_b64": base64.b64encode(payload).decode("utf-8"),
                    }
                )
                await asyncio.sleep(frame_interval)
            await websocket.send_json({"type": "eos", "session_id": session_id})
        except WebSocketDisconnect:
            return
        finally:
            await websocket.close()

    return app


def _build_frame_payloads(record: SessionRecord, out_file: Path) -> list[bytes]:
    frame_count = min(record.frames, 180)
    payload_size = min(record.payload_size, 2048)

    if out_file.exists():
        raw = out_file.read_bytes()
    else:
        raw = b""

    if not raw:
        rng = random.Random(record.session_id)
        return [rng.randbytes(payload_size) for _ in range(frame_count)]

    payloads: list[bytes] = []
    offset = 0
    for _ in range(frame_count):
        end = offset + payload_size
        if end <= len(raw):
            chunk = raw[offset:end]
            offset = end
        else:
            overflow = end - len(raw)
            chunk = raw[offset:] + raw[:overflow]
            offset = overflow
        if len(chunk) < payload_size:
            chunk = chunk.ljust(payload_size, b"\x00")
        payloads.append(chunk)
    return payloads


app = create_app()
