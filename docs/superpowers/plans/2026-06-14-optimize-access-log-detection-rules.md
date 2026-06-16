---
change: optimize-access-log-detection-rules
design-doc: docs/superpowers/specs/2026-06-14-optimize-access-log-detection-rules-design.md
base-ref: 92b4b1762c6ac1830bd1bee127673d69fed94028
---

# Optimize Access Log Detection Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve access-log SQL injection detection so `samples/access1.log` is parsed and reported as a compact grouped boolean-blind SQL injection campaign.

**Architecture:** Add lightweight metadata to parsed `Event` records, then refactor SQLi detection into local helper functions that group access events by source and target, score decoded SQLi traits, and emit bounded evidence. This borrows MaaLogAnalyzer's structured-event and evidence-provenance ideas without porting its trace tree or UI.

**Tech Stack:** Python 3.11 dataclasses, stdlib `re`, `urllib.parse`, existing `unittest`/`pytest` tests, existing Logcheck parser/rule/export model.

---

## File Structure

- Modify `logcheck/models.py`: add backward-compatible `Event.metadata` for access-only structured fields.
- Modify `logcheck/parsers.py`: parse combined access log metadata and decoded request context.
- Modify `logcheck/rules.py`: refactor web SQLi detection helpers, grouping, trait extraction, and evidence selection.
- Modify `tests/test_models.py`: verify metadata default and export compatibility if needed.
- Modify `tests/test_parsers.py`: add failing tests for access metadata extraction.
- Modify `tests/test_rules.py`: add failing tests for grouped blind SQLi, bounded evidence, benign repeated access, and the real `samples/access1.log` fixture.
- Modify `README.md` or sample-listing documentation if the existing docs mention bundled samples.
- Modify `openspec/changes/optimize-access-log-detection-rules/tasks.md`: check off tasks as they complete.

## Task 1: Event Metadata Contract

**Files:**
- Modify: `logcheck/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write the failing metadata default test**

Add this test to `tests/test_models.py`:

```python
def test_event_metadata_defaults_to_empty_dict(self):
    event = Event(source_file="access.log", line_number=1, raw_line="raw")

    self.assertEqual(event.metadata, {})
```

- [ ] **Step 2: Run the model test and verify RED**

Run:

```bash
python -m pytest tests/test_models.py::ModelTests::test_event_metadata_defaults_to_empty_dict -q
```

Expected: FAIL with `AttributeError: 'Event' object has no attribute 'metadata'`.

- [ ] **Step 3: Add minimal metadata field**

In `logcheck/models.py`, update the `Event` dataclass:

```python
@dataclass(frozen=True)
class Event:
    source_file: str
    line_number: int
    raw_line: str
    timestamp: datetime | None = None
    category: str = "unknown"
    actor: str | None = None
    target: str | None = None
    source_address: str | None = None
    message: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
```

- [ ] **Step 4: Run the model test and verify GREEN**

Run:

```bash
python -m pytest tests/test_models.py::ModelTests::test_event_metadata_defaults_to_empty_dict -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add logcheck/models.py tests/test_models.py
git commit -m "feat: add event metadata for parsed log context"
```

## Task 2: Access Parser Metadata

**Files:**
- Modify: `logcheck/parsers.py`
- Modify: `tests/test_parsers.py`

- [ ] **Step 1: Write the failing access metadata test**

Extend `test_parse_access_line_extracts_request_context_and_source_ip` in `tests/test_parsers.py`:

```python
self.assertEqual(event.metadata["method"], "GET")
self.assertEqual(event.metadata["status_code"], 200)
self.assertEqual(event.metadata["response_size"], 472)
self.assertEqual(event.metadata["user_agent"], "python-requests/2.26.0")
self.assertIn("and if(substr(database(),1,1)", event.metadata["decoded_request"])
self.assertEqual(event.metadata["path"], "/index.php")
```

- [ ] **Step 2: Run the parser test and verify RED**

Run:

```bash
python -m pytest tests/test_parsers.py::ParserTests::test_parse_access_line_extracts_request_context_and_source_ip -q
```

Expected: FAIL with missing metadata keys.

- [ ] **Step 3: Update access regex and metadata construction**

In `logcheck/parsers.py`, import `unquote_plus` alongside `urlsplit`:

```python
from urllib.parse import unquote_plus, urlsplit
```

Update `ACCESS_RE` so it captures referrer and user agent:

```python
ACCESS_RE = re.compile(
    rf"^(?P<ip>\d{{1,3}}(?:\.\d{{1,3}}){{3}})\s+\S+\s+\S+\s+\[(?P<access_time>[^\]]+)\]\s+"
    rf'"(?P<method>[A-Z]+)\s+(?P<request>\S+)\s+HTTP/[0-9.]+"\s+'
    rf"(?P<status>\d{{3}})\s+(?P<size>\S+)"
    rf'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?',
    re.IGNORECASE,
)
```

In the access branch of `parse_line`, build metadata:

```python
request = access_match.group("request")
target = urlsplit(request).path or request
size_text = access_match.group("size")
metadata = {
    "method": access_match.group("method").upper(),
    "request": request,
    "decoded_request": unquote_plus(request),
    "path": target,
    "status_code": int(access_match.group("status")),
    "response_size": int(size_text) if size_text.isdigit() else None,
    "referrer": access_match.group("referrer") or None,
    "user_agent": access_match.group("user_agent") or None,
}
return Event(
    source_file=source_file,
    line_number=line_number,
    raw_line=line,
    category="access",
    target=target,
    source_address=access_match.group("ip"),
    message=request,
    metadata=metadata,
)
```

- [ ] **Step 4: Run parser tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_parsers.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add logcheck/parsers.py tests/test_parsers.py
git commit -m "feat: parse access log request metadata"
```

## Task 3: SQLi Trait Extraction Helpers

**Files:**
- Modify: `logcheck/rules.py`
- Modify: `tests/test_rules.py`

- [ ] **Step 1: Write failing small grouped detection test**

Add this test to `tests/test_rules.py`:

```python
def test_boolean_blind_sql_injection_group_mentions_enumeration_traits(self):
    events = [
        Event(
            source_file="access.log",
            line_number=i,
            raw_line=f"raw {i}",
            category="access",
            source_address="172.17.0.1",
            target="/index.php",
            message=f"/index.php?id=1%20and%20if(substr(database(),{i},1)%20=%20'a',1,(select%20table_name%20from%20information_schema.tables))",
            metadata={
                "decoded_request": f"/index.php?id=1 and if(substr(database(),{i},1) = 'a',1,(select table_name from information_schema.tables))",
                "path": "/index.php",
                "status_code": 200,
                "response_size": 420 + i,
                "user_agent": "python-requests/2.26.0",
            },
        )
        for i in range(1, 7)
    ]

    findings = detect_findings(events, default_config())

    sqli = [finding for finding in findings if finding.rule_id == "behavior.web_sql_injection"]
    self.assertEqual(len(sqli), 1)
    self.assertEqual(sqli[0].target, "/index.php")
    self.assertIn("blind", sqli[0].confidence_reason.lower())
    self.assertIn("substr", sqli[0].matched_keyword)
```

- [ ] **Step 2: Run the small rule test and verify RED**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_boolean_blind_sql_injection_group_mentions_enumeration_traits -q
```

Expected: FAIL because existing confidence/matched indicator text does not mention the new traits.

- [ ] **Step 3: Add helper functions in `logcheck/rules.py`**

Add helpers near the SQLi constants:

```python
SUBSTR_POSITION_RE = re.compile(r"substr\([^,]+,\s*(\d+)\s*,\s*1\s*\)", re.IGNORECASE)

def _access_request_text(event: Event) -> str:
    decoded = event.metadata.get("decoded_request") if event.metadata else None
    if isinstance(decoded, str):
        return decoded.lower()
    return _decoded_event_text(event)

def _access_group_key(event: Event) -> tuple[str, str]:
    source = event.source_address or event.actor or event.source_file or "unknown"
    path = event.target
    if not path and event.metadata:
        raw_path = event.metadata.get("path")
        path = raw_path if isinstance(raw_path, str) else None
    return source, path or "unknown"

def _sql_injection_indicators(text: str) -> set[str]:
    return {indicator for indicator in SQL_INJECTION_INDICATORS if indicator in text}

def _substr_positions(text: str) -> set[int]:
    return {int(match.group(1)) for match in SUBSTR_POSITION_RE.finditer(text)}
```

- [ ] **Step 4: Update `_web_sql_injection_findings` grouping and reasoning**

Use `_access_request_text`, `_access_group_key`, indicator sets, position sets, extraction target flags, and response sizes. Keep the existing rule id. Set `matched_keyword` to a comma-separated list that can include `substr`, `and if(`, `information_schema`, and `select flag`. Set `confidence_reason` to mention boolean-blind enumeration when positions or conditional substr probes are present.

- [ ] **Step 5: Run the small rule test and verify GREEN**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_boolean_blind_sql_injection_group_mentions_enumeration_traits -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

```bash
git add logcheck/rules.py tests/test_rules.py
git commit -m "feat: explain grouped blind sql injection traits"
```

## Task 4: Evidence Bounds And Benign Repetition

**Files:**
- Modify: `logcheck/rules.py`
- Modify: `tests/test_rules.py`

- [ ] **Step 1: Write failing bounded evidence test**

Add this test:

```python
def test_web_sql_injection_evidence_is_bounded(self):
    events = [
        Event(
            source_file="access.log",
            line_number=i,
            raw_line=f"raw sqli {i}",
            category="access",
            source_address="172.17.0.1",
            target="/index.php",
            message=f"/index.php?id=1%20and%20if(substr(database(),{i},1)%20=%20'a',1,(select%20table_name%20from%20information_schema.tables))",
            metadata={
                "decoded_request": f"/index.php?id=1 and if(substr(database(),{i},1) = 'a',1,(select table_name from information_schema.tables))",
                "path": "/index.php",
                "status_code": 200,
                "response_size": 427,
            },
        )
        for i in range(1, 21)
    ]

    finding = next(
        finding for finding in detect_findings(events, default_config())
        if finding.rule_id == "behavior.web_sql_injection"
    )

    self.assertLessEqual(len(finding.evidence), 6)
    self.assertEqual(finding.count, 20)
```

- [ ] **Step 2: Write failing benign repetition test**

Add this test:

```python
def test_repeated_benign_access_requests_do_not_emit_sql_injection(self):
    events = [
        Event(
            source_file="access.log",
            line_number=i,
            raw_line=f"raw benign {i}",
            category="access",
            source_address="172.17.0.1",
            target="/index.php",
            message="/index.php?page=home",
            metadata={
                "decoded_request": "/index.php?page=home",
                "path": "/index.php",
                "status_code": 200,
                "response_size": 512,
            },
        )
        for i in range(1, 30)
    ]

    findings = detect_findings(events, default_config())

    self.assertFalse(any(f.rule_id == "behavior.web_sql_injection" for f in findings))
```

- [ ] **Step 3: Run both tests and verify RED where behavior is missing**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_web_sql_injection_evidence_is_bounded tests/test_rules.py::RuleTests::test_repeated_benign_access_requests_do_not_emit_sql_injection -q
```

Expected: bounded evidence test fails if existing evidence is too broad or count/reasoning is incomplete; benign test should pass or confirm no regression.

- [ ] **Step 4: Implement bounded representative evidence**

In `logcheck/rules.py`, add helper:

```python
def _representative_evidence(events: list[Event], limit: int = 6) -> list[str]:
    evidence: list[str] = []
    seen: set[str] = set()
    for event in events:
        if event.raw_line in seen:
            continue
        evidence.append(event.raw_line)
        seen.add(event.raw_line)
        if len(evidence) >= limit:
            break
    return evidence
```

Use it when creating `Finding.evidence`.

- [ ] **Step 5: Run both tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_web_sql_injection_evidence_is_bounded tests/test_rules.py::RuleTests::test_repeated_benign_access_requests_do_not_emit_sql_injection -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

```bash
git add logcheck/rules.py tests/test_rules.py
git commit -m "feat: bound web sql injection evidence"
```

## Task 5: Full `access1.log` Regression

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/rules.py` if needed
- Modify: `logcheck/parsers.py` if parsing gaps appear

- [ ] **Step 1: Write failing full fixture test**

Add imports if needed:

```python
from logcheck.parsers import parse_files
```

Add test:

```python
def test_access1_sample_creates_grouped_sql_injection_finding(self):
    sample = Path(__file__).resolve().parent.parent / "samples" / "access1.log"
    events = parse_files([sample])

    findings = detect_findings(events, default_config())

    sqli = [
        finding for finding in findings
        if finding.rule_id == "behavior.web_sql_injection"
        and finding.source_address == "172.17.0.1"
        and finding.target == "/index.php"
    ]
    self.assertEqual(len(sqli), 1)
    self.assertGreaterEqual(sqli[0].count, 100)
    self.assertLessEqual(len(sqli[0].evidence), 6)
    self.assertTrue(
        any(token in (sqli[0].matched_keyword or "") for token in ("information_schema", "substr", "select flag"))
    )
    self.assertIn("blind", (sqli[0].confidence_reason or "").lower())
```

- [ ] **Step 2: Run full fixture test and verify RED**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_access1_sample_creates_grouped_sql_injection_finding -q
```

Expected: FAIL until parser metadata and rule grouping fully support the sample.

- [ ] **Step 3: Fix parser/rule gaps minimally**

If the test fails because `target`, decoded request, size, or user-agent are missing, fix `logcheck/parsers.py`. If it fails because grouping or reasoning is weak, fix `logcheck/rules.py`. Do not add network behavior or external dependencies.

- [ ] **Step 4: Run fixture test and verify GREEN**

Run:

```bash
python -m pytest tests/test_rules.py::RuleTests::test_access1_sample_creates_grouped_sql_injection_finding -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

```bash
git add logcheck/parsers.py logcheck/rules.py tests/test_rules.py
git commit -m "test: cover access1 blind sql injection sample"
```

## Task 6: Sample Documentation And OpenSpec Task Updates

**Files:**
- Modify: `README.md` or existing sample documentation
- Modify: `openspec/changes/optimize-access-log-detection-rules/tasks.md`

- [ ] **Step 1: Locate sample documentation**

Run:

```bash
rg "access1|samples|sample" README.md docs openspec -n
```

Expected: identify the smallest existing place to describe `samples/access1.log`.

- [ ] **Step 2: Update documentation**

Add a concise note:

```markdown
- `samples/access1.log`: middleware common access-log fixture showing repeated URL-encoded boolean-blind SQL injection enumeration against `/index.php`.
```

- [ ] **Step 3: Check off completed OpenSpec tasks**

In `openspec/changes/optimize-access-log-detection-rules/tasks.md`, change completed checkboxes from `- [ ]` to `- [x]`.

- [ ] **Step 4: Run strict OpenSpec validation**

Run:

```bash
openspec validate optimize-access-log-detection-rules --strict
```

Expected: `Change 'optimize-access-log-detection-rules' is valid`.

- [ ] **Step 5: Commit Task 6**

```bash
git add README.md openspec/changes/optimize-access-log-detection-rules/tasks.md
git commit -m "docs: describe access1 sql injection fixture"
```

## Task 7: Final Verification

**Files:**
- No production edits expected

- [ ] **Step 1: Run targeted tests**

Run:

```bash
python -m pytest tests/test_models.py tests/test_parsers.py tests/test_rules.py tests/test_samples.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full Python suite**

Run:

```bash
python -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 3: Run frontend syntax check if serializers or web sample listing changed**

Run if web/static files changed:

```bash
node --check logcheck/web_static/app.js
```

Expected: no syntax errors.

- [ ] **Step 4: Run OpenSpec strict validation**

Run:

```bash
openspec validate optimize-access-log-detection-rules --strict
```

Expected: `Change 'optimize-access-log-detection-rules' is valid`.

- [ ] **Step 5: Commit final verification notes if any task/report file changed**

```bash
git add openspec/changes/optimize-access-log-detection-rules/tasks.md
git commit -m "chore: complete access log detection build tasks"
```

## Self-Review

- Spec coverage: parser metadata, SQLi grouping, `access1.log`, bounded evidence, local-only safety, and documentation are all mapped to tasks.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: plan uses `Event.metadata` consistently as `dict[str, object]`; rule tests use existing `Finding` fields for user-visible output.
