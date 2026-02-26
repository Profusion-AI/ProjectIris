# Known Issues Log

Use this log to document accepted known issues when shipping with a `YELLOW` review outcome.

## Policy
A `YELLOW` issue may ship only if this file records:
- impact and blast radius,
- clear owner,
- follow-up plan,
- acknowledgment/decision details.

`ORANGE` and `RED` issues are not tracked as shippable known issues.

## Entry Template
Copy this block for each issue.

```md
## KI-XXXX: Short issue title
- Status: Open | Mitigated | Closed
- Gate outcome: YELLOW
- Owner: @owner
- Date opened: YYYY-MM-DD
- Target resolution: YYYY-MM-DD
- Acknowledged by: Kyle (YYYY-MM-DD)
- Related PR/commit: <link-or-hash>
- Related service/path: <service-or-path>

### Issue summary
One short paragraph describing the defect and current behavior.

### Impact
- User impact:
- Operational impact:
- Security/compliance impact:

### Blast radius
Describe what surfaces are affected and what remains unaffected.

### Why shipping now
Explain why this is acceptable to ship before full resolution.

### Mitigation in place
- Mitigation 1
- Mitigation 2

### Follow-up plan
1. Action item one
2. Action item two
3. Verification step required to close

### Closure criteria
Define objective checks needed to mark this issue Closed.
```

## Active Issues

<!-- Add new entries below this line. -->

## GOV-001: Branch protection approval count below intended pre-external-user posture
- Status: Open
- Gate outcome: YELLOW
- Owner: Kyle
- Date opened: 2026-02-26
- Target resolution: Before external user milestone
- Acknowledged by: Kyle (2026-02-26)
- Related PR/commit: codex/72h-remediation
- Related service/path: GitHub repository settings / `docs/contributing.md`

### Issue summary
`docs/contributing.md` previously stated that required pull request review approvals were an active
branch protection control. GitHub is actually configured with **0 required approvals** during the
current bootstrap phase. The doc has been corrected to reflect actual state. The gap in posture
(0 vs ≥1) is tracked here as an open governance item.

### Impact
- User impact: None (no external users yet).
- Operational impact: PRs can merge without peer review approval; relies on author discipline and
  CI gate checks (`repo-gate`, `test`).
- Security/compliance impact: Low at current stage; elevated before external user exposure.

### Blast radius
Only affects merge-time governance controls for the `main` branch. All automated CI checks remain
required. No production code paths are affected.

### Why shipping now
Project is in pre-external-user bootstrap phase. Kyle has acknowledged the gap and has committed to
tightening the setting before the first external user milestone.

### Mitigation in place
- All merges to `main` require both `repo-gate` and `test` status checks to pass.
- Conversation resolution before merge is enforced.
- Small team with direct communication and self-review discipline.

### Follow-up plan
1. Set GitHub branch protection for `main` to require ≥1 review approval.
2. Update `docs/contributing.md` to remove the "currently set to 0" qualifier.
3. Close this entry with the commit that tightens the setting.

### Closure criteria
GitHub branch protection on `main` shows required approvals ≥1, and `docs/contributing.md`
no longer references the bootstrap exception.
