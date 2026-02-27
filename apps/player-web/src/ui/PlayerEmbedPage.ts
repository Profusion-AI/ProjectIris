// SPDX-License-Identifier: Apache-2.0
import { PlayerStore } from "./store.js";
import { mountAppShell } from "./AppShell.js";
import { renderStatusBanner } from "./StatusBanner.js";
import { renderMetricPill } from "./MetricPill.js";
import { renderErrorPanel } from "./ErrorPanel.js";
import { renderActionBar } from "./ActionBar.js";
import type { DemoTelemetryEvent, PlayerStatusModel } from "./types.js";

// ── API types ────────────────────────────────────────────────────────────────

type Profile = "real-time" | "buffered";

interface PlayerSessionResponse {
  session_id: string;
  session_token: string;
  relay_url: string;
  stream_id: number;
  profile: Profile;
  metrics_url: string;
  websocket_url: string;
  correlation_id: string;
}

interface SessionMetrics {
  status: string;
  frames_received: number | null;
  frames_dropped: number | null;
  avg_latency_ms: number | null;
  correlation_id: string;
}

// ── Telemetry (console sink; replace with analytics backend later) ────────────

function emit(event: DemoTelemetryEvent): void {
  console.info("[telemetry]", event.name, event);
}

// ── Main page class ───────────────────────────────────────────────────────────

export class PlayerEmbedPage {
  private store: PlayerStore;
  private root: HTMLElement;
  private slots!: ReturnType<typeof mountAppShell>;
  private metricsPoll: number | undefined;
  private socket: WebSocket | undefined;
  private unsub: (() => void) | undefined;

  constructor(root: HTMLElement) {
    this.root = root;
    this.store = new PlayerStore();
  }

  mount(): void {
    this.slots = mountAppShell(this.root);
    this.unsub = this.store.subscribe((model) => this.render(model));
    this.render(this.store.getModel());
    emit({ name: "ui_loaded", timestamp: new Date().toISOString() });
  }

  unmount(): void {
    this.teardownSession();
    this.unsub?.();
  }

  // ── Rendering ─────────────────────────────────────────────────────────────

  private render(model: PlayerStatusModel): void {
    renderStatusBanner(this.slots.statusEl, model);
    renderMetricPill(this.slots.metricsEl, model);
    renderErrorPanel(this.slots.errorEl, model, () => this.handleRetry());
    renderActionBar(
      this.slots.actionEl,
      model.state,
      (profile) => void this.handleConnect(profile),
      () => this.handleReset(),
    );
  }

  // ── Session lifecycle ──────────────────────────────────────────────────────

  private async handleConnect(profile: Profile): Promise<void> {
    this.teardownSession();
    this.store.dispatch("CONNECT_REQUEST");
    emit({ name: "connect_started", timestamp: new Date().toISOString() });

    try {
      const session = await this.createSession(profile);
      this.store.dispatch("CONNECT_SUCCESS", {
        sessionId: session.session_id,
        transportMode: profile === "real-time" ? "realtime" : "buffered",
      });
      emit({
        name: "connect_succeeded",
        timestamp: new Date().toISOString(),
        sessionId: session.session_id,
      });

      // Start metrics polling
      this.metricsPoll = window.setInterval(() => {
        void this.pollMetrics(session.metrics_url, session.session_token);
      }, 1000);

      // Open frame WebSocket
      this.openFrameSocket(session.websocket_url, session.session_token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      this.store.dispatch("FAILURE", { message });
      emit({ name: "error_shown", timestamp: new Date().toISOString(), meta: { message } });
    }
  }

  private handleReset(): void {
    this.teardownSession();
    this.store.dispatch("RESET");
  }

  private handleRetry(): void {
    // Retry goes back to idle, then immediately starts connecting with last profile.
    // For simplicity: reset to idle so the user can re-submit the form.
    this.teardownSession();
    this.store.dispatch("RESET");
  }

  private teardownSession(): void {
    if (this.metricsPoll !== undefined) {
      window.clearInterval(this.metricsPoll);
      this.metricsPoll = undefined;
    }
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.close();
    }
    this.socket = undefined;
  }

  // ── API helpers ───────────────────────────────────────────────────────────

  private async createSession(profile: Profile): Promise<PlayerSessionResponse> {
    const res = await fetch("/player/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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

    if (!res.ok) {
      throw new Error(`Session creation failed: HTTP ${res.status}`);
    }

    return res.json() as Promise<PlayerSessionResponse>;
  }

  private async pollMetrics(metricsPath: string, sessionToken: string): Promise<void> {
    try {
      const res = await fetch(metricsPath, {
        headers: { "X-Session-Token": sessionToken },
      });
      if (!res.ok) return;

      const payload: SessionMetrics = await res.json();
      this.store.dispatch("STREAM_READY", {
        latencyMs: payload.avg_latency_ms ?? undefined,
      });
    } catch {
      // Non-fatal; polling will retry on next interval
    }
  }

  private openFrameSocket(websocketPath: string, sessionToken: string): void {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    this.socket = new WebSocket(
      `${scheme}://${window.location.host}${websocketPath}?session_token=${encodeURIComponent(sessionToken)}`,
    );

    this.socket.onmessage = (event: MessageEvent<string>) => {
      const msg = JSON.parse(event.data) as {
        type: string;
        payload_b64?: string;
        detail?: string;
      };

      if (msg.type === "frame" && msg.payload_b64) {
        this.store.dispatch("STREAM_READY");
        this.renderFrame(msg.payload_b64);
        return;
      }
      if (msg.type === "error") {
        this.store.dispatch("FAILURE", {
          message: msg.detail ?? "Stream error",
        });
        return;
      }
      if (msg.type === "eos") {
        // Stream ended cleanly; stay in streaming_ready (session completed)
      }
    };

    this.socket.onerror = () => {
      this.store.dispatch("DEGRADE_NOTICE", { message: "WebSocket stream error" });
    };
  }

  // ── Canvas rendering ──────────────────────────────────────────────────────

  private renderFrame(payloadB64: string): void {
    const canvas = this.slots.canvasEl;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const raw = atob(payloadB64);
    const width = canvas.width;
    const height = canvas.height;
    const image = ctx.createImageData(width, height);

    for (let i = 0; i < width * height; i++) {
      const base = i * 4;
      image.data[base] = raw.charCodeAt(i % raw.length);
      image.data[base + 1] = raw.charCodeAt((i + 17) % raw.length);
      image.data[base + 2] = raw.charCodeAt((i + 43) % raw.length);
      image.data[base + 3] = 255;
    }

    ctx.putImageData(image, 0, 0);
  }
}
