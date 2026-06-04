## ADDED Requirements

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
