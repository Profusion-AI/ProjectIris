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
