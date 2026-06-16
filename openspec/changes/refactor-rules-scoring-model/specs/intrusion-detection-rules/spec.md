## MODIFIED Requirements

### Requirement: Detect configurable behavior patterns
The intrusion detection rules capability SHALL detect configurable behavior patterns through a three-tier scoring pipeline (indicator → pattern → correlation) with numerical score accumulation, replacing hardcoded severity assignments.

#### Scenario: Suspicious command pattern
- **WHEN** parsed events contain suspicious command execution indicators
- **THEN** the system emits a pattern-tier finding with rule identifier, numerical score, confidence, severity (mapped from score), matched evidence, and explanation

#### Scenario: Multi-signal suspicious actor
- **WHEN** one actor or source address triggers multiple lower-severity indicators in a local analysis run
- **THEN** the system SHALL emit a correlation-tier finding with cumulative score reflecting all contributing indicators and a correlation bonus

#### Scenario: SQL injection severity reflects attack characteristics
- **WHEN** a single URL-encoded request contains one SQL injection indicator
- **THEN** the finding severity SHALL be "low" or "medium" (based on the single indicator score)
- **AND** SHALL NOT be "critical" unless multiple indicators, sustained enumeration, or data extraction patterns are detected

#### Scenario: Sustained SQL injection enumeration maps to critical
- **WHEN** a source sends 50+ requests with boolean-blind SQL injection indicators across 10+ distinct character positions
- **AND** the requests span information_schema enumeration and data extraction attempts
- **THEN** the cumulative score SHALL map to "critical" severity

### Requirement: Explain severity and confidence
The intrusion detection rules capability SHALL explain why each finding received its numerical score, severity, and confidence through both human-readable reasons and quantifiable metrics.

#### Scenario: Severity explanation
- **WHEN** the system emits a finding
- **THEN** the finding includes a numerical score (0-100), a severity label mapped from that score, and a human-readable severity reason

#### Scenario: Confidence explanation
- **WHEN** the system emits a finding from a behavior pattern
- **THEN** the finding includes a numerical confidence value (0-100), and a human-readable confidence reason that distinguishes exact matches, repeated behavior diversity, and correlated signals

#### Scenario: Score breakdown available
- **WHEN** a finding results from multiple contributing rules
- **THEN** the finding SHALL include the list of contributing indicator rule IDs

### Requirement: Validate enhanced rule configuration safely
The intrusion detection rules capability SHALL validate enhanced local rule configuration before applying it.

#### Scenario: Reject unsafe or malformed enhanced rules
- **WHEN** a local rule file contains malformed behavior patterns, invalid thresholds, or unsupported rule fields
- **THEN** the system rejects the file with a clear error
- **AND** it does not silently apply partial unsafe configuration

#### Scenario: Validate score ranges
- **WHEN** a rule file specifies indicator scores or severity thresholds outside the valid 0-100 range
- **THEN** the system SHALL reject the configuration with an error describing the invalid range

## REMOVED Requirements

### Requirement: Static SEVERITY_BY_RULE mapping
**Reason**: Replaced by the configurable score-to-severity mapping in the scoring engine. The old static mapping (SEVERITY_BY_RULE dict in rules.py) could not express context-dependent severity and forced all matches of a given rule name to the same severity regardless of attack characteristics.

**Migration**: Severity is now determined by the cumulative numerical score crossing configurable thresholds. Existing rule names map to indicator/pattern rules in the default rule configuration file, each with appropriate score contributions.
