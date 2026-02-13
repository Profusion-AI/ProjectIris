# Repository Guidelines

## Project Structure & Module Organization
This repository is documentation-first and currently stores content at the root.
- `README.md`: primary architecture overview and core narrative.
- `gcp-spanner-gettingstarted.md`: focused Google Cloud Spanner setup guide.

When adding content, keep one topic per file and use descriptive `kebab-case` names (for example, `moq-latency-notes.md`). Link new documents from `README.md` so readers can discover them quickly.

## Build, Test, and Development Commands
There is no build pipeline or runtime service in this repo. Use lightweight checks:
- `rg --files`: list tracked documentation files.
- `wc -w *.md`: quick word-count pass for concision.
- `markdownlint *.md` (if installed): validate Markdown style and heading consistency.

## Coding Style & Naming Conventions
Write in clear, technical Markdown with short sections and actionable language.
- Use `#`/`##`/`###` ATX headings in a logical hierarchy.
- Prefer fenced code blocks with language tags (for example, ` ```sql `).
- Keep examples copy/paste-ready and scoped to the section topic.
- Use `kebab-case` for file names and avoid spaces.
- Date time-sensitive claims explicitly (for example, “as of 2026-02-13”).

## Testing Guidelines
Testing here means documentation quality checks:
- Run linting (`markdownlint *.md`) before opening a PR.
- Manually verify command snippets and SQL examples for syntax correctness.
- Confirm internal links and filenames resolve correctly after edits.

## Commit & Pull Request Guidelines
Git history is not available in this workspace snapshot, so use a standard convention:
- Commit format: `docs: concise imperative summary` (example: `docs: add spanner trial setup caveats`).
- Keep commits focused on a single document concern.
- PRs should include: purpose, files changed, key reader impact, and any source links for factual updates.

## Security & Configuration Tips
Do not commit secrets, tokens, or real project IDs in examples. Use placeholders like `<PROJECT_ID>` and redact sensitive values in command output.
