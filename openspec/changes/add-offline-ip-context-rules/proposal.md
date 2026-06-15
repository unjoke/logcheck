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
