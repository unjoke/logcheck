## MODIFIED Requirements

### Requirement: Support configurable rules
The system SHALL load detection rules and thresholds from a local configuration file while providing secure defaults when no configuration is supplied.

#### Scenario: Use default rules
- **WHEN** the user runs analysis without a custom rule file
- **THEN** the system applies the default course-demo rule set

#### Scenario: Use custom threshold
- **WHEN** the user supplies a configuration file with a changed brute-force threshold
- **THEN** the system applies that threshold in the repeated-behavior analysis

#### Scenario: Load JSON rule file
- **WHEN** the user supplies a readable local JSON rule file with `keywords` and optional `brute_force` settings
- **THEN** the system loads keyword groups and brute-force parameters from that file
- **AND** subsequent analysis uses the loaded rule configuration

#### Scenario: Load YAML rule file when parser is available
- **WHEN** the user supplies a readable local YAML rule file with `keywords` and optional `brute_force` settings
- **AND** the local runtime has YAML parser support
- **THEN** the system loads keyword groups and brute-force parameters from that file
- **AND** subsequent analysis uses the loaded rule configuration

#### Scenario: Reject invalid structured rule file
- **WHEN** a supplied JSON or YAML rule file is malformed or does not contain the expected structured values
- **THEN** the system rejects the file with a clear error
- **AND** does not silently fall back to a different custom rule set

### Requirement: Export active rule configuration
The system SHALL serialize the active detection rule configuration to a local structured file that users can inspect and edit.

#### Scenario: Export rules as JSON
- **WHEN** the user requests a rule configuration download from the desktop frontend
- **THEN** the system writes the active keyword groups and brute-force parameters as readable JSON

#### Scenario: Exported rules can be re-imported
- **WHEN** the user imports a rule JSON file previously exported by the system
- **THEN** the loaded detection configuration is equivalent to the exported active configuration
