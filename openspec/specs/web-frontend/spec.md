## Purpose

Define the browser-based local Logcheck workspace, including local analysis, source context review, exports, safety boundaries, and verification evidence.

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
