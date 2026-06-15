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
