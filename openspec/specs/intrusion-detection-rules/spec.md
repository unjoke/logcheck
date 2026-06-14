## Purpose

Define local intrusion detection rule behavior, severity explanation, confidence explanation, and safe enhanced rule configuration.

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
