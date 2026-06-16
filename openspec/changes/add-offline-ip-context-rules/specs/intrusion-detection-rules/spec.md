### Requirement: Preserve offline source address context
The intrusion detection rules capability SHALL classify source addresses locally and preserve that context for rule decisions and evidence review.

#### Scenario: Parsed event includes local IP context
- **WHEN** a local log line contains a source address
- **THEN** the parsed event metadata includes local source address context with validity, category, global routability, and a human-readable reason
- **AND** classification does not perform DNS, GeoIP, threat-intelligence, map, network, or remote database lookups

### Requirement: Highlight repeated suspicious activity from public sources
The intrusion detection rules capability SHALL add an explainable contextual finding when a globally routable source address triggers multiple suspicious findings.

#### Scenario: Public source triggers multiple findings
- **WHEN** a globally routable source address is associated with at least two existing keyword, behavior, or correlation findings
- **THEN** the system emits a `behavior.public_source_cluster` finding
- **AND** the finding explains that the source is globally routable and lists bounded evidence from the related findings

#### Scenario: Local and non-global sources are suppressed
- **WHEN** a private, loopback, link-local, multicast, reserved, documentation-only, or invalid source address triggers multiple findings
- **THEN** the public-source contextual rule does not emit a finding for that source
