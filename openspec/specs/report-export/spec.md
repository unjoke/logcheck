## Purpose

Define local report export behavior for insights, source context, existing JSON, CSV, and Markdown compatibility, and web analysis result downloads.

## Requirements

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

### Requirement: Export selected web analysis result
The report export capability SHALL return a downloadable local report for a completed web analysis result identified by analysis id.

#### Scenario: Web export succeeds after analysis
- **WHEN** a web analysis has completed and the caller requests JSON, CSV, or Markdown export with that analysis id
- **THEN** the system returns a downloadable report file for that result
- **AND** the report content preserves existing finding fields, insights when available, and source context metadata

#### Scenario: Web export uses supported filenames
- **WHEN** a supported web export format is requested
- **THEN** the downloaded filename is `analysis.json`, `analysis.csv`, or `analysis.md` according to the requested format
- **AND** the response content type matches the exported format closely enough for browsers to download it

### Requirement: Report web export errors clearly
The report export capability SHALL return clear local errors when a web export cannot be produced.

#### Scenario: Missing analysis id
- **WHEN** a web export request omits the analysis id
- **THEN** the system returns an error explaining that analysis must run and an analysis id is required before exporting

#### Scenario: Unknown analysis id
- **WHEN** a web export request references an analysis id that is not available in the current local session
- **THEN** the system returns an error explaining that analysis must run before exporting

#### Scenario: Unsupported export format
- **WHEN** a web export request uses an unsupported format
- **THEN** the system rejects the request without creating a report

#### Scenario: Exporter failure
- **WHEN** the local exporter cannot write or serve the report file
- **THEN** the system returns a clear local error
- **AND** it does not report a successful download
