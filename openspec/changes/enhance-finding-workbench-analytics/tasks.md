## 1. Regression Coverage

- [x] 1.1 Add tests or static checks that the desktop layout keeps `Finding queue` and selected `Log detail` adjacent and that the visual report does not sit between them.
- [x] 1.2 Add tests or static checks that mobile reading order keeps finding queue directly before evidence detail.
- [x] 1.3 Add tests or static checks for finding queue pagination controls, page counts, and selected-finding behavior.
- [x] 1.4 Add tests or static checks for Chinese/English language switching and missing translation keys.
- [x] 1.5 Add tests that the visual report includes an explicit time-distribution chart with timestamp and evidence-order fallback states.
- [x] 1.6 Add tests for detailed attacker IP statistics fields, dedicated source-IP area, and empty state.
- [x] 1.7 Add tests for keyword/facet filtering across structured fields and evidence text.
- [x] 1.8 Add safety checks confirming no URL/domain inputs, external fetches, CDN imports, GeoIP/map controls, scan/block/exploit controls, or external reporting controls are introduced.
- [x] 1.9 Add static checks that FastWLAT/MaaLogAnalyzer are referenced only in docs/specs if needed, not imported or copied into runtime code.

## 2. Reference Learning and Local Architecture

- [ ] 2.1 Record the specific FastWLAT strengths to adapt: dashboard summary, multi-view thinking, fast filters, rule/category review, and dimensional aggregation.
- [ ] 2.2 Record the specific MaaLogAnalyzer strengths to adapt: master-detail flow, split evidence comparison, large-log ergonomics, search context jumps, and parser/projection separation.
- [ ] 2.3 Explicitly reject copied code, external maps/GeoIP, online mode, framework rewrites, and runtime dependency on either project.
- [ ] 2.4 Audit the current analysis payload, insight serialization, and frontend chart helpers to decide which analytics can be derived in the browser.

## 3. Workbench Information Architecture

- [x] 3.1 Rebuild the static layout so source intake and summary are supporting regions, while finding queue and log detail form the primary investigation lane.
- [x] 3.2 Move visual report below or beside the investigation lane so it supports review without separating queue from detail.
- [x] 3.3 Keep selected alert, source context, reasoning, and raw `Log detail` together in the detail region.
- [x] 3.4 Add responsive CSS so mobile order is intake/summary, queue/filter, detail/evidence, visual report, insights/export.
- [ ] 3.5 Verify text does not overlap and fixed-format controls do not resize unpredictably at desktop and mobile widths.

## 4. Local Aggregation and Detection Review Logic

- [x] 4.1 Implement or update local helper functions for filtered finding sets, pagination state, time buckets, and source-address aggregation.
- [x] 4.2 Add normalized evidence text helper logic only if needed for useful keyword matching, preserving raw evidence display.
- [ ] 4.3 Add local sequence/context grouping only from existing timestamps, source order, line numbers, or insight timeline data.
- [ ] 4.4 Keep rule explanations deterministic and avoid importing external rulesets, model weights, or online inference.

## 5. Workbench UI Implementation

- [x] 5.1 Add finding queue pagination controls and integrate them with selection and filters.
- [x] 5.2 Add a compact local i18n dictionary and visible English/Chinese language control.
- [x] 5.3 Ensure core UI labels, status text, filter labels, chart labels, empty states, and export/status messages use the language dictionary.
- [x] 5.4 Render the time-distribution chart clearly in the visual report area.
- [x] 5.5 Render detailed attacker IP statistics with counts, severity mix, related rules, targets or actors, first/last observation, and evidence access.
- [x] 5.6 Add keyword and facet filter controls that filter first and paginate second.
- [x] 5.7 Make selecting an attacker/source IP focus the queue and selected evidence without performing lookup, scan, block, or enrichment.

## 6. Insight and Serialization Updates

- [x] 6.1 Extend `analysis-insights` data or web serialization only where frontend-only derivation is insufficient.
- [x] 6.2 Ensure source-address profile data remains local-only and does not perform enrichment or network actions.
- [x] 6.3 Ensure exports and selected finding details still show raw evidence after normalized filtering support is added.

## 7. Verification

- [ ] 7.1 Run the Python test suite covering insights, web serialization, web app behavior, and existing analysis/export behavior.
- [ ] 7.2 Run JavaScript syntax or static checks for `logcheck/web_static/app.js`.
- [ ] 7.3 Run the local web dashboard and verify desktop and mobile layouts with the Browser plugin or Playwright.
- [ ] 7.4 Verify a sample analysis demonstrates adjacent queue/detail review, paginated findings, Chinese/English switching, time distribution, detailed attacker IP statistics, and keyword/facet filtering.
- [ ] 7.5 Record that runtime behavior remains offline/local-only and does not depend on the research links used during design.
