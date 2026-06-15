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
