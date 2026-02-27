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
    <main class="app-shell" data-testid="app-shell">
      <section class="hero">
        <h1>Iris Player Web MVP</h1>
        <p>Session bootstrap · WebSocket frame bridge · QoS telemetry</p>
      </section>
      <div id="status-banner-slot" data-testid="status-banner"></div>
      <div id="metrics-strip-slot" data-testid="metrics-strip"></div>
      <div id="action-bar-slot" data-testid="action-bar"></div>
      <div id="error-panel-slot" data-testid="error-panel"></div>
      <section class="card render-section">
        <h2>Render Surface</h2>
        <canvas id="frame-canvas" width="640" height="360"></canvas>
      </section>
    </main>
  `;

  return {
    statusEl: root.querySelector("#status-banner-slot") as HTMLElement,
    metricsEl: root.querySelector("#metrics-strip-slot") as HTMLElement,
    actionEl: root.querySelector("#action-bar-slot") as HTMLElement,
    errorEl: root.querySelector("#error-panel-slot") as HTMLElement,
    canvasEl: root.querySelector("#frame-canvas") as HTMLCanvasElement,
  };
}
