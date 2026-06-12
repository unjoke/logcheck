## Why

The current Logcheck workbench no longer matches the way a reviewer investigates an alert. `Finding queue` sits below the visual report, while `Log detail` lives in a separate right-side column. That splits the most important action loop too far apart: choose a finding, read the evidence, adjust filters, and compare nearby context.

`Attacker IP statistics` is also not concrete enough. It behaves like a generic entity chart instead of an investigation surface that explains source address behavior, severity mix, related rules, targets, observation span, and representative evidence.

This change reframes the work as a full frontend workbench reconstruction, not a small widget patch. It should learn from the strengths of FastWLAT and MaaLogAnalyzer without copying their code or product shape:

- FastWLAT strengths to adapt: dashboard-level situational awareness, multi-view log browsing, fast search/filtering, rule-oriented threat categorization, and dimensional aggregation by time/source/status/path/user-agent.
- MaaLogAnalyzer strengths to adapt: master-detail investigation flow, split-screen evidence comparison, virtual/large-log thinking, search result context jumps, layout-ratio persistence as a future-friendly idea, and clean parser/kernel/projection boundaries.
- Capabilities to reject: remote/online usage, GeoIP or threat-intelligence enrichment, external maps, domain/URL target controls, network scanning, blocking, exploitation actions, and runtime dependency on those repositories.

The result should be a local CTF investigation workbench whose first screen prioritizes evidence review, not a report page with the queue pushed underneath.

## What Changes

- Rebuild the frontend information architecture so the finding queue and selected log detail are visually adjacent and form the primary investigation lane.
- Move visual report, insights, exports, and source/intake controls into supporting regions that do not interrupt the finding-to-evidence loop.
- Add pagination to the finding queue so large analysis results remain scannable and the selected finding stays predictable across page changes.
- Add a visible Chinese/English language toggle for the web interface, covering core navigation, analysis status, finding queue labels, chart labels, filters, empty states, and export/status messages.
- Ensure the visual report includes an explicit time-distribution chart based on timestamps when available and deterministic evidence order when timestamps are missing.
- Expand attacker IP statistics beyond simple counts to include severity mix, related rules, targets or actors, first/last observed time or source position, and representative evidence links.
- Improve keyword filtering and detection review logic using lightweight ideas from current log-analysis projects and papers:
  - FastWLAT-style multi-dimensional filters and rule-category review, adapted to local findings rather than copied UI.
  - MaaLogAnalyzer-style split evidence comparison and parser/projection separation, adapted to the existing Python model.
  - LogAI-style unified local analytics workflow and task separation.
  - LogPAI/logparser/Drain-style template/message normalization for noisy log text.
  - LogBERT-style sequence-aware thinking as inspiration for filter facets and suspicious sequence review, without adding model training or online inference.
- Keep all filtering, charting, statistics, and evidence review local to uploaded or bundled sample logs.
- Do not add URL/domain inputs, remote fetching, network scanning, blocking, exploitation, external reporting, GeoIP/map enrichment, or internet-dependent runtime behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend`: The local workbench must support an evidence-first redesigned layout, adjacent finding/detail review, paginated finding review, bilingual UI switching, visible time distribution, detailed attacker IP statistics, and research-informed keyword filtering.
- `analysis-insights`: Insight data must expose or enable richer local distributions, source-address profiles, and normalized evidence context that the frontend can render without remote services.

## Impact

- Affects `logcheck/web_static/index.html`, `logcheck/web_static/styles.css`, `logcheck/web_static/app.js`, and tests for frontend rendering/state behavior.
- May affect `logcheck/insights.py`, `logcheck/analysis.py`, and serialization in `logcheck/webapp.py` if richer chart, source-address profile, or normalized evidence data should be produced server-side instead of only derived in the browser.
- Adds or updates tests in `tests/test_webapp.py`, `tests/test_web_serialization.py`, `tests/test_insights.py`, and frontend static checks as appropriate.
- No new network dependency is required. FastWLAT, MaaLogAnalyzer, and research references are design-time inspiration only; runtime behavior remains offline and local-only.
