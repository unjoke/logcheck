# Comet Design Handoff

- Change: design-logcheck-desktop-frontend
- Phase: design
- Mode: compact
- Context hash: 1b833c0c46b2997a849a769e56bef3b4aa6b1c0c6dcda865abfdc62ea089e036

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/design-logcheck-desktop-frontend/proposal.md

- Source: openspec/changes/design-logcheck-desktop-frontend/proposal.md
- Lines: 1-28
- SHA256: 0b2a5cf6163a9fe37efaa65749b97f94e7975b1565c26b57cd05847743c3cf21

```md
## Why

Logcheck already works as a local command-line log intrusion detector, but a course demo and report screenshots need a more intuitive software front end. A desktop black-and-white window, similar in tone to the Codex interface reference, can make the analysis flow easier to present without changing the tool's local-only security posture.

## What Changes

- Add a desktop front-end capability for Logcheck analysis.
- Present a black-and-white application window with a top menu, left navigation, overview metrics, alert queue, log-source panel, rule status, and report export actions.
- Use `worktmp/logcheck_desktop_mockup.py` as the current visual reference for layout direction.
- Connect the future front end to the existing local log analysis pipeline and exported JSON/CSV/Markdown report outputs.
- Keep the interface focused on local files and local analysis; it SHALL NOT introduce network scanning, remote reporting, or domain access.

## Capabilities

### New Capabilities

- `desktop-frontend`: Defines the desktop Logcheck interface, visual structure, analysis workflow, and local-only UI constraints.

### Modified Capabilities

- None.

## Impact

- Affected areas: future desktop UI code, local analysis invocation, output display, and report export workflow.
- Existing CLI behavior and exported file formats remain intact.
- No new network capability is introduced.
- The temporary mockup file in `worktmp/logcheck_desktop_mockup.py` remains a design reference rather than production implementation.
```

## openspec/changes/design-logcheck-desktop-frontend/design.md

- Source: openspec/changes/design-logcheck-desktop-frontend/design.md
- Lines: 1-80
- SHA256: acfa03731d8bb86f7aa8587f957de118785ad6d9a6de525d658c1810f7f83a74

```md
## Context

Logcheck is currently a Python-based local log analysis tool. It reads local log files, normalizes events, detects intrusion indicators, and exports JSON/CSV/Markdown reports. The requested front end is a desktop software window, not a web application. The visual direction is a restrained black-and-white interface inspired by the Codex desktop screenshot and the existing `worktmp/logcheck_desktop_mockup.py` prototype.

The front end is primarily for course demonstration, screenshots, and easier review of analysis results. It must preserve the project's safety boundary: analyze local logs only, with no network scanning, blocking, exploitation, or remote reporting.

## Goals / Non-Goals

**Goals:**

- Provide a desktop application window that feels like a real Logcheck software interface.
- Use a black-and-white visual system with subtle gray panels, compact spacing, and clear information hierarchy.
- Let users select local log files, start analysis, inspect summary metrics, review findings, see evidence references, and export reports.
- Make the UI suitable for course screenshots and live demonstrations.
- Keep the future implementation compatible with the existing Python analysis pipeline.

**Non-Goals:**

- Build a web app or browser-based dashboard.
- Add real-time monitoring, remote telemetry, network scanning, exploit execution, or automated blocking.
- Redesign the core parser, rule engine, or exporter behavior.
- Replace the CLI; the desktop UI should complement it.

## Decisions

### Use a Desktop Shell Instead of a Web Front End

The interface SHALL be implemented as a local desktop window. A future implementation may use Python desktop tooling such as Tkinter, PySide, or CustomTkinter, but the product surface must remain a native window rather than a browser page.

Alternative considered: a web dashboard. This was rejected because the user explicitly asked for a software window and because local-only desktop presentation better matches the project's security constraints.

### Use the Mockup as the Visual Baseline

`worktmp/logcheck_desktop_mockup.py` establishes the first acceptable visual direction: dark shell, left navigation, top menu, overview cards, alert list, and right-side log/rule/export panel. The production UI should refine that structure rather than restart from an unrelated layout.

Alternative considered: a terminal-like single pane. This would be simpler, but it would not communicate the tool's workflow as clearly in screenshots.

### Keep the UI Information-Dense and Demonstration-Friendly

The UI should avoid landing-page composition. The first screen is the actual analysis workspace: file inputs, run action, metrics, findings, and export actions. Text should be concise and functional, with no in-app tutorial copy.

Alternative considered: a wizard flow. This can help beginners, but it hides the summary and findings behind steps, which is weaker for classroom demonstration.

### Bind UI State to Existing Analysis Results

The desktop UI should call the existing local analysis path, then render structured output from the result model or JSON export. It should show:

- total parsed events
- finding counts by severity
- top suspicious sources
- findings with rule, severity, source, target, evidence, and source file reference
- export status for JSON, CSV, and Markdown

This keeps the front end thin and reduces the chance of diverging from CLI behavior.

### Preserve Local-Only Safety Constraints

The UI SHALL make local mode visible and SHALL NOT provide fields or actions for URLs, remote hosts, domain scans, attack actions, or remote upload. Any future file picker should accept local files only.

## Risks / Trade-offs

- UI toolkit mismatch -> Choose the toolkit after confirming packaging needs; keep the spec focused on behavior and layout.
- Mockup encoding issues -> Treat the mockup as layout reference, and write production UI strings in UTF-8 source files.
- Overbuilding visual polish -> Prioritize a stable demo window, readable results, and export workflow before animations or advanced theming.
- Divergence from CLI analysis -> Render data returned by existing analysis/export modules instead of duplicating detection logic in the UI.

## Migration Plan

1. Keep the CLI unchanged.
2. Add the desktop front end as a separate entry point or module.
3. Use sample logs for initial demo data and screenshots.
4. Wire the UI to existing analysis functions.
5. Validate with unit tests for data mapping and manual screenshot checks for visual layout.

Rollback is straightforward: remove or ignore the desktop entry point while retaining the existing CLI.

## Open Questions

- Which desktop toolkit should be used for the production version: Tkinter for zero dependencies, or a richer toolkit for more polished controls?
- Should the production front end be packaged as a standalone executable, or is running through Python acceptable for the course demo?
```

## openspec/changes/design-logcheck-desktop-frontend/tasks.md

- Source: openspec/changes/design-logcheck-desktop-frontend/tasks.md
- Lines: 1-32
- SHA256: cdb482eeb4b8619086e780f258f17cbcda8c8b30e8ff07cfe511f449add0e958

```md
## 1. Front-End Structure

- [ ] 1.1 Choose the production desktop UI toolkit and document the reason.
- [ ] 1.2 Create a desktop UI entry point separate from the existing CLI.
- [ ] 1.3 Build the top menu, left navigation, main analysis workspace, findings area, and side details panel.
- [ ] 1.4 Apply the black-and-white visual style based on `worktmp/logcheck_desktop_mockup.py`.

## 2. Analysis Workflow

- [ ] 2.1 Add local log file selection for one or more files.
- [ ] 2.2 Invoke the existing Logcheck analysis pipeline from the UI.
- [ ] 2.3 Map analysis results into summary metrics, severity counts, suspicious sources, and finding rows.
- [ ] 2.4 Display missing or unreadable file errors without crashing the window.

## 3. Findings and Evidence

- [ ] 3.1 Render a finding queue with severity, source, target, rule/explanation, and evidence reference.
- [ ] 3.2 Provide a detail area for selected finding evidence and source file context.
- [ ] 3.3 Keep the UI readable at the target desktop window size.

## 4. Report Export

- [ ] 4.1 Add JSON, CSV, and Markdown export controls.
- [ ] 4.2 Reuse the existing exporter behavior for selected output formats.
- [ ] 4.3 Show export completion status and output location.

## 5. Safety and Verification

- [ ] 5.1 Ensure the UI exposes only local file inputs and local report actions.
- [ ] 5.2 Verify that no URL, domain scan, remote upload, blocking, or exploit controls are introduced.
- [ ] 5.3 Add focused tests for result-to-UI data mapping where practical.
- [ ] 5.4 Run existing unit tests and manually launch the desktop window for screenshot verification.
```

## openspec/changes/design-logcheck-desktop-frontend/specs/desktop-frontend/spec.md

- Source: openspec/changes/design-logcheck-desktop-frontend/specs/desktop-frontend/spec.md
- Lines: 1-74
- SHA256: 451ed15466bf328e14ba5be8e137bc596ab406012447052cf9250b2de0c8f13e

```md
## ADDED Requirements

### Requirement: Display desktop analysis workspace
The system SHALL provide a local desktop application window for Logcheck analysis.

#### Scenario: Open desktop window
- **WHEN** the user starts the desktop front end
- **THEN** the system displays a native software window rather than a browser page

#### Scenario: Show primary workspace on first screen
- **WHEN** the desktop window opens
- **THEN** the first screen includes local log inputs, an analysis action, summary metrics, findings, and export actions

### Requirement: Use black-and-white visual style
The system SHALL use a black-and-white visual style with subtle gray panels and compact information hierarchy.

#### Scenario: Render Codex-inspired shell
- **WHEN** the desktop front end is displayed
- **THEN** the window uses a dark background, light text, gray panel boundaries, a top menu area, and left navigation similar to the approved mockup direction

#### Scenario: Preserve readability
- **WHEN** findings and metrics are shown
- **THEN** text, numbers, severity labels, and file references remain readable without relying on bright multi-color decoration

### Requirement: Select and analyze local log files
The system SHALL allow the user to select one or more local log files and run Logcheck analysis from the desktop UI.

#### Scenario: Run analysis from selected files
- **WHEN** the user selects readable local log files and starts analysis
- **THEN** the system invokes the existing local analysis pipeline and displays the resulting metrics and findings

#### Scenario: Report missing or unreadable files
- **WHEN** a selected local file is missing or unreadable
- **THEN** the system reports the file problem in the UI without crashing

### Requirement: Display analysis summary
The system SHALL display a concise summary of the latest analysis result.

#### Scenario: Show metrics after analysis
- **WHEN** analysis completes successfully
- **THEN** the UI shows total parsed events, total findings, severity counts, and top suspicious sources

### Requirement: Display finding details
The system SHALL display finding details that support manual review and course demonstration.

#### Scenario: Show finding queue
- **WHEN** findings are available
- **THEN** the UI lists each finding with severity, rule or explanation, source, target when available, evidence reference, and source file reference

#### Scenario: Preserve evidence context
- **WHEN** the user reviews a finding
- **THEN** the UI provides enough evidence text or file-line reference to explain why the finding was produced

### Requirement: Export reports from desktop UI
The system SHALL allow users to export analysis results in the existing JSON, CSV, and Markdown formats from the desktop UI.

#### Scenario: Export requested formats
- **WHEN** the user chooses report export formats
- **THEN** the system writes the selected JSON, CSV, and Markdown outputs using the existing exporter behavior

#### Scenario: Show export completion
- **WHEN** export completes
- **THEN** the UI displays the output location or completion status

### Requirement: Preserve local-only safety boundary
The desktop front end SHALL remain a local analysis interface and MUST NOT introduce network scanning, remote upload, blocking, exploitation, or domain access.

#### Scenario: No remote target controls
- **WHEN** the user views available inputs and actions
- **THEN** the UI provides local file selection and local report actions only, with no URL, domain, host scanning, or remote upload controls

#### Scenario: Local mode visible
- **WHEN** the desktop window is displayed
- **THEN** the UI indicates that Logcheck is operating in local mode
```

