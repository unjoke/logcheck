## Purpose

Generate local investigation insight summaries, entity profiles, timelines, and safe remediation suggestions from parsed log events and findings.

## Requirements

### Requirement: Generate local investigation insights
The system SHALL generate local investigation insights from parsed events and detected findings without using network access or external services.

#### Scenario: Insight summary after analysis
- **WHEN** analysis completes with one or more findings
- **THEN** the system produces an insight summary describing the most important suspicious behavior, affected entities, and evidence references
- **AND** the summary is derived only from local parsed events and findings

#### Scenario: No findings insight
- **WHEN** analysis completes with parsed events but no findings
- **THEN** the system produces a low-risk insight summary that states no configured rule patterns were detected

### Requirement: Profile suspicious entities
The system SHALL identify suspicious local entities such as source addresses, actors, targets, and files from analysis results.

#### Scenario: Entity profile includes evidence
- **WHEN** a source address, actor, target, or file appears in multiple findings
- **THEN** the system creates an entity profile with finding count, severity distribution, related rules, and evidence references

#### Scenario: Unknown entity handling
- **WHEN** a finding lacks source address or actor information
- **THEN** the system preserves the finding in an unknown-entity group instead of discarding it

### Requirement: Highlight incident timeline
The system SHALL produce a concise timeline of notable local log activity.

#### Scenario: Timeline highlights suspicious sequence
- **WHEN** multiple findings have timestamps
- **THEN** the system orders notable activity by time and includes rule, entity, severity, and source-file context

#### Scenario: Missing timestamps
- **WHEN** findings do not contain timestamps
- **THEN** the system still provides ordered evidence based on file and line references where available

### Requirement: Suggest local remediation steps
The system SHALL provide local remediation suggestions that are safe, review-oriented, and non-destructive.

#### Scenario: Suggestions remain non-destructive
- **WHEN** insights include remediation suggestions
- **THEN** the suggestions describe manual review, account audit, password policy, rule tuning, or log collection steps
- **AND** they do not perform blocking, scanning, exploitation, remote access, or system modification
