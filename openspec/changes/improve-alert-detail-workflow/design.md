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
