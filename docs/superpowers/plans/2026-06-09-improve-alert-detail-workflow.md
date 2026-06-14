# Improve Alert Detail Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Logcheck's web dashboard support a clearer alert review workflow where clicking a finding shows detailed local log evidence without chart or insight overlap.

**Architecture:** Keep the existing Flask app and static frontend. Add behavior through focused tests, frontend rendering helpers in `logcheck/web_static/app.js`, CSS constraints in `logcheck/web_static/styles.css`, and only minimal serialization changes if tests prove the existing `Finding.to_dict()` payload is not enough.

**Tech Stack:** Python, pytest, Flask test client, static JavaScript, CSS, OpenSpec/Comet.

---
change: improve-alert-detail-workflow
design-doc: docs/superpowers/specs/2026-06-09-improve-alert-detail-workflow-design.md
base-ref: 959fb8ec6c2b21667fb96ddc81c11dde92a4435c
---

## File Map

- Modify `tests/test_webapp.py`: add static regression tests for alert list/detail behavior, stale detail clearing, concise insights, and chart layout CSS hooks.
- Modify `tests/test_web_serialization.py`: add a focused serialization test only if frontend tests show the existing payload cannot expose the exact alert log line; otherwise leave unchanged.
- Modify `logcheck/web_static/app.js`: refactor finding list and selected alert detail rendering; reduce insight duplication; preserve local-only fetch behavior.
- Modify `logcheck/web_static/styles.css`: constrain alert detail, evidence, insight, and chart label layout so long text does not create page-level horizontal overflow.
- Modify `openspec/changes/improve-alert-detail-workflow/tasks.md`: check off tasks as they are completed.
- Modify `docs/web-frontend-verification.md`: append browser verification notes after implementation.

## Task 1: Add Failing Alert Detail Rendering Tests

**Files:**
- Modify: `tests/test_webapp.py`
- Later modify: `logcheck/web_static/app.js`

- [ ] **Step 1: Add static tests for selected alert detail behavior**

Append these tests near the existing dashboard script tests in `tests/test_webapp.py`:

```python
def test_dashboard_script_renders_structured_selected_alert_detail():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    for expected in [
        "renderSelectedAlert",
        "alert-detail-section",
        "alert-log-detail",
        "Severity reason",
        "Confidence reason",
        "Selected alert",
    ]:
        assert expected in script

    assert "No evidence lines were attached to this finding." not in script


def test_dashboard_script_clears_stale_selected_alert_when_no_findings():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "clearSelectedAlert" in script
    assert "No findings were produced for the selected local material." in script
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_renders_structured_selected_alert_detail tests/test_webapp.py::test_dashboard_script_clears_stale_selected_alert_when_no_findings -q
```

Expected: both tests fail because `renderSelectedAlert`, `clearSelectedAlert`, `alert-detail-section`, and `alert-log-detail` are not in the current script.

- [ ] **Step 3: Implement minimal selected alert renderer**

In `logcheck/web_static/app.js`, replace the `renderEvidence` function and its call sites with `renderSelectedAlert`.

Change `renderResult(payload)` from:

```javascript
  if (state.findings.length) {
    renderEvidence(state.findings[0], 0);
  } else {
    evidenceDetail.innerHTML = '<p class="empty-state">No findings were produced for the selected local material.</p>';
  }
```

to:

```javascript
  if (state.findings.length) {
    renderSelectedAlert(state.findings[0], 0);
  } else {
    clearSelectedAlert("No findings were produced for the selected local material.");
  }
```

Change the finding click handler from:

```javascript
      renderEvidence(finding, index);
```

to:

```javascript
      renderSelectedAlert(finding, index);
```

Replace `renderEvidence` with:

```javascript
function renderSelectedAlert(finding, index) {
  const lines = finding.evidence || finding.matched_lines || [];
  const logMarkup = lines.length
    ? lines.map((line) => `<div class="alert-log-line">${escapeHtml(String(line))}</div>`).join("")
    : '<p class="empty-state">No alert-specific log detail is available for this finding.</p>';
  const sourceContext = sourceContextRows(finding);
  const reasonRows = reasonContextRows(finding);
  evidenceDetail.innerHTML = `
    <section class="alert-detail-section">
      <p class="detail-eyebrow">Selected alert</p>
      <h3>${escapeHtml(finding.rule_id || `Finding ${index + 1}`)}</h3>
      <div class="detail-meta">
        ${escapeHtml(finding.explanation || "Review evidence")} | ${escapeHtml(finding.source_file || "Local source")} | ${escapeHtml(finding.severity || "info")}
      </div>
    </section>
    <section class="alert-detail-section">
      <h4>Source context</h4>
      <dl class="source-context">${sourceContext}</dl>
    </section>
    ${reasonRows}
    <section class="alert-detail-section">
      <h4>Log detail</h4>
      <div class="alert-log-detail">${logMarkup}</div>
    </section>
  `;
}

function clearSelectedAlert(message) {
  evidenceDetail.innerHTML = `<p class="empty-state">${escapeHtml(message)}</p>`;
}
```

Add this helper after `sourceContextRows`:

```javascript
function reasonContextRows(finding) {
  const fields = [
    ["Severity reason", finding.severity_reason],
    ["Confidence reason", finding.confidence_reason],
  ];
  const rows = fields
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(
      ([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(String(value))}</dd>
        </div>
      `
    )
    .join("");
  if (!rows) {
    return "";
  }
  return `
    <section class="alert-detail-section">
      <h4>Reasoning</h4>
      <dl class="source-context">${rows}</dl>
    </section>
  `;
}
```

In `renderError(message)`, change:

```javascript
  evidenceDetail.innerHTML = '<p class="empty-state">Select local material and run analysis.</p>';
```

to:

```javascript
  clearSelectedAlert("Select local material and run analysis.");
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_renders_structured_selected_alert_detail tests/test_webapp.py::test_dashboard_script_clears_stale_selected_alert_when_no_findings -q
```

Expected: both tests pass.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add tests/test_webapp.py logcheck/web_static/app.js openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "feat: render structured selected alert details"
```

## Task 2: Add Failing Tests for Concise Insights and Optional Fields

**Files:**
- Modify: `tests/test_webapp.py`
- Later modify: `logcheck/web_static/app.js`

- [ ] **Step 1: Add tests for concise insight rendering and optional rows**

Append:

```python
def test_dashboard_script_keeps_insights_separate_from_alert_evidence():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "entity_profiles" in script
    assert "timeline" not in re.search(
        r"function normalizeInsights\(insights\) \{(?P<body>.*?)\n\}",
        script,
        re.DOTALL,
    ).group("body")


def test_dashboard_script_omits_empty_optional_detail_fields():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "value !== null && value !== undefined && value !== \"\"" in script
    assert "Severity reason" in script
    assert "Confidence reason" in script
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_keeps_insights_separate_from_alert_evidence tests/test_webapp.py::test_dashboard_script_omits_empty_optional_detail_fields -q
```

Expected: the insight test fails because `normalizeInsights` currently includes timeline entries, duplicating alert-like content.

- [ ] **Step 3: Refactor `normalizeInsights` to summarize instead of duplicate every alert**

In `logcheck/web_static/app.js`, replace `normalizeInsights` with:

```javascript
function normalizeInsights(insights) {
  if (!insights) {
    return [];
  }
  if (Array.isArray(insights)) {
    return insights.map((insight) => insight.title || insight.message || String(insight));
  }
  const items = [];
  if (insights.headline) {
    items.push(insights.headline);
  }
  if (insights.risk_level) {
    items.push(`Risk level: ${insights.risk_level}`);
  }
  for (const profile of insights.entity_profiles || []) {
    const value = profile.value || "unknown";
    const count = profile.finding_count || 0;
    items.push(`Affected ${profile.kind || "entity"}: ${value} (${count} findings)`);
  }
  for (const suggestion of insights.suggestions || []) {
    items.push(`${suggestion.title}: ${suggestion.detail}`);
  }
  return items.filter(Boolean).slice(0, 6);
}
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_keeps_insights_separate_from_alert_evidence tests/test_webapp.py::test_dashboard_script_omits_empty_optional_detail_fields -q
```

Expected: both tests pass.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add tests/test_webapp.py logcheck/web_static/app.js openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "feat: keep insights concise and separate"
```

## Task 3: Add Failing Layout Tests for Evidence and Chart Overflow

**Files:**
- Modify: `tests/test_webapp.py`
- Later modify: `logcheck/web_static/styles.css`

- [ ] **Step 1: Add CSS regression tests**

Append:

```python
def test_dashboard_styles_constrain_alert_log_detail_overflow():
    styles = (PROJECT_ROOT / "logcheck" / "web_static" / "styles.css").read_text(encoding="utf-8")

    for selector in [".alert-detail-section", ".alert-log-detail", ".alert-log-line"]:
        assert selector in styles
    assert "overflow-x: auto" in styles
    assert "overflow-wrap: anywhere" in styles


def test_dashboard_styles_prevent_chart_label_overlap():
    styles = (PROJECT_ROOT / "logcheck" / "web_static" / "styles.css").read_text(encoding="utf-8")

    assert "grid-template-columns: minmax(0, 1.1fr) minmax(80px, 1.8fr) minmax(24px, auto)" in styles
    assert ".chart-label" in styles
    assert "max-width: 100%" in styles
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_styles_constrain_alert_log_detail_overflow tests/test_webapp.py::test_dashboard_styles_prevent_chart_label_overlap -q
```

Expected: both tests fail because the new selectors and exact chart grid constraint are not present.

- [ ] **Step 3: Add CSS constraints**

In `logcheck/web_static/styles.css`, add after `.evidence-detail h3`:

```css
.detail-eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.alert-detail-section {
  min-width: 0;
  margin-bottom: 14px;
}

.alert-detail-section:last-child {
  margin-bottom: 0;
}

.alert-detail-section h4 {
  margin: 0 0 8px;
  font-size: 13px;
}

.alert-log-detail {
  display: grid;
  max-width: 100%;
  gap: 8px;
  overflow-x: auto;
}

.alert-log-line {
  min-width: 0;
  border-left: 3px solid var(--accent);
  background: #f7faf8;
  padding: 8px 10px;
  color: #24342b;
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
```

Keep `.evidence-line` temporarily for compatibility or remove it after all references are gone. Change `.chart-row` grid columns to:

```css
  grid-template-columns: minmax(0, 1.1fr) minmax(80px, 1.8fr) minmax(24px, auto);
```

Add `max-width: 100%;` inside `.chart-label`.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_styles_constrain_alert_log_detail_overflow tests/test_webapp.py::test_dashboard_styles_prevent_chart_label_overlap -q
```

Expected: both tests pass.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add tests/test_webapp.py logcheck/web_static/styles.css openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "fix: constrain alert evidence and chart layout"
```

## Task 4: Verify Existing Payload Is Sufficient

**Files:**
- Modify only if needed: `tests/test_web_serialization.py`
- Modify only if needed: `logcheck/web_serialization.py`

- [ ] **Step 1: Add a serialization regression if evidence line coverage is missing**

Inspect `tests/test_web_serialization.py`. If `test_serialize_result_includes_summary_and_source_context` already asserts `finding["evidence"]`, no change is needed. If it does not, add:

```python
    assert finding["evidence"] == ["Failed password for root from 192.0.2.10"]
```

- [ ] **Step 2: Run serialization test and verify RED or already-covered**

Run:

```bash
python -m pytest tests/test_web_serialization.py::test_serialize_result_includes_summary_and_source_context -q
```

Expected: if the assertion was newly added and payload lacks evidence, fail on missing/incorrect `evidence`. If it passes, the current payload is sufficient and no serializer implementation is needed.

- [ ] **Step 3: Implement only if the test fails**

If the test fails because `evidence` is missing, update `logcheck/web_serialization.py` so serialized findings include the existing `Finding.to_dict()` evidence field. Do not add a new backend context model for this change.

- [ ] **Step 4: Run serialization test and verify GREEN**

Run:

```bash
python -m pytest tests/test_web_serialization.py::test_serialize_result_includes_summary_and_source_context -q
```

Expected: pass.

- [ ] **Step 5: Commit Task 4**

If files changed, run:

```bash
git add tests/test_web_serialization.py logcheck/web_serialization.py openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "test: preserve alert evidence serialization"
```

If no files changed, check off the related task in `openspec/changes/improve-alert-detail-workflow/tasks.md` in the next commit.

## Task 5: Full Automated Verification

**Files:**
- Modify: `openspec/changes/improve-alert-detail-workflow/tasks.md`

- [ ] **Step 1: Run focused web tests**

Run:

```bash
python -m pytest tests/test_webapp.py tests/test_web_serialization.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Syntax check frontend JavaScript**

Run:

```bash
node --check logcheck/web_static/app.js
```

Expected: no syntax errors.

- [ ] **Step 4: Mark OpenSpec build tasks complete**

In `openspec/changes/improve-alert-detail-workflow/tasks.md`, change all completed checkboxes from `- [ ]` to `- [x]` for tasks covered by implementation and tests.

- [ ] **Step 5: Commit verification task state**

Run:

```bash
git add openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "chore: mark alert workflow tasks complete"
```

## Task 6: Browser Verification Notes

**Files:**
- Modify: `docs/web-frontend-verification.md`
- Modify: `openspec/changes/improve-alert-detail-workflow/tasks.md`

- [ ] **Step 1: Start local web app**

Run the project web app using the existing project command. If no helper command is documented, use:

```bash
python -m logcheck.webapp
```

Expected: local server starts and prints or serves a local URL.

- [ ] **Step 2: Verify desktop layout in browser**

Open the local dashboard in the in-app browser. Select `incident.log` or another bundled sample, run analysis, click a finding, and confirm:

- selected alert detail shows the clicked alert's log evidence
- source metadata is visible
- insights are concise and separate
- chart labels do not overlap adjacent chart groups

- [ ] **Step 3: Verify mobile-width layout in browser**

Resize browser to a mobile-width viewport such as 390x844. Confirm:

- visual report charts stack vertically
- alert detail remains readable
- long log text stays inside its panel
- no page-level horizontal scrolling is required for chart/detail content

- [ ] **Step 4: Append verification notes**

Append a dated section to `docs/web-frontend-verification.md`:

```markdown
## 2026-06-09 Alert Detail Workflow Verification

- Desktop: selected alert detail displayed alert-specific log evidence after clicking a finding.
- Desktop: insights stayed concise and separate from selected evidence.
- Desktop: visual report labels stayed inside chart groups.
- Mobile width: charts stacked vertically and alert detail remained readable without incoherent overlap.
- Commands: `python -m pytest -q`; `node --check logcheck/web_static/app.js`.
```

- [ ] **Step 5: Commit browser verification notes**

Run:

```bash
git add docs/web-frontend-verification.md openspec/changes/improve-alert-detail-workflow/tasks.md
git commit -m "docs: record alert workflow verification"
```

## Self-Review

- Spec coverage: tasks cover selected alert list/detail behavior, detailed local log evidence, concise separate insights, chart overlap prevention, empty states, automated tests, and browser verification.
- Placeholder scan: no unfinished placeholder markers or unspecified implementation steps remain.
- Type consistency: plan uses existing `finding` fields from `Finding.to_dict()` and existing frontend state names.
