## 1. Regression Characterization

- [ ] 1.1 Add a focused test or fixture helper that reads `samples/access1.log` and verifies it parses as common access-log input.
- [ ] 1.2 Add a rule regression test that expects `samples/access1.log` to produce a grouped `behavior.web_sql_injection` finding for `172.17.0.1` and `/index.php`.
- [ ] 1.3 Add small parser unit tests for access method, target path, request text, status code, response size, user agent, source file, and line number.
- [ ] 1.4 Add small rule unit tests for decoded SQLi indicators, boolean-blind `if(substr(...))` probes, bounded evidence, and non-repeated benign access lines.

## 2. Access Event Metadata

- [x] 2.1 Extend the event model or metadata representation to carry access request method, status code, response size, user agent, decoded request text, and query context without breaking existing serializers.
- [x] 2.2 Update `parse_line` access-log handling to extract the new metadata from common/combined access log lines.
- [x] 2.3 Preserve original raw lines unchanged for evidence while exposing decoded request context to local rules.
- [ ] 2.4 Update serialization/export tests if the new metadata is intentionally surfaced to the web UI or reports.

## 3. SQL Injection Behavior Rules

- [ ] 3.1 Refactor SQLi detection helpers for decoded text normalization, indicator extraction, request grouping, and request-shape fingerprinting.
- [ ] 3.2 Group candidate access events by source address and target path, with optional user-agent or query-shape support when useful.
- [ ] 3.3 Detect boolean-blind enumeration traits: repeated conditional expressions, `substr` position coverage, extraction targets, repeated request count, and response-size variance.
- [ ] 3.4 Emit compact grouped findings with severity, confidence reason, severity reason, matched indicators, count, source context, target path, and bounded representative evidence.
- [ ] 3.5 Keep all detection local-only and avoid any URL/domain fetching, scanning, exploitation, blocking, or external reporting behavior.

## 4. Examples And Documentation

- [ ] 4.1 Keep `samples/access1.log` as the full realistic middleware attack fixture.
- [ ] 4.2 Add or update sample-listing documentation so `access1.log` is described as a SQL injection enumeration access log.
- [ ] 4.3 If a shorter companion example is needed for UI demos, create it without replacing the full `access1.log` regression fixture.

## 5. Verification

- [ ] 5.1 Run parser, rules, sample, and serialization tests affected by the change.
- [ ] 5.2 Run the full Python test suite when targeted tests pass.
- [ ] 5.3 Run frontend/static checks only if exposed web serialization or UI sample listing changes.
- [ ] 5.4 Record verification output and confirm OpenSpec validation remains strict-pass.
