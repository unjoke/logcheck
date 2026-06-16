## ADDED Requirements

### Requirement: TOML as default rule configuration format
The rule configuration SHALL use TOML as the default format, with JSON and YAML as supported alternatives.

#### Scenario: Load valid TOML rule file
- **WHEN** a `.toml` rule file defines indicator_rules, pattern_rules, correlation_rules, and severity_thresholds sections
- **THEN** the system parses and applies all rule definitions without error

#### Scenario: Reject malformed TOML rule file
- **WHEN** a `.toml` rule file contains invalid syntax
- **THEN** the system raises a clear error indicating the parse failure location

#### Scenario: JSON rule file loads as alternative
- **WHEN** a `.json` rule file defines equivalent rule structure
- **THEN** the system parses and applies the rules identically to TOML

### Requirement: Indicator rule definition
Each indicator rule SHALL define a single-event detection condition with a configurable score contribution.

#### Scenario: Keyword indicator rule
- **WHEN** an indicator rule specifies text_contains with one or more keywords
- **AND** an event's text contains any of those keywords
- **THEN** the rule matches and contributes its score to the finding

#### Scenario: Category-scoped indicator rule
- **WHEN** an indicator rule specifies event_category
- **AND** the event does not match that category
- **THEN** the rule SHALL NOT match

#### Scenario: Regex indicator rule
- **WHEN** an indicator rule specifies a regex pattern
- **AND** the event text matches the regex
- **THEN** the rule matches and extracts named capture groups as match metadata

### Requirement: Pattern rule definition
Each pattern rule SHALL define multi-event behavior detection with required indicators, minimum events, and score contribution.

#### Scenario: Pattern activates when indicator and event thresholds met
- **WHEN** a pattern rule requires indicators ["sql_injection_substr", "sql_injection_if"]
- **AND** a grouped set of events has at least min_events matching those indicators
- **THEN** the pattern rule activates and contributes its score

#### Scenario: Pattern does not activate below event threshold
- **WHEN** a pattern rule has min_events set to 5
- **AND** only 3 grouped events match the required indicators
- **THEN** the pattern rule SHALL NOT activate

### Requirement: Correlation rule definition
Each correlation rule SHALL define cross-entity or cross-category detection with minimum diversity requirements.

#### Scenario: Correlation activates across detection categories
- **WHEN** a correlation rule requires min_distinct_categories of 2
- **AND** a source entity has findings in two different categories
- **THEN** the correlation rule activates and adds its score bonus

### Requirement: Severity threshold configuration
The severity_thresholds section SHALL define the score ranges for each severity level.

#### Scenario: Custom severity thresholds override defaults
- **WHEN** a rule file defines severity_thresholds with low=0, medium=30, high=60, critical=85
- **THEN** score 25 maps to "low" (below custom medium=30)

#### Scenario: Missing threshold defaults to built-in value
- **WHEN** a rule file omits the severity_thresholds section
- **THEN** the system SHALL use default thresholds: low=0, medium=20, high=50, critical=80
