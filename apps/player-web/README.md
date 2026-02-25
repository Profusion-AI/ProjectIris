# player-web

TypeScript web player integration surface intended for Apache-licensed distribution.

## Scope (MVP)
- Bootstrap player session via `POST /player/sessions`.
- Receive frame events through `/player/sessions/{session_id}/ws`.
- Render frames to `<canvas>`.
- Poll QoS telemetry from `/player/sessions/{session_id}/metrics`.

## Local Run
Serve this folder statically and proxy API/websocket requests to `iris-server` on port `8080`.

Example static server:
```bash
cd /home/kyle/ProjectIris/apps/player-web
python3 -m http.server 5173
```

Then open `http://localhost:5173/index.html`.

## Type Check
```bash
cd /home/kyle/ProjectIris
npx --yes -p typescript@5.7.3 tsc --project apps/player-web/tsconfig.json
```
