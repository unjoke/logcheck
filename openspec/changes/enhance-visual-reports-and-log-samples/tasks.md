## 1. Chart Library Spike

- [ ] 1.1 Prototype Apache ECharts against the current local analysis payload using bundled/static delivery only.
- [ ] 1.2 Prototype Chart.js against the current local analysis payload, including any required local time-axis adapter.
- [ ] 1.3 Record the selected renderer and the rejected alternatives in implementation notes or the final design update.

## 2. Visual Report Data Model

- [ ] 2.1 Add frontend chart-data adapter functions for top source IPs, time buckets, severity counts, rule counts, and source-file contribution.
- [ ] 2.2 Add deterministic tests or browser-verifiable fixtures for chart-data aggregation, including missing timestamps and empty findings.
- [ ] 2.3 Preserve readable text/table summaries for every charted metric.

## 3. Frontend Report Upgrade

- [ ] 3.1 Integrate the selected renderer into `logcheck/web_static/` without runtime external network fetches.
- [ ] 3.2 Render source IP, time distribution, severity, rule, and source contribution charts from the latest successful analysis result.
- [ ] 3.3 Ensure chart rendering failure leaves the report reviewable through fallback summaries.
- [ ] 3.4 Verify the visual report on desktop and mobile local browser viewports.

## 4. Bundled Log Samples

- [ ] 4.1 Review existing `samples/access1.log`, `auth.log`, `app.log`, and `incident.log` for coverage gaps.
- [ ] 4.2 Create deterministic access-log variants from `access1.log` with diverse source IPs, timestamps, paths, status codes, and user agents.
- [ ] 4.3 Add or curate representative auth and application-security logs for local sample analysis.
- [ ] 4.4 Keep generation scripts and intermediate files under `worktmp/`, promoting only curated sample logs into `samples/`.

## 5. Verification

- [ ] 5.1 Add or update tests proving bundled samples are listed by the web API and parse into findings useful for charts.
- [ ] 5.2 Run the relevant Python test suite for parsing, sample discovery, serialization, and web frontend behavior.
- [ ] 5.3 Run local Flask browser verification to confirm charts render offline and no active external controls are introduced.
- [ ] 5.4 Update OpenSpec task checkboxes as implementation tasks complete.
