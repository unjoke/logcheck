---
comet_change: enhance-visual-reports-and-log-samples
role: technical-design
canonical_spec: openspec
---

# Enhance Visual Reports And Log Samples Design

## Context

The OpenSpec change `enhance-visual-reports-and-log-samples` extends the local Flask dashboard and bundled log samples. OpenSpec remains the canonical requirements source. This document fixes the implementation shape for build planning.

The current web frontend is static JavaScript served from `logcheck/web_static/`. It already has simple chart entry points in `renderCharts`, `chartSourceDistribution`, `chartTimeDistribution`, and `chartSeverityDistribution`, plus an attacker IP summary path. The backend already returns serialized analysis results from local sample files and uploads, and `samples/access1.log` is a large CTF-style Apache access log containing encoded SQL injection activity from one source address.

## Architecture

The implementation should keep the existing Flask and static JavaScript architecture.

Data flow:

1. The user selects bundled samples or local files in the browser.
2. `POST /api/analyze` runs local analysis through `analyze_logs`.
3. The frontend receives the serialized payload and stores the latest successful analysis id.
4. A new frontend chart-data adapter transforms `payload.findings`, `payload.summary`, and `payload.insights` into renderer-neutral datasets.
5. A renderer layer draws the charts from those datasets and leaves readable fallback summaries in the DOM.

The backend should only change if sample metadata or test fixtures require it. Chart aggregation should start in the frontend because the browser already receives all fields needed for the requested report charts.

## Chart Renderer Decision

Use a short spike to compare Apache ECharts and Chart.js against the existing payload, then select one. The recommended default is ECharts:

- It works as a standalone browser asset without moving the app to React.
- It supports dataset-driven charts and time axes well enough for source IP, time bucket, severity, rule, and file contribution charts.
- It keeps the build path simple if vendored as a reviewed static file.

Chart.js remains the fallback if the spike shows a smaller or cleaner integration. Recharts and Nivo should be documented as rejected for this build because they assume a React component stack and would turn this change into a frontend migration.

The selected renderer must be isolated behind functions that accept renderer-neutral datasets. Tests should validate dataset generation without requiring the chart library.

## Frontend Components

Add a small chart-data adapter layer near the existing chart functions in `app.js`.

Adapter outputs:

- `sourceIpRows`: top source addresses ranked by finding count, carrying max severity and related rules.
- `timeBucketRows`: findings grouped by minute or hour depending on timestamp span, plus an unknown timestamp count.
- `severityRows`: severity counts derived from summary when present and findings as fallback.
- `ruleRows`: top rule ids by finding count.
- `sourceFileRows`: source file or sample contribution counts.

Renderer responsibilities:

- Render each chart from adapter output.
- Cap crowded dimensions with a top-N limit and aggregate the remainder as "Other".
- Keep the visible text/table fallback synchronized with the chart data.
- Catch renderer failures and leave the fallback summaries intact.
- Avoid adding any active security actions, external report targets, blocking controls, scan controls, or domain/IP action buttons.

## Sample Log Design

Use `samples/access1.log` as seed data, but do not mutate it directly unless a later task intentionally replaces it. Add curated sample files only when they are final and useful for tests or demos.

Access-log variants should:

- Preserve parser-supported Apache combined-log format.
- Vary source IPs, timestamps, request paths, status codes, response sizes, and user agents.
- Keep exploit-like payloads as inert text.
- Include enough timestamp and source-address diversity for visual source IP and time charts.

Auth and application samples should remain compact but cover brute force, invalid users, unauthorized access, permission denial, suspicious command execution, and normal background activity.

Temporary scripts and generated scratch outputs must live under `worktmp/` by default. Only curated final `.log` files should be promoted into `samples/`.

## Testing Strategy

Python tests:

- Verify `/api/samples` lists representative bundled samples.
- Verify curated samples parse without crashing and produce findings.
- Verify access samples produce multiple source addresses and timestamped findings suitable for charts.
- Verify sample analysis does not perform network access and treats payloads as text.

Frontend and browser checks:

- Validate chart-data adapter outputs for empty findings, missing timestamps, mixed severities, and top-N aggregation.
- Run the local Flask app and verify desktop and mobile chart rendering.
- Verify offline runtime behavior by ensuring charts are loaded from local static assets and no external chart scripts are requested.
- Verify fallback text/table summaries remain visible or recoverable if the renderer is unavailable.

## Risks

- A chart library can increase static asset size. Mitigation: compare ECharts and Chart.js in the spike and keep renderer fallback summaries.
- Large `access1.log` can create unreadable charts. Mitigation: aggregate top-N categories and long-tail rows.
- Timestamp formats differ across log types. Mitigation: bucket only normalized timestamps and count unknown timestamps separately.
- Synthetic samples can become unrealistic. Mitigation: keep them parser-supported, compact, deterministic, and scenario-named.

## Build Boundaries

This build should not migrate to React, introduce remote network targets, add external runtime fetches, or modify unrelated archived OpenSpec changes. It may update the existing OpenSpec delta specs only for small missing acceptance cases discovered during implementation.
