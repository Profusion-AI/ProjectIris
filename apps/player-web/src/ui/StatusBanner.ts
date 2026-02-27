// SPDX-License-Identifier: Apache-2.0
import type { PlayerStatusModel } from "./types.js";

const STATE_COLORS: Record<string, string> = {
  idle: "var(--muted)",
  connecting: "var(--accent)",
  connected: "#2ecc71",
  streaming_ready: "#27ae60",
  degraded: "#e67e22",
  failed: "#e74c3c",
};

export function renderStatusBanner(container: HTMLElement, model: PlayerStatusModel): void {
  const color = STATE_COLORS[model.state] ?? "var(--muted)";
  const sessionLine = model.sessionId
    ? `<span class="status-session-id">Session: ${model.sessionId}</span>`
    : "";
  container.innerHTML = `
    <div class="status-banner" data-state="${model.state}">
      <span class="status-dot" style="background:${color}"></span>
      <span class="status-label" id="session-status">${model.state}</span>
      ${sessionLine}
    </div>
  `;
}
