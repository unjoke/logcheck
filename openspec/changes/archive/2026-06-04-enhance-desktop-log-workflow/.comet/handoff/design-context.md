# Comet Design Handoff

- Change: enhance-desktop-log-workflow
- Phase: design
- Mode: compact
- Context hash: 74f911f67eaacaff88cd6e1d106a722351c0edbbb1309cd1ad112b847da5b44c

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/enhance-desktop-log-workflow/proposal.md

- Source: openspec/changes/enhance-desktop-log-workflow/proposal.md
- Lines: 1-29
- SHA256: ae5f145b5a5751a5a9b3e8e19561fd08912cb2917e3bffee79c9c880a4e561e7

```md
## Why

The desktop UI needs to support a more realistic local analysis workflow: users often keep logs in folders, want to analyze only selected files, need visible rule details, and may export an earlier analysis result rather than only the latest one. The current course-demo entry is no longer useful and should be removed from the production navigation.

## What Changes

- Add folder-based log sources; by default, a chosen folder contributes all regular files directly under that folder.
- Allow analysis from either selected files in the configured log source or standalone files chosen from the computer.
- Remove the unused Course Demo navigation section from the desktop UI.
- Render detection rule details in the desktop frontend instead of only showing high-level rule labels.
- Keep multiple local analysis runs in a timestamped in-memory history for the session.
- Let report export choose which timestamped analysis run to export.
- Preserve the local-only safety boundary: no URL inputs, remote uploads, domain access, scanning, blocking, exploitation, or network reporting.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-frontend`: Extend the desktop workflow for folder log sources, selectable source files, standalone local file analysis, timestamped report export history, detection rule presentation, and removal of the course demo navigation entry.

## Impact

- Affected code: `logcheck/desktop.py`, focused desktop tests, and possibly small helper functions for UI data mapping.
- Existing CLI analysis, parser, rule engine, and exporter formats remain unchanged.
- The frontend remains a local desktop app with local file dialogs only.
```

## openspec/changes/enhance-desktop-log-workflow/design.md

- Source: openspec/changes/enhance-desktop-log-workflow/design.md
- Lines: 1-59
- SHA256: a726c1a20ed6ac149c2c3a75ec7cb7a5a12a21b34f637d8461fc1badc01725fa

```md
## Context

`LogcheckDesktop` is a PyQt6 local desktop UI that currently lets users choose local files, run analysis, view summary/finding details, and export JSON/CSV/Markdown for the latest result. The left navigation includes a Course Demo section from earlier course-oriented work, a basic Log Sources section, and a Detection Rules section that only displays static labels. Export always uses `latest_result`, so previous runs cannot be selected by time.

## Goals / Non-Goals

**Goals:**

- Make Log Sources useful for folder-backed local logs and per-file selection.
- Let users analyze either selected source files or ad hoc standalone files from the computer.
- Remove the Course Demo section from navigation and workspace setup.
- Present detection rule details from the existing local `DetectionConfig`.
- Store timestamped analysis runs in the desktop session and export a selected run.
- Keep all actions local-only.

**Non-Goals:**

- Change parser behavior, detection logic, exporter formats, or CLI behavior.
- Persist analysis history across app restarts.
- Recursively crawl folders by default.
- Add remote sources, URLs, uploads, monitoring daemons, or network behavior.

## Decisions

### Model UI Log Sources as Local Path Entries

The desktop window will track a folder source and a derived list of regular files under that folder. Folder selection uses `QFileDialog.getExistingDirectory()`. The default folder mode includes all files directly inside the folder and excludes subdirectories.

Alternative considered: recursive folder crawling. This was rejected for the default behavior because it can unexpectedly include too much data and complicates course/demo expectations.

### Keep Analysis Selection in the UI Layer

Analysis will still call `analyze_logs(paths)`. The desktop UI decides which `Path` list to pass:

- selected files from the configured folder source
- standalone files chosen from the computer

This keeps the analysis pipeline stable and makes the change frontend-scoped.

### Store Session Analysis History In Memory

Add a small session history list on `LogcheckDesktop`, storing timestamp label, selected paths, and `AnalysisResult`. Each successful analysis appends one entry and updates export controls. Export chooses the selected history entry instead of implicitly using only `latest_result`.

Alternative considered: write history metadata to disk. Rejected because the request only needs choosing among runs in the current UI flow and persistent history would expand scope.

### Render Rule Details from Existing Config

The Detection Rules section should read from `default_config()` or `load_config(None)` and display keyword groups plus brute-force threshold/window. This avoids duplicating rule definitions in UI text.

### Remove Course Demo Navigation

`nav_demo` will be removed from `NAV_ITEMS`, UI copy, and section construction. Course demo text is no longer part of the production desktop workflow.

## Risks / Trade-offs

- Large folder selection -> Display file count and keep non-recursive default to avoid surprise.
- Empty folders -> Show an empty-state message and prevent analysis until files are selected.
- Multiple report runs -> Use stable timestamp labels and default the export selector to the latest successful run.
- Tests around dialogs -> Patch dialog functions in tests and test helper methods directly where possible.
```

## openspec/changes/enhance-desktop-log-workflow/tasks.md

- Source: openspec/changes/enhance-desktop-log-workflow/tasks.md
- Lines: 1-23
- SHA256: 5419a376cd0ceea14ec90aefd00ed85db1ae53844b117a88a41ee4c8848363f5

```md
## 1. OpenSpec and Comet Setup

- [ ] 1.1 Create proposal, design, delta spec, and implementation tasks for enhanced desktop log workflow.
- [ ] 1.2 Initialize Comet state and pass the open-phase guard.

## 2. Desktop Source Selection Tests

- [ ] 2.1 Add failing tests for folder log source discovery and selected source file analysis.
- [ ] 2.2 Add failing tests for standalone local file analysis.

## 3. Desktop Workflow Implementation

- [ ] 3.1 Add folder log source selection and direct-file discovery.
- [ ] 3.2 Add source file selection state and analysis path resolution.
- [ ] 3.3 Remove Course Demo navigation and section construction.
- [ ] 3.4 Render detection rule details from the local detection configuration.
- [ ] 3.5 Store timestamped successful analysis runs in session history.
- [ ] 3.6 Export reports from the selected analysis history entry.

## 4. Verification and Delivery

- [ ] 4.1 Run focused desktop tests and the full test suite.
- [ ] 4.2 Complete Comet verify/archive, commit, push, and create a PR to `unjoke/logcheck.git`.
```

## openspec/changes/enhance-desktop-log-workflow/specs/desktop-frontend/spec.md

- Source: openspec/changes/enhance-desktop-log-workflow/specs/desktop-frontend/spec.md
- Lines: 1-67
- SHA256: aff16586f5d481bf3a8f1c64bcb41fedfcde7d9015649a741fc11c479d10b0fe

```md
## ADDED Requirements

### Requirement: Select log source folders
The desktop frontend SHALL allow users to choose a local folder as a log source.

#### Scenario: Folder source includes direct files by default
- **WHEN** the user selects a local log source folder
- **THEN** the desktop UI lists all regular files directly under that folder as candidate log files

#### Scenario: Empty folder source
- **WHEN** the selected folder contains no regular files
- **THEN** the desktop UI reports that no log files are available from that source

### Requirement: Analyze selected source files or standalone files
The desktop frontend SHALL allow analysis from selected log-source files or from standalone local files selected from the computer.

#### Scenario: Analyze selected source files
- **WHEN** the user has selected one or more files from the configured log source
- **THEN** starting analysis uses those selected files

#### Scenario: Analyze standalone local files
- **WHEN** the user chooses standalone local files from the computer
- **THEN** starting analysis uses those chosen files without requiring a configured log source folder

### Requirement: Remove course demo navigation
The desktop frontend SHALL NOT include the unused Course Demo sidebar navigation entry or workspace section.

#### Scenario: Navigation omits course demo
- **WHEN** the desktop window is displayed
- **THEN** the left navigation does not include a Course Demo button

### Requirement: Present detection rule details
The desktop frontend SHALL display detection rule details from the local detection configuration.

#### Scenario: Show keyword rules
- **WHEN** the user opens the Detection Rules section
- **THEN** the UI lists configured keyword groups and their indicator terms

#### Scenario: Show brute-force rule parameters
- **WHEN** the user opens the Detection Rules section
- **THEN** the UI shows the brute-force threshold and time window

### Requirement: Export a selected analysis run
The desktop frontend SHALL let users select which timestamped local analysis run to export.

#### Scenario: Store successful analysis in history
- **WHEN** a local analysis completes successfully
- **THEN** the desktop UI adds the result to a timestamped analysis history for the current session

#### Scenario: Export selected historical run
- **WHEN** the user chooses a timestamped analysis run and exports reports
- **THEN** the exported JSON, CSV, and Markdown files are generated from that selected run

#### Scenario: Export without analysis history
- **WHEN** no successful analysis run exists
- **THEN** the desktop UI reports that analysis must run before exporting

### Requirement: Preserve local-only safety boundary for enhanced workflow
The enhanced desktop workflow SHALL remain limited to local files and local report output.

#### Scenario: No remote source controls
- **WHEN** the user configures log sources or analysis inputs
- **THEN** the UI exposes only local file and local folder selection controls

#### Scenario: No network behavior added
- **WHEN** the enhanced desktop workflow is used
- **THEN** it does not add URL inputs, domain access, remote uploads, network scanning, blocking, exploitation, or remote reporting
```

