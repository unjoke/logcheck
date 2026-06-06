## ADDED Requirements

### Requirement: Report local batch ingestion diagnostics
The log ingestion capability SHALL report diagnostics for local batch inputs while continuing to parse readable files.

#### Scenario: Mixed readable and unreadable files
- **WHEN** a batch includes readable files and files that are missing or unreadable
- **THEN** the system reports diagnostics for the problem files
- **AND** the readable files remain available for analysis when the caller supports partial results

#### Scenario: Empty local file
- **WHEN** a selected local file contains no parseable lines
- **THEN** the system records a diagnostic indicating that the file contributed no events

### Requirement: Normalize richer event metadata
The log ingestion capability SHALL preserve source context needed for frontend review, insight generation, and reports.

#### Scenario: Preserve source context
- **WHEN** a local log line is parsed
- **THEN** the event includes source file, line number, raw line, category, timestamp when available, actor, target, source address, and parser confidence when available

#### Scenario: Mixed format batch
- **WHEN** local batch input contains Linux authentication logs, system logs, and generic application logs
- **THEN** the system normalizes known patterns and preserves unknown lines as unknown events
