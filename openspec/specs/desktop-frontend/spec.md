## Purpose

Define the local desktop frontend for Logcheck analysis, including workspace layout, local file analysis actions, report export, and meaningful sidebar navigation while preserving the local-only safety boundary.

## Requirements

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

### Requirement: Sidebar navigation actions are meaningful
The desktop front end SHALL ensure every left sidebar button either switches the visible workspace section to matching content or triggers the existing local function named by the button.

#### Scenario: Switch to overview section
- **WHEN** the user clicks the Overview sidebar button
- **THEN** the main workspace displays the analysis overview section

#### Scenario: Open local log source selection
- **WHEN** the user clicks the Log Sources sidebar button
- **THEN** the desktop UI invokes the local log file selection workflow

#### Scenario: Switch to rule section
- **WHEN** the user clicks the Detection Rules sidebar button
- **THEN** the main workspace displays detection rule status content

#### Scenario: Switch to suspicious source section
- **WHEN** the user clicks the Suspicious Sources sidebar button
- **THEN** the main workspace displays suspicious source content derived from the latest local analysis when available

#### Scenario: Trigger report export
- **WHEN** the user clicks the Export Report sidebar button
- **THEN** the desktop UI invokes the existing local report export workflow

#### Scenario: Switch to course demo section
- **WHEN** the user clicks the Course Demo sidebar button
- **THEN** the main workspace displays local course demonstration content

### Requirement: Sidebar buttons provide click feedback
The desktop front end SHALL provide visible hover, pressed, and selected states for left sidebar buttons.

#### Scenario: Highlight selected sidebar section
- **WHEN** a sidebar section is selected
- **THEN** that button is visually distinguished from unselected sidebar buttons

#### Scenario: Show tactile button state
- **WHEN** the user hovers over or presses a sidebar button
- **THEN** the button appearance changes to communicate that it is clickable
