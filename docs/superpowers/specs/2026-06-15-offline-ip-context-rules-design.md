---
comet_change: add-offline-ip-context-rules
role: technical-design
canonical_spec: openspec
---

# Offline IP Context Rules Technical Design

## Goal

Add deterministic source-address context to local log analysis so repeated suspicious activity from globally routable sources can be highlighted without treating private lab, loopback, documentation, reserved, multicast, or invalid addresses as public attackers.

## Architecture

The implementation uses a small offline enrichment boundary instead of a GeoIP service. `logcheck/ip_context.py` owns IP classification with the Python standard library `ipaddress` module and exposes `classify_ip_address(address)`. The classifier returns an `IPContext` dataclass with stable fields: `address`, `is_valid`, `version`, `category`, `is_global`, and `reason`.

`logcheck/parsers.py` remains responsible for turning raw log lines into `Event` objects. When a parser extracts `source_address`, it also writes `metadata["source_address_context"]` as a plain dictionary. Existing event fields and serialized finding fields remain stable.

`logcheck/rules.py` keeps existing keyword, behavior, and correlation rules unchanged, then runs a contextual post-processing rule. `_public_source_cluster_findings()` groups findings by `source_address`, reads the parser-provided context when available, falls back to the same local classifier when needed, and emits `behavior.public_source_cluster` only for globally routable sources with at least two suspicious findings.

## Borrowed Pattern

FastWLAT's `ipGeoLocationService.ts` is useful for its shape rather than its dependency choices: validate first, classify local/private addresses locally, keep repeat lookups stable, and return safe fallback data when optional databases are missing. Logcheck adapts those ideas into standard-library classification only. It does not add MaxMind databases, country/city/ASN fields, DNS, maps, remote threat intelligence, URL inputs, network scanning, blocking, or external reporting.

## Data Flow

```text
local log line
  -> parser extracts source_address
  -> ip_context classifies the address locally
  -> Event.metadata["source_address_context"] stores the result
  -> existing rule engine emits keyword, behavior, and correlation findings
  -> public-source cluster rule adds a contextual finding when warranted
```

## Classification Rules

The classifier explicitly checks documentation networks before generic private checks because Python's `ipaddress` can treat documentation ranges as non-global/private-like. It handles:

- `global`: valid and globally routable.
- `documentation`: RFC documentation/test ranges such as `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, and `2001:db8::/32`.
- `private`, `loopback`, `link-local`, `multicast`, `unspecified`, `reserved`, and `invalid`.

Only `category="global"` with `is_global=true` can trigger `behavior.public_source_cluster`.

## Rule Behavior

The contextual rule is deliberately medium severity because it adds review context rather than replacing stronger behavior detections such as SQL injection or brute force. Evidence is deduplicated and bounded to five lines to keep exports and UI detail panels readable. Missing metadata is not fatal; the rule falls back to local classification from `Finding.source_address`.

## Error Handling

Invalid addresses return an invalid context dictionary instead of raising. Missing source addresses are ignored by the contextual rule. Events with malformed or absent `source_address_context` metadata are reclassified locally when a source address is available.

## Testing Strategy

Tests cover IP classification boundaries, parser metadata preservation, public-source cluster creation, private/documentation suppression, and the existing parser/rule suite. Full verification is `python -m pytest -q`, with syntax verification for the touched Python modules.

## Risks

The main risk is accidental noise if a lab or documentation address is treated as global. The explicit documentation network checks and non-global suppression mitigate that. Another risk is duplicated contextual findings, so the rule runs after existing findings and emits at most one cluster finding per source bucket.
