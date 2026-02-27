// SPDX-License-Identifier: Apache-2.0
import type { PlayerStatusModel } from "./types.js";

export function renderMetricPill(container: HTMLElement, model: PlayerStatusModel): void {
  const visible =
    model.state === "connected" ||
    model.state === "streaming_ready" ||
    model.latencyMs !== undefined;

  if (!visible) {
    container.innerHTML = "";
    return;
  }

  const modePill = model.transportMode
    ? `<span class="metric-pill mode-pill" data-testid="metric-mode">${model.transportMode}</span>`
    : "";
  const latencyPill =
    model.latencyMs !== undefined
      ? `<span class="metric-pill latency-pill" id="avg-latency" data-testid="metric-latency">${model.latencyMs.toFixed(1)} ms</span>`
      : "";

  container.innerHTML = `
    <div class="metrics-strip" data-testid="metrics-strip-inner">
      ${modePill}${latencyPill}
    </div>
  `;
}
