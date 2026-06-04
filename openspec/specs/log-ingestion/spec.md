## Purpose
The log ingestion capability accepts local log files and normalizes common log formats into analysis-ready event records while handling malformed input safely.

## Requirements

### Requirement: Accept local log files
The system SHALL accept one or more local log file paths as analysis input.

#### Scenario: Analyze a single readable log file
- **WHEN** the user provides a readable local log file path
- **THEN** the system parses the file and includes its records in the analysis result

#### Scenario: Reject a missing log file
- **WHEN** the user provides a path that does not exist
- **THEN** the system reports the missing file and exits with a non-zero status

### Requirement: Normalize common log formats
The system SHALL normalize Linux authentication/system log lines and generic application log lines into event records containing timestamp, source file, raw line, category, actor, target, source address, and message fields where available.

#### Scenario: Parse Linux authentication log line
- **WHEN** the input contains an SSH failed-login line from `/var/log/auth.log` or equivalent sample data
- **THEN** the system extracts a normalized failed-login event with the source address and account name when present

#### Scenario: Preserve unknown log line
- **WHEN** the input contains a line that does not match a known parser
- **THEN** the system preserves the raw line as an unknown event instead of discarding it

### Requirement: Handle malformed input safely
The system SHALL continue analysis when individual log lines are malformed or partially missing fields.

#### Scenario: Encounter malformed line
- **WHEN** one line cannot be parsed into a known format
- **THEN** the system records it as an unknown or malformed event and continues parsing later lines
