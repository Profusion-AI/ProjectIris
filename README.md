# Project Iris

Project Iris is a build-in-public effort to prototype a transport-first video platform based on the 2026 greenfield stack thesis.

## Current Focus
- Prove tunable latency with MoQ over QUIC before building product surfaces.
- Prioritize Rust, Mojo, and TypeScript (Python only as a fallback).
- Keep architecture and operational decisions documented from day one.

## Repository Layout
- `apps/`: user-facing applications (`player-web/`, `control-plane/`).
- `services/`: backend services and protocol components (`transport-core/`, `iris-server/`).
- `platform/`: shared data/messaging contracts and social graph assets.
- `infra/`: provisioning and deployment config (`terraform/`, `kubernetes/`).
- `docs/`: architecture, roadmap, platform notes, and runbooks.
- `tests/`: integration and end-to-end test plans.

## Roadmap (Initial)
1. `iris-transport-core` (Rust + Quinn/Tokio, AGPLv3)
2. `iris-server` (Mojo API benchmark, AGPLv3)
3. `iris-player-web` (TypeScript frontend player, Apache 2.0)
4. "Escaping the Bandwidth Tax" manifesto
5. `iris-graph` schema and scale demo on Spanner

See `docs/roadmap/build-in-public.md` for milestone detail and `docs/architecture/adr-0001-runtime-and-deployment.md` for the deployment decision.
