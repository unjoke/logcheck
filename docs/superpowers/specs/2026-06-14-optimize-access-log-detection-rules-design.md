---
comet_change: optimize-access-log-detection-rules
role: technical-design
canonical_spec: openspec
---

# Optimize Access Log Detection Rules Design

## Context

Logcheck already parses local lines into `Event` records and emits explainable `Finding` records. The current access-log SQL injection behavior rule detects repeated decoded SQLi indicators, but `samples/access1.log` is a stronger case: 2764 common access log entries in roughly nine minutes, all from `172.17.0.1`, all targeting `/index.php`, all HTTP 200, all using `python-requests/2.26.0`, and all carrying decoded SQL traits such as `information_schema`, `select table_name`, `substr(`, and `and if(`. Later requests enumerate `select flag from sqli.flag`, and `substr(...,position,1)` covers 43 character positions.

MaaLogAnalyzer was reviewed as the reference project. It is not an intrusion-signature engine, so its value here is architectural rather than a rule list: it parses raw log lines into structured events, preserves raw-line provenance separately, builds indexes/statistics over structured data, and projects compact evidence to the user. Logcheck should borrow that shape lightly, without porting MaaLogAnalyzer's trace tree, UI, or package structure.

## Approach

The implementation will keep Logcheck local-only and dependency-light. Access parsing will enrich `Event` with a small metadata dictionary for access-only fields such as request method, decoded request, status code, response size, referrer, and user agent. The existing core fields will continue to carry source file, line number, raw line, source address, target path, category, and message.

Rules will stop treating the access sample as just repeated keyword matches. SQLi detection will normalize decoded request text, extract indicators and blind-injection traits, group access events by source address and target path, compute request count, extraction targets, `substr` position coverage, status/size distributions, and then emit a compact grouped finding. The finding should preserve representative raw evidence and use `count`, `matched_keyword`, `target`, `severity_reason`, and `confidence_reason` to make the result reviewable.

## Data Flow

```text
local access log line
  -> parse_line()
  -> Event(category="access", target="/index.php", metadata={...})
  -> detect_findings()
  -> _web_sql_injection_findings()
  -> grouped attack statistics
  -> Finding(rule_id="behavior.web_sql_injection", evidence=[bounded examples])
```

The raw line remains unchanged for evidence. Decoded request text is used only for local matching and explanation. No URL/domain lookup, scan, blocking, exploitation, external upload, or remote report is introduced.

## Key Decisions

### Add Event Metadata

Use `Event.metadata: dict[str, object] = field(default_factory=dict)` for access-specific attributes. This keeps existing constructors compatible, avoids adding many optional model fields, and gives rules structured inputs without reparsing raw lines. Because the dataclass is frozen, callers should pass a complete metadata dictionary at construction time and avoid mutation.

### Group By Source And Target

Group SQLi candidates by `(source_address or actor or source_file, target or parsed path)`. `access1.log` is one source and one path, so this yields a single attack campaign. User-agent and request shape can be used inside confidence reasoning, but they should not over-split the first implementation.

### Use Multi-Signal Scoring

Emit a critical/high-confidence SQLi finding only when a group has repeated behavior plus multiple indicators, or when it has strong blind-injection structure. Strong traits include `and if(`, `substr(`, `information_schema`, `select flag`, multiple `substr` positions, high request count, and response-size variance.

### Keep Evidence Bounded

Limit evidence to representative lines instead of attaching all 2764 raw lines. Prefer the earliest examples and lines that show distinct extraction targets or response sizes. The full group size is carried in `Finding.count`.

## Testing Strategy

Use TDD for implementation. First add failing parser tests for metadata extraction from a combined access line. Then add failing rule tests for a small blind-injection group, bounded evidence, benign repeated access lines, and the real `samples/access1.log` fixture. After those tests fail for the expected reasons, implement minimal parser and rule changes, then run targeted tests and the full Python suite.

## Risks

- False positives: mitigate by requiring repeated grouped behavior and multiple decoded traits.
- Metadata churn: keep metadata internal unless a serializer or UI test proves it must be exposed.
- Large sample runtime: keep the full sample regression targeted and supplement it with smaller unit tests.
- Existing dirty worktree: implementation must read current files and layer changes without reverting unrelated user edits.

## Acceptance

- `samples/access1.log` produces a grouped `behavior.web_sql_injection` finding for `172.17.0.1` and `/index.php`.
- The finding count reflects repeated behavior, not a single-line match.
- The finding explanation or reason fields mention decoded local traits such as conditional `substr`, `information_schema`, table enumeration, or flag extraction.
- Evidence remains bounded and source-linked.
- OpenSpec strict validation and targeted parser/rule/sample tests pass.
