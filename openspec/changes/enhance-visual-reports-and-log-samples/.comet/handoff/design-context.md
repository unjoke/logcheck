# Comet Design Handoff

- Change: enhance-visual-reports-and-log-samples
- Phase: design
- Mode: compact
- Context hash: d03030ac5d48624dd6bca915e7fd70f692756b1968b2184340c049eed5f3e1b3

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/enhance-visual-reports-and-log-samples/proposal.md

- Source: openspec/changes/enhance-visual-reports-and-log-samples/proposal.md
- Lines: 1-30
- SHA256: e46e3b29e9aa4e3c30b5e7b01213b6a8c5d43155b369c8108d861e870ae50786

```md
## Why

The current web report already surfaces findings, but the visual reporting surface is still too thin for quickly explaining attack source concentration and time-based bursts. The project also needs richer bundled log samples so the frontend charts and parser behavior can be demonstrated without relying on external targets.

## What Changes

- Upgrade the web frontend report area with clearer visual analytics for attack source IP statistics, time distribution, severity, rule mix, and file/sample contribution.
- Add a small charting-library spike that compares common frontend visualization options and implements the chosen local-only chart renderer behind the existing dashboard flow.
- Expand bundled sample logs by using the existing `samples/access1.log` as the seed for CTF-style access-log scenarios and by adding or curating common auth/application/access examples.
- Keep all analysis, visualization, and sample selection local; no remote scanning, external reporting, blocking, or active attack workflow is introduced.
- Add tests or fixtures that prove the sample logs are discoverable, parseable, and useful for visual report scenarios.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend`: Add visual report requirements for chart-driven attack source and time-distribution analysis.
- `log-ingestion`: Add bundled sample-log requirements for representative access/auth/application examples and generated variants based on `access1.log`.

## Impact

- Frontend files under `logcheck/web_static/`, especially existing chart functions in `app.js` and their supporting markup/styles.
- Local web API sample listing and analysis flow in `logcheck/webapp.py` if sample metadata or grouping is needed.
- Sample data under `samples/`, with temporary generation scripts or scratch outputs kept under `worktmp/` by default.
- Tests covering sample discovery/parsing and frontend serialization or chart-data behavior.
- Potential frontend dependency decision: Apache ECharts, Chart.js, or a lighter existing DOM/SVG approach, selected for local static delivery and maintainability.
```

## openspec/changes/enhance-visual-reports-and-log-samples/design.md

- Source: openspec/changes/enhance-visual-reports-and-log-samples/design.md
- Lines: 1-83
- SHA256: a3a8113e0179c0cbb4b280ddcbf98c5eaae07cecf2724a319749c1a41257fa3a

[TRUNCATED]

```md
## Context

The web frontend is a static local dashboard served by Flask. It already computes simple chart rows in `logcheck/web_static/app.js` through `renderCharts`, `chartSourceDistribution`, `chartTimeDistribution`, and `chartSeverityDistribution`, and it receives normalized findings plus insights from the local analysis endpoint. The `samples/` directory already includes `access1.log`, `auth.log`, `app.log`, and `incident.log`; `access1.log` is a dense CTF-style Apache combined-log SQL injection trace.

External research points to four common visualization choices:

- Apache ECharts: strong standalone browser library, dataset/data-transform support, time axes, responsive dashboards, and downloadable static bundle support.
- Chart.js: compact and popular, with cartesian/time axes, but time scales require a date adapter.
- Recharts: composable React charting library built around React components.
- Nivo: React/D3 component suite with rich charts, but it implies a React stack.

Because this project is static JavaScript rather than React, the practical spike should compare ECharts and Chart.js first, while documenting Recharts/Nivo as non-primary options unless the frontend is later rebuilt in React.

## Goals / Non-Goals

**Goals:**

- Make the local web report clearly answer: which source IPs generated the most findings, when did activity cluster, which severities/rules dominate, and which selected files contributed evidence.
- Introduce chart rendering through a maintainable local static asset or a minimal fallback that works offline after install.
- Derive chart datasets from existing serialized analysis results instead of adding remote calls or backend-only aggregation unless frontend performance requires it.
- Expand bundled local log examples with representative access, auth, and application scenarios, including generated variants based on `access1.log`.
- Keep generated temporary files and one-off scripts under `worktmp/` unless a generated sample is intentionally promoted into `samples/`.

**Non-Goals:**

- No remote scanning, exploit execution, traffic generation against real domains, external reporting endpoint, or active blocking workflow.
- No wholesale React/Vite rebuild as part of this change.
- No dependency on internet availability at runtime.
- No ingestion of large third-party datasets directly into the repository without explicit review.

## Decisions

### Decision 1: Prefer an offline static chart bundle spike

The implementation should prototype ECharts and Chart.js with the existing dashboard data shape and choose one. ECharts is the recommended first attempt because its dataset model separates data from chart configuration, supports transforms, and can be saved as a static browser file. Chart.js is the fallback if bundle size or styling integration is better, with the known cost that time-series rendering needs a date adapter.

Alternatives considered:

- Keep hand-built DOM/SVG bars only: lowest dependency risk, but weaker for timeline interaction and multi-chart maintenance.
- Recharts or Nivo: capable, but they fit React applications and would add framework migration cost.

### Decision 2: Build a chart-data adapter inside the frontend

The frontend should normalize the analysis payload into chart-friendly series in one small adapter layer, then pass those datasets to the selected renderer. This keeps chart code isolated from raw findings and makes unit-style browser tests easier.

The adapter should produce at least:

- Top source addresses by finding count and highest severity.
- Time buckets by hour or minute, depending on available timestamps and span.
- Severity counts.
- Rule counts.
- Source file/sample contribution counts.

### Decision 3: Preserve accessible tabular summaries

Charts should not be the only representation. Each visual report section should keep or expose a compact text/table summary so findings remain readable if the chart library fails to load, if a browser canvas/SVG issue occurs, or if a user relies on non-visual review.

### Decision 4: Generate curated local samples from safe seeds

Sample expansion should start from existing local files and public format knowledge rather than downloading large raw datasets. `samples/access1.log` can seed generated variants that vary timestamps, source IPs, status codes, user agents, and payload families while remaining inert text. Common log examples should follow Apache common/combined format, auth failure patterns, and generic application security messages.

## Risks / Trade-offs

- New chart dependency increases static asset size -> vendor a reviewed minified file or keep a no-dependency fallback if the spike shows little value.
- Time parsing can be inconsistent across log formats -> bucket only normalized timestamps from parsed findings, and show an "unknown time" count separately.
- Dense `access1.log` data can overwhelm charts -> cap top-N categories, aggregate long tails, and keep raw findings paginated.
- Synthetic samples might look unrealistic -> base them on existing parser-supported formats and document each sample's intended scenario in filename or metadata.
- Existing worktree has unrelated changes -> keep this change scoped to its OpenSpec files until implementation begins.

## Migration Plan

1. Implement the chart-library spike in a temporary branch or local working set, comparing ECharts and Chart.js against current sample payloads.
2. Promote the chosen renderer into `logcheck/web_static/` as a local static asset or no-build dependency.
3. Add chart-data adapter functions and tests around deterministic datasets.
4. Add curated samples under `samples/` and generation notes/scripts under `worktmp/` during development.
5. Verify through Python tests and browser checks on local Flask only.

Rollback is straightforward: remove the static chart asset and adapter usage, leaving existing table and simple chart summaries intact.

## Open Questions
```

Full source: openspec/changes/enhance-visual-reports-and-log-samples/design.md

## openspec/changes/enhance-visual-reports-and-log-samples/tasks.md

- Source: openspec/changes/enhance-visual-reports-and-log-samples/tasks.md
- Lines: 1-32
- SHA256: 045142d41cfe89ab54c5b8737176645a4f9fb0f932666a32bad92d7247037657

```md
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
```

## openspec/changes/enhance-visual-reports-and-log-samples/specs/log-ingestion/spec.md

- Source: openspec/changes/enhance-visual-reports-and-log-samples/specs/log-ingestion/spec.md
- Lines: 1-35
- SHA256: bf3e23cd77cbe235b2bf7befd36273f49f698a2a18e61952ff5c85cfa25fd46a

```md
## ADDED Requirements

### Requirement: Provide representative bundled sample logs
The log ingestion capability SHALL include representative bundled sample logs that exercise web access, authentication, and application-security analysis paths.

#### Scenario: Sample listing includes representative logs
- **WHEN** the local web app lists bundled samples
- **THEN** the list includes sample logs covering access-log attacks, authentication failures, and application security events
- **AND** each listed sample can be selected for local analysis

#### Scenario: Access sample supports visual reporting
- **WHEN** the user analyzes the bundled access-log sample set
- **THEN** the resulting findings include enough source-address and timestamp diversity to populate source IP and time distribution charts

#### Scenario: Samples remain inert text
- **WHEN** bundled samples contain exploit-like payload strings
- **THEN** the payloads remain inert log text
- **AND** analyzing them does not send requests to the payload domains or addresses

### Requirement: Generate access-log variants from local seed data
The log ingestion capability SHALL support creating curated access-log sample variants from the existing `access1.log` seed data.

#### Scenario: Generated variants preserve parseable format
- **WHEN** access-log variants are generated from `access1.log`
- **THEN** the generated lines preserve a parser-supported access-log format
- **AND** timestamps, source addresses, paths, status codes, and user agents remain available for analysis

#### Scenario: Temporary generation artifacts stay in worktmp
- **WHEN** scripts or intermediate files are used to create sample variants
- **THEN** temporary artifacts are stored under `worktmp/` by default
- **AND** only curated final sample logs are promoted into `samples/`

#### Scenario: Sample generation is deterministic enough for tests
- **WHEN** tests analyze curated generated samples
- **THEN** the expected source-address and time-distribution characteristics are stable across test runs
```

## openspec/changes/enhance-visual-reports-and-log-samples/specs/web-frontend/spec.md

- Source: openspec/changes/enhance-visual-reports-and-log-samples/specs/web-frontend/spec.md
- Lines: 1-47
- SHA256: b0b6bcb9723b42f55a8fdf24df7940639647660d6d115caf06d1acd69c2d6b8b

```md
## ADDED Requirements

### Requirement: Present visual attack analytics
The web frontend SHALL present local visual analytics for completed analyses using the latest local analysis result.

#### Scenario: Source IP statistics are shown
- **WHEN** a local analysis result contains findings with source addresses
- **THEN** the report displays a visual source-address distribution ranked by finding count
- **AND** the report preserves the source-address values in readable text or table form

#### Scenario: Time distribution is shown
- **WHEN** a local analysis result contains timestamped findings
- **THEN** the report displays a visual time distribution of findings across appropriate time buckets
- **AND** findings without timestamps do not break chart rendering

#### Scenario: Rule and severity context are shown
- **WHEN** a local analysis result contains findings with rule ids and severities
- **THEN** the report displays visual summaries for severity and rule distribution
- **AND** the summaries are based on the latest completed analysis result

### Requirement: Keep visualization local and passive
The web frontend SHALL keep report visualization local, offline-capable, and passive.

#### Scenario: Charts do not introduce active security actions
- **WHEN** the visual report renders
- **THEN** it does not display remote scan controls, exploit controls, blocking controls, external reporting controls, or domain/IP action buttons

#### Scenario: Runtime visualization works without internet access
- **WHEN** the web frontend is served from the local Flask app after dependencies are installed
- **THEN** the visual report can render without fetching chart scripts or data from external networks

#### Scenario: Chart failure preserves reviewability
- **WHEN** the selected chart renderer fails to load or render
- **THEN** the report still exposes the underlying local summary values in readable text or table form

### Requirement: Support chart-library evaluation
The frontend implementation SHALL include a documented evaluation path for selecting a chart renderer suitable for this static local dashboard.

#### Scenario: Candidate libraries are compared
- **WHEN** implementation begins
- **THEN** Apache ECharts and Chart.js are compared against the existing local analysis payload shape
- **AND** React-only options such as Recharts or Nivo are documented as non-primary unless the frontend stack changes

#### Scenario: Selected renderer is isolated
- **WHEN** a renderer is selected
- **THEN** chart-data preparation is separated from renderer-specific chart configuration
- **AND** tests can validate chart datasets without requiring external network access
```

