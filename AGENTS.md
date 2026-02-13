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

## Commit & Pull Request Guidelines
- Follow conventional-style commits (`docs:`, `chore:`, `feat:`, `fix:`).
- Keep commits single-purpose and scoped to one concern.
- PRs should include: summary, changed paths, validation steps, and follow-up work.
- Link roadmap or ADR docs when a change introduces architectural impact.

## Security & Configuration Tips
Do not commit secrets or cloud credentials. Use placeholders such as `<PROJECT_ID>` and keep environment-specific values in ignored `.env` files.
