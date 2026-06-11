## ADDED Requirements

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
