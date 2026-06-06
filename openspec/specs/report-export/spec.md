## ADDED Requirements

### Requirement: Export local insight summaries
The report export capability SHALL include local investigation insights in supported report formats.

#### Scenario: JSON includes insights
- **WHEN** JSON export is requested after analysis with insights
- **THEN** the JSON output includes insight summary, entity profiles, timeline highlights, remediation suggestions, and evidence references

#### Scenario: Markdown includes readable insight section
- **WHEN** Markdown export is requested after analysis with insights
- **THEN** the Markdown output includes a readable investigation insight section suitable for demo review and coursework screenshots

### Requirement: Export selected source context
The report export capability SHALL include source-selection context for the exported analysis run.

#### Scenario: Export source context
- **WHEN** a report is exported from a selected analysis run
- **THEN** the report metadata includes analyzed file names or paths, event count, finding count, active rule source, and export timestamp

### Requirement: Preserve existing export compatibility
The report export capability SHALL preserve existing JSON, CSV, and Markdown report availability.

#### Scenario: Existing formats remain available
- **WHEN** the user exports reports after the comprehensive iteration
- **THEN** JSON, CSV, and Markdown outputs are still written locally
- **AND** existing finding-level fields remain available
