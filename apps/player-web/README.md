# player-web

TypeScript web player integration surface intended for Apache-licensed distribution.

## Scope (MVP)
- Bootstrap player session via `POST /player/sessions`.
- Receive frame events through `/player/sessions/{session_id}/ws`.
- Render frames to `<canvas>`.
- Poll QoS telemetry from `/player/sessions/{session_id}/metrics`.

## Setup

From repository root (`/home/kyle/ProjectIris`):

**Install** (once, generates lockfile):
```bash
cd apps/player-web
npm install
```

## Development

**Dev server** (with `/player/` proxy to iris-server):
```bash
npm run dev
```
Opens at `http://localhost:5173`. iris-server must be running on port 8080.

**Start iris-server** (run from repository root in a separate terminal):
```bash
uvicorn app.main:app --app-dir services/iris-server --port 8080
```

## Build

**Vite build** (produces `dist/`):
```bash
npm run build
```

## Testing

**Browser smoke test** (Playwright headless Chromium):
```bash
npm run test:browser
```
Builds + serves the app preview, then validates built-page DOM. No iris-server required.

**Type check**:
```bash
npm run typecheck
```
