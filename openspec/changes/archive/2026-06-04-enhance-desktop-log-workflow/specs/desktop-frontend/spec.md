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
