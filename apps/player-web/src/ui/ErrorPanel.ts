// SPDX-License-Identifier: Apache-2.0
import type { PlayerStatusModel } from "./types.js";

export function renderErrorPanel(
  container: HTMLElement,
  model: PlayerStatusModel,
  onRetry: () => void,
): void {
  const isError = model.state === "degraded" || model.state === "failed";
  if (!isError) {
    container.innerHTML = "";
    return;
  }

  const title = model.state === "degraded" ? "Connection Degraded" : "Connection Failed";
  const message =
    model.message ??
    "Unable to reach iris-server. Ensure the server is running on port 8080.";

  container.innerHTML = `
    <div class="error-panel" data-state="${model.state}" data-testid="error-panel-inner">
      <strong class="error-title">${title}</strong>
      <p class="error-message">${message}</p>
      <button class="retry-btn" id="retry-btn" data-testid="retry-btn">Retry Connection</button>
    </div>
  `;

  container.querySelector<HTMLButtonElement>("#retry-btn")?.addEventListener("click", onRetry);
}
