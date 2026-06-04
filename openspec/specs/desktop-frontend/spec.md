## Purpose
The desktop frontend provides a local-only native UI for choosing log inputs, running Logcheck analysis, reviewing findings, viewing detection rules, and exporting analysis reports.

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
The system SHALL display finding details that support manual review.

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

### Requirement: Analyze selected existing source files from Log Sources
The desktop frontend SHALL allow users to select existing files shown in the Log Sources section and analyze only the selected files.

#### Scenario: Analyze one selected source file
- **WHEN** the user selects exactly one existing file from the configured log source
- **AND** the user starts analysis from Log Sources or Overview
- **THEN** the desktop frontend runs analysis using only that selected file

#### Scenario: Analyze multiple selected source files
- **WHEN** the user selects multiple existing files from the configured log source
- **AND** the user starts analysis from Log Sources or Overview
- **THEN** the desktop frontend runs analysis using only those selected files

#### Scenario: No selected source files
- **WHEN** a log source contains files but no source files are selected for analysis
- **AND** the user starts source-based analysis
- **THEN** the desktop frontend reports that at least one source file must be selected
- **AND** analysis does not run with an unintended file set

### Requirement: Reuse Log Sources selection from Overview
The desktop frontend SHALL let the overview analysis flow use the file selection maintained by Log Sources.

#### Scenario: Overview analyzes selected source file
- **WHEN** the user has selected a source file in Log Sources
- **AND** the user starts analysis from the overview screen
- **THEN** the selected source file is used as the overview analysis input

#### Scenario: Overview reflects source selection
- **WHEN** the user changes selected source files in Log Sources
- **THEN** the overview screen reflects the selected source count or selected source-file summary

### Requirement: Import local rule files from frontend
The desktop frontend SHALL provide a local file control for importing custom detection rule files.

#### Scenario: Import JSON rule file
- **WHEN** the user imports a readable local JSON rule file with valid rule structure
- **THEN** the desktop frontend uses those rules for subsequent analysis
- **AND** the Detection Rules section displays the imported keyword groups and brute-force parameters

#### Scenario: Import YAML rule file when supported
- **WHEN** the user imports a readable local YAML rule file
- **AND** the local runtime supports YAML parsing
- **THEN** the desktop frontend uses those rules for subsequent analysis

#### Scenario: YAML parser unavailable
- **WHEN** the user imports a YAML rule file
- **AND** the local runtime does not support YAML parsing
- **THEN** the desktop frontend reports that JSON is supported and YAML requires optional parser support
- **AND** the active rules remain unchanged

#### Scenario: Reject malformed rule file
- **WHEN** the user imports a malformed or structurally invalid rule file
- **THEN** the desktop frontend reports the rule-file problem without crashing
- **AND** the active rules remain unchanged

### Requirement: Download active rule file
The desktop frontend SHALL allow users to save the active detection rules to a local file for review or editing.

#### Scenario: Save active rules as JSON
- **WHEN** the user chooses to download or save the active rules
- **THEN** the desktop frontend writes a readable local JSON file containing the active keyword groups and brute-force parameters

#### Scenario: Save reports local output
- **WHEN** the active rules are saved successfully
- **THEN** the desktop frontend displays the local output path or completion status

### Requirement: Keep overview alert details from covering export controls
The desktop frontend SHALL lay out overview alert details and export controls so both remain visible and usable.

#### Scenario: Initial overview layout does not overlap
- **WHEN** the desktop window opens at its configured initial or minimum size
- **THEN** the alert details area does not cover or obscure export controls

#### Scenario: Export controls remain reachable after analysis
- **WHEN** analysis completes and alert details are populated
- **THEN** the export controls remain visible and clickable from the overview screen
