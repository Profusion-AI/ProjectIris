# ADR-0001: Runtime and Deployment Baseline

## Status
Accepted (2026-02-13)

## Context
Iris is transport-first, and the first milestone (`iris-transport-core`) requires MoQ over QUIC/UDP with tunable latency. The project also needs low operational overhead and budget discipline.

## Decision
Use a phased runtime strategy with Terraform as the infra source of truth:
- Local development: direct binaries and containerized test harnesses.
- Shared dev/staging: GKE Autopilot for UDP-capable workloads and service isolation.
- Deployment config: Kubernetes manifests in `infra/kubernetes/`, provisioned via `infra/terraform/`.
- CI/CD: GitHub Actions driving lint/test/build and environment promotion.

## Why This Decision
- QUIC/UDP transport requirements make generic HTTP-only serverless paths a poor default.
- GKE Autopilot reduces cluster operations compared with self-managed Kubernetes.
- Terraform + Kubernetes keeps paths consistent from prototype to production.

## Consequences
- Adds Kubernetes complexity earlier than fully managed HTTP stacks.
- Avoids re-platforming when transport requirements grow.
- Preserves a clear migration path to multi-region global services and Spanner-backed state.
