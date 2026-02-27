// SPDX-License-Identifier: Apache-2.0

/**
 * Escapes characters that have special meaning in HTML.
 * Must be applied to any untrusted string before interpolating into innerHTML.
 */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}
