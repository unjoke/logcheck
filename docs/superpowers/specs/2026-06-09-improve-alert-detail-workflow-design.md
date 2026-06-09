---
comet_change: improve-alert-detail-workflow
role: technical-design
canonical_spec: openspec
---

# Improve Alert Detail Workflow Technical Design

## Context

Logcheck already has a browser-based local investigation dashboard with source intake, summary metrics, charts, finding cards, evidence detail, insights, and export actions. The current page proves the backend integration works, but the review flow is too compressed: chart labels can overlap, findings are not treated as a primary review surface, and insight content can compete with the exact evidence needed to verify an alert.

OpenSpec remains the canonical requirement source. This design records how to implement the `improve-alert-detail-workflow` change without expanding the safety boundary beyond passive local log review.

## Selected Approach

Use the existing Flask web app and static frontend. Keep the implementation local-only and dependency-light. The dashboard should become an alert-first review surface:

```text
Source intake
  -> Analysis summary
  -> Visual report
  -> Alert review list
  -> Selected alert detail
  -> Concise investigation insights
```

The key shift is that selected alert detail becomes the source-of-truth area for the clicked finding. Insights remain useful guidance, but they do not duplicate every alert or replace the raw log evidence.

## Components

### Alert Review List

Refactor the current finding card list into an explicit alert review list. Each item should show:

- severity
- rule id
- source file
- line number when available
- a short explanation or entity hint

Clicking a finding moves the selected state to that item and updates the selected alert detail. A new analysis result with no findings must clear stale selected detail.

### Selected Alert Detail

Refactor `renderEvidence` into a clearer selected alert renderer. The detail area should have stable sections:

- summary: rule id, severity, explanation
- provenance: source file, line number, timestamp when present
- entities: actor, target, source address, matched keyword, count when present
- reasoning: severity reason and confidence reason when present
- log detail: available alert-specific evidence rendered as readable log text

The preferred minimum log detail is the single log line associated with the selected alert. If the backend provides other local detail for the alert, such as additional evidence strings or derived local evidence notes, render those as supporting detail. Do not require a fixed "before and after context" model.

Long evidence must stay inside the panel through wrapping or an internal scroll area. It must not force page-level horizontal overflow.

### Investigation Insights

Keep insights separate from alert evidence. The insight area should summarize:

- risk level or headline
- affected entities
- concise suggestions

It should not render a long duplicate list of every finding. The selected alert detail is where a user verifies one alert; insights are where they orient the investigation.

### Visual Report

Tighten chart layout constraints rather than changing chart semantics. Long file names, source labels, and line references must stay within their chart group. On narrow viewports, chart groups should stack vertically so labels and bars remain readable without horizontal page scrolling.

## Data Flow

```text
/api/analyze response
  -> renderResult(payload)
  -> renderFindings(payload.findings)
  -> renderSelectedAlert(selectedFinding)
  -> renderInsights(payload.insights)
  -> renderCharts(payload)
```

Start with the existing `Finding.to_dict()` payload:

- `rule_id`
- `severity`
- `explanation`
- `evidence`
- `source_file`
- `line_number`
- `timestamp`
- `source_address`
- `actor`
- `target`
- `matched_keyword`
- `count`
- `severity_reason`
- `confidence_reason`

If implementation finds that the payload cannot display the single alert log line reliably, add the smallest local-only field needed through existing serialization. Do not change detection semantics or report exports unless required to preserve existing behavior.

## Error Handling

- No analysis yet: alert detail prompts the user to run local analysis.
- Analysis error: clear metrics, findings, selected alert detail, insights, and charts.
- No findings: alert list and selected detail show empty states, not stale previous details.
- Missing optional fields: omit their UI rows instead of rendering empty placeholders.
- Long evidence: preserve readability with wrapping or internal scrolling.

## Testing Strategy

Use TDD during implementation.

Automated tests should cover:

- finding selection updates selected alert detail with rule, severity, metadata, and evidence
- a no-finding result clears stale selected detail
- optional fields do not render empty placeholders
- long evidence does not imply page-level horizontal overflow in static/layout checks where feasible
- chart label markup and CSS prevent overlap-prone unrestricted columns
- forbidden remote controls remain absent
- existing parser, rules, analysis, insights, export, webapp, and serialization tests remain green

Browser verification should cover:

- desktop view: selected alert detail shows the exact log line or other available evidence for the clicked alert
- mobile-width view: visual report and alert detail remain readable without incoherent overlap

## Risks

- The current frontend has some coupled rendering responsibilities. Keep the refactor focused on finding rendering, selected alert detail, insights, and chart layout.
- Additional detail fields could drift into a second data model. Prefer the existing finding payload and only add a minimal serializer field if evidence is genuinely missing.
- Making every panel more prominent could increase visual density. Reduce duplicate finding snippets in insights to compensate.

## Spec Patch

No additional OpenSpec patch is needed beyond the updated `web-frontend` delta. The delta now allows selected alert detail to show a single matched log line or other local alert-specific evidence, without requiring a fixed surrounding-context display.
