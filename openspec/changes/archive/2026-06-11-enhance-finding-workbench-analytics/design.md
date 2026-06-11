## Context

Logcheck already has a browser-based local investigation dashboard, analysis insights, alert detail review, and basic chart requirements. The new request focuses on usability and completeness rather than a new detection engine: long finding lists need pagination, the visible UI must switch between Chinese and English, the time-distribution chart must be present, attacker IP statistics need more investigative detail, and keyword filtering should be informed by established log-analysis research/projects.

The project must remain safe in the private CTF deployment where domains redirect to `192.168.2.1`. The dashboard must not depend on external browsing at runtime and must not add remote target controls.

Research basis used for design only:
- Salesforce LogAI frames log analytics as a unified local workflow with preprocessing, extraction, analytics, and anomaly-detection tasks.
- LogPAI/logparser/Drain shows the value of turning noisy raw messages into templates or normalized event forms before analysis.
- LogBERT demonstrates sequence-aware anomaly review, but this project should only borrow the idea of sequence/facet visibility, not model training or online downloads.

## Goals / Non-Goals

**Goals:**
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
- No full localization framework unless the existing code structure clearly warrants it; a compact local translation dictionary is enough.

## Decisions

### 1. Derive UI analytics from the latest local result first

The frontend should derive pagination, filters, visible chart buckets, and attacker IP rows from the latest analysis payload wherever possible. Server-side insight changes should be limited to fields that are hard to compute consistently in the browser or already belong in `analysis-insights`.

Alternative considered: add new backend endpoints for every chart and table. That would increase API surface and test burden without much benefit for a local single-user dashboard.

### 2. Use a small local i18n dictionary

Add a compact translation map for core UI copy and a language state such as `en`/`zh`. The selected language can be stored in browser state or localStorage, and changing it should re-render labels without changing analysis data.

Alternative considered: introduce a full i18n package. That is unnecessary for this small static frontend and risks adding dependency churn.

### 3. Treat time distribution as a required visual report chart

The visual report must include a chart explicitly labeled as time distribution. Use parsed timestamps when present. If findings lack timestamps, bucket by deterministic evidence order or source order and label the fallback clearly in the selected language.

Alternative considered: hide the chart when timestamps are unavailable. That makes demos inconsistent and repeats the current “chart missing” problem.

### 4. Expand attacker IP stats as an investigation table plus chart

For each source address, show count, severity distribution, related rules, top target or actor values, first/last observed time or source reference, and a representative evidence link or selected-finding action. Non-IP entities can remain in general entity charts, while this view should focus on source addresses so “attack IP statistics” is concrete.

Alternative considered: only improve labels in the existing entity chart. That would still be too shallow for attack-source analysis.

### 5. Keep keyword filtering local but research-informed

Filtering should search structured finding fields and evidence, support simple facets such as severity/rule/source address, and normalize noisy message text enough that variable tokens do not prevent useful matches. Drain/logparser-style template thinking can guide normalization; LogAI and LogBERT can be cited in design/docs as inspiration for workflow and sequence awareness. The implementation must not import those projects or fetch papers at runtime.

Alternative considered: add model-based semantic search. That is too heavy for the course project and conflicts with the local-only constraint.

## Risks / Trade-offs

- Large result sets could make frontend filtering slow -> cap rendered rows per page, debounce text input if needed, and keep derived indexes simple.
- Translation coverage can drift as UI copy changes -> centralize user-visible labels in one dictionary and add static tests for missing language keys.
- Time fallback labels may confuse users -> label fallback buckets as evidence/source order rather than pretending timestamps exist.
- Detailed IP stats may duplicate insight profiles -> share small aggregation helpers or keep a clearly documented mapping from findings to display rows.
- Research references may be mistaken for runtime dependencies -> document them as design inspiration only and add tests/inspection to ensure no external fetches or CDN imports are introduced.

## Migration Plan

1. Add failing tests for pagination, i18n labels, time distribution presence, attacker IP detail fields, and keyword filtering behavior.
2. Implement local aggregation helpers and UI rendering changes.
3. Update insight serialization only if frontend-only derivation is insufficient.
4. Verify desktop and mobile browser layouts and confirm the dashboard still has no forbidden remote controls.
5. Roll back by removing the new frontend helpers and spec additions; no data migration is required.

## Open Questions

- Should the default language follow the browser locale or stay English until the user toggles it?
- What page size is preferred for the finding queue: 10, 20, or a selectable value?
- Should keyword filtering search only current-page findings or all findings before pagination? The recommended behavior is filter first, then paginate filtered results.
