# Repository Guidelines

## Project Structure & Module Organization
Project Iris is organized as an architecture-first monorepo:
- `services/`: backend components (`transport-core/` in Rust, `iris-server/` in Mojo).
- `apps/`: frontend surfaces (`player-web/` in TypeScript, `control-plane/`).
- `platform/`: shared capabilities (`data/`, `messaging/`, `graph/`).
- `infra/`: deployment and provisioning (`terraform/`, `kubernetes/`).
- `docs/`: architecture, roadmap, platform notes, and runbooks.
- `tests/`: integration and end-to-end suites.

Keep new work inside domain folders; avoid adding product code at repo root.

## Build, Test, and Development Commands
Early-stage commands for repo hygiene:
- `rg --files`: list tracked files quickly.
- `find . -maxdepth 3 -type d | sort`: inspect architecture layout.
- `markdownlint "**/*.md"` (if installed): enforce Markdown consistency.
- `git log --oneline --decorate -n 10`: review recent architectural decisions.

As components mature, add component-local commands in each folder README (for example, Cargo or TypeScript scripts).

## Coding Style & Naming Conventions
- Use `kebab-case` for folders and Markdown files.
- Prefer concise docs with explicit dates for time-sensitive claims (`YYYY-MM-DD`).
- In Rust, Mojo, and TypeScript code, keep modules small and domain-scoped.
- Name ADRs as `adr-XXXX-short-title.md` under `docs/architecture/`.

## Testing Guidelines
- Place cross-service checks in `tests/integration/`.
- Place user-journey/system checks in `tests/e2e/`.
- Validate examples and command snippets before merging.
- Add test strategy notes in component READMEs until unified tooling is established.

## CI/CD Business Risk Control
- Treat GitHub Actions as a business control system, not only an engineering convenience.
- Require automated checks before merge on protected branches to reduce release regressions, incident response cost, and customer trust risk.
- Keep branch protection enabled for default branches with at least:
  - required status checks from GitHub Actions,
  - conversation resolution before merge.
- Pull requests require passing status checks (`repo-gate` and `test`). Required review approvals
  are currently set to **0** during the bootstrap phase; this will be tightened to ≥1 before the
  first external user milestone. See `docs/runbooks/known-issues.md` (GOV-001) for the open item.
- `repo-gate` and `test` are required branch protection contexts for `main` and must pass on every merge path.
- `repo-gate` enforces AGPLv3 SPDX headers (`SPDX-License-Identifier: AGPL-3.0-only`) on newly added core source files under:
  - `services/iris-server/**`
  - `services/transport-core/**`
- Do not bypass failed checks for production-critical scope without explicit, documented approval and a follow-up plan in `docs/runbooks/known-issues.md`.
- For transport/performance-affecting work, preserve reproducible evidence capture (tests, smoke, benchmark artifacts) so release decisions are evidence-based.
- Docs fast-lane uses a controlled nightly sync:
  - push docs-only work to `docs-staging`,
  - GitHub Actions workflow `docs-daily-sync` runs at `22:00 UTC`,
  - the workflow creates/updates a PR from `docs-staging` to `main` only when the diff is limited to `docs/**`.
  - recovery procedure for non-doc drift is documented in `docs/runbooks/docs-fast-lane-recovery.md`.

## Commit & Pull Request Guidelines
- Follow conventional-style commits (`docs:`, `chore:`, `feat:`, `fix:`).
- Keep commits single-purpose and scoped to one concern.
- PRs should include: summary, changed paths, validation steps, and follow-up work.
- Link roadmap or ADR docs when a change introduces architectural impact.

## Security & Configuration Tips
Do not commit secrets or cloud credentials. Use placeholders such as `<PROJECT_ID>` and keep environment-specific values in ignored `.env` files.

## Product Governance Docs
- Keep business and policy docs current when changing product posture:
  - `docs/policy/licensing-strategy.md`
  - `docs/policy/data-governance-baseline.md`
  - `docs/strategy/market-wedge.md`
