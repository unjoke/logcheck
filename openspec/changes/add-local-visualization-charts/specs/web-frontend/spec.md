## ADDED Requirements

### Requirement: Show local visual report charts
The web frontend SHALL show local visualization charts derived from the latest Logcheck analysis result.

#### Scenario: Display charts after local analysis
- **WHEN** the user runs analysis against local sample logs or uploaded local log files
- **THEN** the web frontend displays source/entity frequency, time or evidence-order distribution, and severity distribution charts
- **AND** the charts are derived from local analysis results already available to the frontend

#### Scenario: Chart empty states
- **WHEN** no analysis has run or the latest analysis has no findings
- **THEN** the visual report area shows a clear empty state instead of broken or stale charts

#### Scenario: Charts preserve local-only safety
- **WHEN** the visual report area is displayed
- **THEN** it does not introduce URL inputs, domain inputs, remote fetching, network scanning, blocking, exploitation, or external reporting controls

#### Scenario: Charts remain responsive
- **WHEN** the dashboard is viewed on desktop and mobile-width viewports
- **THEN** the chart area remains readable without horizontal overflow or overlapping text

### Requirement: Highlight privilege-escalation evidence in local review
The web frontend SHALL make passive privilege-escalation evidence easy to identify in local analysis results.

#### Scenario: Privilege-escalation indicators appear in findings
- **WHEN** local logs contain sudo failure, su failure, sensitive-file access, or admin/root path access indicators
- **THEN** the analysis result includes findings whose rule identifiers or explanations clearly identify privilege-escalation behavior
- **AND** the evidence remains tied to local source file and line context

#### Scenario: Privilege-escalation remains passive
- **WHEN** privilege-escalation evidence is displayed
- **THEN** the dashboard provides review-oriented evidence and suggestions only
- **AND** it does not perform account changes, blocking, exploitation, remote access, or system modification

### Requirement: Provide richer local incident sample
The project SHALL include a bundled local incident sample suitable for coursework demonstration.

#### Scenario: Incident sample exercises major report sections
- **WHEN** the user analyzes the bundled incident sample
- **THEN** the result includes enough local findings to populate source/entity, time or evidence-order, and severity charts
- **AND** the sample includes brute-force, invalid-user, unauthorized-access, privilege-escalation, suspicious-command, and benign baseline lines

