// SPDX-License-Identifier: Apache-2.0
import { escapeHtml } from "./utils.js";
import type { PlayerStatusModel } from "./types.js";

export function renderStatusBanner(container: HTMLElement, model: PlayerStatusModel): void {
  const sessionLine = model.sessionId
    ? `<span class="status-session-id">${escapeHtml(model.sessionId)}</span>`
    : "";
  container.innerHTML = `
    <div class="status-chip" data-state="${model.state}">
      <span class="status-dot"></span>
      <span class="status-label" id="session-status">${model.state}</span>
      ${sessionLine}
    </div>
  `;
}
