# Docs Fast-Lane Recovery

Use this runbook when `docs-daily-sync` fails because `docs-staging` contains non-`docs/**` changes.

## Why This Fails
The workflow `.github/workflows/docs-daily-sync.yml` only allows diffs rooted in `docs/**`.
If any other path appears in `origin/main..origin/docs-staging`, the sync job exits with failure by design.

## Detection
1. Check latest docs sync runs:
```bash
cd /home/kyle/ProjectIris
gh run list -R Profusion-AI/ProjectIris --workflow docs-daily-sync --limit 5
```
2. Inspect the failing run log and confirm the non-doc file list:
```bash
cd /home/kyle/ProjectIris
gh run view <run_id> -R Profusion-AI/ProjectIris --log
```

## Recovery Procedure
1. Create a backup pointer before repair:
```bash
cd /home/kyle/ProjectIris
git fetch origin
git switch -c backup/docs-staging-$(date -u +%Y%m%d-%H%M%S) origin/docs-staging
```
2. Reset `docs-staging` scope to current `main` and re-apply docs-only changes:
```bash
cd /home/kyle/ProjectIris
git switch -C docs-staging origin/main
# re-apply only docs/** commits/cherry-picks as needed
```
3. Push repaired branch:
```bash
cd /home/kyle/ProjectIris
git push --force-with-lease origin docs-staging
```
4. Validate fast-lane:
```bash
cd /home/kyle/ProjectIris
gh workflow run docs-daily-sync -R Profusion-AI/ProjectIris
gh run list -R Profusion-AI/ProjectIris --workflow docs-daily-sync --limit 3
```

## Guardrails
- Keep `docs-staging` docs-only (`docs/**`).
- Route all non-doc changes through normal PR flow to `main`.
- Do not disable the non-doc block in workflow logic.
