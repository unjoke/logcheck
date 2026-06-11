## Purpose

Define local intrusion detection rule behavior, severity explanation, confidence explanation, safe enhanced rule configuration, and explainable research-inspired behavior detection.

## Requirements

### Requirement: Detect configurable behavior patterns
The intrusion detection rules capability SHALL detect configurable behavior patterns beyond individual keyword matches.

#### Scenario: Suspicious command pattern
- **WHEN** parsed events contain suspicious command execution indicators
- **THEN** the system emits a behavior-pattern finding with rule identifier, severity, confidence, matched evidence, and explanation

#### Scenario: Multi-signal suspicious actor
- **WHEN** one actor or source address triggers multiple lower-severity indicators in a local analysis run
- **THEN** the system can emit a correlated behavior finding with evidence references

### Requirement: Explain severity and confidence
The intrusion detection rules capability SHALL explain why each finding received its severity and confidence.

#### Scenario: Severity explanation
- **WHEN** the system emits a finding
- **THEN** the finding includes or can derive a human-readable severity reason based on rule type, count, evidence, and configured thresholds

#### Scenario: Confidence explanation
- **WHEN** the system emits a finding from a behavior pattern
- **THEN** the finding includes or can derive a confidence reason that distinguishes exact keyword matches, repeated behavior, and correlated signals

### Requirement: Validate enhanced rule configuration safely
The intrusion detection rules capability SHALL validate enhanced local rule configuration before applying it.

#### Scenario: Reject unsafe or malformed enhanced rules
- **WHEN** a local rule file contains malformed behavior patterns, invalid thresholds, or unsupported rule fields
- **THEN** the system rejects the file with a clear error
- **AND** it does not silently apply partial unsafe configuration

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
