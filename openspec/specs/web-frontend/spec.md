## Purpose

Define the browser-based local Logcheck workspace, including local analysis, source context review, exports, safety boundaries, visualization, and verification evidence.

## Requirements

### Requirement: Provide browser-based Logcheck workspace
The system SHALL provide a browser-based Logcheck web application as the primary frontend.

#### Scenario: Open web workspace
- **WHEN** the user opens the Logcheck web frontend
- **THEN** the first screen presents the working analysis interface rather than a landing page or desktop-style GUI shell

#### Scenario: Choose implementation direction
- **WHEN** the web frontend rebuild begins
- **THEN** the implementation direction is selected from Local Investigation Dashboard, Log Review Workbench, or Guided Analysis Wizard

### Requirement: Support local log analysis workflow
The web frontend SHALL let users run Logcheck analysis against local log inputs and review structured local results.

#### Scenario: Analyze local logs
- **WHEN** the user provides local log files or approved local sample logs and starts analysis
- **THEN** the web frontend runs the existing local analysis pipeline and displays summary, findings, evidence, and insights

#### Scenario: Preserve local source context
- **WHEN** findings or insights are displayed
- **THEN** the web frontend shows source context including file, line, raw evidence, actor, target, source address, or parser confidence when available

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

### Requirement: Export reports from web frontend
The web frontend SHALL expose local report export actions for supported report formats.

#### Scenario: Export latest result
- **WHEN** analysis has completed and the user requests an export
- **THEN** the web frontend writes or downloads a local JSON, CSV, or Markdown report using the existing exporter behavior

#### Scenario: Export before analysis
- **WHEN** the user requests an export before a result exists
- **THEN** the web frontend reports that analysis must run before exporting

### Requirement: Preserve local-only safety boundary
The web frontend MUST remain a local analysis interface and MUST NOT introduce remote target actions.

#### Scenario: Forbidden remote controls absent
- **WHEN** the web frontend is displayed
- **THEN** it does not show URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, or external reporting controls

#### Scenario: CTF redirect environment remains safe
- **WHEN** the project is demonstrated in an environment where domains redirect to `192.168.2.1`
- **THEN** the web frontend workflow does not depend on domain entry, external browsing, or remote fetching

### Requirement: Verify web frontend visually and automatically
The web frontend SHALL be covered by focused automated checks and browser-based visual verification.

#### Scenario: Automated web checks
- **WHEN** the web frontend test suite is run
- **THEN** tests cover local input handling, analysis result rendering, report export states, and absence of forbidden remote controls

#### Scenario: Browser visual verification
- **WHEN** the implemented web frontend is reviewed in a browser
- **THEN** screenshots or notes show that the selected web application shape is readable, non-overlapping, and usable on target desktop and mobile-width viewports

### Requirement: Manage export controls from analysis state
The web frontend SHALL manage report export controls according to the latest local analysis state.

#### Scenario: Export disabled before analysis
- **WHEN** no local analysis result is available
- **THEN** JSON, CSV, and Markdown export controls are unavailable or report that analysis must run before exporting

#### Scenario: Export uses latest analysis id
- **WHEN** a local analysis completes successfully and the user requests an export
- **THEN** the frontend calls the export endpoint with the latest returned analysis id
- **AND** it does not use a stale analysis id from an earlier failed or replaced analysis

#### Scenario: Export failure is visible
- **WHEN** the export endpoint returns an error
- **THEN** the frontend displays or exposes a clear local error state instead of silently failing

### Requirement: Preserve local-only export UX
The web frontend SHALL keep export behavior local and passive.

#### Scenario: Export controls do not introduce remote targets
- **WHEN** the export controls are displayed
- **THEN** they do not introduce URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, or external reporting controls

#### Scenario: Browser download remains local report output
- **WHEN** the user downloads a report from the web frontend
- **THEN** the downloaded content is generated from local analysis results already held by the application
- **AND** the workflow does not require external browsing or internet access
