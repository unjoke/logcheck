---
comet_change: enhance-finding-workbench-analytics
role: technical-design
canonical_spec: openspec
---

# Enhance Finding Workbench Analytics Technical Design

## Context

OpenSpec change: `openspec/changes/enhance-finding-workbench-analytics`

The existing Logcheck web workbench already supports local analysis, findings, details, insights, charts, and exports. The next iteration improves the investigation experience for coursework and demo use:

- Finding queue pagination for large local results.
- Chinese/English UI switching.
- A clearly visible time-distribution chart.
- More detailed attacker IP statistics.
- Keyword and facet filtering informed by current log-analysis work.

The CTF deployment constraint is strict: every runtime interaction must remain local-only. The app must not add domain input, URL fetch, remote enrichment, network scanning, blocking, exploitation, or external reporting controls.

Design-time references:

- Salesforce LogAI: unified log analytics workflow and task framing.
- LogPAI/logparser/Drain: message template extraction and structured-event thinking.
- LogBERT: sequence-aware anomaly review concepts.

These references guide the design only. The implementation must not import LogAI, LogPAI, LogBERT, model weights, remote datasets, CDNs, or external runtime services.

## Architecture

Use frontend-local derivation as the default:

```text
Local logs / bundled samples
  -> existing /api/analyze
  -> serialized local AnalysisResult
  -> app.js state
  -> filter helpers
  -> pagination helpers
  -> chart bucket helpers
  -> attacker IP aggregation helpers
  -> localized render functions
```

Backend changes should be narrow. Extend `analysis-insights` or web serialization only when a value cannot be derived reliably from the current analysis payload. The likely implementation can stay mostly in `logcheck/web_static/app.js` plus focused tests.

## Data Flow

1. User runs local analysis through the existing web workflow.
2. The frontend stores the latest analysis result and selected finding state.
3. Filters are applied to the full finding set before pagination.
4. Pagination slices the filtered finding set into visible rows.
5. Charts and attacker IP statistics are derived from the latest full or filtered finding set, depending on UI intent:
   - Overview charts should use the latest full result.
   - Focused queue counts and page totals should use the filtered result.
6. Selecting a finding or source address updates local UI state only.
7. Language changes re-render labels and helper text without changing analysis data.

## UI Units

### Finding Queue Pagination

Add state fields for `findingPage` and `findingsPerPage`. Default to 10 findings per page for dense but readable review. The visible queue is computed by:

1. `filteredFindings = applyFindingFilters(allFindings, filters)`
2. `pageCount = Math.max(1, Math.ceil(filteredFindings.length / findingsPerPage))`
3. `currentPage = clamp(findingPage, 1, pageCount)`
4. `visibleFindings = filteredFindings.slice(start, end)`

When the page changes, preserve the selected finding if it is visible on the new page. Otherwise select the first visible finding, or clear selection when the page is empty.

### Localization

Add a compact `TRANSLATIONS` dictionary in `app.js`:

```js
const TRANSLATIONS = {
  en: {
    languageLabel: "Language",
    findingQueue: "Finding queue",
    timeDistribution: "Time distribution",
  },
  zh: {
    languageLabel: "\u8bed\u8a00",
    findingQueue: "\u53d1\u73b0\u961f\u5217",
    timeDistribution: "\u65f6\u95f4\u5206\u5e03",
  },
};
```

The final implementation should centralize visible UI labels through a helper such as `t(key)`. Dynamic analysis values such as raw evidence, rule ids, source files, IP addresses, and timestamps must not be translated.

### Time Distribution

Keep or update the existing time chart helper so the chart is explicit and always represented in the visual report area:

- If findings have timestamps, bucket by local time range.
- If timestamps are missing, bucket by deterministic evidence/source order.
- Label fallback mode clearly in both languages.
- Show localized empty states before analysis and when no findings exist.

### Attacker IP Statistics

Add a source-address aggregation helper. Each row should include:

- Source address.
- Finding count.
- Severity mix.
- Related rules.
- Top actor or target values when present.
- First and last observed timestamp or source reference.
- A representative finding id/index used to select local evidence.

Selecting an IP row should filter or focus the queue to findings with that source address. This remains a local UI action and must not perform lookup, scan, block, or enrichment.

### Keyword And Facet Filtering

Filter first, paginate second. Keyword search should include:

- `rule_id`
- `severity`
- `source_file`
- `source_address`
- `actor`
- `target`
- `matched_keyword`
- `explanation`
- `evidence`

Structured facets should cover at least severity, rule, and source address if the current UI can support them cleanly. Lightweight normalization can replace noisy tokens such as IPs, numbers, timestamps, and paths with stable placeholders for matching. Raw evidence must remain visible and exportable.

## Testing Strategy

Use tests before implementation where practical:

- Static/frontend tests for pagination helper output, page clamping, and selected-finding reset behavior.
- Static/frontend tests for language key coverage and rendering of key English/Chinese labels.
- Tests confirming an explicit time-distribution chart exists and supports timestamp and evidence-order fallback labels.
- Tests for attacker IP aggregation fields and empty state.
- Tests for keyword and facet filtering across structured fields and evidence.
- Safety checks that frontend code does not introduce URL/domain inputs, remote fetches, CDN imports, scan/block/exploit actions, external reporting, geolocation, DNS lookup, or threat-intelligence lookups.
- Existing Python tests for `webapp`, `web_serialization`, `insights`, `analysis`, and exporters must continue to pass.
- Browser verification at desktop and mobile widths should confirm text does not overlap, pagination remains stable, charts are visible, and bilingual labels fit.

## Risks And Mitigations

- Filtering large result sets may be slow. Mitigate with simple local helpers, page slicing, and optional debounce if needed.
- Localization coverage can drift. Mitigate with a static missing-key check over `TRANSLATIONS.en` and `TRANSLATIONS.zh`.
- Time fallback could be misleading. Mitigate by labeling fallback buckets as evidence/source order rather than timestamps.
- IP statistics can duplicate insight profiles. Mitigate by keeping source-address aggregation narrow and reusable.
- Research references can be over-interpreted. Mitigate by keeping them in docs/tests only and explicitly forbidding runtime external dependencies.

## Open Decisions

- Default language: start with English for stable existing UI behavior, then allow the user to switch to Chinese.
- Page size: start with 10 findings per page.
- Filter order: apply filters across all findings, then paginate filtered results.

These defaults can be changed later without affecting the OpenSpec contract.
