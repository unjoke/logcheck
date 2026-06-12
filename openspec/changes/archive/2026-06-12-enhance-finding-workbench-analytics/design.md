## Context

Logcheck already has a browser-based local investigation dashboard, analysis insights, alert detail review, and basic chart requirements. The new request is broader than adding missing controls: the current information architecture separates the finding queue from the selected log detail too much, pushes the investigation queue underneath the visual report, and makes attacker IP statistics feel like a shallow chart instead of an evidence-driven source profile.

The redesigned workbench should make the primary workflow obvious:

```text
choose local evidence -> review findings -> inspect log detail -> focus by attacker/source/rule -> export or explain
```

That means `Finding queue` and `Log detail` should become adjacent parts of the same investigation lane. Source intake, summary metrics, visual report, insights, and exports should become supporting surfaces around that lane.

The project must remain safe in the private CTF deployment where domains redirect to `192.168.2.1`. The dashboard must not depend on external browsing at runtime and must not add remote target controls.

Project references used for design only:

- FastWLAT demonstrates useful product-level ideas: first-screen situational awareness, multi-view log browsing, fast search/filtering, rule/category review, and dimensional aggregation by time/source/status/path/user-agent. Logcheck should adapt the investigation value, not copy its Electron/Vue implementation, visual style, GeoIP map, or runtime enrichment.
- MaaLogAnalyzer demonstrates useful workflow ideas: master-detail and split-screen review, virtual-scroll/large-file thinking, search result context jumps, layout ratio persistence, and separation of parsing/kernel/projection concerns. Logcheck should adapt those concepts within its current Flask/static frontend and Python analysis model.

Research basis used for design only:

- Salesforce LogAI frames log analytics as a unified local workflow with preprocessing, extraction, analytics, and anomaly-detection tasks.
- LogPAI/logparser/Drain shows the value of turning noisy raw messages into templates or normalized event forms before analysis.
- LogBERT demonstrates sequence-aware anomaly review, but this project should only borrow the idea of sequence/facet visibility, not model training or online downloads.

## Goals / Non-Goals

**Goals:**

- Rebuild the first-screen frontend around an evidence-first investigation lane.
- Keep `Finding queue` and selected `Log detail` visually adjacent on desktop and sequentially adjacent on mobile.
- Promote attacker IP statistics to a dedicated source profile area rather than burying it in generic source/entity frequency.
- Make the finding queue manageable for large local results through deterministic pagination.
- Let users switch the web interface between Chinese and English without re-running analysis.
- Show an explicit time-distribution chart in the visual report area.
- Provide detailed attacker IP statistics suitable for screenshots, report writing, and oral demo explanation.
- Add keyword filtering that searches across rule, severity, source, actor, target, matched keyword, explanation, and evidence, with normalized-message behavior where useful.
- Preserve existing local analysis, export, insight, and selected-alert workflows.
- Keep the implementation dependency-light and fully local.

**Non-Goals:**

- No machine learning training, BERT inference, LogAI/LogPAI dependency integration, or external dataset download.
- No real-time monitoring, remote log collection, domain lookup, threat-intel enrichment, network scan, blocking, exploitation, or external reporting.
- No copying frontend code, styles, parser code, worker code, or rule definitions from FastWLAT or MaaLogAnalyzer.
- No GeoIP maps, external map data, online mode, desktop shell migration, or large framework rewrite in this change.
- No full localization framework unless the existing code structure clearly warrants it; a compact local translation dictionary is enough.

## Decisions

### 1. Redesign around an evidence-first investigation lane

The desktop layout should prioritize the loop the reviewer repeats most:

```text
┌──────────────┬───────────────────────────────┬────────────────────────────┐
│ Intake/Scope │ Finding queue + filters       │ Selected log detail        │
│ Summary      │ Attacker/source focus chips   │ Source context/reasoning   │
│ Exports      │ Page controls                 │ Raw evidence               │
├──────────────┴───────────────────────────────┴────────────────────────────┤
│ Visual report: time distribution, severity, source/entity, IP profiles     │
└────────────────────────────────────────────────────────────────────────────┘
```

On narrower screens, the order should be intake/summary, queue/filter, selected detail, then visual report. This keeps `Finding queue` and `Log detail` close in reading order and fixes the current disconnect where queue review sits below charts while evidence is far away.

Alternative considered: keep the current three-column layout and only move the queue higher. That still leaves charts competing with the primary investigation loop and does not solve the attacker IP statistics problem.

### 2. Derive UI analytics from the latest local result first

The frontend should derive pagination, filters, visible chart buckets, and attacker IP rows from the latest analysis payload wherever possible. Server-side insight changes should be limited to fields that are hard to compute consistently in the browser or already belong in `analysis-insights`.

Alternative considered: add new backend endpoints for every chart and table. That would increase API surface and test burden without much benefit for a local single-user dashboard.

### 3. Use a small local i18n dictionary

Add a compact translation map for core UI copy and a language state such as `en`/`zh`. The selected language can be stored in browser state or localStorage, and changing it should re-render labels without changing analysis data.

Alternative considered: introduce a full i18n package. That is unnecessary for this small static frontend and risks adding dependency churn.

### 4. Treat time distribution as a required visual report chart

The visual report must include a chart explicitly labeled as time distribution. Use parsed timestamps when present. If findings lack timestamps, bucket by deterministic evidence order or source order and label the fallback clearly in the selected language.

Alternative considered: hide the chart when timestamps are unavailable. That makes demos inconsistent and repeats the current chart-missing problem.

### 5. Expand attacker IP stats as an investigation table plus chart

For each source address, show count, severity distribution, related rules, top target or actor values, first/last observed time or source reference, and a representative evidence link or selected-finding action. Non-IP entities can remain in general entity charts, while this view should focus on source addresses so "attack IP statistics" is concrete.

Alternative considered: only improve labels in the existing entity chart. That would still be too shallow for attack-source analysis.

### 6. Improve detection review logic without importing external engines

Filtering should search structured finding fields and evidence, support simple facets such as severity/rule/source address, and normalize noisy message text enough that variable tokens do not prevent useful matches. Drain/logparser-style template thinking can guide normalization; FastWLAT-style conditional review can guide field/facet choices; MaaLogAnalyzer-style parser/projection separation can guide where normalized evidence belongs; LogAI and LogBERT can be cited in design/docs as inspiration for workflow and sequence awareness.

The detection logic improvement in this change should be conservative:

- Add local normalized evidence/search context for review and filtering.
- Preserve raw evidence and export behavior.
- Prefer deterministic rule/facet/category explanations over opaque scoring.
- Surface suspicious sequence clusters only from existing local findings and timeline order.
- Keep the existing Python rule engine as the source of findings unless a narrow helper is clearly needed.

The implementation must not import FastWLAT, MaaLogAnalyzer, LogAI, LogPAI, LogBERT, model weights, external rulesets, or online data at runtime.

Alternative considered: add model-based semantic search. That is too heavy for the course project and conflicts with the local-only constraint.

## Risks / Trade-offs

- A full UI reconstruction can become too large -> keep the scope to markup/CSS/static JS state and existing backend payloads unless tests prove a narrow backend helper is needed.
- Large result sets could make frontend filtering slow -> cap rendered rows per page, debounce text input if needed, and keep derived indexes simple.
- Translation coverage can drift as UI copy changes -> centralize user-visible labels in one dictionary and add static tests for missing language keys.
- Time fallback labels may confuse users -> label fallback buckets as evidence/source order rather than pretending timestamps exist.
- Detailed IP stats may duplicate insight profiles -> share small aggregation helpers or keep a clearly documented mapping from findings to display rows.
- Research references may be mistaken for runtime dependencies -> document them as design inspiration only and add tests/inspection to ensure no external fetches or CDN imports are introduced.

## Migration Plan

1. Add failing tests for evidence-first layout regions, queue/detail adjacency, pagination, i18n labels, time distribution presence, attacker IP detail fields, and keyword filtering behavior.
2. Implement the new static layout and CSS before deeper JS behavior so the investigation lane can be reviewed visually.
3. Implement local aggregation helpers and UI rendering changes.
4. Update insight serialization only if frontend-only derivation is insufficient.
5. Verify desktop and mobile browser layouts and confirm the dashboard still has no forbidden remote controls.
6. Roll back by restoring the previous static layout and removing the new frontend helpers/spec additions; no data migration is required.

## Open Questions

- Should the default language follow the browser locale or stay English until the user toggles it?
- What page size is preferred for the finding queue: 10, 20, or a selectable value?
- Should keyword filtering search only current-page findings or all findings before pagination? The recommended behavior is filter first, then paginate filtered results.
- Should the visual report live below the investigation lane by default, or should it become a collapsible right/secondary rail once the queue/detail lane is implemented?
