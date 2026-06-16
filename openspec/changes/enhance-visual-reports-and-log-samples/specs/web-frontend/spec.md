## ADDED Requirements

### Requirement: Present visual attack analytics
The web frontend SHALL present local visual analytics for completed analyses using the latest local analysis result.

#### Scenario: Source IP statistics are shown
- **WHEN** a local analysis result contains findings with source addresses
- **THEN** the report displays a visual source-address distribution ranked by finding count
- **AND** the report preserves the source-address values in readable text or table form

#### Scenario: Time distribution is shown
- **WHEN** a local analysis result contains timestamped findings
- **THEN** the report displays a visual time distribution of findings across appropriate time buckets
- **AND** findings without timestamps do not break chart rendering

#### Scenario: Rule and severity context are shown
- **WHEN** a local analysis result contains findings with rule ids and severities
- **THEN** the report displays visual summaries for severity and rule distribution
- **AND** the summaries are based on the latest completed analysis result

### Requirement: Keep visualization local and passive
The web frontend SHALL keep report visualization local, offline-capable, and passive.

#### Scenario: Charts do not introduce active security actions
- **WHEN** the visual report renders
- **THEN** it does not display remote scan controls, exploit controls, blocking controls, external reporting controls, or domain/IP action buttons

#### Scenario: Runtime visualization works without internet access
- **WHEN** the web frontend is served from the local Flask app after dependencies are installed
- **THEN** the visual report can render without fetching chart scripts or data from external networks

#### Scenario: Chart failure preserves reviewability
- **WHEN** the selected chart renderer fails to load or render
- **THEN** the report still exposes the underlying local summary values in readable text or table form

### Requirement: Support chart-library evaluation
The frontend implementation SHALL include a documented evaluation path for selecting a chart renderer suitable for this static local dashboard.

#### Scenario: Candidate libraries are compared
- **WHEN** implementation begins
- **THEN** Apache ECharts and Chart.js are compared against the existing local analysis payload shape
- **AND** React-only options such as Recharts or Nivo are documented as non-primary unless the frontend stack changes

#### Scenario: Selected renderer is isolated
- **WHEN** a renderer is selected
- **THEN** chart-data preparation is separated from renderer-specific chart configuration
- **AND** tests can validate chart datasets without requiring external network access
