# Comet Design Handoff

- Change: redesign-desktop-investigation-workbench
- Phase: design
- Mode: compact
- Context hash: c2a77c3101ba0403da511519c13f8e0567349188eaa597ff25c3d7d2023d73a8

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/redesign-desktop-investigation-workbench/proposal.md

- Source: openspec/changes/redesign-desktop-investigation-workbench/proposal.md
- Lines: 1-32
- SHA256: 27c707a823ada6bb25c4ea7cf73cde4fc4de02917d18a7e31a7b049f88a09e56

```md
## Why

The current desktop frontend has grown through incremental screens and now feels more like a collection of panels than a focused investigation tool. Logcheck needs a full frontend reset into a compact local workbench that helps users inspect logs, run rules, review evidence, and export reports without navigating through scattered views.

## What Changes

- Replace the current overview-first desktop layout with an investigation workbench layout:
  - left pane for local log sources and source diagnostics
  - center pane for a readable log viewer with highlighted rule hits
  - right pane for local rule controls and analysis context
  - bottom pane for findings, evidence detail, analysis history, and local exports
- Keep the first screen as the usable analysis workspace rather than a landing, hero, or explanatory page.
- Preserve the local-only safety boundary: local files, local rules, local analysis, and local exports only.
- Remove or de-emphasize duplicated navigation that forces users to jump between pages for one investigation flow.
- Keep the existing parsing, analysis, insight generation, and export behavior as backend logic; this change focuses on frontend composition and interaction ergonomics.

## Capabilities

### New Capabilities

- `investigation-workbench-ui`: Defines the redesigned workbench-style desktop interface, including pane layout, log viewer, finding/evidence workflow, and local-only UI constraints.

### Modified Capabilities

- `desktop-frontend`: Tightens the desktop frontend requirement from a polished multi-section analysis workspace to a cohesive investigation workbench that makes log inspection, rule review, finding detail, and export actions available in one stable surface.

## Impact

- Affected code: primarily `logcheck/desktop.py` and its desktop UI tests in `tests/test_desktop.py`.
- Affected behavior: desktop layout, visual hierarchy, navigation model, source review workflow, finding detail workflow, rule control placement, and export placement.
- Unchanged systems: log parsing, detection rules, insight generation, CLI behavior, export file formats, and local-only security posture.
- Dependencies: no new network services or external reporting dependencies are expected.
```

## openspec/changes/redesign-desktop-investigation-workbench/design.md

- Source: openspec/changes/redesign-desktop-investigation-workbench/design.md
- Lines: 1-87
- SHA256: d57163e4bce621fc680adab79c789166d359f605609a0d7bacca71356fc67255

[TRUNCATED]

```md
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
```

Full source: openspec/changes/redesign-desktop-investigation-workbench/design.md

## openspec/changes/redesign-desktop-investigation-workbench/tasks.md

- Source: openspec/changes/redesign-desktop-investigation-workbench/tasks.md
- Lines: 1-36
- SHA256: 075be292744c65cd4ae4dd92e75995f43b5c6058b56617449c20714687807f2e

```md
## 1. Layout Contract And Tests

- [ ] 1.1 Add or update desktop tests that assert the first screen exposes the workbench regions: local sources, log viewer, rule/context panel, and findings/evidence/history area.
- [ ] 1.2 Add desktop tests that assert remote controls are absent, including URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, and external reporting controls.
- [ ] 1.3 Add tests for source diagnostics remaining visible while readable files stay analyzable.
- [ ] 1.4 Add tests for finding selection driving evidence detail in the workbench output area.

## 2. Workbench Shell

- [ ] 2.1 Replace the current primary desktop shell composition with a workbench layout using stable left, center, right, and bottom regions.
- [ ] 2.2 Move source selection, selected source state, and source diagnostics into the left source region.
- [ ] 2.3 Add the central log viewer surface with stable row styling, empty state, and room for highlighted finding rows.
- [ ] 2.4 Move local rule status, rule file state, and local threshold/context controls into the right region.
- [ ] 2.5 Move findings, selected evidence detail, analysis history, and local export actions into the bottom output region.

## 3. Interaction Wiring

- [ ] 3.1 Wire existing import-folder and import-file actions into the workbench source region.
- [ ] 3.2 Wire existing analysis execution into the workbench top or source-adjacent action area.
- [ ] 3.3 Refresh source counts, diagnostics, log viewer rows, findings, insights, history, and export availability after analysis completes.
- [ ] 3.4 Link finding selection to highlighted log evidence and detail content where parsed event data is available.
- [ ] 3.5 Preserve existing JSON, CSV, and Markdown export behavior from the new bottom output region.

## 4. Visual Polish And Responsiveness

- [ ] 4.1 Update the stylesheet for a restrained investigation-tool look with readable contrast, consistent borders, and compact controls.
- [ ] 4.2 Ensure monospaced log rows, severity indicators, buttons, labels, and scroll areas do not overlap or resize unpredictably.
- [ ] 4.3 Define minimum dimensions or collapse behavior so the center log viewer remains usable on smaller windows.
- [ ] 4.4 Remove duplicated or obsolete section controls that conflict with the workbench-first flow.

## 5. Verification

- [ ] 5.1 Run the desktop-focused tests and fix regressions.
- [ ] 5.2 Run the full test suite.
- [ ] 5.3 Launch the desktop app and visually verify the workbench layout, source flow, analysis flow, finding detail, local exports, and absence of remote controls.
- [ ] 5.4 Update README or course-facing documentation only if the user workflow changes enough to make current instructions misleading.
```

## openspec/changes/redesign-desktop-investigation-workbench/specs/desktop-frontend/spec.md

- Source: openspec/changes/redesign-desktop-investigation-workbench/specs/desktop-frontend/spec.md
- Lines: 1-25
- SHA256: 7de28c37589e55caead553f00ddb1adffdff86a0165f152b42fb2a7f6166d1fe

```md
## MODIFIED Requirements

### Requirement: Present polished analysis workspace
The desktop frontend SHALL present a visually consistent local investigation workbench with clear hierarchy, stable layout, and readable controls.

#### Scenario: Consistent workspace surfaces
- **WHEN** the desktop frontend is displayed
- **THEN** panes, rows, buttons, labels, and scroll areas use consistent spacing, background hierarchy, and borders
- **AND** text rows do not appear as accidental black strips against unrelated gray regions

#### Scenario: Workbench-first analysis actions
- **WHEN** the primary desktop screen is displayed
- **THEN** it focuses on local source status, log inspection, analysis action, rule context, findings, evidence detail, recent history, and local exports in a single workbench surface
- **AND** it does not duplicate export actions across unrelated sections

### Requirement: Preserve local-only safety during frontend iteration
The iterated desktop frontend SHALL remain limited to local files, local rules, local analysis, and local exports.

#### Scenario: No remote controls after redesign
- **WHEN** the redesigned UI is displayed
- **THEN** it does not include URL inputs, domain inputs, remote uploads, network scans, blocking actions, exploitation actions, or external reporting controls

#### Scenario: Workbench actions remain local
- **WHEN** the user imports sources, runs analysis, reviews rules, opens history, or exports reports
- **THEN** the action operates on local files, local rules, in-process analysis results, or local output files only
```

## openspec/changes/redesign-desktop-investigation-workbench/specs/investigation-workbench-ui/spec.md

- Source: openspec/changes/redesign-desktop-investigation-workbench/specs/investigation-workbench-ui/spec.md
- Lines: 1-62
- SHA256: 75322ddb64a9aa1c485fc6f33e58eb002d8a588ecd4e8f446b2daf8ca853e11d

```md
## ADDED Requirements

### Requirement: Present an investigation workbench shell
The desktop frontend SHALL present a single workbench-style investigation shell as the primary first screen.

#### Scenario: First screen shows workbench regions
- **WHEN** the desktop frontend opens
- **THEN** the first screen displays a local source region, a log viewer region, a local rule/context region, and a findings/evidence/history region
- **AND** the user can start the core investigation flow without first opening a marketing, landing, or explanatory page

#### Scenario: Stable investigation layout
- **WHEN** source counts, finding counts, or selected details change
- **THEN** the major workbench regions retain stable dimensions and do not jump, overlap, or resize unpredictably

### Requirement: Inspect local log sources beside log content
The desktop frontend SHALL keep selected local log sources and source diagnostics visible beside the log viewer.

#### Scenario: Source list remains visible during investigation
- **WHEN** the user selects local folders or files for analysis
- **THEN** eligible log files are listed in the source region with selected state and basic status
- **AND** the selected source can be reviewed without leaving the workbench

#### Scenario: Diagnostics do not block readable files
- **WHEN** selected sources include unreadable, empty, or unsupported files
- **THEN** diagnostics are shown in the source region
- **AND** readable files remain available for analysis

### Requirement: Show highlighted log evidence
The desktop frontend SHALL provide a central log viewer that supports evidence review for analysis findings.

#### Scenario: Rule hits are visible in log context
- **WHEN** analysis produces findings tied to parsed log events
- **THEN** the log viewer highlights matching events or rows with severity-aware styling
- **AND** selecting a highlighted row exposes the related finding detail

#### Scenario: No analysis state is useful
- **WHEN** no analysis has been run
- **THEN** the log viewer presents an empty local investigation state with available import and run-analysis actions nearby

### Requirement: Keep rule controls local-only
The desktop frontend SHALL expose rule status and local rule controls without introducing remote actions.

#### Scenario: Rule context is available during investigation
- **WHEN** the workbench is displayed
- **THEN** the rule/context region shows enabled local detection rules, active rule file status, or local thresholds

#### Scenario: Remote controls are absent
- **WHEN** the workbench is displayed
- **THEN** it does not include domain inputs, URL inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, or external reporting controls

### Requirement: Review findings and evidence in an output panel
The desktop frontend SHALL present analysis output in a bottom workbench region for quick review.

#### Scenario: Finding list drives evidence detail
- **WHEN** analysis completes with one or more findings
- **THEN** the bottom region shows a severity-aware finding list
- **AND** selecting a finding shows its evidence, related source, and concise review guidance in the detail area

#### Scenario: History and exports remain local
- **WHEN** analysis history or export actions are shown
- **THEN** they appear as local actions in the workbench output area
- **AND** exports remain limited to the supported local JSON, CSV, and Markdown formats
```

