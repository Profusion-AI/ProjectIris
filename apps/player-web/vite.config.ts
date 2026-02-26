// SPDX-License-Identifier: Apache-2.0
import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/player": {
        target: "http://127.0.0.1:8080",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
