// SPDX-License-Identifier: Apache-2.0
import type { PlayerSessionState } from "./types.js";

export function renderActionBar(
  container: HTMLElement,
  state: PlayerSessionState,
  onConnect: (profile: "real-time" | "buffered") => void,
  onReset: () => void,
): void {
  const isBusy = state === "connecting";
  const showReset =
    state === "connected" ||
    state === "streaming_ready" ||
    state === "degraded" ||
    state === "failed";

  const resetBtn = showReset
    ? `<button type="button" id="reset-btn" data-testid="reset-btn" class="btn-ghost">Reset</button>`
    : "";

  container.innerHTML = `
    <div class="action-bar" data-testid="action-bar-inner">
      <form id="session-form" data-testid="session-form" class="controls-form">
        <label class="field">
          <span class="field-lbl">Profile</span>
          <select id="profile" name="profile">
            <option value="real-time">real-time</option>
            <option value="buffered">buffered</option>
          </select>
        </label>
        <button
          type="submit"
          id="connect-btn"
          data-testid="connect-btn"
          class="btn-primary"
          ${isBusy ? "disabled" : ""}
        >${isBusy ? "Connecting…" : "Connect"}</button>
        ${resetBtn}
      </form>
    </div>
  `;

  container.querySelector<HTMLFormElement>("#session-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const profileVal =
      container.querySelector<HTMLSelectElement>("#profile")?.value as
        | "real-time"
        | "buffered";
    onConnect(profileVal ?? "real-time");
  });

  container.querySelector<HTMLButtonElement>("#reset-btn")?.addEventListener("click", () => {
    onReset();
  });
}
