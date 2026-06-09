## ADDED Requirements

### Requirement: Provide alert-focused review workflow
The web frontend SHALL provide a dedicated workflow for scanning local findings and reviewing one selected alert at a time.

#### Scenario: Findings are separately reviewable
- **WHEN** local analysis produces findings
- **THEN** the web frontend displays a distinct alert or finding list separate from investigation insight cards
- **AND** each list item identifies severity, rule, source file, and line number when available

#### Scenario: Selecting an alert updates detail
- **WHEN** the user selects a finding from the alert list
- **THEN** the selected state moves to that finding
- **AND** the alert detail area updates to show that finding's rule, severity, explanation, source metadata, and evidence

#### Scenario: No finding selection is available
- **WHEN** local analysis produces no findings
- **THEN** the alert review area shows an empty state
- **AND** it does not display stale details from a previous analysis result

### Requirement: Show detailed local log evidence for selected alerts
The web frontend SHALL show detailed local log evidence for the currently selected alert.

#### Scenario: Selected alert shows matched log line
- **WHEN** a selected finding contains evidence or matched log lines
- **THEN** the alert detail area renders the raw matched evidence as readable log text
- **AND** the detail area identifies the source file and line number associated with the evidence when available

#### Scenario: Selected alert shows available context fields
- **WHEN** a selected finding includes actor, target, source address, timestamp, matched keyword, count, severity reason, or confidence reason
- **THEN** the alert detail area displays those fields in a structured form
- **AND** absent fields do not create empty placeholder blocks

#### Scenario: Selected alert can show additional local detail
- **WHEN** the analysis result includes a single matched log line or other local detail for a selected finding
- **THEN** the alert detail area shows that available alert-specific log detail
- **AND** the detail remains visually distinct from generated insight text

#### Scenario: Long evidence remains readable
- **WHEN** selected alert evidence contains long file paths, long log messages, or multiple evidence lines
- **THEN** the alert detail area remains scrollable or wrapped within its panel
- **AND** it does not force page-level horizontal overflow

### Requirement: Keep insights separate from alert evidence
The web frontend SHALL present investigation insights as summary guidance that is separate from selected-alert evidence.

#### Scenario: Insights do not replace selected evidence
- **WHEN** both findings and generated insights are available
- **THEN** selecting a finding shows that finding's detailed evidence
- **AND** investigation insights remain separate summary or recommendation content

#### Scenario: Insight list remains concise
- **WHEN** many findings exist
- **THEN** the insights area shows concise summaries, risk information, affected entities, or suggestions
- **AND** it does not duplicate every alert as an unbounded list that crowds the evidence detail

### Requirement: Prevent visual report overlap
The web frontend SHALL keep visual report charts readable and non-overlapping across supported viewport widths.

#### Scenario: Long labels do not overlap chart groups
- **WHEN** chart labels include long source names, file paths, addresses, or entity names
- **THEN** labels remain constrained to their chart area
- **AND** they do not overlap neighboring chart columns, bars, or text

#### Scenario: Charts adapt to narrow viewports
- **WHEN** the dashboard is viewed at mobile-width or otherwise narrow viewport sizes
- **THEN** visual report chart groups stack or reflow into a readable layout
- **AND** the page does not require horizontal scrolling to read chart content
