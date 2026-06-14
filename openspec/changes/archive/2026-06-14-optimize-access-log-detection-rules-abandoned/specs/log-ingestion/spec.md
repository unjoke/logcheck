## MODIFIED Requirements

### Requirement: Normalize richer event metadata
The log ingestion capability SHALL preserve source context needed for frontend review, insight generation, reports, and behavior-rule grouping.

#### Scenario: Preserve source context
- **WHEN** a local log line is parsed
- **THEN** the event includes source file, line number, raw line, category, timestamp when available, actor, target, source address, and parser confidence when available

#### Scenario: Mixed format batch
- **WHEN** local batch input contains Linux authentication logs, system logs, generic application logs, and common access logs
- **THEN** the system normalizes known patterns and preserves unknown lines as unknown events

#### Scenario: Preserve access request metadata
- **WHEN** the parser reads a common access log line with a client IP, timestamp, HTTP request, status code, response size, referrer, and user agent
- **THEN** it creates an access-category event with source address, target path, request method, request text, status code, response size, user agent, raw line, source file, and line number when those fields are available

## ADDED Requirements

### Requirement: Decode access request context for local rules
The log ingestion capability SHALL make URL-encoded access request context available to local behavior rules without changing the stored raw evidence line.

#### Scenario: Encoded request remains reviewable
- **WHEN** a common access log request contains URL-encoded query text
- **THEN** the parsed event preserves the original raw line for evidence
- **AND** downstream detection can inspect decoded request text for local rule matching

