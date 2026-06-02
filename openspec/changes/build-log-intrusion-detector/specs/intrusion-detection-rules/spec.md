## ADDED Requirements

### Requirement: Detect keyword indicators
The system SHALL detect intrusion-related keywords such as failed login, unauthorized access, invalid user, authentication failure, permission denied, sudo failure, and suspicious command execution.

#### Scenario: Failed login keyword match
- **WHEN** a parsed log event contains a failed-login indicator
- **THEN** the system emits a finding with a rule identifier, severity, matched keyword, evidence line, and explanation

### Requirement: Detect repeated suspicious behavior
The system SHALL detect repeated suspicious behavior from the same actor or source address within a configurable time window.

#### Scenario: Brute force threshold exceeded
- **WHEN** one source address produces failed-login events at or above the configured threshold within the time window
- **THEN** the system emits a brute-force finding with the source address, count, window, severity, and supporting evidence

### Requirement: Support configurable rules
The system SHALL load detection rules and thresholds from a local configuration file while providing secure defaults when no configuration is supplied.

#### Scenario: Use default rules
- **WHEN** the user runs analysis without a custom rule file
- **THEN** the system applies the default course-demo rule set

#### Scenario: Use custom threshold
- **WHEN** the user supplies a configuration file with a changed brute-force threshold
- **THEN** the system applies that threshold in the repeated-behavior analysis

### Requirement: Classify finding severity
The system SHALL classify each finding as low, medium, high, or critical based on rule type, event count, and confidence.

#### Scenario: Severity appears in result
- **WHEN** the system emits a finding
- **THEN** the finding includes a severity value suitable for terminal display and report export
