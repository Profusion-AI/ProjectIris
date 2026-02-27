# player-web

TypeScript web player integration surface — player-embed UI scaffold with deterministic
demo states and CI-backed browser validation.

## Architecture

```
src/client.ts           Entry point; mounts PlayerEmbedPage onto #player-root
src/ui/
  types.ts              State contract types (PlayerSessionState, PlayerStatusModel, …)
  store.ts              State machine — reducer + pub/sub
  AppShell.ts           Outer layout skeleton
  StatusBanner.ts       Session state dot + label
  MetricPill.ts         Transport mode + latency chips
  ErrorPanel.ts         Actionable error display + retry
  ActionBar.ts          Profile selector + Connect/Reset buttons
  PlayerEmbedPage.ts    Lifecycle orchestrator; owns session API calls
```

### Session state lifecycle

```
idle → connecting → connected → streaming_ready
                └─► degraded / failed → (retry) → idle
```

## Setup

From repository root:

```bash
cd apps/player-web
npm ci          # install (uses committed package-lock.json)
```

## Development

**Start iris-server** (separate terminal, from repository root):

```bash
uvicorn app.main:app --app-dir services/iris-server --port 8080
```

**Dev server** (proxies `/player/` to iris-server on port 8080):

```bash
npm run dev     # http://localhost:5173
```

Expected UI states once iris-server is running:
1. **idle** — page loads, no session
2. **connecting** — Connect clicked, POST /player/sessions in flight
3. **connected** — session created, WebSocket opened
4. **streaming_ready** — first frame received via WebSocket
5. **failed** — backend unreachable; ErrorPanel with Retry button shown
6. **degraded** — partial failure (e.g. WS error mid-stream); Retry available

## Type check

```bash
npm run typecheck
```

## Build

```bash
npm run build   # outputs to dist/
```

## Testing

**Browser acceptance tests** (5 scenarios, Playwright headless Chromium):

```bash
npm run test:browser
```

Scenarios covered:
1. Boot Smoke — scaffold renders with idle state, no backend required
2. Connect Success — mocked backend; state progresses to `streaming_ready`
3. Backend Unavailable — 503 mock; `failed` state + ErrorPanel shown
4. Reset/Retry — retry from failed → idle → reconnects
5. CI Determinism — repeated navigation loads cleanly

**Python e2e tests** (server-side session contract, from repository root):

```bash
pytest -q tests/e2e/test_player_flow.py
```

## Demo runbook

See [`docs/runbooks/player-web-demo.md`](../../docs/runbooks/player-web-demo.md)
for the full presenter script, troubleshooting table, and DoD checklist.
