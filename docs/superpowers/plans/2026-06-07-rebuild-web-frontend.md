---
change: rebuild-web-frontend
design-doc: docs/superpowers/specs/2026-06-07-rebuild-web-frontend-technical-design.md
base-ref: f9a1d1b18623222f2c000a5ade464f3304c0e82b
archived-with: 2026-06-09-rebuild-web-frontend
---

# Rebuild Web Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the GUI frontend direction with a local-only browser dashboard for Logcheck analysis.

**Architecture:** Add a lightweight Flask web entry point that serves static dashboard assets and exposes local API routes. Keep detection logic in the existing parser, analysis, insight, and exporter modules; the web layer handles local input intake, result serialization, rendering, and export state.

**Tech Stack:** Python 3.11, Flask test client, vanilla HTML/CSS/JavaScript, existing Logcheck analysis/exporter modules, pytest/unittest.

---

## File Structure

- Create `logcheck/web_serialization.py`: convert `AnalysisResult`, summaries, findings, diagnostics, and insights into dashboard JSON.
- Create `logcheck/webapp.py`: Flask app factory, local sample listing, upload handling, analysis route, export route, health route, and static asset serving.
- Create `logcheck/web_static/index.html`: single-page Local Investigation Dashboard markup.
- Create `logcheck/web_static/styles.css`: dense operational dashboard styling with responsive desktop/mobile-width layout.
- Create `logcheck/web_static/app.js`: dashboard state, file/sample selection, API calls, result rendering, export actions.
- Create `tests/test_web_serialization.py`: unit tests for JSON shape and source context.
- Create `tests/test_webapp.py`: API tests for samples, upload analysis, mixed inputs, exports, pre-analysis export error, and forbidden controls.
- Modify `pyproject.toml`: replace PyQt dependency with Flask, add `logcheck-web` script, include static package data, and remove or deprecate `logcheck-desktop`.
- Modify `openspec/changes/rebuild-web-frontend/tasks.md`: check implementation tasks as they are completed.

## Task 1: Web Result Serialization

**Files:**
- Create: `logcheck/web_serialization.py`
- Test: `tests/test_web_serialization.py`

- [ ] **Step 1: Write serialization tests**

Create `tests/test_web_serialization.py`:

```python
from logcheck.insights import generate_insights
from logcheck.models import AnalysisResult, Event, Finding
from logcheck.web_serialization import serialize_result


def make_result() -> AnalysisResult:
    result = AnalysisResult(
        events=[
            Event(
                source_file="auth.log",
                line_number=7,
                raw_line="Failed password for root from 192.0.2.10",
                category="auth",
                actor="root",
                target="sshd",
                source_address="192.0.2.10",
            )
        ],
        findings=[
            Finding(
                rule_id="keyword.failed_login",
                severity="medium",
                explanation="Matched failed login keyword",
                evidence=["Failed password for root from 192.0.2.10"],
                source_file="auth.log",
                line_number=7,
                source_address="192.0.2.10",
                actor="root",
                target="sshd",
                matched_keyword="Failed password",
                confidence_reason="exact keyword match",
            )
        ],
        diagnostics=["empty.log contributed no events"],
    )
    result.insights = generate_insights(result)
    return result


def test_serialize_result_includes_summary_and_source_context():
    payload = serialize_result(make_result())

    assert payload["summary"]["total_events"] == 1
    assert payload["summary"]["total_findings"] == 1
    assert payload["summary"]["findings_by_severity"] == {"medium": 1}
    assert payload["diagnostics"] == ["empty.log contributed no events"]
    finding = payload["findings"][0]
    assert finding["rule_id"] == "keyword.failed_login"
    assert finding["source_file"] == "auth.log"
    assert finding["line_number"] == 7
    assert finding["actor"] == "root"
    assert finding["target"] == "sshd"
    assert finding["source_address"] == "192.0.2.10"
    assert finding["confidence_reason"] == "exact keyword match"


def test_serialize_result_includes_insights_when_present():
    payload = serialize_result(make_result())

    assert payload["insights"]["headline"]
    assert "entity_profiles" in payload["insights"]
    assert "timeline" in payload["insights"]
    assert "suggestions" in payload["insights"]
```

- [ ] **Step 2: Run serialization tests and verify failure**

Run: `python -m pytest tests/test_web_serialization.py -q`

Expected: FAIL because `logcheck.web_serialization` does not exist.

- [ ] **Step 3: Implement serialization**

Create `logcheck/web_serialization.py`:

```python
from __future__ import annotations

from collections import Counter
from typing import Any

from .models import AnalysisResult


def _serialize_insights(insights: object | None) -> dict[str, Any] | None:
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


def serialize_result(result: AnalysisResult) -> dict[str, Any]:
    severities = Counter(finding.severity for finding in result.findings)
    sources = sorted(
        {event.source_file for event in result.events if event.source_file}
        or {finding.source_file for finding in result.findings if finding.source_file}
    )
    payload: dict[str, Any] = {
        "summary": {
            "total_events": len(result.events),
            "total_findings": len(result.findings),
            "findings_by_severity": dict(severities),
            "analyzed_sources": sources,
        },
        "diagnostics": list(result.diagnostics),
        "findings": [finding.to_dict() for finding in result.findings],
        "events": [
            {
                "source_file": event.source_file,
                "line_number": event.line_number,
                "raw_line": event.raw_line,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "category": event.category,
                "actor": event.actor,
                "target": event.target,
                "source_address": event.source_address,
                "message": event.message,
            }
            for event in result.events[:200]
        ],
    }
    insights = _serialize_insights(result.insights)
    if insights is not None:
        payload["insights"] = insights
    return payload
```

- [ ] **Step 4: Run serialization tests and verify pass**

Run: `python -m pytest tests/test_web_serialization.py -q`

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Run:

```bash
git add logcheck/web_serialization.py tests/test_web_serialization.py
git commit -m "feat: serialize analysis results for web dashboard"
```

## Task 2: Local Web API

**Files:**
- Create: `logcheck/webapp.py`
- Test: `tests/test_webapp.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add Flask dependency and web script expectation**

Modify `pyproject.toml` so dependencies and scripts include:

```toml
dependencies = ["Flask>=3.0"]

[project.scripts]
logcheck = "logcheck.cli:main"
logcheck-web = "logcheck.webapp:main"

[tool.setuptools.package-data]
logcheck = ["web_static/*"]
```

Keep the desktop script only if implementation has not yet removed `logcheck/desktop.py`; remove it in Task 6 when replacement coverage exists.

- [ ] **Step 2: Write API tests**

Create `tests/test_webapp.py`:

```python
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from logcheck.webapp import create_app


def make_app(tmp_path: Path):
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    (sample_dir / "auth.log").write_text(
        "Jun  1 10:00:00 host sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2\n",
        encoding="utf-8",
    )
    return create_app(sample_dir=sample_dir, upload_dir=tmp_path / "uploads").test_client()


def test_health_endpoint(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_samples_endpoint_lists_local_samples(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/samples")

    assert response.status_code == 200
    assert response.get_json()["samples"] == [{"id": "auth.log", "name": "auth.log"}]


def test_analyze_uploaded_file(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={
            "files": (
                BytesIO(b"Jun  1 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.11 port 22 ssh2\n"),
                "upload.log",
            )
        },
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["summary"]["total_events"] == 1
    assert payload["summary"]["total_findings"] >= 1
    assert payload["findings"][0]["source_file"].endswith("upload.log")


def test_analyze_sample_and_uploaded_file_together(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={
            "sample_ids": "auth.log",
            "files": (BytesIO(b"generic suspicious malware line\n"), "extra.log"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json()["summary"]["total_events"] >= 2


def test_analyze_requires_local_input(tmp_path):
    client = make_app(tmp_path)

    response = client.post("/api/analyze", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert "local log" in response.get_json()["error"].lower()


def test_export_requires_analysis_first(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/json")

    assert response.status_code == 400
    assert "analysis must run" in response.get_json()["error"].lower()


def test_export_json_after_analysis(tmp_path):
    client = make_app(tmp_path)
    client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")

    response = client.get("/api/exports/json")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert b"findings" in response.data
```

- [ ] **Step 3: Run API tests and verify failure**

Run: `python -m pytest tests/test_webapp.py -q`

Expected: FAIL because `logcheck.webapp` does not exist or Flask dependency is missing.

- [ ] **Step 4: Implement Flask app**

Create `logcheck/webapp.py`:

```python
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename

from .analysis import analyze_logs
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
from .web_serialization import serialize_result


EXPORTERS = {
    "json": ("analysis.json", "application/json", export_json),
    "csv": ("analysis.csv", "text/csv", export_csv),
    "markdown": ("analysis.md", "text/markdown", export_markdown),
}


def create_app(sample_dir: Path | None = None, upload_dir: Path | None = None) -> Flask:
    static_dir = Path(__file__).with_name("web_static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config["SAMPLE_DIR"] = sample_dir or Path("samples")
    app.config["UPLOAD_DIR"] = upload_dir or Path("worktmp") / "web_uploads"
    app.config["LATEST_RESULT"] = None

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/samples")
    def samples():
        root = Path(app.config["SAMPLE_DIR"])
        entries = []
        if root.exists():
            entries = [
                {"id": path.name, "name": path.name}
                for path in sorted(root.iterdir())
                if path.is_file()
            ]
        return jsonify({"samples": entries})

    @app.post("/api/analyze")
    def analyze():
        paths = _selected_sample_paths(Path(app.config["SAMPLE_DIR"]), request.form.getlist("sample_ids"))
        paths.extend(_save_uploads(Path(app.config["UPLOAD_DIR"])))
        if not paths:
            return jsonify({"error": "Select at least one local log file or sample log."}), 400
        try:
            result = analyze_logs(paths)
        except (OSError, FileNotFoundError) as exc:
            return jsonify({"error": f"Could not analyze local input: {exc}"}), 400
        app.config["LATEST_RESULT"] = result
        return jsonify(serialize_result(result))

    @app.get("/api/exports/<fmt>")
    def export(fmt: str):
        if fmt not in EXPORTERS:
            return jsonify({"error": "Unsupported export format."}), 404
        result: AnalysisResult | None = app.config.get("LATEST_RESULT")
        if result is None:
            return jsonify({"error": "Analysis must run before exporting."}), 400
        filename, mimetype, exporter = EXPORTERS[fmt]
        export_root = Path(app.config["UPLOAD_DIR"]) / "exports"
        export_path = export_root / f"{uuid4().hex}-{filename}"
        exporter(result, export_path)
        return send_file(export_path, mimetype=mimetype, as_attachment=True, download_name=filename)

    return app


def _selected_sample_paths(sample_dir: Path, sample_ids: list[str]) -> list[Path]:
    paths = []
    for sample_id in sample_ids:
        safe_name = Path(sample_id).name
        path = sample_dir / safe_name
        if path.is_file():
            paths.append(path)
    return paths


def _save_uploads(upload_dir: Path) -> list[Path]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for upload in request.files.getlist("files"):
        if not upload.filename:
            continue
        filename = secure_filename(upload.filename)
        if not filename:
            continue
        path = upload_dir / f"{uuid4().hex}-{filename}"
        upload.save(path)
        paths.append(path)
    return paths


def main() -> None:
    upload_root = Path("worktmp") / "web_uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    app = create_app(upload_dir=upload_root)
    app.run(host="127.0.0.1", port=8765, debug=False)
```

- [ ] **Step 5: Run API tests and verify pass**

Run: `python -m pytest tests/test_webapp.py tests/test_web_serialization.py -q`

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add pyproject.toml logcheck/webapp.py tests/test_webapp.py
git commit -m "feat: add local web analysis API"
```

## Task 3: Dashboard Static UI

**Files:**
- Create: `logcheck/web_static/index.html`
- Create: `logcheck/web_static/styles.css`
- Create: `logcheck/web_static/app.js`
- Test: `tests/test_webapp.py`

- [ ] **Step 1: Add dashboard rendering and forbidden-control tests**

Append to `tests/test_webapp.py`:

```python
def test_index_renders_dashboard_regions(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Logcheck" in html
    assert "Source intake" in html
    assert "Analysis summary" in html
    assert "Finding queue" in html
    assert "Evidence detail" in html
    assert "Investigation insights" in html
    assert "Exports" in html


def test_index_does_not_offer_remote_controls(tmp_path):
    client = make_app(tmp_path)

    html = client.get("/").get_data(as_text=True).lower()

    forbidden = [
        "url",
        "domain",
        "remote upload",
        "network scan",
        "scan target",
        "exploit",
        "block ip",
        "external report",
    ]
    for text in forbidden:
        assert text not in html
```

- [ ] **Step 2: Run dashboard tests and verify failure**

Run: `python -m pytest tests/test_webapp.py::test_index_renders_dashboard_regions tests/test_webapp.py::test_index_does_not_offer_remote_controls -q`

Expected: FAIL because static dashboard assets do not exist.

- [ ] **Step 3: Create dashboard HTML**

Create `logcheck/web_static/index.html` with these fixed regions:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Logcheck</title>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <main class="dashboard">
    <header class="topbar">
      <div>
        <h1>Logcheck</h1>
        <p>Local investigation dashboard</p>
      </div>
      <div id="status" class="status">Idle</div>
    </header>

    <section class="panel source-panel" aria-labelledby="source-title">
      <h2 id="source-title">Source intake</h2>
      <label class="upload-zone">
        <span>Upload local logs</span>
        <input id="file-input" type="file" name="files" multiple>
      </label>
      <div class="sample-row">
        <label for="sample-select">Sample logs</label>
        <select id="sample-select" multiple></select>
      </div>
      <button id="analyze-button" type="button">Run analysis</button>
      <p id="input-message" class="message"></p>
    </section>

    <section class="panel summary-panel" aria-labelledby="summary-title">
      <h2 id="summary-title">Analysis summary</h2>
      <div class="metrics">
        <div><span id="metric-events">0</span><small>Events</small></div>
        <div><span id="metric-findings">0</span><small>Findings</small></div>
        <div><span id="metric-risk">-</span><small>Risk</small></div>
      </div>
      <dl id="severity-list" class="severity-list"></dl>
    </section>

    <section class="panel findings-panel" aria-labelledby="findings-title">
      <h2 id="findings-title">Finding queue</h2>
      <div id="finding-list" class="finding-list"></div>
    </section>

    <section class="panel evidence-panel" aria-labelledby="evidence-title">
      <h2 id="evidence-title">Evidence detail</h2>
      <article id="evidence-detail" class="evidence-detail">Select a finding to inspect evidence.</article>
    </section>

    <section class="panel insights-panel" aria-labelledby="insights-title">
      <h2 id="insights-title">Investigation insights</h2>
      <div id="insights"></div>
    </section>

    <section class="panel export-panel" aria-labelledby="exports-title">
      <h2 id="exports-title">Exports</h2>
      <div class="export-actions">
        <button data-export="json" type="button" disabled>JSON</button>
        <button data-export="csv" type="button" disabled>CSV</button>
        <button data-export="markdown" type="button" disabled>Markdown</button>
      </div>
    </section>
  </main>
  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create dashboard CSS**

Create `logcheck/web_static/styles.css` with stable, responsive panel sizing:

```css
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f4f6f8;
  color: #18212f;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select {
  font: inherit;
}

.dashboard {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(320px, 1fr) minmax(280px, 380px);
  grid-template-rows: auto minmax(190px, auto) minmax(280px, 1fr) auto;
  gap: 12px;
  padding: 14px;
}

.topbar,
.panel {
  background: #ffffff;
  border: 1px solid #d8dee8;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(24, 33, 47, 0.06);
}

.topbar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-size: 22px;
}

h2 {
  font-size: 15px;
  margin-bottom: 12px;
}

.panel {
  padding: 14px;
  min-width: 0;
}

.source-panel {
  grid-row: 2 / 4;
}

.summary-panel {
  grid-column: 2;
}

.findings-panel {
  grid-column: 2;
}

.evidence-panel {
  grid-column: 3;
  grid-row: 2 / 4;
}

.insights-panel {
  grid-column: 1 / 3;
}

.export-panel {
  grid-column: 3;
}

.status,
.message {
  color: #516070;
}

.upload-zone,
.sample-row {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}

select {
  min-height: 118px;
}

button {
  min-height: 36px;
  border: 1px solid #aab4c3;
  border-radius: 6px;
  background: #18212f;
  color: #ffffff;
  cursor: pointer;
}

button:disabled {
  background: #d8dee8;
  color: #6c7787;
  cursor: not-allowed;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.metrics div {
  border: 1px solid #e1e6ee;
  border-radius: 6px;
  padding: 10px;
}

.metrics span {
  display: block;
  font-size: 24px;
  font-weight: 700;
}

.metrics small {
  color: #516070;
}

.finding-list {
  display: grid;
  gap: 8px;
  max-height: 360px;
  overflow: auto;
}

.finding-item {
  border: 1px solid #e1e6ee;
  border-radius: 6px;
  background: #f9fbfd;
  padding: 10px;
  text-align: left;
  color: #18212f;
}

.evidence-detail,
#insights {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.export-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

@media (max-width: 820px) {
  .dashboard {
    grid-template-columns: 1fr;
    grid-template-rows: none;
  }

  .topbar,
  .source-panel,
  .summary-panel,
  .findings-panel,
  .evidence-panel,
  .insights-panel,
  .export-panel {
    grid-column: 1;
    grid-row: auto;
  }

  .topbar {
    align-items: flex-start;
    gap: 10px;
    flex-direction: column;
  }
}
```

- [ ] **Step 5: Create dashboard JavaScript**

Create `logcheck/web_static/app.js`:

```javascript
const state = {
  latestResult: null,
  selectedFinding: null
};

const statusEl = document.querySelector("#status");
const sampleSelect = document.querySelector("#sample-select");
const fileInput = document.querySelector("#file-input");
const analyzeButton = document.querySelector("#analyze-button");
const inputMessage = document.querySelector("#input-message");

async function loadSamples() {
  const response = await fetch("/api/samples");
  const payload = await response.json();
  sampleSelect.innerHTML = "";
  for (const sample of payload.samples) {
    const option = document.createElement("option");
    option.value = sample.id;
    option.textContent = sample.name;
    sampleSelect.append(option);
  }
}

function selectedSamples() {
  return Array.from(sampleSelect.selectedOptions).map((option) => option.value);
}

async function runAnalysis() {
  statusEl.textContent = "Analyzing";
  inputMessage.textContent = "";
  const body = new FormData();
  for (const file of fileInput.files) {
    body.append("files", file);
  }
  for (const sampleId of selectedSamples()) {
    body.append("sample_ids", sampleId);
  }

  const response = await fetch("/api/analyze", { method: "POST", body });
  const payload = await response.json();
  if (!response.ok) {
    statusEl.textContent = "Idle";
    inputMessage.textContent = payload.error || "Could not analyze local input.";
    return;
  }
  state.latestResult = payload;
  state.selectedFinding = payload.findings[0] || null;
  renderResult(payload);
  statusEl.textContent = "Analysis ready";
}

function renderResult(payload) {
  document.querySelector("#metric-events").textContent = payload.summary.total_events;
  document.querySelector("#metric-findings").textContent = payload.summary.total_findings;
  document.querySelector("#metric-risk").textContent = payload.insights?.risk_level || "-";

  const severityList = document.querySelector("#severity-list");
  severityList.innerHTML = "";
  for (const [severity, count] of Object.entries(payload.summary.findings_by_severity)) {
    severityList.innerHTML += `<dt>${severity}</dt><dd>${count}</dd>`;
  }

  renderFindings(payload.findings);
  renderEvidence(state.selectedFinding);
  renderInsights(payload.insights);

  for (const button of document.querySelectorAll("[data-export]")) {
    button.disabled = false;
  }
}

function renderFindings(findings) {
  const list = document.querySelector("#finding-list");
  list.innerHTML = "";
  if (findings.length === 0) {
    list.textContent = "No findings detected in the selected local logs.";
    return;
  }
  findings.forEach((finding, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "finding-item";
    button.textContent = `${finding.severity} - ${finding.rule_id} - ${finding.source_file || "unknown source"}`;
    button.addEventListener("click", () => {
      state.selectedFinding = finding;
      renderEvidence(finding);
    });
    if (index === 0) {
      state.selectedFinding = finding;
    }
    list.append(button);
  });
}

function renderEvidence(finding) {
  const detail = document.querySelector("#evidence-detail");
  if (!finding) {
    detail.textContent = "No finding selected.";
    return;
  }
  detail.textContent = [
    `${finding.rule_id} (${finding.severity})`,
    finding.explanation,
    `Source: ${finding.source_file || "unknown"}:${finding.line_number || "-"}`,
    `Actor: ${finding.actor || "-"}`,
    `Target: ${finding.target || "-"}`,
    `Address: ${finding.source_address || "-"}`,
    "Evidence:",
    ...(finding.evidence || []).map((line) => `- ${line}`)
  ].join("\n");
}

function renderInsights(insights) {
  const container = document.querySelector("#insights");
  if (!insights) {
    container.textContent = "Insights will appear after analysis.";
    return;
  }
  container.textContent = [
    insights.headline,
    `Evidence count: ${insights.evidence_count}`,
    `Entities: ${(insights.entity_profiles || []).length}`,
    `Suggestions: ${(insights.suggestions || []).length}`
  ].join("\n");
}

async function exportReport(format) {
  window.location.href = `/api/exports/${format}`;
}

analyzeButton.addEventListener("click", runAnalysis);
for (const button of document.querySelectorAll("[data-export]")) {
  button.addEventListener("click", () => exportReport(button.dataset.export));
}

loadSamples().catch(() => {
  inputMessage.textContent = "Sample logs could not be loaded.";
});
```

- [ ] **Step 6: Run dashboard tests and verify pass**

Run: `python -m pytest tests/test_webapp.py -q`

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add logcheck/web_static tests/test_webapp.py
git commit -m "feat: add local investigation dashboard"
```

## Task 4: Safety and Export Coverage

**Files:**
- Modify: `tests/test_webapp.py`
- Modify: `logcheck/webapp.py`

- [ ] **Step 1: Add export format and safety tests**

Append to `tests/test_webapp.py`:

```python
def test_export_csv_and_markdown_after_analysis(tmp_path):
    client = make_app(tmp_path)
    client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")

    csv_response = client.get("/api/exports/csv")
    markdown_response = client.get("/api/exports/markdown")

    assert csv_response.status_code == 200
    assert csv_response.mimetype == "text/csv"
    assert b"rule_id,severity" in csv_response.data
    assert markdown_response.status_code == 200
    assert markdown_response.mimetype == "text/markdown"
    assert b"Log Intrusion Analysis Report" in markdown_response.data


def test_unknown_sample_id_is_ignored_but_valid_local_sample_runs(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={"sample_ids": ["missing.log", "auth.log"]},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.get_json()["summary"]["total_events"] == 1


def test_static_javascript_does_not_fetch_external_inputs(tmp_path):
    client = make_app(tmp_path)

    script = client.get("/app.js").get_data(as_text=True).lower()

    assert "http://" not in script
    assert "https://" not in script
```

- [ ] **Step 2: Run focused safety/export tests**

Run: `python -m pytest tests/test_webapp.py::test_export_csv_and_markdown_after_analysis tests/test_webapp.py::test_unknown_sample_id_is_ignored_but_valid_local_sample_runs tests/test_webapp.py::test_static_javascript_does_not_fetch_external_inputs -q`

Expected: PASS after Task 2 and Task 3 implementation.

- [ ] **Step 3: Run all web tests**

Run: `python -m pytest tests/test_web_serialization.py tests/test_webapp.py -q`

Expected: PASS.

- [ ] **Step 4: Commit Task 4**

Run:

```bash
git add logcheck/webapp.py tests/test_webapp.py
git commit -m "test: cover web safety and exports"
```

## Task 5: Desktop Direction Cleanup

**Files:**
- Modify: `pyproject.toml`
- Delete or keep deprecated: `logcheck/desktop.py`
- Delete or replace: `tests/test_desktop.py`

- [ ] **Step 1: Remove GUI package dependency and script entry point**

Ensure `pyproject.toml` no longer includes `PyQt6` or `logcheck-desktop`. The scripts section should be:

```toml
[project.scripts]
logcheck = "logcheck.cli:main"
logcheck-web = "logcheck.webapp:main"
```

- [ ] **Step 2: Remove desktop tests after web replacement coverage exists**

Remove `tests/test_desktop.py` once `tests/test_webapp.py` covers source intake, analysis result rendering, exports, and forbidden remote controls.

- [ ] **Step 3: Decide whether to delete or leave `logcheck/desktop.py` deprecated**

Preferred first implementation: delete `logcheck/desktop.py` after PyQt dependency and script entry point are removed. If deletion causes package or import failures, leave the file temporarily but remove all entry points and add no new desktop work.

- [ ] **Step 4: Run backend and web tests**

Run: `python -m pytest tests/test_analysis.py tests/test_cli.py tests/test_exporters.py tests/test_insights.py tests/test_models.py tests/test_parsers.py tests/test_rules.py tests/test_web_serialization.py tests/test_webapp.py -q`

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

Run:

```bash
git add pyproject.toml logcheck tests
git commit -m "chore: replace desktop frontend with web entry point"
```

## Task 6: Browser Verification and OpenSpec Task Closure

**Files:**
- Modify: `openspec/changes/rebuild-web-frontend/tasks.md`
- Create: `docs/web-frontend-verification.md`

- [ ] **Step 1: Start local web app**

Run: `python -m logcheck.webapp`

Expected: server starts on `http://127.0.0.1:8765`.

- [ ] **Step 2: Verify in browser**

Use the in-app browser or Playwright to open `http://127.0.0.1:8765`.

Verify:
- Dashboard is nonblank.
- Source intake, Analysis summary, Finding queue, Evidence detail, Investigation insights, and Exports are visible.
- Layout does not overlap at desktop width.
- Layout stacks cleanly at mobile-width viewport.
- No forbidden remote controls are visible.

- [ ] **Step 3: Record verification notes**

Create `docs/web-frontend-verification.md`:

```markdown
# Web Frontend Verification

Change: rebuild-web-frontend

## Manual Browser Checks

- Desktop viewport: Dashboard rendered without overlap.
- Mobile-width viewport: Dashboard stacked without overlap.
- Local-only controls: No URL, domain, remote upload, network scan, blocking, exploitation, or external reporting controls were visible.
- Source intake: Uploaded local files and bundled sample logs were available.
- Analysis review: Summary, findings, evidence, insights, and exports were visible after analysis.

## Commands

- `python -m pytest tests/test_analysis.py tests/test_cli.py tests/test_exporters.py tests/test_insights.py tests/test_models.py tests/test_parsers.py tests/test_rules.py tests/test_web_serialization.py tests/test_webapp.py -q`
- `python -m logcheck.webapp`
```

- [ ] **Step 4: Check OpenSpec tasks**

Update `openspec/changes/rebuild-web-frontend/tasks.md` to mark all completed implementation tasks with `[x]`.

- [ ] **Step 5: Run final strict validation**

Run: `openspec validate rebuild-web-frontend --strict`

Expected: PASS.

- [ ] **Step 6: Commit Task 6**

Run:

```bash
git add docs/web-frontend-verification.md openspec/changes/rebuild-web-frontend/tasks.md
git commit -m "docs: record web frontend verification"
```

## Final Verification

Run:

```bash
python -m pytest tests/test_analysis.py tests/test_cli.py tests/test_exporters.py tests/test_insights.py tests/test_models.py tests/test_parsers.py tests/test_rules.py tests/test_web_serialization.py tests/test_webapp.py -q
openspec validate rebuild-web-frontend --strict
```

Expected:
- Pytest exits with all listed tests passing.
- OpenSpec reports `Change 'rebuild-web-frontend' is valid`.

## Spec Coverage Review

- Browser-based workspace: Task 3.
- Local uploaded files and sample logs: Task 2 and Task 4.
- Existing local analysis pipeline: Task 2.
- Findings, evidence, insights, and source context: Task 1 and Task 3.
- JSON/CSV/Markdown exports: Task 2 and Task 4.
- Local-only safety boundary: Task 3 and Task 4.
- Browser visual verification: Task 6.
- Course deliverable web evidence: Task 6.
