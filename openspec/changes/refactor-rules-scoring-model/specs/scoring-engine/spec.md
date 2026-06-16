## ADDED Requirements

### Requirement: Three-tier scoring pipeline
The scoring engine SHALL process events through a three-tier pipeline: indicator scanning, pattern detection, and correlation analysis.

#### Scenario: Single indicator match produces low-score finding
- **WHEN** a single event matches exactly one indicator rule with weight 2 and score 15
- **THEN** the engine emits a finding with score 15, tier "indicator", and severity mapped from the score

#### Scenario: Multiple indicators accumulate to higher score
- **WHEN** multiple events from the same source match two different indicator rules (scores 15 and 20 respectively)
- **AND** a pattern rule activates with score 40
- **THEN** the engine emits a pattern-tier finding whose score reflects the accumulated indicator scores plus the pattern score

#### Scenario: Correlation bonus raises severity tier
- **WHEN** a source triggers findings in two distinct detection categories
- **AND** a correlation rule with score 25 activates
- **THEN** the final finding's score includes the correlation bonus, potentially raising the severity to a higher tier

### Requirement: Score-to-severity mapping
The scoring engine SHALL map numerical scores (0-100) to severity labels using configurable thresholds.

#### Scenario: Score below medium threshold maps to low
- **WHEN** a finding has a cumulative score of 10
- **AND** the medium threshold is configured at 20
- **THEN** the finding severity is "low"

#### Scenario: Score above critical threshold maps to critical
- **WHEN** a finding has a cumulative score of 85
- **AND** the critical threshold is configured at 80
- **THEN** the finding severity is "critical"

#### Scenario: Default thresholds apply when not configured
- **WHEN** no severity thresholds are specified in the rule configuration
- **THEN** the engine SHALL use default thresholds: low=0, medium=20, high=50, critical=80

### Requirement: Independent confidence calculation
The scoring engine SHALL calculate confidence (0-100) independently from severity, based on indicator diversity, evidence quality, and rule-specific base confidence.

#### Scenario: High confidence from multiple diverse indicators
- **WHEN** a finding is supported by three distinct indicator types
- **AND** each indicator has decoded evidence available
- **THEN** the confidence score SHALL be at least 60

#### Scenario: Low confidence from single weak indicator
- **WHEN** a finding is supported by only one generic keyword match
- **AND** no structured evidence is available
- **THEN** the confidence score SHALL be below 40

### Requirement: Per-rule score capping
The scoring engine SHALL support optional maximum score limits per rule to prevent individual rules from inflating severity disproportionately.

#### Scenario: Rule score capped at configured maximum
- **WHEN** a pattern rule has max_final_score set to 75
- **AND** accumulated indicator scores plus pattern score would reach 90
- **THEN** the final finding score is capped at 75
