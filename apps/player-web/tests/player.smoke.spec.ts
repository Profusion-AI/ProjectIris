// SPDX-License-Identifier: Apache-2.0
import { test, expect } from "@playwright/test";

// ── Scenario 1: Boot Smoke ────────────────────────────────────────────────────
// Given: UI starts with no backend.
// Then: Shell, banner, and action-bar render; status shows idle.

test("boot smoke — scaffold renders with idle state", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Iris Player Web MVP");

  // AppShell visible
  await expect(page.locator("[data-testid='app-shell']")).toBeVisible();

  // StatusBanner shows idle
  await expect(page.locator("[data-testid='status-banner']")).toBeVisible();
  await expect(page.locator("#session-status")).toHaveText("idle");

  // ActionBar has form + profile selector + connect button
  await expect(page.locator("[data-testid='action-bar']")).toBeVisible();
  await expect(page.locator("#session-form")).toBeVisible();
  await expect(page.locator("#profile")).toBeVisible();
  await expect(page.locator("#connect-btn")).toBeVisible();

  // Canvas present
  await expect(page.locator("#frame-canvas")).toBeVisible();

  // Error panel not shown at boot
  await expect(page.locator("[data-testid='error-panel-inner']")).not.toBeVisible();
});

// ── Scenario 2: Connect Success ───────────────────────────────────────────────
// Given: Backend is reachable (mocked).
// Then: State progresses connecting → connected → streaming_ready; telemetry emits.

test("connect success — state progresses to streaming_ready", async ({ page }) => {
  const sessionId = "test-session-42";
  const sessionToken = "tok-test-abc";

  // Mock session creation
  await page.route("**/player/sessions", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: sessionId,
        session_token: sessionToken,
        relay_url: "ws://127.0.0.1:7443",
        stream_id: 777,
        profile: "real-time",
        metrics_url: `/player/sessions/${sessionId}/metrics`,
        websocket_url: `/player/sessions/${sessionId}/ws`,
        correlation_id: "corr-abc",
      }),
    });
  });

  // Mock metrics endpoint
  await page.route(`**/player/sessions/${sessionId}/metrics`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "running",
        frames_received: 10,
        frames_dropped: 0,
        avg_latency_ms: 14.5,
        correlation_id: "corr-abc",
      }),
    });
  });

  // Mock WebSocket — deliver one frame then eos
  await page.routeWebSocket(`**/${sessionId}/ws**`, (ws) => {
    ws.send(
      JSON.stringify({
        type: "frame",
        payload_b64: Buffer.from("test-frame-data").toString("base64"),
        correlation_id: "corr-abc",
      }),
    );
    ws.send(JSON.stringify({ type: "eos" }));
  });

  await page.goto("/");
  await page.click("#connect-btn");

  // State reaches streaming_ready (driven by first frame event)
  await expect(page.locator("#session-status")).toHaveText("streaming_ready", {
    timeout: 5000,
  });

  // Error panel should remain hidden
  await expect(page.locator("[data-testid='error-panel-inner']")).not.toBeVisible();

  // Session ID appears in the status banner
  await expect(page.locator(".status-session-id")).toContainText(sessionId);
});

// ── Scenario 3: Backend Unavailable ──────────────────────────────────────────
// Given: Backend not reachable (mock returns 503).
// Then: State moves to failed; ErrorPanel shows actionable message + retry button.

test("backend unavailable — error panel shown with retry button", async ({ page }) => {
  await page.route("**/player/sessions", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({ status: 503 });
  });

  await page.goto("/");
  await page.click("#connect-btn");

  // State reaches failed
  await expect(page.locator("#session-status")).toHaveText("failed", { timeout: 5000 });

  // ErrorPanel visible with actionable content
  await expect(page.locator("[data-testid='error-panel-inner']")).toBeVisible();
  await expect(page.locator("[data-testid='retry-btn']")).toBeVisible();

  // Error panel contains helpful message
  await expect(page.locator(".error-message")).not.toBeEmpty();
});

// ── Scenario 4: Reset / Retry ─────────────────────────────────────────────────
// Given: In degraded/failed state.
// Then: Clicking Retry → state goes to idle; clicking Connect → connecting again.

test("reset/retry — from failed state returns to idle and can reconnect", async ({ page }) => {
  // First connect attempt fails
  let callCount = 0;
  await page.route("**/player/sessions", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    callCount++;
    if (callCount === 1) {
      await route.fulfill({ status: 503 });
    } else {
      // Second attempt also fails (still no server), but we just need connecting state
      await route.fulfill({ status: 503 });
    }
  });

  await page.goto("/");
  await page.click("#connect-btn");

  // Wait for failed state
  await expect(page.locator("#session-status")).toHaveText("failed", { timeout: 5000 });

  // Click Retry → back to idle
  await page.click("[data-testid='retry-btn']");
  await expect(page.locator("#session-status")).toHaveText("idle", { timeout: 3000 });

  // Can submit the form again → connecting state
  await page.click("#connect-btn");
  await expect(page.locator("#session-status")).toHaveText("connecting", { timeout: 3000 });
});

// ── Scenario 5: CI Determinism ────────────────────────────────────────────────
// The four scenarios above constitute the determinism suite.
// This test confirms the page can be loaded and torn down cleanly twice in succession.

test("ci determinism — page loads cleanly on repeated navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#session-status")).toHaveText("idle");

  // Navigate away and back
  await page.goto("about:blank");
  await page.goto("/");
  await expect(page.locator("#session-status")).toHaveText("idle");
  await expect(page.locator("[data-testid='app-shell']")).toBeVisible();
  await expect(page.locator("[data-testid='error-panel-inner']")).not.toBeVisible();
});
