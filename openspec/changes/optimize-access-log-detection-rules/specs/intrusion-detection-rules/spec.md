## MODIFIED Requirements

### Requirement: Detect URL-encoded SQL injection in local access logs
The intrusion detection rules capability SHALL support explainable local behavior signals for repeated URL-encoded and decoded SQL injection attempts in parsed access logs.

#### Scenario: Repeated encoded SQL injection attempts
- **WHEN** local parsed access events from the same source address repeatedly contain URL-encoded SQL injection indicators
- **THEN** the system emits a `behavior.web_sql_injection` finding with severity, confidence reason, severity reason, count, source context, and representative raw evidence

#### Scenario: Source address is preserved
- **WHEN** an access-log SQL injection finding is emitted
- **THEN** the finding includes the source address from the access log when available

#### Scenario: Boolean-blind enumeration is grouped
- **WHEN** local parsed access events from the same source and target path repeatedly contain decoded conditional SQL expressions such as `and if(` with `substr(...)` extraction probes
- **THEN** the system emits a grouped SQL injection behavior finding that summarizes the attack count, source, target path, matched indicators, and representative evidence instead of requiring one finding per request

#### Scenario: Enumeration traits improve explanation
- **WHEN** the grouped access events show repeated character-position probes, database/table/flag extraction targets, or response-size variance under the same request shape
- **THEN** the finding includes confidence or severity reasoning that names those local traits without contacting external services

### Requirement: Preserve explainability for local access-log findings
The intrusion detection rules capability SHALL keep access-log behavior detections explainable and reviewable.

#### Scenario: Behavior finding includes provenance
- **WHEN** an access-log SQL injection behavior finding is emitted
- **THEN** the finding includes local source file, line number when available, actor or source address when available, raw evidence lines, severity reason, and confidence reason

#### Scenario: Detection remains local-only
- **WHEN** access-log SQL injection detection runs
- **THEN** it uses only local parsed events and local configuration
- **AND** it does not fetch external data, query domains, scan networks, train remote models, or submit reports externally

#### Scenario: Evidence remains compact
- **WHEN** a repeated access-log attack group contains many matching events
- **THEN** the finding includes a bounded set of representative raw evidence lines and a count for the full group

## ADDED Requirements

### Requirement: Detect supplied middleware SQL injection example
The intrusion detection rules capability SHALL detect the supplied `samples/access1.log` middleware access-log example as a repeated boolean-blind SQL injection enumeration attempt.

#### Scenario: Access1 sample emits SQL injection behavior
- **WHEN** the system analyzes `samples/access1.log`
- **THEN** it emits at least one `behavior.web_sql_injection` finding for source `172.17.0.1` and target `/index.php`
- **AND** the finding count reflects repeated behavior rather than a single-line match

#### Scenario: Access1 explanation references decoded attack traits
- **WHEN** the SQL injection finding for `samples/access1.log` is reviewed
- **THEN** its explanation, matched indicators, severity reason, or confidence reason identifies local decoded SQL traits such as `information_schema`, `substr`, conditional `if`, table enumeration, or flag extraction

