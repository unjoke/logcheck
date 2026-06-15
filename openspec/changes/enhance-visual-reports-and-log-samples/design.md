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

- Should the final chart library be vendored into the repository, or should the project add a package-management step for frontend assets?
- Should generated sample variants be committed as static `.log` files only, or should a generator script also be retained for reproducibility?
