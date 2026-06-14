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

## Open Questions

- Should access metadata be added as explicit dataclass fields on `Event`, or stored in a generic metadata dictionary to reduce future schema churn?
- Should `behavior.web_sql_injection` remain the rule id for all grouped web SQLi, or should blind enumeration use a more specific id such as `behavior.web_sql_injection.boolean_blind`?
- Should the full `access1.log` regression run in every test suite invocation, or should it be isolated in a targeted sample test if runtime becomes noticeable?
