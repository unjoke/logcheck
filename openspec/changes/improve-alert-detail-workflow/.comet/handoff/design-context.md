# Comet Design Handoff

- Change: improve-alert-detail-workflow
- Phase: design
- Mode: compact
- Context hash: 0f2e3e1de24ae21088c79f9b98e5608012c873b229b4ba632e5b8c47c8ef5b56

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/improve-alert-detail-workflow/proposal.md

- Source: openspec/changes/improve-alert-detail-workflow/proposal.md
- Lines: 1-27
- SHA256: b7c170e77363e97c5786ec4117b17089e9d5f2063b269b17df91bc41bf637cab

```md
## Why

The current web dashboard shows local findings, charts, and insights, but the review workflow is too compressed: visual report text can overflow, insight content competes with evidence, and clicking a finding does not guarantee enough raw log context for an audit. This change makes the alert review experience clearer and more defensible for coursework demonstration and local incident investigation.

## What Changes

- Separate alert review from general insights so findings can be scanned, selected, and inspected without being buried in the right panel.
- Require selected alerts to show detailed log evidence, such as the single matched log line or other local evidence available for that alert.
- Improve visual report presentation so chart labels and bars remain readable without overlap or accidental horizontal overflow.
- Keep insights as a summary aid, not a replacement for the selected alert's evidence.
- Preserve the local-only safety boundary: no URL/domain inputs, remote fetching, scanning, blocking, exploitation, external reporting, or internet-dependent behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend`: Adds requirements for alert-focused review, selected-alert log detail, clearer visual report layout, and separation between evidence detail and investigation insights.

## Impact

- Affects `logcheck/web_static/app.js`, web CSS/templates, and web/desktop-oriented tests that assert finding selection and detail rendering behavior.
- May require extending frontend result rendering to use existing `Finding.evidence`, `source_file`, `line_number`, actor, target, source address, matched keyword, severity reason, confidence reason, and other local evidence data.
- Does not change parser, detector, exporter, CLI, or any remote/network behavior unless a small local data-shaping change is needed to expose already-computed evidence.
```

## openspec/changes/improve-alert-detail-workflow/design.md

- Source: openspec/changes/improve-alert-detail-workflow/design.md
- Lines: 1-62
- SHA256: 31b0ef16ba0032e0f69b1b3bc23047387ff7c52b574149253b76deb619ac239d

```md
## Context

Logcheck is a local investigation dashboard. Existing specs already require a browser-based local workflow and source context preservation, but they do not define how the user moves from a chart or alert summary into a specific alert's raw evidence. The current UI places visual reports, evidence detail, insight cards, and finding snippets close together, which makes the most important review action unclear: selecting an alert and reading the exact local log evidence behind it.

The implementation should build on the current result payload. `Finding.to_dict()` already exposes rule, severity, explanation, evidence, source file, line number, timestamp, source address, actor, target, matched keyword, count, severity reason, and confidence reason. The frontend can use those fields to create a stronger alert detail view before considering any deeper backend model change.

## Goals / Non-Goals

**Goals:**

- Make alert selection an explicit workflow with a clear selected state and stable detail area.
- Show detailed log evidence for the selected alert, including the single matched log line or other local evidence the analysis result can provide.
- Keep visual report charts compact, readable, and non-overlapping on desktop and mobile-width viewports.
- Keep insights visible as investigation guidance while preventing them from crowding or replacing alert evidence.
- Preserve local-only, passive analysis behavior.

**Non-Goals:**

- No remote investigation features, URL/domain target handling, network scanning, blocking, exploitation, or external reporting.
- No rule-engine redesign unless implementation discovers a minimal local data-shaping gap for detailed alert evidence.
- No new persistence layer or multi-user case-management system.
- No requirement to build a full incident ticketing workflow.

## Decisions

### Decision: Use an alert-first review layout

The review area should prioritize a dedicated finding list and a selected-alert detail panel. Charts remain a summary tool, but they should not be the only way to discover findings. The selected alert detail should have stable sections for summary fields, reasons, evidence lines, and optional supporting detail.

Alternative considered: keep the current right panel and add more text to it. This would be faster, but it would worsen the existing density problem and make long evidence harder to audit.

### Decision: Treat raw log evidence as the detail source of truth

The selected-alert view should render the available evidence as preformatted log text and identify file and line provenance next to it. The preferred minimum detail is the exact single log line that triggered the alert; if the backend provides other local evidence for that alert, render it as supporting detail instead of mixing it into insight suggestions.

Alternative considered: show only explanation, rule id, and matched keyword. That is insufficient for a reviewer who needs to verify the alert against the original log.

### Decision: Keep insights separate and summarized

Investigation insights should stay useful, but they should be visually and semantically separate from the selected alert evidence. They can summarize risk, affected entities, and review suggestions, while the alert detail remains the place for exact log evidence.

Alternative considered: merge insights and selected alert details into one stream. This is simpler to render, but it blurs generated guidance with source evidence.

### Decision: Fix chart readability with layout constraints

Charts should use bounded label columns, wrapping or truncation where appropriate, and stable chart tracks so long source names such as `samples\\incident.log:2` do not overlap adjacent chart groups. On narrow viewports, charts can stack vertically rather than trying to preserve a dense multi-column row.

Alternative considered: reduce font size globally. That would only hide the issue and make the dashboard harder to read.

## Risks / Trade-offs

- Long raw log lines may still exceed compact panels -> render evidence in scrollable preformatted blocks with predictable width and wrapping rules.
- Additional alert evidence may not exist in the current result payload -> first use existing `evidence` and provenance fields, then add a minimal local-only detail field only if required.
- More distinct panels can make the dashboard feel busy -> use clear hierarchy, stable section labels, and avoid duplicating the same finding snippets in multiple places.
- Tests may currently assume the old detail panel structure -> update tests around behavior rather than brittle markup.

## Migration Plan

1. Add or update tests that describe selected-alert detail behavior and chart layout constraints.
2. Refactor frontend rendering so findings, selected alert detail, charts, and insights each have a clear responsibility.
3. If needed, expose additional local alert detail through the existing analysis result serialization without changing detection semantics.
4. Verify with automated tests and browser screenshots at desktop and mobile-width viewports.
```

## openspec/changes/improve-alert-detail-workflow/tasks.md

- Source: openspec/changes/improve-alert-detail-workflow/tasks.md
- Lines: 1-26
- SHA256: bd5654a658275cf56d1618c76ce447a3056b683c1f6f42eb8b33b2f987c7ed11

```md
## 1. Tests

- [ ] 1.1 Add or update frontend tests for selecting a finding and rendering its detailed evidence, metadata, and selected state.
- [ ] 1.2 Add a regression test that a new analysis with no findings clears stale selected-alert detail.
- [ ] 1.3 Add a test or browser verification note for long evidence/log paths staying inside the detail panel without page-level horizontal overflow.
- [ ] 1.4 Add a test or browser verification note for visual report labels not overlapping adjacent chart groups.

## 2. Data Flow

- [ ] 2.1 Audit the current analysis result payload for fields needed by the selected-alert detail view.
- [ ] 2.2 If existing evidence is insufficient, add a minimal local-only detail representation for the matched log line or other alert-specific evidence without changing detection semantics.
- [ ] 2.3 Ensure serialized finding data omits empty optional detail fields from the rendered UI while preserving existing export behavior.

## 3. Frontend Rendering

- [ ] 3.1 Refactor finding list rendering into an explicit alert review list with clear selected state and source metadata.
- [ ] 3.2 Refactor selected-alert detail rendering into structured sections for summary, evidence, reasons, and optional supporting detail.
- [ ] 3.3 Refactor investigation insights so they stay concise and separate from selected-alert evidence.
- [ ] 3.4 Adjust visual report chart layout constraints to prevent label/bar overlap and page-level horizontal scrolling.
- [ ] 3.5 Verify empty states for no analysis, no findings, and findings without optional metadata.

## 4. Verification

- [ ] 4.1 Run the automated test suite covering models, rules, insights, exports, and web rendering.
- [ ] 4.2 Run the web dashboard locally and capture desktop verification that selected alerts show detailed log evidence.
- [ ] 4.3 Capture mobile-width verification that charts and alert detail remain readable without incoherent overlap.
```

## openspec/changes/improve-alert-detail-workflow/specs/web-frontend/spec.md

- Source: openspec/changes/improve-alert-detail-workflow/specs/web-frontend/spec.md
- Lines: 1-68
- SHA256: 5728f32a1fabf3ca9d5e7192192b2e465d073ea17fe9ddea2cb8dd1c6ae9919d

```md
## ADDED Requirements

### Requirement: Provide alert-focused review workflow
The web frontend SHALL provide a dedicated workflow for scanning local findings and reviewing one selected alert at a time.

#### Scenario: Findings are separately reviewable
- **WHEN** local analysis produces findings
- **THEN** the web frontend displays a distinct alert or finding list separate from investigation insight cards
- **AND** each list item identifies severity, rule, source file, and line number when available

#### Scenario: Selecting an alert updates detail
- **WHEN** the user selects a finding from the alert list
- **THEN** the selected state moves to that finding
- **AND** the alert detail area updates to show that finding's rule, severity, explanation, source metadata, and evidence

#### Scenario: No finding selection is available
- **WHEN** local analysis produces no findings
- **THEN** the alert review area shows an empty state
- **AND** it does not display stale details from a previous analysis result

### Requirement: Show detailed local log evidence for selected alerts
The web frontend SHALL show detailed local log evidence for the currently selected alert.

#### Scenario: Selected alert shows matched log line
- **WHEN** a selected finding contains evidence or matched log lines
- **THEN** the alert detail area renders the raw matched evidence as readable log text
- **AND** the detail area identifies the source file and line number associated with the evidence when available

#### Scenario: Selected alert shows available context fields
- **WHEN** a selected finding includes actor, target, source address, timestamp, matched keyword, count, severity reason, or confidence reason
- **THEN** the alert detail area displays those fields in a structured form
- **AND** absent fields do not create empty placeholder blocks

#### Scenario: Selected alert can show additional local detail
- **WHEN** the analysis result includes a single matched log line or other local detail for a selected finding
- **THEN** the alert detail area shows that available alert-specific log detail
- **AND** the detail remains visually distinct from generated insight text

#### Scenario: Long evidence remains readable
- **WHEN** selected alert evidence contains long file paths, long log messages, or multiple evidence lines
- **THEN** the alert detail area remains scrollable or wrapped within its panel
- **AND** it does not force page-level horizontal overflow

### Requirement: Keep insights separate from alert evidence
The web frontend SHALL present investigation insights as summary guidance that is separate from selected-alert evidence.

#### Scenario: Insights do not replace selected evidence
- **WHEN** both findings and generated insights are available
- **THEN** selecting a finding shows that finding's detailed evidence
- **AND** investigation insights remain separate summary or recommendation content

#### Scenario: Insight list remains concise
- **WHEN** many findings exist
- **THEN** the insights area shows concise summaries, risk information, affected entities, or suggestions
- **AND** it does not duplicate every alert as an unbounded list that crowds the evidence detail

### Requirement: Prevent visual report overlap
The web frontend SHALL keep visual report charts readable and non-overlapping across supported viewport widths.

#### Scenario: Long labels do not overlap chart groups
- **WHEN** chart labels include long source names, file paths, addresses, or entity names
- **THEN** labels remain constrained to their chart area
- **AND** they do not overlap neighboring chart columns, bars, or text

#### Scenario: Charts adapt to narrow viewports
- **WHEN** the dashboard is viewed at mobile-width or otherwise narrow viewport sizes
- **THEN** visual report chart groups stack or reflow into a readable layout
- **AND** the page does not require horizontal scrolling to read chart content
```

