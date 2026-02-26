// SPDX-License-Identifier: Apache-2.0
type Profile = "real-time" | "buffered";

type PlayerSessionResponse = {
  session_id: string;
  session_token: string;
  relay_url: string;
  stream_id: number;
  profile: Profile;
  metrics_url: string;
  websocket_url: string;
  correlation_id: string;
};

type SessionMetrics = {
  status: string;
  frames_received: number | null;
  frames_dropped: number | null;
  avg_latency_ms: number | null;
  correlation_id: string;
};

const formEl = document.querySelector<HTMLFormElement>("#session-form");
const profileSelectEl = document.querySelector<HTMLSelectElement>("#profile");
const statusNode = document.querySelector<HTMLElement>("#session-status");
const correlationNode = document.querySelector<HTMLElement>("#corr-id");
const framesNode = document.querySelector<HTMLElement>("#frames-received");
const dropsNode = document.querySelector<HTMLElement>("#frames-dropped");
const latencyNode = document.querySelector<HTMLElement>("#avg-latency");
const canvasEl = document.querySelector<HTMLCanvasElement>("#frame-canvas");

if (!formEl || !profileSelectEl || !statusNode || !correlationNode || !framesNode || !dropsNode || !latencyNode || !canvasEl) {
  throw new Error("player UI is missing required elements");
}

const ctxNode = canvasEl.getContext("2d");
if (!ctxNode) {
  throw new Error("canvas 2d context unavailable");
}

const form = formEl;
const profileSelect = profileSelectEl;
const statusEl = statusNode;
const correlationEl = correlationNode;
const framesEl = framesNode;
const dropsEl = dropsNode;
const latencyEl = latencyNode;
const canvas = canvasEl;
const ctx = ctxNode;

let metricsPoll: number | undefined;
let socket: WebSocket | undefined;

function renderFrame(payloadB64: string): void {
  const raw = atob(payloadB64);
  const width = canvas.width;
  const height = canvas.height;
  const image = ctx.createImageData(width, height);

  for (let i = 0; i < width * height; i += 1) {
    const base = i * 4;
    const a = raw.charCodeAt(i % raw.length);
    const b = raw.charCodeAt((i + 17) % raw.length);
    const c = raw.charCodeAt((i + 43) % raw.length);
    image.data[base] = a;
    image.data[base + 1] = b;
    image.data[base + 2] = c;
    image.data[base + 3] = 255;
  }

  ctx.putImageData(image, 0, 0);
}

function resetSessionState(): void {
  if (metricsPoll !== undefined) {
    window.clearInterval(metricsPoll);
    metricsPoll = undefined;
  }
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.close();
  }
  socket = undefined;
}

async function pollMetrics(metricsPath: string, sessionToken: string): Promise<void> {
  const response = await fetch(metricsPath, {
    headers: {
      "X-Session-Token": sessionToken,
    },
  });
  if (!response.ok) {
    throw new Error(`metrics request failed: ${response.status}`);
  }

  const payload: SessionMetrics = await response.json();
  statusEl.textContent = payload.status;
  correlationEl.textContent = payload.correlation_id;
  framesEl.textContent = payload.frames_received === null ? "-" : String(payload.frames_received);
  dropsEl.textContent = payload.frames_dropped === null ? "-" : String(payload.frames_dropped);
  latencyEl.textContent = payload.avg_latency_ms === null ? "-" : `${payload.avg_latency_ms.toFixed(2)} ms`;
}

function openFrameSocket(websocketPath: string, sessionToken: string): void {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(
    `${scheme}://${window.location.host}${websocketPath}?session_token=${encodeURIComponent(sessionToken)}`,
  );

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data) as { type: string; payload_b64?: string; detail?: string };
    if (payload.type === "frame" && payload.payload_b64) {
      renderFrame(payload.payload_b64);
      return;
    }
    if (payload.type === "error") {
      statusEl.textContent = `error: ${payload.detail ?? "session stream failed"}`;
      return;
    }
    if (payload.type === "eos") {
      statusEl.textContent = "completed";
    }
  };

  socket.onerror = () => {
    statusEl.textContent = "stream-error";
  };
}

async function createSession(profile: Profile): Promise<PlayerSessionResponse> {
  const response = await fetch("/player/sessions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      profile,
      relay_addr: "127.0.0.1:7443",
      stream_id: profile === "real-time" ? 777 : 778,
      frames: profile === "real-time" ? 120 : 60,
      fps: 30,
      payload_size: 1024,
      timeout_ms: 20000,
    }),
  });

  if (!response.ok) {
    throw new Error(`create session failed: ${response.status}`);
  }

  return response.json() as Promise<PlayerSessionResponse>;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetSessionState();

  statusEl.textContent = "starting";
  correlationEl.textContent = "-";
  framesEl.textContent = "-";
  dropsEl.textContent = "-";
  latencyEl.textContent = "-";

  try {
    const profile = profileSelect.value as Profile;
    const session = await createSession(profile);
    statusEl.textContent = "running";
    correlationEl.textContent = session.correlation_id;

    await pollMetrics(session.metrics_url, session.session_token);
    metricsPoll = window.setInterval(async () => {
      try {
        await pollMetrics(session.metrics_url, session.session_token);
      } catch {
        statusEl.textContent = "metrics-error";
      }
    }, 1000);

    openFrameSocket(session.websocket_url, session.session_token);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown error";
    statusEl.textContent = `error: ${message}`;
  }
});
