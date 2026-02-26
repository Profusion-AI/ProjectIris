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

## Readiness Snapshot (2026-02-25)
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
