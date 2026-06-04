## Purpose
The report export capability presents analysis summaries and writes detailed local reports in formats suitable for review, demos, and course-report material.

## Requirements

### Requirement: Display terminal summary
The system SHALL display a concise terminal summary after analysis.

#### Scenario: Summary after successful analysis
- **WHEN** analysis completes successfully
- **THEN** the terminal output includes total files, total parsed events, finding count by severity, and top suspicious sources

### Requirement: Export detailed analysis logs
The system SHALL export detailed analysis results to JSON and CSV formats.

#### Scenario: JSON export requested
- **WHEN** the user requests JSON output
- **THEN** the system writes a JSON file containing metadata, parsed-event counts, findings, and evidence records

#### Scenario: CSV export requested
- **WHEN** the user requests CSV output
- **THEN** the system writes a CSV file containing one row per finding with rule, severity, source, target, timestamp, and evidence fields

### Requirement: Produce report-friendly Markdown
The system SHALL generate a Markdown report suitable for screenshots, demo explanation, and inclusion in the course paper.

#### Scenario: Markdown report requested
- **WHEN** the user requests Markdown output
- **THEN** the system writes a report containing overview metrics, rule summaries, key findings, and interpretation notes
