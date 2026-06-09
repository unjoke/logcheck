# Add Local Visualization Charts Verification

Change: `add-local-visualization-charts`
Branch: `codex/add-local-visualization-charts`
Verification mode: full

## Scope Review

- Added passive privilege-escalation findings for sudo/su failure and sensitive/admin path access.
- Added `samples/incident.log` as a richer local demo sample.
- Added the web `Visual report` region with source/entity, time/evidence-order, and severity charts.
- Kept the frontend local-only: no new remote API route, CDN, domain input, network scan, blocking, exploitation, or external reporting control.

## Automated Checks

- `python -m pytest tests -q`
  - Result: PASS, `76 passed in 0.58s`
- `node --check logcheck/web_static/app.js`
  - Result: PASS
- `openspec validate add-local-visualization-charts --strict`
  - Result: PASS, change is valid
- `python -m logcheck.cli samples/incident.log --out-dir worktmp/incident-verify --format json --format markdown`
  - Result: PASS
  - Events: 12
  - Findings: 27
  - Severity counts: `{'medium': 13, 'high': 13, 'critical': 1}`
  - Top suspicious sources include `192.0.2.10`, `198.51.100.7`, and unknown/root-derived evidence.

## Browser Verification

Local web app was started on `http://127.0.0.1:8768` for verification.

After selecting `incident.log` and running analysis:

- Run state: `Complete`
- Findings metric: `27`
- High priority metric: `14`
- Chart count: `3 charts`
- Chart rows rendered: `12`
- Chart titles rendered:
  - `Source/entity frequency`
  - `Time/evidence order`
  - `Severity distribution`
- Source chart rows included:
  - `192.0.2.10 13`
  - `198.51.100.7 8`
  - `root 6`
- Severity chart rows included:
  - `critical 1`
  - `high 13`
  - `medium 13`
- `behavior.privilege_escalation` was visible in the analyzed finding queue/detail content.
- Layout check at the active browser width: `scrollWidth` equaled `clientWidth` (`584`), so no horizontal overflow was observed.

The browser text search saw `url` only because incident evidence contains a `curl http://...` command string. No URL/domain input, network scan, blocking, exploitation, or external reporting control was added.

## Result

PASS. The implementation satisfies the OpenSpec scenarios and the technical design acceptance criteria.

