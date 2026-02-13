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
