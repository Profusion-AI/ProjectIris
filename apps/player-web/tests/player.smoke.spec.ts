// SPDX-License-Identifier: Apache-2.0
import { test, expect } from "@playwright/test";

test("player page loads with required DOM elements", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle("Iris Player Web MVP");
  await expect(page.locator("#frame-canvas")).toBeVisible();
  await expect(page.locator("#session-form")).toBeVisible();
  await expect(page.locator("#session-status")).toHaveText("idle");
  await expect(page.locator("#profile")).toBeVisible();
});
