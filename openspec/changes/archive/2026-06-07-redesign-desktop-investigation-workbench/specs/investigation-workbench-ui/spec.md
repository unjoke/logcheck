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
