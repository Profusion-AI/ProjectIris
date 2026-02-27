# player-web Demo Runbook

> **Audience:** New engineers and demo presenters.
> **Goal:** Run the deterministic player-embed demo in <15 minutes from a clean checkout.
> **Prereqs:** Node 20+, Python 3.11+, Rust toolchain (for iris-server transport binary).

---

## 1. Quick-start (< 5 minutes)

### 1a. Install dependencies (once)

```bash
# From repository root
cd apps/player-web
npm ci
cd ../..
pip install -r services/iris-server/requirements.txt
```

### 1b. Start iris-server

Open **Terminal A**:

```bash
# From repository root
uvicorn app.main:app --app-dir services/iris-server --port 8080
```

Expected output: `Uvicorn running on http://127.0.0.1:8080`

### 1c. Start the player-web dev server

Open **Terminal B**:

```bash
cd apps/player-web
npm run dev
```

Expected output: `➜  Local:   http://localhost:5173/`

### 1d. Open the browser

Navigate to **http://localhost:5173** — you should see the Iris Player scaffold with:

- Status banner showing **idle**
- Profile selector (real-time / buffered)
- **Connect** button

---

## 2. Demo flow (presenter script)

### State 1 — Idle

> "This is the player embed scaffold. It starts in idle state — no session, no stream."

Point to the status banner dot (grey) and the Connect button.

### State 2 — Connecting

> "When a viewer clicks Connect, the client immediately enters the connecting state
> while the session is negotiated with iris-server."

Click **Connect**. Status banner transitions: **idle → connecting**.

### State 3 — Connected / Streaming Ready

> "Once the session is live, we enter connected state. As frames arrive over the
> WebSocket bridge, the player enters streaming_ready and the render surface updates."

Watch status banner transition: **connecting → connected → streaming_ready**.
The canvas will show colour-mapped frame data from the transport core.

Optionally point to the metrics pill (transport mode + latency) that appears once streaming.

### State 4 — Error / Degraded (fallback demo)

If iris-server is not running or the transport fails:

> "When the backend is unavailable, the player moves to a failed state and surfaces
> an actionable error panel — not a silent hang or a raw console error."

Stop iris-server (`Ctrl+C` in Terminal A), then click **Reset** → **Connect**.
Status banner shows **failed**. Error panel appears with a Retry button.

### State 5 — Retry

> "Retry returns the player to idle state. Once iris-server is back, click
> Connect to start a new session."

Click **Retry Connection**. Status → **idle**. Restart iris-server, then click **Connect** again to begin a new session.

---

## 3. Running the acceptance test suite (CI validation)

All 5 acceptance scenarios are covered by Playwright:

```bash
cd apps/player-web

# Type check
npm run typecheck

# Build
npm run build

# Browser tests (5 scenarios, ~3 s total)
npm run test:browser
```

Expected output:

```
5 passed (2.5s)
```

Run Python e2e tests (server-side contract):

```bash
# From repository root
pytest -q tests/e2e/test_player_flow.py
```

Expected output: `4 passed`

---

## 4. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Status stays at **connecting** | iris-server not running | Start iris-server (step 1b) |
| Status shows **failed** immediately | Port 8080 blocked or server error | Check Terminal A for errors |
| Canvas stays dark | Transport binary missing | Run `cargo build` in `services/transport-core` |
| `npm run typecheck` fails | Node version mismatch | Use Node 20 (`node --version`) |
| Playwright tests fail | Need to rebuild | Run `npm run build` before `npm run test:browser` |

---

## 5. Acceptance criteria checklist (Definition of Done)

- [ ] `npm run typecheck` passes with zero errors
- [ ] `npm run build` produces `dist/` cleanly
- [ ] `npm run test:browser` — all 5 scenarios pass
- [ ] `pytest tests/e2e/test_player_flow.py` — 4 tests pass
- [ ] Status banner renders for all states: idle, connecting, connected, streaming_ready, degraded, failed
- [ ] Error panel shows retry button in failed/degraded state
- [ ] Reset returns to idle from any error state

---

## 6. Architecture quick-reference

```
index.html
  └─ src/client.ts         Entry point — mounts PlayerEmbedPage
       └─ src/ui/
            ├─ types.ts          PlayerSessionState, PlayerStatusModel, PlayerAction
            ├─ store.ts          State machine (reducer + pub/sub)
            ├─ AppShell.ts       Outer layout skeleton
            ├─ StatusBanner.ts   State dot + label
            ├─ MetricPill.ts     Transport mode + latency chips
            ├─ ErrorPanel.ts     Error display + retry button
            ├─ ActionBar.ts      Profile selector + Connect/Reset buttons
            └─ PlayerEmbedPage.ts  Orchestrates everything; owns session lifecycle
```

State transitions:

```
idle ──[CONNECT_REQUEST]──► connecting ──[CONNECT_SUCCESS]──► connected ──[STREAM_READY]──► streaming_ready
                                │                                                                │
                           [FAILURE]                                                        [DEGRADE_NOTICE]
                                │                                                                │
                                ▼                                                                ▼
                             failed ◄─────────────────────────────────────────────────── degraded
                                │
                            [RESET]
                                │
                                ▼
                              idle
```
