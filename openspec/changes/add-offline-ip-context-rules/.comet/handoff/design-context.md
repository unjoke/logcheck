# Comet Design Handoff

- Change: add-offline-ip-context-rules
- Phase: design
- Mode: compact
- Context hash: 70cddf92eefae0fa45f693b903cecc2fed1b139ba6d003044fd98d0b73eebc52

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/add-offline-ip-context-rules/proposal.md

- Source: openspec/changes/add-offline-ip-context-rules/proposal.md
- Lines: 1-20
- SHA256: 42234b38523738ffad14b47961dc363c5553814fdb81ec7f07ccdefd7b527e22

```md
# Add Offline IP Context Rules

## Why

The detector already extracts source addresses and groups attack behavior by source, but it does not preserve local context about whether an address is valid, private, loopback, documentation-only, multicast, or globally routable. FastWLAT's `ipGeoLocationService.ts` shows a useful pattern for IP enrichment: validate first, classify local/private addresses locally, cache repeat lookups, and return stable fallback data when external databases are absent.

This project must remain an offline log analysis tool, so the useful part to borrow is the local classification and stable fallback behavior, not GeoIP lookup, DNS lookup, map rendering, or MaxMind database integration.

## What

- Add an offline IP context helper that validates and classifies IPv4 source addresses using local standard-library logic.
- Attach IP context metadata to parsed events when a source address is present.
- Add an explainable rule that highlights repeated suspicious findings from globally routable sources while suppressing local/private, loopback, multicast, reserved, and documentation-only ranges.
- Keep all analysis local and deterministic with no external network, domain, DNS, GeoIP, threat-intelligence, or map dependencies.

## Non-Goals

- Do not add GeoIP country, city, ASN, coordinates, maps, remote lookups, or downloaded databases.
- Do not add URL/domain inputs, remote fetch, network scanning, blocking, exploitation, or external reporting.
- Do not change the frontend workflow in this change.
```

## openspec/changes/add-offline-ip-context-rules/design.md

- Source: openspec/changes/add-offline-ip-context-rules/design.md
- Lines: 1-32
- SHA256: 49ebcefa5a7be141534ce4b222eeb9fbaad6974345d887bf5256f05d027393c6

```md
# Design

## Context Borrowed From FastWLAT

FastWLAT's IP geolocation service has several useful engineering qualities: it validates IPs before enrichment, treats private/local IPs as a first-class offline result, caches repeated lookups, supports batch processing, and returns stable default data when optional external databases are unavailable. For Logcheck, the appropriate adaptation is a smaller local classifier: validate and classify source addresses with the Python standard library, then use that context to make rule explanations more precise.

## Architecture

Add `logcheck/ip_context.py` with a frozen `IPContext` dataclass and `classify_ip_address(address)`. The classifier uses `ipaddress.ip_address` and returns structured metadata: address, validity, version, category, whether the address is globally routable, and a short explanation. Invalid input is represented as an invalid context instead of raising into the parser or rule engine.

`logcheck/parsers.py` will call the classifier whenever it extracts a source address and store the result as plain metadata under `metadata["source_address_context"]`. Existing event fields remain unchanged.

`logcheck/rules.py` will add a post-processing rule after existing behavior and correlation rules. It groups findings by source address, consults the attached IP context, and emits `behavior.public_source_cluster` only when a globally routable source has at least two suspicious findings. This avoids noisy alerts for local lab ranges such as `192.168.0.0/16`, Docker `172.16.0.0/12`, loopback, multicast, documentation networks, and invalid strings.

## Data Flow

```text
raw log line
  -> parser extracts source_address
  -> ip_context classifies locally
  -> Event.metadata["source_address_context"]
  -> rule engine emits original findings
  -> public-source cluster rule adds explainable context finding when warranted
```

## Error Handling

Invalid addresses produce a metadata dictionary with `is_valid=false`, `category="invalid"`, and a reason. Missing source addresses are left alone. The rule engine treats missing, invalid, or non-global context as non-actionable context for this specific rule.

## Testing

Unit tests cover private/local suppression, globally routable clustering, documentation range suppression, and parser metadata attachment. Existing rule and sample tests should continue to pass.
```

## openspec/changes/add-offline-ip-context-rules/tasks.md

- Source: openspec/changes/add-offline-ip-context-rules/tasks.md
- Lines: 1-9
- SHA256: 8fc40907c28a4c52664c13d14dc01e6e9a92a1cd7a5c4bbd490cf1f03d9a9f47

```md
# Tasks

- [x] Add tests for offline IP context classification and parser metadata.
- [x] Add tests for public-source clustered rule behavior and private/documentation suppression.
- [x] Implement `logcheck/ip_context.py` with standard-library IPv4/IPv6 classification.
- [x] Attach source address context during parsing without changing existing event fields.
- [x] Add `behavior.public_source_cluster` to the rule engine with bounded evidence and explanations.
- [x] Run focused tests, full Python tests, and syntax checks.
- [ ] Commit and push only files changed for this enhancement.
```

## openspec/changes/add-offline-ip-context-rules/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/add-offline-ip-context-rules/specs/intrusion-detection-rules/spec.md
- Lines: 1-19
- SHA256: 280e129370cd8b1253de0be209b8aee2ccb6f387fc1c23f8c5a100b497fcff36

```md
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
```

