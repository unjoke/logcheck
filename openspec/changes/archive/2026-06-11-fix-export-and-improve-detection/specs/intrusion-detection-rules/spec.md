## ADDED Requirements

### Requirement: Detect local template behavior signals
The intrusion detection rules capability SHALL support explainable local behavior signals derived from normalized log message templates.

#### Scenario: Repeated template burst
- **WHEN** local parsed events from the same source address or actor repeat a suspicious normalized template at or above a configured threshold
- **THEN** the system emits a behavior finding with rule id, severity, confidence reason, severity reason, count, source context, and representative raw evidence

#### Scenario: Benign repeated template below threshold
- **WHEN** local parsed events repeat a normalized template below the configured threshold or match a benign baseline
- **THEN** the system does not emit a template-burst finding for that behavior

### Requirement: Detect suspicious local behavior sequences
The intrusion detection rules capability SHALL support deterministic sequence rules for suspicious local event progressions.

#### Scenario: Authentication to privilege escalation sequence
- **WHEN** local events from the same source address or actor show failed authentication followed by privilege-escalation indicators within a configured window
- **THEN** the system emits a correlated behavior finding that includes evidence from both stages

#### Scenario: Sequence outside window
- **WHEN** matching local events occur outside the configured correlation window
- **THEN** the system does not emit the sequence finding

### Requirement: Validate behavior rule configuration
The intrusion detection rules capability SHALL validate behavior/template rule configuration before applying it.

#### Scenario: Valid behavior thresholds are loaded
- **WHEN** a local rule configuration provides supported behavior thresholds and windows
- **THEN** the system applies those values to behavior/template detection

#### Scenario: Invalid behavior rules are rejected
- **WHEN** a local rule configuration contains malformed behavior rule fields, invalid thresholds, invalid windows, or unsupported rule types
- **THEN** the system rejects the configuration with a clear error
- **AND** it does not silently apply partial behavior-rule configuration

### Requirement: Preserve explainability for research-inspired rules
The intrusion detection rules capability SHALL keep research-inspired behavior detections explainable and reviewable.

#### Scenario: Behavior finding includes provenance
- **WHEN** a template or sequence behavior finding is emitted
- **THEN** the finding includes local source file, line number when available, actor or source address when available, raw evidence lines, severity reason, and confidence reason

#### Scenario: Detection remains local-only
- **WHEN** behavior/template detection runs
- **THEN** it uses only local parsed events and local configuration
- **AND** it does not fetch external data, query domains, scan networks, train remote models, or submit reports externally
