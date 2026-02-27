// SPDX-License-Identifier: Apache-2.0
import { PlayerEmbedPage } from "./ui/PlayerEmbedPage.js";

const root = document.getElementById("player-root");
if (!root) {
  throw new Error("Missing #player-root mount point");
}

const page = new PlayerEmbedPage(root);
page.mount();
