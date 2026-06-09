# Design

## Overview

The web frontend will gain a compact visualization band inside the existing local investigation workspace. The charts will be rendered from the latest analysis result already returned by `/api/analyze`, keeping all computation and rendering local to the browser and Flask app. The same iteration will also make privilege-escalation evidence more explicit and add a richer incident sample so the course demo exercises the charts and rule library with realistic scenarios.

## Architecture

Use a small, local chart renderer in `logcheck/web_static/app.js` with ordinary DOM/CSS or Canvas primitives. This avoids external chart dependencies and preserves the project safety boundary.

Data flow:

```text
Local log files / samples
  -> Flask /api/analyze
  -> existing AnalysisResult serialization
  -> browser state
  -> chart data aggregation + attack-family labels
  -> source, time, severity charts + privilege-escalation callouts
```

## Chart Behavior

Source chart:
- Prefer `source_address` when present.
- Fall back to `actor`, then `source_file`, then `unknown`.
- Show the top entries with counts and labels.

Time chart:
- Use finding `timestamp` when available.
- Fall back to insight timeline labels or finding source order when timestamps are missing.
- Display a deterministic evidence-order distribution for sample logs that do not include parseable dates.

Severity chart:
- Use `summary.findings_by_severity`.
- Preserve the severity ladder `critical`, `high`, `medium`, `low`.
- Show zero/empty state clearly when no findings exist.

Privilege-escalation display:
- Treat sudo authentication failure, `su` authentication failure, sensitive file access, and admin/root path access as privilege-escalation indicators.
- Surface these findings with a clear rule identifier and explanation, not just a generic keyword match.
- Let charts and insights reveal the privilege-escalation family through labels or finding text without adding active response controls.

Richer sample log:
- Add a bundled local incident sample, for example `samples/incident.log`.
- Include benign baseline activity plus brute force, invalid user, unauthorized access, permission denied, sudo/su failure, sensitive path access, and suspicious command download lines.
- Keep sample addresses in documentation ranges such as `192.0.2.0/24`, `198.51.100.0/24`, or `203.0.113.0/24`.

## UI Placement

Add a "Visual report" region near the analysis summary and investigation insights. It should be visible after analysis and have a quiet empty state before analysis. The layout should stack cleanly on mobile width and avoid nested cards.

Recommended layout: place the visual report in the main column after the analysis summary and before the finding queue. Desktop shows three compact charts side by side; mobile stacks them vertically.

## Safety

Charts are read-only local summaries. They do not add URL/domain inputs, remote fetches, scanning, blocking, exploitation, or external reporting. Any browser fetch targets remain local API paths.

## Testing

- Unit-style frontend checks for chart helper names, labels, local-only fetch targets, and empty-state text.
- Web app tests that the dashboard includes the visual report region and excludes forbidden remote-control terms.
- Rule/parser tests for privilege-escalation indicators and rich sample coverage.
- Sample-analysis tests or fixture checks that `samples/incident.log` produces source, time/evidence-order, severity, brute-force, privilege-escalation, and suspicious-command evidence.
- Existing API/export tests must continue to pass.
- Manual browser verification should record desktop and mobile layout metrics and note the chart section.
