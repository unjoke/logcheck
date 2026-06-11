## 1. Regression Coverage

- [x] 1.1 Add tests or static checks for finding queue pagination controls, page counts, and selected-finding behavior.
- [x] 1.2 Add tests or static checks for Chinese/English language switching and missing translation keys.
- [x] 1.3 Add tests that the visual report includes an explicit time-distribution chart with timestamp and evidence-order fallback states.
- [x] 1.4 Add tests for detailed attacker IP statistics fields and empty state.
- [x] 1.5 Add tests for keyword/facet filtering across structured fields and evidence text.
- [x] 1.6 Add safety checks confirming no URL/domain inputs, external fetches, CDN imports, scan/block/exploit controls, or external reporting controls are introduced.

## 2. Local Aggregation Design

- [x] 2.1 Audit the current analysis payload, insight serialization, and frontend chart helpers to decide which analytics can be derived in the browser.
- [x] 2.2 Implement or update local helper functions for filtered finding sets, pagination state, time buckets, and source-address aggregation.
- [x] 2.3 Add normalized evidence text helper logic only if needed for useful keyword matching, preserving raw evidence display.

## 3. Workbench UI Implementation

- [x] 3.1 Add finding queue pagination controls and integrate them with selection and filters.
- [x] 3.2 Add a compact local i18n dictionary and visible English/Chinese language control.
- [x] 3.3 Ensure core UI labels, status text, filter labels, chart labels, empty states, and export/status messages use the language dictionary.
- [ ] 3.4 Render the time-distribution chart clearly in the visual report area.
- [ ] 3.5 Render detailed attacker IP statistics with counts, severity mix, related rules, targets or actors, first/last observation, and evidence access.
- [x] 3.6 Add keyword and facet filter controls that filter first and paginate second.

## 4. Insight and Serialization Updates

- [ ] 4.1 Extend `analysis-insights` data or web serialization only where frontend-only derivation is insufficient.
- [ ] 4.2 Ensure source-address profile data remains local-only and does not perform enrichment or network actions.
- [ ] 4.3 Ensure exports and selected finding details still show raw evidence after normalized filtering support is added.

## 5. Verification

- [ ] 5.1 Run the Python test suite covering insights, web serialization, web app behavior, and existing analysis/export behavior.
- [ ] 5.2 Run JavaScript syntax or static checks for `logcheck/web_static/app.js`.
- [ ] 5.3 Run the local web dashboard and verify desktop and mobile layouts with the Browser plugin or Playwright.
- [ ] 5.4 Verify a sample analysis demonstrates paginated findings, Chinese/English switching, time distribution, detailed attacker IP statistics, and keyword/facet filtering.
- [ ] 5.5 Record that runtime behavior remains offline/local-only and does not depend on the research links used during design.
