---
comet_change: add-local-visualization-charts
role: technical-design
canonical_spec: openspec
---

# Local Visualization Charts Technical Design

## Goal

Improve the Logcheck coursework demo by adding local visual report charts, clearer passive privilege-escalation evidence, and a richer bundled incident sample. OpenSpec remains the source of truth for requirements; this document records implementation decisions, risks, and verification strategy.

## Proposed Approach

Use the existing Flask web app and static frontend. Do not add a charting dependency, CDN, or remote data source. The browser will derive chart data from the existing `/api/analyze` response and render small, responsive DOM/CSS charts.

Place a `Visual report` region in the main dashboard column after `Analysis summary` and before `Finding queue`. This keeps the demo flow direct:

```text
Source intake -> Analysis summary -> Visual report -> Finding queue -> Evidence detail
```

Desktop should show the three charts side by side. Mobile should stack them vertically without horizontal overflow.

## Components

### Frontend Markup

Add a `Visual report` panel to `logcheck/web_static/index.html`.

The panel contains three chart slots:
- `Source/entity frequency`
- `Time/evidence order`
- `Severity distribution`

Before analysis, and when no findings exist, the panel shows a clear empty state instead of stale content.

### Frontend Chart Helpers

Add focused helpers in `logcheck/web_static/app.js`:

- `renderCharts(payload)`
- `chartSourceDistribution(findings)`
- `chartTimeDistribution(findings, insights)`
- `chartSeverityDistribution(summary, findings)`
- `renderBarChart(container, rows, options)`

Source/entity rules:
- Prefer `source_address`.
- Fall back to `actor`.
- Fall back to `source_file`.
- Fall back to `unknown`.

Time/evidence-order rules:
- Use `timestamp` when present.
- Otherwise use insight timeline labels or deterministic finding order.
- The fallback should still populate the chart for sample logs with partial timestamps.

Severity rules:
- Use `summary.findings_by_severity` where present.
- Render severities in `critical`, `high`, `medium`, `low` order.

### Styling

Extend `logcheck/web_static/styles.css` with chart-specific classes that match the existing restrained dashboard style. Use stable dimensions, predictable bars, short labels, and responsive grid behavior.

Avoid decorative chart libraries, gradients, external fonts, remote assets, or animated effects that could distract from coursework evidence.

### Privilege-Escalation Detection Presentation

Refine passive rule coverage so privilege escalation is not buried as generic keyword evidence.

Indicators:
- sudo authentication failure
- `su` authentication failure
- sensitive file paths such as `/etc/shadow`
- admin/root paths such as `/root` or `/admin`

Findings should use clear rule IDs or explanations such as `behavior.privilege_escalation` or equivalent wording. They must retain local source file, line number, actor/source address when available, matched evidence, severity reason, and confidence reason.

This remains review-only. No blocking, account modification, firewall update, exploitation, remote access, or system modification is in scope.

### Rich Incident Sample

Add `samples/incident.log` as a bundled local sample for recording and screenshots.

It should include:
- benign login or request activity
- repeated failed SSH login attempts
- invalid user attempts
- unauthorized application access
- sudo or su failure
- sensitive/admin path access
- suspicious command download/execution indicator
- multiple documentation-range source addresses

Use documentation ranges only, such as `192.0.2.0/24`, `198.51.100.0/24`, and `203.0.113.0/24`.

## Data Flow

```text
Local sample/upload
  -> Flask /api/analyze
  -> AnalysisResult serialization
  -> renderResult(payload)
  -> renderCharts(payload)
  -> DOM/CSS charts
```

No new API endpoint is required unless implementation discovers the current payload lacks a required field. If that happens, prefer extending the existing serializer with local-only derived metadata rather than adding another route.

## Error Handling

- No analysis yet: visual report shows a neutral empty state.
- Analysis error: reset charts alongside summary, queue, detail, and insights.
- No findings: charts show no-findings empty state.
- Missing timestamps: time chart uses deterministic evidence-order fallback.
- Long labels: truncate visually while preserving title text or full text where practical.

## Tests

Automated checks:
- Dashboard includes `Visual report`, chart labels, and empty-state text.
- Frontend script includes chart helper names and calls chart rendering from `renderResult` and error/reset paths.
- Fetch targets remain limited to local app endpoints.
- Forbidden remote-control terms remain absent from dashboard controls.
- Privilege-escalation indicators produce clear findings with source context.
- `samples/incident.log` analysis covers brute-force, invalid-user, unauthorized-access, privilege-escalation, suspicious-command, and severity/source chart data.

Manual verification:
- Run the full test suite.
- Run frontend syntax check.
- Start the web app locally.
- Verify desktop and mobile-width layouts have no horizontal overflow or overlapping chart text.
- Record notes/screenshots for course evidence.

## Risks

- Current Linux auth parsing does not create full datetimes from syslog month/day/time. The design therefore requires an evidence-order fallback for the time chart.
- If privilege-escalation findings are implemented as additional keyword rules only, the course demo may still look generic. Prefer a behavior-specific finding or at least a clear rule family label.
- Extra sample findings can make the queue noisy. Keep charts compact and preserve evidence detail for drill-down.

## Acceptance

The design is complete when the dashboard can analyze local samples, show the three visual charts, visibly identify privilege-escalation evidence, and demonstrate all of this from a richer bundled local incident sample without adding remote controls or active response behavior.

