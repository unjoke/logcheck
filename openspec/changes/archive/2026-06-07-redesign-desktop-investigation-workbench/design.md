## Context

Logcheck is a local desktop log intrusion detection tool built around PyQt. The current frontend already supports source selection, analysis execution, findings, insights, rules, history, and exports, but those workflows are distributed across navigation sections. The selected redesign direction is a minimal investigation workbench: users should land directly in a dense, practical surface that resembles a log investigation IDE.

The redesign must respect the project safety constraint discovered during private CTF deployment: all UI affordances remain local-only. The frontend must not introduce domain inputs, URL scanning, remote uploads, exploitation actions, blocking controls, or external reporting.

## Goals / Non-Goals

**Goals:**

- Recompose the desktop frontend into four stable regions: source tree, log viewer, local rule/context panel, and bottom evidence/results area.
- Make the primary analysis path visible on first launch: import local logs, run analysis, inspect highlighted log hits, review evidence detail, and export local reports.
- Preserve existing backend logic for parsing, detection, insights, history, and export formats.
- Improve visual hierarchy with stable pane sizing, readable monospaced log rows, consistent controls, and clear severity indicators.
- Keep the UI ergonomic for repeated local investigation rather than explanatory or marketing-like presentation.

**Non-Goals:**

- Replacing PyQt with a browser frontend.
- Adding remote log collection, URL/domain inputs, network scanning, automatic blocking, exploitation, or external reporting.
- Changing the detection rules engine, parser behavior, insight algorithms, or export file formats.
- Implementing multi-user collaboration, authentication, or server-hosted state.

## Decisions

### Use a single workbench shell instead of page-first navigation

The main window should be structured as a workbench with persistent panes rather than several independent sections. Navigation can remain for secondary modes, but the first screen is the investigation workspace.

Alternatives considered:
- Keep the current overview/sources/rules/export section model: lower implementation risk, but it preserves the workflow fragmentation this change is meant to fix.
- Build a separate web frontend: easier to style, but it introduces packaging and runtime complexity that does not fit the local desktop course project.

### Put log source state on the left

Local folders, individual files, selected analysis set, and diagnostics should live in the left pane. This mirrors common file-tree workflows and keeps source review close to the log viewer.

Alternatives considered:
- Keep source selection as buttons in an overview screen: simpler, but weak for multi-file review.
- Put source controls in a modal: saves space, but hides diagnostics that matter during investigation.

### Put the log viewer in the center

The center pane should show selected log content or parsed event rows using a monospaced, line-stable presentation. Rule hits should be highlighted in-place and linked to finding detail.

Alternatives considered:
- Show only aggregated metrics and findings: good for summary, but poor for evidence review.
- Show raw files in an external editor: avoids UI work, but breaks the integrated investigation flow.

### Put local rules and analysis context on the right

The right pane should contain enabled local rules, rule file status, thresholds, and selected-context controls. It must avoid remote controls.

Alternatives considered:
- Put rules in a separate tab: saves horizontal space, but makes analysis configuration feel disconnected.
- Put findings on the right: useful for alerts, but the bottom area gives findings more horizontal room and keeps details close to history/export.

### Use the bottom area for findings, evidence, history, and export

The bottom pane should behave like an IDE output/debug panel: findings list, selected evidence detail, recent analysis runs, and local export actions.

Alternatives considered:
- Put export controls in the top bar: faster access, but risks cluttering the main command area.
- Keep a dedicated export page only: cleaner separation, but too much navigation for a common end-of-investigation action.

## Risks / Trade-offs

- Pane density can overwhelm first-time users -> Use restrained visual hierarchy, concise labels, and sensible defaults without adding explanatory text blocks.
- A center log viewer could be expensive for large files -> Render parsed or selected rows incrementally where possible and keep tests focused on representative datasets.
- Reworking `desktop.py` may touch a large file -> Split helper methods around pane construction and refresh logic while avoiding unrelated backend refactors.
- Existing tests may assert old labels or section structure -> Update tests to target user-visible behavior and safety constraints rather than brittle widget placement.
- Horizontal layout can be tight on small screens -> Define minimum sizes and hide or collapse the right pane before the central log viewer becomes unusable.

## Migration Plan

1. Keep the existing analysis backend and data models unchanged.
2. Replace the desktop shell layout with the workbench panes in `logcheck/desktop.py`.
3. Wire existing source selection, analysis execution, findings, insights, history, and export actions into the new pane locations.
4. Update desktop tests to assert the new layout contract, source diagnostics, local-only controls, finding detail, and export availability.
5. Run the existing test suite and visually verify the desktop window.

Rollback is straightforward: revert the desktop frontend changes and associated desktop tests without touching parser, rule, insight, or exporter modules.

## Open Questions

- Whether the center log viewer should initially show raw log lines, parsed event rows, or a hybrid; implementation can start with parsed rows and preserve room for raw-line display.
- Whether the right pane should expose threshold editing immediately or only show rule status in the first implementation pass.
