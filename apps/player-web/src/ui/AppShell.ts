// SPDX-License-Identifier: Apache-2.0

export interface AppShellSlots {
  statusEl: HTMLElement;
  metricsEl: HTMLElement;
  actionEl: HTMLElement;
  errorEl: HTMLElement;
  canvasEl: HTMLCanvasElement;
}

export function mountAppShell(root: HTMLElement): AppShellSlots {
  root.innerHTML = `
    <div class="embed" data-testid="app-shell">
      <header class="embed-head">
        <div class="brand">
          <span class="brand-glyph" aria-hidden="true">&#9672;</span>
          <span class="brand-name">IRIS</span>
          <span class="brand-tag">PLAYER</span>
        </div>
        <div id="status-banner-slot" data-testid="status-banner"></div>
      </header>

      <div class="stage-wrap">
        <canvas id="frame-canvas" width="640" height="360"></canvas>
        <div id="metrics-strip-slot" class="metrics-pos" data-testid="metrics-strip"></div>
      </div>

      <div id="error-panel-slot" data-testid="error-panel"></div>

      <footer class="embed-foot">
        <div id="action-bar-slot" data-testid="action-bar"></div>
      </footer>
    </div>
  `;

  return {
    statusEl: root.querySelector("#status-banner-slot") as HTMLElement,
    metricsEl: root.querySelector("#metrics-strip-slot") as HTMLElement,
    actionEl: root.querySelector("#action-bar-slot") as HTMLElement,
    errorEl: root.querySelector("#error-panel-slot") as HTMLElement,
    canvasEl: root.querySelector("#frame-canvas") as HTMLCanvasElement,
  };
}
