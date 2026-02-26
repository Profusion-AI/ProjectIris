# Licensing Strategy (Draft)

Date: 2026-02-26
Owner: Kyle
Support: Codex

## Current Boundary
- Core transport and server code under `services/transport-core/**` and `services/iris-server/**` remains AGPLv3.
- Player web surface under `apps/player-web/**` remains Apache-2.0.

## Operating Model
- Open-core boundary is enforced at repository path level and verified in PR review.
- Derivative works of AGPL components retain AGPL obligations.
- Apache-2.0 player assets are intended for embeddable integration workflows.

## Contributor Guidance
- Contributions to AGPL paths must preserve AGPL SPDX headers.
- Contributions to Apache paths must keep Apache headers and avoid importing AGPL-only code.
- Cross-boundary changes require an explicit licensing note in the PR description.

## Commercial Posture
- Commercial value is expected from operated service quality, transport performance, and integration experience.
- Source availability and protocol clarity are part of the go-to-market trust model.

## Follow-Up
1. Publish contribution FAQ clarifying AGPL vs Apache obligations.
2. Add CI-level path policy checks when multiple licenses expand.
3. Re-review this memo at first paid pilot.
