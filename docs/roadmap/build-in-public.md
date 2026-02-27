# Build in Public Roadmap

## Guiding Principle
Efficiency via Elimination: validate the hardest system boundary first and avoid premature product complexity.

## Milestones
1. Week 1: `iris-transport-core` (Rust, AGPLv3)
Action: build a MoQ relay and CLI demo with latency profiles (real-time vs buffered).
Goal: prove tunable-latency transport is viable.

2. Week 3: `iris-server` (Mojo, AGPLv3)
Action: expose a simple HTTP endpoint with matrix-heavy compute path and publish benchmark vs Python baseline.
Goal: validate Mojo backend viability and performance narrative.

3. Week 5: `iris-player-web` (TypeScript, Apache 2.0)
Action: ship minimal web player integration path for protocol adoption.
Goal: create an embeddable developer-facing entry point.

4. Week 7: "Escaping the Bandwidth Tax" manifesto
Action: publish neural compression strategy and economics model.
Goal: attract ML contributors and explain long-term infra economics.

5. Next: `iris-graph` on Spanner
Action: define graph-first schema and high-volume comment simulation.
Goal: prove social-state scalability and linear behavior under load.

## Delivery Governance Baseline
- CI/CD and branch protection are required risk controls for each public milestone.
- Milestones are not considered complete until automated checks are passing and merge protections are enforced on `main`.
- Licensing, privacy, and market positioning docs are tracked alongside engineering milestones:
  - `docs/policy/licensing-strategy.md`
  - `docs/policy/data-governance-baseline.md`
  - `docs/strategy/market-wedge.md`

## Readiness Snapshot (2026-02-27)
- Week 1 (`iris-transport-core`): `In Progress / Operationally Gated`.
  - Delivered: Rust relay/sender/receiver binaries, framing/profile logic, smoke and CI baseline.
  - Remaining: benchmark evidence discipline per release, authn/authz and abuse-resistance hardening, additional protocol robustness/interoperability coverage.
- Week 2 (governance and CI controls): `Delivered`.
  - Delivered: branch protection wiring (`repo-gate` + `test`), repo guard checks, CI policy enforcement, docs fast-lane automation.
  - Open: GOV-001 — required PR approval count at 0; resolution required before external-user milestone (see `docs/runbooks/known-issues.md`).
- Week 3 (`iris-server`): `GO (Conditional), implementation merged`.
  - Delivered: FastAPI runtime bootstrap, OpenAPI contract validation, benchmark harness, session/token orchestration endpoints.
  - Remaining: auth token lifecycle tightening, guardrail test coverage extension.
- Week 4 (hardening): `Delivered`.
  - Delivered: session TTL/revocation, concurrency limits, internal control token hardening, benchmark artifact discipline, expanded e2e checks, 72h review remediation complete.
- Week 5 (`iris-player-web`): `GO (Delivered, Conditional)`.
  - Delivered: formal npm project with Apache-2.0, Vite dev/build/typecheck workflow, Playwright browser smoke, `player-web-ci` pipeline, server-side e2e.
  - Remaining: evolve DOM smoke test to full live-session browser journey, developer embedding guide.
- Ops open items:
  - CI: `transport-core-ci` push trigger now always runs on `main` commits (fixed 2026-02-27); `test` check will be consistently visible.
  - Docs: `docs-daily-sync` nightly auto-PR blocked by GitHub Actions PR-creation permission (repo setting). Manual `gh pr create --base main --head docs-staging` required when a docs delta exists until the setting is enabled.

## Readiness Snapshot (2026-02-25) — superseded by 2026-02-27 snapshot above
- Week 1 (`iris-transport-core`): `In Progress / Operationally Gated`.
- Completed:
  - Rust transport PoC scaffold and CLI flows added under `services/transport-core/`.
  - GitHub Actions workflow `transport-core-ci` is active and passing on `main`.
  - `main` protection now requires CI status checks `repo-gate` and `test` plus PR review controls.
- Remaining for transport hardening:
  - benchmark evidence discipline across releases,
  - authn/authz and abuse-resistance hardening,
  - additional protocol robustness/interoperability coverage.

## Week 3 Start Decision (`iris-server`)
- Decision: `GO (Conditional)`.
- Scope allowed now:
  - simple HTTP endpoint in Mojo,
  - matrix-heavy compute benchmark path,
  - published benchmark against Python baseline.
- Non-negotiables while executing Week 3:
  - keep transport hardening backlog explicit and tracked,
  - maintain green CI on `main`,
  - document residual risk and rollback notes for production-critical changes.

## Sprint MVP Execution Plan (2026-02-25)
- Runtime decision: `Python FastAPI` is approved as a temporary strawman for sprint delivery speed.
- Delivery slices:
  1. P0: CI baseline stabilization and benchmark evidence resiliency.
  2. P1: `iris-server` runtime + internal transport orchestration bridge.
  3. P2: `player-web` vertical slice + integration/e2e evidence gates.
- Non-negotiable boundaries for strawman phase:
  - artifact-backed persistence only (`docs/evidence/**`), no DB,
  - internal control endpoints require signed bearer token,
  - allowlist-only subprocess orchestration (`iris-relay`, `iris-send`, `iris-recv`),
  - correlation ID and artifact path must propagate end-to-end.

### Mojo Cutover Triggers
- Trigger 1: move `BenchmarkBackend` from Python when MLIR-target execution is required and Python serialization overhead blocks benchmark progression.
- Trigger 2: move session-control runtime from FastAPI when concurrency control degrades at sustained >400 session-control requests per core.
- Trigger 3: backend cutover may proceed only with API contract parity, unchanged evidence schema, and side-by-side benchmark publication.

## Week 5 Delivery Entry (`iris-player-web`) — 2026-02-26
- Decision: `GO (Delivered, Conditional)`.
- Delivery objective:
  - ship a minimal, embeddable web integration path that TypeScript developers can run against `iris-server`.
- Scope delivered:
  - `apps/player-web` is now a formal npm project with Apache-2.0 license metadata and lockfile-backed installs.
  - Vite-based local developer workflow is active (`dev`, `build`, `typecheck`) with `/player` HTTP + WebSocket proxy to `iris-server` on port `8080`.
  - Browser smoke validation is in place via Playwright and enforced in CI.
  - Manual generated file drift was removed (`src/client.js` deleted; source of truth is `src/client.ts`).
  - `player-web-ci` now validates npm install, TypeScript checks, production build, browser smoke, and Python e2e flow.
- Verification evidence:
  - PR #7 merged to `main` on 2026-02-26 with green required checks (`repo-gate`, `test`) and green player-web smoke pipeline.
  - Docs fast-lane health was repaired and `docs-daily-sync` was validated successful after repair.
- Residual risk:
  - current browser test is a smoke test and not yet a full live-session browser journey.
  - transport and server remain prototype-grade with hardening backlog active (correctness/performance/security depth still expanding).

## Weeks 1-4 Build Summary (Layman View)
- Week 1: built the transport engine (`iris-transport-core`).
  - Layman translation: the "high-speed road" for frames now exists and can run in low-latency or buffered mode.
  - Technical outcome: relay/sender/receiver binaries, framing/profile logic, smoke test path, and CI baseline for transport.
- Week 2: built release controls and guardrails around delivery.
  - Layman translation: merged code now has safety gates before it can reach `main`.
  - Technical outcome: branch protection wiring, repo guard checks, CI policy enforcement, and docs fast-lane automation.
- Week 3: built server orchestration (`iris-server`) as a sprint runtime.
  - Layman translation: a control tower now starts sessions, manages tokens, and exposes metrics/health.
  - Technical outcome: FastAPI runtime bootstrap, OpenAPI contract validation, benchmark harness, and transport orchestration endpoints.
- Week 4: hardened reliability and abuse resistance for server + transport integration.
  - Layman translation: the system now has stronger brakes and guardrails under stress and misuse.
  - Technical outcome: session TTL/revocation controls, concurrency limits, internal control token hardening, benchmark artifact discipline, and expanded integration/e2e checks.

## Technical Blueprint: Next Execution Window
- Track A: transport correctness and performance hardening (`services/transport-core/**`).
  - Deliverables:
    - add failure-mode coverage for disconnects, packet loss, and relay restarts.
    - keep benchmark evidence generation reproducible per change and release candidate.
    - expand interoperability behavior checks toward MoQ draft alignment boundaries.
  - Exit criteria:
    - no critical protocol correctness gaps open for release candidate path.
    - benchmark artifacts produced and validated in CI for transport-affecting changes.
- Track B: `iris-server` production-path controls (`services/iris-server/**`).
  - Deliverables:
    - tighten internal auth token lifecycle and rotation handling.
    - extend guardrail tests for session/subprocess limits and token-expiry edge cases.
    - maintain contract-first changes only (OpenAPI + internal control spec updates together).
  - Exit criteria:
    - security/control regressions blocked in CI.
    - each critical-path change includes verification commands and residual-risk notes.
- Track C: player integration maturity (`apps/player-web/**`).
  - Deliverables:
    - evolve from DOM smoke test to live browser flow against running `iris-server`.
    - publish concise developer embedding guide with expected local/CI commands.
    - keep Apache boundary clean and avoid AGPL path leakage into player package.
  - Exit criteria:
    - browser e2e covers session start, frame render, and metrics state transitions.
    - CI catches regressions in both build output and runtime integration assumptions.
- Track D: governance and operating discipline (`docs/**`, repo settings).
  - Deliverables:
    - close GOV-001 by raising required PR approvals to >=1 before external-user phase.
    - keep docs fast-lane docs-only and healthy with nightly verification.
    - maintain known-issues log entries for any intentional YELLOW shipments.
  - Exit criteria:
    - branch policy and docs match actual enforcement state.
    - no unresolved ORANGE/RED items carried without Kyle acknowledgment.
