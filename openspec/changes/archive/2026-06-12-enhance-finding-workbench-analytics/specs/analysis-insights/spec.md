## ADDED Requirements

### Requirement: Support evidence-first frontend projections
The system SHALL preserve enough local finding context for the frontend to render adjacent queue/detail review without extra remote calls.

#### Scenario: Finding selection has stable evidence context
- **WHEN** a finding is serialized for the web frontend
- **THEN** it includes stable local fields needed to display rule, severity, source file, line number, source address, actor, target, matched keyword, explanation, reasons, timestamp, and raw evidence

#### Scenario: Frontend projections remain local
- **WHEN** the frontend derives queue rows, detail panels, visual summaries, or attacker IP profiles
- **THEN** it uses the serialized local analysis payload
- **AND** it does not require additional runtime fetches to external projects, CDNs, threat intelligence, maps, DNS, or geolocation services

### Requirement: Provide chart-ready local time distribution
The system SHALL provide enough local analysis data for the frontend to render a time-distribution chart for findings.

#### Scenario: Findings include timestamps
- **WHEN** detected findings include parsed timestamps
- **THEN** the analysis result or derived insight data supports grouping findings into ordered time buckets

#### Scenario: Findings lack timestamps
- **WHEN** detected findings do not include parsed timestamps
- **THEN** the analysis result preserves deterministic source order, line order, or insight timeline labels sufficient for an evidence-order distribution

### Requirement: Provide detailed source-address profiles
The system SHALL support detailed local source-address profiles for attacker IP statistics.

#### Scenario: Source-address profile aggregates findings
- **WHEN** multiple findings share the same source address
- **THEN** the insight data or frontend-derivable fields include finding count, severity distribution, related rules, associated targets or actors, first and last observed timestamp or source reference, and representative evidence references

#### Scenario: Source-address profile remains local
- **WHEN** source-address profiles are generated
- **THEN** the system uses only parsed local events and local findings
- **AND** it does not perform IP geolocation, DNS lookup, threat-intelligence lookup, remote enrichment, blocking, or scanning

### Requirement: Preserve normalized keyword context
The system SHALL preserve enough finding and evidence context for research-informed local keyword filtering.

#### Scenario: Raw evidence remains available
- **WHEN** a finding is produced from local log evidence
- **THEN** the raw evidence remains available for display and export

#### Scenario: Normalized context can support filtering
- **WHEN** the implementation adds normalized or template-like message context for filtering
- **THEN** that normalized context is derived from local raw log text
- **AND** it does not replace raw evidence or require external model services

### Requirement: Support conservative sequence-aware review
The system SHALL support local sequence-aware review using existing findings and timeline order without adding model inference.

#### Scenario: Sequence context is derived locally
- **WHEN** the frontend or insights layer groups suspicious sequences
- **THEN** it uses local finding timestamps, source order, line numbers, or existing insight timeline labels
- **AND** it does not train models, load model weights, download datasets, or call online inference services
