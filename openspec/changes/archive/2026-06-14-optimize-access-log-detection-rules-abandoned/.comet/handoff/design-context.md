# Comet Design Handoff

- Change: optimize-access-log-detection-rules
- Phase: design
- Mode: compact
- Context hash: 864d01d0fc051beb97c67d9bed1521405ff9488260a82e57b468615ac913e4db

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/optimize-access-log-detection-rules/proposal.md

- Source: openspec/changes/optimize-access-log-detection-rules/proposal.md
- Lines: 1-31
- SHA256: 08ff2e3d6ad1909957cdf17c5304097ab32dc16122799be2462bf0fdf56125bc

```md
## Why

The current access-log SQL injection detection is useful but still too shallow for the middleware example in `samples/access1.log`. That file contains a concentrated CTF-style web attack stream: 2764 parsed access lines, all from `172.17.0.1`, all targeting `/index.php`, all returning HTTP 200, with `python-requests/2.26.0` as the user agent, over the interval `01/Sep/2021:01:37:25 +0000` to `01/Sep/2021:01:46:06 +0000`. URL-decoded requests repeatedly contain `information_schema`, `select table_name`, `substr(`, `database()`, `and if(`, and later `select flag from sqli.flag`, with `substr(...,position,1)` covering 43 character positions.

This shape is stronger than a simple keyword burst. It is a boolean-blind SQL injection enumeration pattern where the repeated request template, decoded SQL markers, source grouping, response-size differences, target path, and representative raw evidence should be preserved as one explainable finding. Without that optimization the tool can either under-explain the attack or produce noisy per-line keyword alerts.

The requested reference project, MaaLogAnalyzer (`MaaXYZ/MaaLogAnalyzer`, cloned and reviewed under `worktmp/MaaLogAnalyzer` at commit `649d420`), does not provide intrusion signatures directly. Its useful lesson is architectural: parse raw lines into structured events, keep raw-line provenance separate, build indexes/statistics over structured events, and project compact evidence for users. Logcheck should adopt that style at a small scale for web access detections while staying local-only and course-friendly.

## What Changes

- Improve access-log parsing so common combined log lines retain method, request path/query, status code, response size, user agent, timestamp, source address, source file, and line number where the existing `Event` model can carry them.
- Refine SQL injection rule matching from a pure indicator burst into a grouped behavior detector for URL-decoded web requests.
- Add detection for boolean-blind SQL injection enumeration traits visible in `access1.log`: repeated source/path, repeated conditional `if(substr(...))` probes, database/table/flag extraction targets, many guessed character positions, and response-size variance.
- Keep generated findings compact and explainable: one behavior finding per source/path attack group with count, severity reason, confidence reason, matched indicators, representative raw evidence, and source context.
- Optimize the example logs and test coverage so `access1.log` acts as a regression fixture for realistic middleware access-log attacks rather than a loose sample.
- Preserve Logcheck's safety boundary: local file analysis only, no domain fetching, no scanning, no exploitation, no active blocking, no external reporting, and no internet-dependent detection.

## Capabilities

### Modified Capabilities

- `intrusion-detection-rules`: Access-log SQL injection detection should identify repeated URL-encoded and decoded web attack behavior with richer grouping, confidence, severity, and evidence.
- `log-ingestion`: Access-log parsing should preserve enough request metadata for behavior rules to group by source, target, status, size, and user agent.
- `course-deliverables`: Example logs and regression tests should demonstrate realistic detection on the supplied middleware access log.

## Impact

- Expected code areas: `logcheck/parsers.py`, `logcheck/models.py`, `logcheck/rules.py`, `logcheck/analysis.py` or serializers only if new metadata needs to surface, and parser/rule/sample tests.
- Expected sample areas: `samples/access1.log` should remain the full realistic fixture; smaller companion examples may be added only if tests or UI demos need faster focused coverage.
- Expected documentation/spec areas: update OpenSpec requirements for access-log parsing and SQL injection behavior findings.
- Non-goals: no remote network capabilities, no large ML dependency, no production SIEM redesign, no full MaaLogAnalyzer port, and no unrelated frontend redesign.
```

## openspec/changes/optimize-access-log-detection-rules/design.md

- Source: openspec/changes/optimize-access-log-detection-rules/design.md
- Lines: 1-86
- SHA256: a96ee2ac833711c772f49078028bbb0376bd8580f77f0265a07994da2d1f5187

[TRUNCATED]

```md
## Context

Logcheck currently parses local logs into `Event` objects, runs keyword and behavior rules, and returns explainable `Finding` records for the CLI and local web UI. The existing access-log support is intentionally small: it recognizes common access lines and has a `behavior.web_sql_injection` rule that URL-decodes event text and groups repeated SQLi indicators by source.

The supplied `samples/access1.log` is richer than that baseline. It has 2764 common access log entries in about nine minutes, all from `172.17.0.1` to `/index.php`, all HTTP 200, all `python-requests/2.26.0`. Every line includes `information_schema`, `select table_name`, `substr(`, and `and if(` after URL decoding; later lines include `select flag from sqli.flag`; `substr(...,position,1)` covers 43 positions; response sizes cluster around repeated values such as 427, 426, 428, and 425 bytes. This is best represented as a compact boolean-blind SQL injection enumeration finding, not thousands of independent alerts.

MaaLogAnalyzer was reviewed as requested under `worktmp/MaaLogAnalyzer` at commit `649d420`. It is a MaaFramework log visualization and parser project, not an intrusion-signature project. The relevant takeaways are architectural:

- Extract raw lines into structured protocol events before analysis.
- Keep raw-line provenance in a separate raw line store so evidence can point back to exact source lines.
- Build indexes and statistics over structured events rather than searching raw text repeatedly.
- Project compact user-facing task/evidence views from richer internal artifacts.

Logcheck should adopt these ideas lightly: enrich parsed access events enough for rules, compute grouped request statistics inside the detector, and emit compact explainable evidence. A full MaaLogAnalyzer-style trace tree would be out of scope.

## Goals / Non-Goals

**Goals:**

- Preserve access-log metadata needed for web attack behavior grouping: method, decoded request, target path, query string, status, response size, user agent, source address, source file, and line number.
- Detect repeated URL-encoded and decoded SQL injection attempts from local access logs.
- Detect boolean-blind enumeration traits in `access1.log`, including repeated conditional `if(substr(...))` probes, multiple guessed character positions, extraction targets, and response-size variance.
- Collapse the attack into one or a few high-value behavior findings with count, indicators, attack traits, representative evidence, severity reason, confidence reason, and provenance.
- Keep the implementation deterministic, local-only, dependency-light, and suitable for coursework tests.

**Non-Goals:**

- No full port of MaaLogAnalyzer packages, UI, trace reducer, or query protocol.
- No network lookups, URL/domain target fetching, active scanning, exploitation, blocking, or external reporting.
- No ML classifier or online threat intelligence dependency.
- No broad SIEM/event database redesign.

## Decisions

### Decision: Enrich access events with structured request metadata

Access parsing should extract common-log fields and preserve them either on the existing `Event` model or through conservative fields that downstream serializers can handle. The parser should keep the raw line untouched for evidence and use decoded request text only for matching and explanation.

Alternative considered: leave `Event` unchanged and parse raw access lines again in rules. That repeats parsing work, makes tests brittle, and loses the separation between ingestion and detection that MaaLogAnalyzer handles well.

### Decision: Group web attack behavior by source and request shape

The detector should group candidate access events by source address and target path, with optional user-agent and query parameter shape when available. Within each group it should compute indicators, request count, decoded attack targets, `substr` position coverage, status-code distribution, response-size distribution, and representative evidence.

Alternative considered: emit a finding per SQLi line. That is noisy for `access1.log` and does not communicate that the important event is the repeated enumeration campaign.

### Decision: Use multi-signal SQLi scoring instead of single keywords

The rule should require multiple SQLi indicators or strong blind-injection structure before emitting a high-severity finding. Strong traits include conditional `and if(`, `substr(` extraction, `information_schema` enumeration, `select flag`, many repeated attempts, and response-size variance under the same path.

Alternative considered: add more default keyword strings. Keyword expansion alone improves recall but does not distinguish a one-off suspicious query from a 2764-line attack.

### Decision: Keep evidence compact and source-linked

Findings should include a small representative evidence set: earliest examples, examples around notable response-size changes, and examples from database/table/flag extraction phases when possible. The finding should still carry count and source context for the full group.

Alternative considered: store every matching raw line as finding evidence. That bloats JSON/CSV/Markdown output and makes the UI harder to review.

### Decision: Treat `access1.log` as the regression fixture

Tests should analyze the real supplied file to prove the optimized rule catches the attack shape. Smaller unit tests should cover parser extraction and edge cases, but the full fixture should remain in the suite or a targeted sample test so future rule edits do not drift away from the user-provided middleware log.

Alternative considered: replace `access1.log` with a synthetic short file. That would be faster but would lose the response-size and enumeration distribution that make the rule meaningful.

## Risks / Trade-offs

- Broad SQLi matching can create false positives -> Require grouped repeated behavior and multiple decoded indicators before raising high/critical severity.
- Extra event metadata can ripple into serializers -> Keep additions backward-compatible and update serialization tests only where user-visible fields are intentionally exposed.
- Full fixture tests may be slower -> Use targeted tests that read `access1.log` once and assert on the aggregated finding, while unit tests use small inline logs.
- Response-size variance is server-dependent -> Treat size variance as a confidence booster, not the only trigger.
- Existing uncommitted changes already touch rules/parsers/tests -> During implementation, read current files carefully and layer changes without reverting user work.

## Migration Plan

1. Add or update parser tests for combined access log extraction, including status, size, user agent, path, decoded request context, and source address.
2. Add a focused rule test that analyzes `samples/access1.log` and asserts a compact boolean-blind SQL injection finding with source/path/count/traits/evidence.
3. Enrich the parser/event data model only as much as needed for access metadata and existing serializers.
4. Refactor SQLi detection into small helper functions for decoded text, request fingerprinting, indicator extraction, grouping, scoring, and representative evidence selection.
5. Update sample/documentation references so `access1.log` is clearly a middleware SQLi enumeration example.
6. Run parser, rules, sample, CLI/web serialization tests, then full Python tests if feasible.
```

Full source: openspec/changes/optimize-access-log-detection-rules/design.md

## openspec/changes/optimize-access-log-detection-rules/tasks.md

- Source: openspec/changes/optimize-access-log-detection-rules/tasks.md
- Lines: 1-34
- SHA256: cda8d3a00503eef99f0ecb4778fcb2dd60b3421fac2f17c3685ca20b9c2a771a

```md
## 1. Regression Characterization

- [ ] 1.1 Add a focused test or fixture helper that reads `samples/access1.log` and verifies it parses as common access-log input.
- [ ] 1.2 Add a rule regression test that expects `samples/access1.log` to produce a grouped `behavior.web_sql_injection` finding for `172.17.0.1` and `/index.php`.
- [ ] 1.3 Add small parser unit tests for access method, target path, request text, status code, response size, user agent, source file, and line number.
- [ ] 1.4 Add small rule unit tests for decoded SQLi indicators, boolean-blind `if(substr(...))` probes, bounded evidence, and non-repeated benign access lines.

## 2. Access Event Metadata

- [ ] 2.1 Extend the event model or metadata representation to carry access request method, status code, response size, user agent, decoded request text, and query context without breaking existing serializers.
- [ ] 2.2 Update `parse_line` access-log handling to extract the new metadata from common/combined access log lines.
- [ ] 2.3 Preserve original raw lines unchanged for evidence while exposing decoded request context to local rules.
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
```

## openspec/changes/optimize-access-log-detection-rules/specs/course-deliverables/spec.md

- Source: openspec/changes/optimize-access-log-detection-rules/specs/course-deliverables/spec.md
- Lines: 1-16
- SHA256: cf7529d97036afb69cb756c8f1d0aa8da485229be9691ea9aa79b31c26e077a3

```md
## ADDED Requirements

### Requirement: Demonstrate realistic access-log attack detection
The project SHALL include coursework evidence that the supplied middleware access-log example is handled as a realistic local attack fixture.

#### Scenario: Access1 is covered by automated verification
- **WHEN** automated verification for detection rules is run
- **THEN** tests cover `samples/access1.log` or an equivalent fixture derived from it and assert that repeated SQL injection behavior is detected

#### Scenario: Access1 remains local-only evidence
- **WHEN** the access-log detection example is demonstrated
- **THEN** the evidence shows local file analysis and does not add URL/domain inputs, remote fetching, scanning, exploitation, blocking, or external reporting controls

#### Scenario: Example log intent is documented
- **WHEN** coursework documentation or sample listings describe bundled logs
- **THEN** `access1.log` is identified as a middleware access-log SQL injection enumeration example rather than a generic access log
```

## openspec/changes/optimize-access-log-detection-rules/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/optimize-access-log-detection-rules/specs/intrusion-detection-rules/spec.md
- Lines: 1-51
- SHA256: 2fd9d7b9f052d1439e89d858c90a6e1a5555575a1dd066689a41739ec3808d01

```md
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

```

## openspec/changes/optimize-access-log-detection-rules/specs/log-ingestion/spec.md

- Source: openspec/changes/optimize-access-log-detection-rules/specs/log-ingestion/spec.md
- Lines: 1-27
- SHA256: 2c2a7fd30a60e18ddfc0375da319e8c929b6600c9a55e9821d9a1b24c424a958

```md
## MODIFIED Requirements

### Requirement: Normalize richer event metadata
The log ingestion capability SHALL preserve source context needed for frontend review, insight generation, reports, and behavior-rule grouping.

#### Scenario: Preserve source context
- **WHEN** a local log line is parsed
- **THEN** the event includes source file, line number, raw line, category, timestamp when available, actor, target, source address, and parser confidence when available

#### Scenario: Mixed format batch
- **WHEN** local batch input contains Linux authentication logs, system logs, generic application logs, and common access logs
- **THEN** the system normalizes known patterns and preserves unknown lines as unknown events

#### Scenario: Preserve access request metadata
- **WHEN** the parser reads a common access log line with a client IP, timestamp, HTTP request, status code, response size, referrer, and user agent
- **THEN** it creates an access-category event with source address, target path, request method, request text, status code, response size, user agent, raw line, source file, and line number when those fields are available

## ADDED Requirements

### Requirement: Decode access request context for local rules
The log ingestion capability SHALL make URL-encoded access request context available to local behavior rules without changing the stored raw evidence line.

#### Scenario: Encoded request remains reviewable
- **WHEN** a common access log request contains URL-encoded query text
- **THEN** the parsed event preserves the original raw line for evidence
- **AND** downstream detection can inspect decoded request text for local rule matching

```

