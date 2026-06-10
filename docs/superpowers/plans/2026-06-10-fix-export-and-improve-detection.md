---
change: fix-export-and-improve-detection
design-doc: docs/superpowers/specs/2026-06-10-fix-export-and-improve-detection-design.md
base-ref: 2a0237fbd5600e9aa94db9df44d9082161dccc30
---

# Fix Export and Improve Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make web report export reliable and add lightweight, explainable local template/sequence detection rules.

**Architecture:** Keep the existing Flask route and in-memory analysis id contract for exports, then harden route/frontend state and tests. Extend the existing deterministic rules pipeline with small helper functions and validated config fields rather than adding external anomaly-detection frameworks.

**Tech Stack:** Python 3.11, Flask, unittest/pytest, plain JavaScript, existing Logcheck dataclasses and exporters.

---

## File Map

- Modify `tests/test_webapp.py`: add export filename/content-disposition and unsupported-format coverage.
- Modify `logcheck/webapp.py`: harden `/api/exports/<fmt>` error handling and download response details if tests reveal gaps.
- Modify `logcheck/web_static/app.js`: keep export state tied to the latest successful analysis id and expose visible export errors if route failures are handled without navigation.
- Modify `tests/test_rules.py`: add behavior config and detection regression tests.
- Modify `logcheck/models.py`: extend `DetectionConfig` with behavior-rule fields.
- Modify `logcheck/config.py`: load, validate, and serialize behavior-rule config.
- Modify `logcheck/rules.py`: add template normalization, template burst detection, and auth-to-privilege sequence detection.
- Modify `openspec/changes/fix-export-and-improve-detection/tasks.md`: mark completed checklist items as implementation progresses.

---

### Task 1: Lock Down Web Export Behavior

**Files:**
- Modify: `tests/test_webapp.py`
- Modify if needed: `logcheck/webapp.py`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add missing export API tests**

Add tests near the existing export tests in `tests/test_webapp.py`:

```python
def test_export_json_sets_download_filename(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post(
        "/api/analyze",
        data={"sample_ids": "auth.log"},
        content_type="multipart/form-data",
    )
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/json?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    assert "analysis.json" in response.headers["Content-Disposition"]


def test_export_csv_sets_download_filename(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post(
        "/api/analyze",
        data={"sample_ids": "auth.log"},
        content_type="multipart/form-data",
    )
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/csv?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert "analysis.csv" in response.headers["Content-Disposition"]


def test_export_markdown_sets_download_filename(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post(
        "/api/analyze",
        data={"sample_ids": "auth.log"},
        content_type="multipart/form-data",
    )
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/markdown?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert "analysis.md" in response.headers["Content-Disposition"]


def test_export_rejects_unsupported_format(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/pdf?analysis_id=anything")

    assert response.status_code == 404
    assert "unsupported export format" in response.get_json()["error"].lower()
```

- [ ] **Step 2: Run export tests and inspect failures**

Run:

```powershell
python -m pytest tests/test_webapp.py -q
```

Expected before implementation: existing tests may already pass, but any new filename or unsupported-format assertion failure identifies the exact route gap.

- [ ] **Step 3: Harden the export route if tests fail**

If needed, update `logcheck/webapp.py` inside `export(fmt: str)` to keep the existing behavior but wrap local exporter failures:

```python
        filename, mimetype, exporter = EXPORTERS[fmt]
        export_root = Path(app.config["UPLOAD_DIR"]) / "exports"
        export_path = export_root / f"{uuid4().hex}-{filename}"
        try:
            exporter(result, export_path)
            return send_file(
                export_path,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename,
            )
        except OSError as exc:
            return jsonify({"error": f"Could not export local report: {exc}"}), 500
```

Keep the route local-only. Do not add URL/domain/export-to-remote behavior.

- [ ] **Step 4: Re-run export tests**

Run:

```powershell
python -m pytest tests/test_webapp.py -q
```

Expected: all webapp tests pass.

- [ ] **Step 5: Mark OpenSpec export tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark export coverage/fix tasks that are actually satisfied:

```markdown
- [x] 1.1 Add API regression tests for successful JSON, CSV, and Markdown export downloads after a web analysis run.
- [x] 1.2 Add API tests for unsupported export format, missing analysis id, and unknown or stale analysis id.
- [x] 2.1 Audit the current frontend export button handler and backend `/api/exports/<fmt>` route to identify the failing path.
- [x] 2.2 Fix backend export handling so report files are created under the local worktmp export directory and served with stable filenames/content types.
```

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git add tests/test_webapp.py logcheck/webapp.py openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "test: cover web report export downloads"
```

If `logcheck/webapp.py` did not change, omit it from `git add`.

---

### Task 2: Tighten Frontend Export State

**Files:**
- Modify: `tests/test_webapp.py`
- Modify if needed: `logcheck/web_static/app.js`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add static frontend export-state tests**

Add these assertions near `test_dashboard_script_uses_only_local_api_routes` in `tests/test_webapp.py`:

```python
def test_dashboard_script_clears_stale_analysis_id_on_analysis_failure():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    catch_block = re.search(r"} catch \(error\) \{(?P<body>.*?)\n  \} finally \{", script, re.S)

    assert catch_block is not None
    assert 'state.latestAnalysisId = "";' in catch_block.group("body")
    assert "toggleExports(false);" in catch_block.group("body")


def test_dashboard_export_buttons_are_disabled_until_analysis_id_exists():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "toggleExports(false);" in script
    assert "toggleExports(Boolean(state.latestAnalysisId));" in script
    assert "if (!state.latestAnalysisId)" in script
```

- [ ] **Step 2: Run frontend-related tests**

Run:

```powershell
python -m pytest tests/test_webapp.py -q
node --check logcheck/web_static/app.js
```

Expected: tests pass if existing frontend already handles state correctly.

- [ ] **Step 3: Patch frontend state only if tests fail**

If the catch block does not disable export controls, update `runAnalysis()` in `logcheck/web_static/app.js`:

```javascript
  } catch (error) {
    state.latestAnalysisId = "";
    state.findings = [];
    renderError(error.message || "Analysis failed.");
    toggleExports(false);
    setRunState("Needs attention");
  } finally {
    runButton.disabled = false;
  }
```

- [ ] **Step 4: Re-run frontend checks**

Run:

```powershell
python -m pytest tests/test_webapp.py -q
node --check logcheck/web_static/app.js
```

Expected: both commands pass.

- [ ] **Step 5: Mark OpenSpec frontend export tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 1.3 Add frontend test coverage or browser verification for export buttons before analysis, after analysis, and after export errors.
- [x] 2.3 Fix frontend export invocation so the latest successful `analysis_id` is included and stale state is cleared or handled correctly.
- [x] 2.4 Add clear local error handling for export failures without introducing remote/network behavior.
```

- [ ] **Step 6: Commit Task 2**

Run:

```powershell
git add tests/test_webapp.py logcheck/web_static/app.js openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "test: lock frontend export state"
```

If `logcheck/web_static/app.js` did not change, omit it from `git add`.

---

### Task 3: Add Behavior Config Tests

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/models.py`
- Modify: `logcheck/config.py`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add failing config tests**

Add tests in `tests/test_rules.py` after `test_config_to_dict_can_be_reloaded_from_json`:

```python
    def test_behavior_rule_config_is_loaded(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "behavior": {
                            "enabled": True,
                            "template_burst_threshold": 3,
                            "sequence_window_minutes": 15,
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertTrue(config.behavior_enabled)
        self.assertEqual(config.template_burst_threshold, 3)
        self.assertEqual(config.sequence_window_minutes, 15)

    def test_behavior_config_to_dict_can_be_reloaded_from_json(self):
        original = DetectionConfig(
            keywords={"custom_rule": ["needle"]},
            brute_force_threshold=4,
            brute_force_window_minutes=12,
            behavior_enabled=True,
            template_burst_threshold=3,
            sequence_window_minutes=15,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps(config_to_dict(original)), encoding="utf-8")

            reloaded = load_config(path)

        self.assertEqual(reloaded, original)

    def test_rule_config_rejects_invalid_behavior_values(self):
        cases = [
            {"enabled": "yes"},
            {"template_burst_threshold": True},
            {"template_burst_threshold": 0},
            {"template_burst_threshold": 2.5},
            {"sequence_window_minutes": False},
            {"sequence_window_minutes": 0},
            {"sequence_window_minutes": 7.5},
        ]
        for behavior in cases:
            with self.subTest(behavior=behavior):
                with TemporaryDirectory() as tmp:
                    path = Path(tmp) / "rules.json"
                    path.write_text(json.dumps({"behavior": behavior}), encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_config(path)

    def test_rule_config_rejects_unsupported_behavior_fields(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps({"behavior": {"template_burst_threshold": 3, "mode": "remote"}}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_config(path)
```

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```powershell
python -m pytest tests/test_rules.py -q
```

Expected: failures because `DetectionConfig` does not have behavior fields yet.

- [ ] **Step 3: Extend `DetectionConfig`**

Update `logcheck/models.py`:

```python
@dataclass(frozen=True)
class DetectionConfig:
    keywords: dict[str, list[str]]
    brute_force_threshold: int = 5
    brute_force_window_minutes: int = 10
    behavior_enabled: bool = True
    template_burst_threshold: int = 4
    sequence_window_minutes: int = 10
```

- [ ] **Step 4: Load and validate behavior config**

Update `logcheck/config.py`:

```python
SUPPORTED_BEHAVIOR_FIELDS = {
    "enabled",
    "template_burst_threshold",
    "sequence_window_minutes",
}
```

Add helper:

```python
def _validate_behavior(behavior: object) -> None:
    if not isinstance(behavior, dict):
        raise ValueError("behavior must be an object")
    unsupported = set(behavior) - SUPPORTED_BEHAVIOR_FIELDS
    if unsupported:
        raise ValueError(f"Unsupported behavior rule fields: {', '.join(sorted(unsupported))}")
    if "enabled" in behavior and not isinstance(behavior["enabled"], bool):
        raise ValueError("behavior.enabled must be a boolean")
    for field_name in ("template_burst_threshold", "sequence_window_minutes"):
        if field_name in behavior:
            value = _parse_int(behavior[field_name], f"behavior.{field_name}")
            if value < 1:
                raise ValueError(f"behavior.{field_name} must be positive")
```

In `load_config()` after brute-force validation:

```python
    behavior = data.get("behavior", {})
    _validate_behavior(behavior)
```

In the returned `DetectionConfig`:

```python
        behavior_enabled=behavior.get("enabled", base.behavior_enabled),
        template_burst_threshold=_parse_int(
            behavior.get("template_burst_threshold", base.template_burst_threshold),
            "behavior.template_burst_threshold",
        ),
        sequence_window_minutes=_parse_int(
            behavior.get("sequence_window_minutes", base.sequence_window_minutes),
            "behavior.sequence_window_minutes",
        ),
```

Then add behavior to `config_to_dict()`:

```python
        "behavior": {
            "enabled": config.behavior_enabled,
            "template_burst_threshold": config.template_burst_threshold,
            "sequence_window_minutes": config.sequence_window_minutes,
        },
```

- [ ] **Step 5: Run config/rule tests**

Run:

```powershell
python -m pytest tests/test_rules.py tests/test_models.py -q
```

Expected: tests pass or only expected assertion updates are needed for exact `config_to_dict()` output in existing tests.

- [ ] **Step 6: Update existing config assertions if needed**

If existing tests compare exact dictionaries, update expected dictionaries to include the default behavior block:

```python
"behavior": {
    "enabled": True,
    "template_burst_threshold": 4,
    "sequence_window_minutes": 10,
},
```

- [ ] **Step 7: Mark OpenSpec config tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 3.4 Add tests for behavior-rule configuration validation, including invalid thresholds and unsupported fields.
- [x] 4.2 Extend `DetectionConfig` and config loading with validated behavior/template thresholds and windows.
```

- [ ] **Step 8: Commit Task 3**

Run:

```powershell
git add tests/test_rules.py logcheck/models.py logcheck/config.py openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "feat: add behavior rule configuration"
```

---

### Task 4: Implement Template Burst Detection

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/rules.py`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add failing template burst tests**

Add tests in `tests/test_rules.py` near other behavior tests:

```python
    def test_template_burst_detects_repeated_variable_suspicious_events(self):
        config = DetectionConfig(
            keywords=default_config().keywords,
            template_burst_threshold=3,
        )
        events = [
            Event(
                "app.log",
                i,
                f"2026-06-10 ERROR unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
                category="application",
                actor="guest",
                source_address="192.0.2.10",
                message=f"unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
            )
            for i in range(1, 4)
        ]

        findings = detect_findings(events, config)
        burst = [finding for finding in findings if finding.rule_id == "behavior.template_burst"]

        self.assertEqual(len(burst), 1)
        self.assertEqual(burst[0].count, 3)
        self.assertEqual(burst[0].source_address, "192.0.2.10")
        self.assertIn("unauthorized access", burst[0].explanation.lower())
        self.assertIsNotNone(burst[0].severity_reason)
        self.assertIsNotNone(burst[0].confidence_reason)
        self.assertEqual(len(burst[0].evidence), 3)

    def test_template_burst_ignores_repeated_events_below_threshold(self):
        config = DetectionConfig(
            keywords=default_config().keywords,
            template_burst_threshold=4,
        )
        events = [
            Event(
                "app.log",
                i,
                f"2026-06-10 ERROR unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
                category="application",
                actor="guest",
                source_address="192.0.2.10",
                message=f"unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
            )
            for i in range(1, 4)
        ]

        findings = detect_findings(events, config)

        self.assertFalse(any(finding.rule_id == "behavior.template_burst" for finding in findings))
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_rules.py -q
```

Expected: template burst tests fail because the rule does not exist.

- [ ] **Step 3: Add template normalization helpers**

In `logcheck/rules.py`, add imports and helpers:

```python
import re
```

```python
SUSPICIOUS_TEMPLATE_TERMS = (
    "failed password",
    "failed login",
    "authentication failure",
    "invalid user",
    "unauthorized access",
    "permission denied",
    "sudo",
    "su:",
    "/etc/shadow",
    "/root",
    "/admin",
    "curl http",
    "wget http",
    "nc -e",
    "bash -i",
)


def _normalize_template(text: str) -> str:
    template = text.lower()
    template = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<ip>", template)
    template = re.sub(r"\b[0-9a-f]{12,}\b", "<hex>", template)
    template = re.sub(r"(['\"])(?:(?=(\\?))\2.)*?\1", "<quoted>", template)
    template = re.sub(r"/[a-z0-9_./-]+", "<path>", template)
    template = re.sub(r"\b\d+\b", "<num>", template)
    template = re.sub(r"\s+", " ", template).strip()
    return template


def _is_suspicious_template(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in SUSPICIOUS_TEMPLATE_TERMS)
```

- [ ] **Step 4: Add template burst rule**

In `logcheck/rules.py`, add:

```python
def _template_burst_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    if not config.behavior_enabled:
        return []

    buckets: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for event in events:
        text = _event_text(event)
        if not _is_suspicious_template(text):
            continue
        entity = event.source_address or event.actor or "unknown"
        buckets[(entity, _normalize_template(text))].append(event)

    findings: list[Finding] = []
    for (entity, template), bucket in buckets.items():
        if len(bucket) < config.template_burst_threshold:
            continue
        first = bucket[0]
        findings.append(
            Finding(
                rule_id="behavior.template_burst",
                severity="high",
                explanation=(
                    f"{len(bucket)} suspicious local events matched normalized template "
                    f"`{template}` for {entity}."
                ),
                evidence=[event.raw_line for event in bucket[:5]],
                source_file=first.source_file,
                line_number=first.line_number,
                timestamp=first.timestamp,
                source_address=first.source_address,
                actor=first.actor,
                target=first.target,
                count=len(bucket),
                severity_reason=(
                    "Repeated suspicious template activity meets the configured burst threshold."
                ),
                confidence_reason=(
                    "Variable tokens were normalized and repeated raw local evidence matched "
                    "the same suspicious template."
                ),
            )
        )
    return findings
```

Call it in `detect_findings()` after `_brute_force_findings` and before `_multi_signal_findings`:

```python
    findings.extend(_template_burst_findings(events, config))
```

- [ ] **Step 5: Run rule tests**

Run:

```powershell
python -m pytest tests/test_rules.py -q
```

Expected: rule tests pass.

- [ ] **Step 6: Mark OpenSpec template tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 3.2 Add tests for normalized-template burst detection using repeated local log messages with variable tokens.
- [x] 4.1 Add a small local template-normalization helper for rule logic while preserving original raw evidence.
```

- [ ] **Step 7: Commit Task 4**

Run:

```powershell
git add tests/test_rules.py logcheck/rules.py openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "feat: detect suspicious template bursts"
```

---

### Task 5: Implement Suspicious Sequence Detection

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/rules.py`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add sequence detection tests**

Add tests in `tests/test_rules.py`:

```python
    def test_auth_to_privilege_sequence_creates_correlated_finding(self):
        config = DetectionConfig(
            keywords=default_config().keywords,
            sequence_window_minutes=10,
        )
        events = [
            Event(
                "auth.log",
                1,
                "Jun 10 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.10 port 22 ssh2",
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                message="Failed password for admin from 192.0.2.10",
            ),
            Event(
                "auth.log",
                2,
                "Jun 10 10:03:00 host sudo: pam_unix(sudo:auth): authentication failure; user=root",
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                target="root",
                message="sudo:auth authentication failure user=root",
            ),
        ]

        findings = detect_findings(events, config)
        sequence = [
            finding
            for finding in findings
            if finding.rule_id == "behavior.auth_to_privilege_sequence"
        ]

        self.assertEqual(len(sequence), 1)
        self.assertEqual(sequence[0].source_address, "192.0.2.10")
        self.assertEqual(sequence[0].count, 2)
        self.assertEqual(len(sequence[0].evidence), 2)
        self.assertIsNotNone(sequence[0].severity_reason)
        self.assertIsNotNone(sequence[0].confidence_reason)

    def test_auth_to_privilege_sequence_requires_same_entity(self):
        events = [
            Event(
                "auth.log",
                1,
                "Failed password for admin from 192.0.2.10",
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                message="Failed password for admin from 192.0.2.10",
            ),
            Event(
                "auth.log",
                2,
                "sudo:auth authentication failure user=root",
                category="auth",
                source_address="198.51.100.7",
                actor="root",
                target="root",
                message="sudo:auth authentication failure user=root",
            ),
        ]

        findings = detect_findings(events, default_config())

        self.assertFalse(
            any(
                finding.rule_id == "behavior.auth_to_privilege_sequence"
                for finding in findings
            )
        )
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_rules.py -q
```

Expected: sequence tests fail because the rule does not exist.

- [ ] **Step 3: Implement sequence helper**

In `logcheck/rules.py`, add:

```python
AUTH_FAILURE_TERMS = ("failed password", "failed login", "authentication failure")


def _is_auth_failure(event: Event) -> bool:
    text = _event_text(event)
    return any(term in text for term in AUTH_FAILURE_TERMS)


def _is_privilege_signal(event: Event) -> bool:
    text = _event_text(event)
    return any(indicator.lower() in text for indicator in PRIVILEGE_ESCALATION_INDICATORS)


def _entity_keys(event: Event) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    if event.source_address:
        keys.append(("source", event.source_address))
    if event.actor:
        keys.append(("actor", event.actor))
    return keys
```

- [ ] **Step 4: Implement sequence rule**

Add:

```python
def _auth_to_privilege_sequence_findings(
    events: list[Event], config: DetectionConfig
) -> list[Finding]:
    if not config.behavior_enabled:
        return []

    auth_by_entity: dict[tuple[str, str], list[Event]] = defaultdict(list)
    privilege_by_entity: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for event in events:
        for key in _entity_keys(event):
            if _is_auth_failure(event):
                auth_by_entity[key].append(event)
            if _is_privilege_signal(event):
                privilege_by_entity[key].append(event)

    findings: list[Finding] = []
    for key, auth_events in auth_by_entity.items():
        privilege_events = privilege_by_entity.get(key, [])
        if not privilege_events:
            continue
        first_auth = auth_events[0]
        first_privilege = privilege_events[0]
        entity_type, entity = key
        findings.append(
            Finding(
                rule_id="behavior.auth_to_privilege_sequence",
                severity="high",
                explanation=(
                    f"{entity_type.title()} {entity} showed failed authentication followed "
                    "by privilege-escalation evidence in local logs."
                ),
                evidence=[first_auth.raw_line, first_privilege.raw_line],
                source_file=first_auth.source_file,
                line_number=first_auth.line_number,
                timestamp=first_auth.timestamp,
                source_address=entity if entity_type == "source" else first_auth.source_address,
                actor=entity if entity_type == "actor" else first_auth.actor,
                target=first_privilege.target,
                count=2,
                severity_reason=(
                    "Authentication failure followed by privilege-escalation evidence raises "
                    "local review priority."
                ),
                confidence_reason=(
                    "Both stages were observed in raw local log evidence for the same entity."
                ),
            )
        )
    return findings
```

Call it in `detect_findings()` after `_template_burst_findings`:

```python
    findings.extend(_auth_to_privilege_sequence_findings(events, config))
```

- [ ] **Step 5: Run rule tests**

Run:

```powershell
python -m pytest tests/test_rules.py -q
```

Expected: tests pass.

- [ ] **Step 6: Mark OpenSpec sequence tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 3.3 Add tests for suspicious local behavior sequence detection, including a non-matching outside-window case.
- [x] 4.3 Implement deterministic template-burst and sequence-correlation findings with severity and confidence reasons.
- [x] 4.4 Ensure new findings serialize and export with source context, evidence, severity reason, confidence reason, and counts.
```

- [ ] **Step 7: Commit Task 5**

Run:

```powershell
git add tests/test_rules.py logcheck/rules.py openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "feat: correlate auth and privilege behavior"
```

---

### Task 6: Research Note and Final Verification

**Files:**
- Create: `docs/log-detection-research-notes.md`
- Modify: `openspec/changes/fix-export-and-improve-detection/tasks.md`

- [ ] **Step 1: Add concise research adaptation note**

Create `docs/log-detection-research-notes.md`:

```markdown
# Log Detection Research Notes

Logcheck adapts ideas from modern log anomaly detection while staying local and deterministic.

## Adapted Ideas

- LogAI: keep a clear local analysis pipeline with parsing, feature extraction, detection, and reviewable outputs.
- LogPAI/logparser/Drain: normalize volatile log tokens into templates before counting repeated behavior.
- LogBERT-style sequence detection: treat suspicious event order as useful context, but implement deterministic sequence rules instead of training a model.

## Project Boundary

This project does not fetch external logs, query domains, scan networks, train remote models, block accounts, exploit systems, or submit reports externally. All detections are derived from local parsed events and local configuration.
```

- [ ] **Step 2: Mark research task**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 3.1 Document the specific LogAI, LogPAI/logparser/Drain, and LogBERT-inspired ideas being adapted as lightweight local heuristics.
```

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m pytest tests -q
node --check logcheck/web_static/app.js
```

Expected: all tests pass and JavaScript syntax check passes.

- [ ] **Step 4: Run browser verification**

Start the app:

```powershell
python -m logcheck.webapp
```

Open `http://127.0.0.1:8765`, run analysis on a bundled local sample, and verify JSON, CSV, and Markdown downloads work. Confirm the page still has no URL/domain input, remote fetch workflow, scan, block, exploit, or external report controls.

- [ ] **Step 5: Mark verification tasks**

In `openspec/changes/fix-export-and-improve-detection/tasks.md`, mark:

```markdown
- [x] 5.1 Run the Python test suite covering parsers, rules, exporters, CLI, and web API.
- [x] 5.2 Run JavaScript syntax/static checks for the web frontend.
- [x] 5.3 Run the local web dashboard and verify export downloads work from the browser for JSON, CSV, and Markdown.
- [x] 5.4 Verify the UI still has no URL/domain inputs, remote fetching, scanning, blocking, exploitation, or external reporting controls.
```

- [ ] **Step 6: Commit Task 6**

Run:

```powershell
git add docs/log-detection-research-notes.md openspec/changes/fix-export-and-improve-detection/tasks.md
git commit -m "docs: record log detection research adaptation"
```

---

## Self-Review

- Export requirements are covered by Task 1 and Task 2.
- Detection template behavior, sequence behavior, config validation, explainability, and local-only boundaries are covered by Tasks 3 through 6.
- The plan keeps changes inside existing modules and does not add runtime network or ML dependencies.
- The plan uses test-first steps and includes exact commands for local verification.
