---
comet_change: redesign-desktop-investigation-workbench
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-07-redesign-desktop-investigation-workbench
status: final
---

# Redesign Desktop Investigation Workbench Design

## Summary

Redesign the Logcheck desktop frontend as a compact local investigation workbench. The first screen becomes the working surface: local log sources on the left, a central log viewer, local rule/context controls on the right, and findings/evidence/history/export output along the bottom.

The implementation keeps PyQt and the existing backend analysis pipeline. It does not add remote collection, domain inputs, URL scanning, uploads, blocking, exploitation, or external reporting.

## Architecture

The redesign should keep `logcheck/desktop.py` as the desktop entry point while splitting its UI construction into focused helper methods:

- Workbench shell: creates the top command area and four persistent regions.
- Source region: owns local file/folder selection, selected source state, and diagnostics.
- Log viewer region: displays parsed or selected log rows with stable monospaced styling and highlighted finding rows.
- Rule/context region: displays enabled local rules, active rule file state, and local thresholds or context.
- Output region: displays findings, selected evidence detail, analysis history, and local export actions.

Existing parsing, analysis, insights, models, rules, and exporters remain unchanged unless implementation exposes a small presentation-only adapter.

## Data Flow

1. User imports local folders or files from the source region or top action area.
2. The source region lists eligible files and reports diagnostics for unreadable, empty, or unsupported files.
3. User runs analysis.
4. Existing analysis code parses selected local files and produces events, findings, summary data, and insights.
5. The UI refreshes:
   - source counts and diagnostics
   - central log viewer rows
   - highlighted finding rows where event data is available
   - bottom findings list and selected evidence detail
   - history and local export availability
6. User selects a finding or highlighted log row.
7. The output region shows evidence, source context, severity, and concise review guidance.
8. User exports JSON, CSV, or Markdown locally through existing exporter behavior.

## UI Composition

### Top Command Area

The top area should stay compact: brand, primary workbench tabs if needed, import actions, filtering/search affordance, and run-analysis action. It should not become a hero, tutorial, or dashboard banner.

### Left Source Region

The left pane should show local source groups and files with stable row heights. Diagnostics belong here because they are source-specific and should not block analysis of readable files.

### Center Log Viewer

The center pane is the main working area. It should use monospaced rows, severity-aware highlighting, and stable spacing. The first implementation can render parsed event rows; raw-line display can be layered in later if needed.

### Right Rule/Context Region

The right pane should show local detection rules, active rule file state, and local rule context. It must not include URL/domain fields, network scan buttons, remote upload controls, external reporting, blocking controls, or exploitation controls.

### Bottom Output Region

The bottom pane behaves like an IDE output/debug area. It should show a severity-aware finding list, selected evidence detail, recent analysis runs, and local export controls.

## Error Handling

- Empty selection: keep import and run-analysis affordances visible, but explain the missing local source through concise status text.
- Partial source failure: show diagnostics in the source pane and continue with readable files.
- No findings: show a clear empty findings state while keeping event counts and history visible.
- Export before analysis: disable or explain export actions until an analysis result exists.
- Large inputs: avoid rendering unstable or excessive UI rows at once where a summarized or selected-row presentation is enough.

## Testing Strategy

Write desktop tests before implementation where practical:

- Assert the primary screen exposes source, log viewer, rule/context, and output regions.
- Assert remote controls are absent from the redesigned UI.
- Assert source diagnostics remain visible and readable files remain analyzable.
- Assert analysis refresh updates findings and evidence detail.
- Assert finding selection drives detail content.
- Assert local export controls preserve JSON, CSV, and Markdown behavior.

After implementation, run desktop-focused tests, then the full suite. Launch the desktop app and visually inspect layout stability, readable text, no overlap, and the local-only safety boundary.

## Risks And Mitigations

- `desktop.py` may become harder to maintain if all UI logic stays inline -> split construction and refresh methods by pane.
- Dense panes can overwhelm users -> keep labels short, spacing consistent, and avoid explanatory blocks inside the app.
- Log rendering can become slow for large files -> start with parsed/selected rows and avoid unnecessary full-file UI rendering.
- Old tests may be brittle around labels and section names -> update tests toward observable behavior and safety constraints.
- Small windows may compress the center viewer too far -> set minimum dimensions and collapse or simplify secondary panes first.

## Implementation Boundary

In scope:

- PyQt layout, styling, widget placement, and interaction wiring.
- Tests for layout contract, source diagnostics, evidence detail, export placement, and local-only controls.
- Small presentation helpers if they reduce UI complexity.

Out of scope:

- Parser, rules engine, insight algorithm, exporter format changes.
- New web frontend or server runtime.
- Remote log collection or network/security actions beyond local analysis.
