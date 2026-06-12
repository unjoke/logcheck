---
change: enhance-finding-workbench-analytics
design-doc: docs/superpowers/specs/2026-06-11-enhance-finding-workbench-analytics-design.md
base-ref: 970a70a1c15f9a43c8e8f53bcdf2a659e7535178
---

# Enhance Finding Workbench Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct the Logcheck web workbench around adjacent finding/evidence review, then add paginated finding review, Chinese/English UI switching, explicit time distribution, detailed attacker IP statistics, and local keyword/facet filtering.

**Architecture:** Rebuild the static layout so `Finding queue` and selected `Log detail` form the primary investigation lane. Keep analytics derivation in `logcheck/web_static/app.js` unless existing serialized analysis data is insufficient. Add small local helpers for translation, filtering, pagination, time buckets, and source-address aggregation, then wire them into render functions. Keep backend behavior unchanged unless tests prove serialization needs a narrow extension.

**Tech Stack:** Python 3.11, Flask, pytest, static HTML/CSS/JavaScript, local browser verification.

---

## File Structure

- Modify `tests/test_webapp.py`: add static and API-facing checks for new frontend behavior, safety boundaries, labels, and helper names.
- Modify `logcheck/web_static/index.html`: rebuild the workbench regions so queue and detail are adjacent; add language control, filter controls, pagination container, and attacker IP statistics region.
- Modify `logcheck/web_static/app.js`: add state, translation dictionary, filtering, pagination, source-address aggregation, time chart fallback labeling, and localized rendering.
- Modify `logcheck/web_static/styles.css`: style the evidence-first layout, language control, filters, pagination, and attacker IP table without nested cards or horizontal overflow.
- Modify `openspec/changes/enhance-finding-workbench-analytics/tasks.md`: mark implementation tasks complete as they are finished.
- No planned backend changes. Revisit `logcheck/web_serialization.py` and `logcheck/insights.py` only if frontend derivation cannot satisfy source-address or time-distribution requirements.

## Task 1: Add Regression Tests For Evidence-First Static UI Contract

**Files:**
- Modify: `tests/test_webapp.py`
- Read: `logcheck/web_static/index.html`
- Read: `logcheck/web_static/app.js`
- Read: `logcheck/web_static/styles.css`

- [ ] **Step 1: Add failing dashboard layout and markup tests**

Add these tests after `test_dashboard_renders_visual_report_region` in `tests/test_webapp.py`:

```python
def test_dashboard_renders_language_filter_pagination_and_attacker_ip_regions(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for expected in [
        'id="language-select"',
        'id="finding-search"',
        'id="severity-filter"',
        'id="rule-filter"',
        'id="source-filter"',
        'id="finding-pagination"',
        "Attacker IP statistics",
        'id="attacker-ip-stats"',
    ]:
        assert expected in html


def test_dashboard_time_chart_title_is_explicit(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Time distribution" in html
    assert "Time/evidence order" not in html
```

Add this adjacency test beside the markup tests:

```python
def test_dashboard_places_queue_and_detail_in_primary_investigation_lane(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="investigation-lane"' in html
    assert html.index('id="finding-queue-title"') < html.index('id="evidence-detail-title"')
    assert html.index('id="evidence-detail-title"') < html.index('id="visual-report-title"')
```

- [ ] **Step 2: Add failing app.js helper tests**

Add these tests near `test_dashboard_script_includes_local_chart_helpers`:

```python
def test_dashboard_script_includes_pagination_filter_i18n_and_ip_helpers():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    for expected in [
        "TRANSLATIONS",
        "setLanguage",
        "applyFindingFilters",
        "normalizeFilterText",
        "paginateFindings",
        "renderPagination",
        "aggregateAttackerIps",
        "renderAttackerIpStats",
        "buildFilterOptions",
    ]:
        assert expected in script


def test_dashboard_script_filters_before_paginating():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")
    body = script_function_body(script, "renderFindings")

    assert "applyFindingFilters" in body
    assert "paginateFindings" in body
    assert body.index("applyFindingFilters") < body.index("paginateFindings")
```

- [ ] **Step 3: Add failing translation and safety tests**

Add these tests near the existing safety tests:

```python
def test_dashboard_script_translation_keys_cover_english_and_chinese():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "const TRANSLATIONS" in script
    for key in [
        "languageLabel",
        "findingQueue",
        "timeDistribution",
        "attackerIpStatistics",
        "keywordFilter",
        "severityFilter",
        "ruleFilter",
        "sourceFilter",
        "nextPage",
        "previousPage",
        "evidenceOrderDistribution",
    ]:
        assert key in script
    assert "\\u65f6\\u95f4\\u5206\\u5e03" in script


def test_dashboard_script_avoids_external_research_runtime_dependencies():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8").lower()

    for forbidden in [
        "logai",
        "logbert",
        "logpai",
        "fastwlat",
        "maaloganalyzer",
        "cdn.",
        "http://",
        "https://",
        "geoip",
        "mapbox",
        "geolocation",
        "dns",
        "threat-intelligence",
        "threat intelligence",
    ]:
        assert forbidden not in script
```

- [ ] **Step 4: Add failing CSS tests**

Add this test after `test_dashboard_styles_prevent_chart_label_overlap`:

```python
def test_dashboard_styles_include_filters_pagination_and_attacker_ip_rules():
    styles = (PROJECT_ROOT / "logcheck" / "web_static" / "styles.css").read_text(encoding="utf-8")

    for selector in [
        ".investigation-lane",
        ".supporting-report",
        ".language-control",
        ".filter-grid",
        ".queue-toolbar",
        ".pagination-controls",
        ".attacker-ip-table",
        ".attacker-ip-row",
    ]:
        assert selector in styles
    assert "overflow-wrap: anywhere" in styles
```

- [ ] **Step 5: Run tests and verify failure**

Run:

```bash
pytest tests/test_webapp.py -q
```

Expected: the new tests fail because markup, helpers, translation keys, and styles do not exist yet. Existing tests should still pass.

- [ ] **Step 6: Commit tests**

```bash
git add tests/test_webapp.py
git commit -m "test: cover workbench analytics enhancements"
```

## Task 2: Rebuild The Evidence-First Layout And Add Controls

**Files:**
- Modify: `logcheck/web_static/index.html`
- Modify: `logcheck/web_static/styles.css`
- Test: `tests/test_webapp.py`

- [ ] **Step 1: Rebuild the workspace into supporting source rail, investigation lane, and supporting report**

In `logcheck/web_static/index.html`, replace the current `workspace` contents with this structure, preserving the existing form, metric ids, chart ids, queue ids, detail ids, insight ids, and export ids so existing JavaScript can be adapted without changing the API:

```html
<section class="workspace" aria-label="Dashboard workspace">
  <aside class="panel intake-panel source-rail" aria-labelledby="source-intake-title">
    <div class="panel-heading">
      <h2 id="source-intake-title">Source intake</h2>
    </div>
    <form id="analysis-form" class="intake-form">
      <label class="field">
        <span>Local log files</span>
        <input id="log-files" name="files" type="file" multiple>
      </label>
      <label class="field">
        <span>Sample set</span>
        <select id="sample-select" name="sample_ids" multiple size="7">
          <option value="">Loading samples</option>
        </select>
      </label>
      <button id="run-analysis" class="primary-action" type="submit">Run analysis</button>
    </form>

    <section class="summary-panel" aria-labelledby="analysis-summary-title">
      <div class="panel-heading compact">
        <h2 id="analysis-summary-title">Analysis summary</h2>
      </div>
      <dl class="metrics" id="summary-metrics">
        <div>
          <dt>Events</dt>
          <dd id="metric-events">0</dd>
        </div>
        <div>
          <dt>Findings</dt>
          <dd id="metric-findings">0</dd>
        </div>
        <div>
          <dt>Sources</dt>
          <dd id="metric-sources">0</dd>
        </div>
        <div>
          <dt>High priority</dt>
          <dd id="metric-high">0</dd>
        </div>
      </dl>
    </section>

    <section class="panel-section" aria-labelledby="exports-title">
      <div class="panel-heading compact">
        <h2 id="exports-title">Exports</h2>
      </div>
      <div class="export-actions">
        <button type="button" class="export-button" data-format="json" disabled>JSON</button>
        <button type="button" class="export-button" data-format="csv" disabled>CSV</button>
        <button type="button" class="export-button" data-format="markdown" disabled>Markdown</button>
      </div>
    </section>
  </aside>

  <section class="investigation-lane" aria-label="Finding and evidence review">
    <section class="panel queue-panel" aria-labelledby="finding-queue-title">
      <div class="panel-heading">
        <h2 id="finding-queue-title" data-i18n="findingQueue">Finding queue</h2>
        <span id="queue-count">0 items</span>
      </div>
      <div class="queue-toolbar">
        <label class="field compact-field">
          <span data-i18n="keywordFilter">Keyword filter</span>
          <input id="finding-search" type="search" autocomplete="off">
        </label>
        <div class="filter-grid">
          <label class="field compact-field">
            <span data-i18n="severityFilter">Severity</span>
            <select id="severity-filter">
              <option value="">All severities</option>
            </select>
          </label>
          <label class="field compact-field">
            <span data-i18n="ruleFilter">Rule</span>
            <select id="rule-filter">
              <option value="">All rules</option>
            </select>
          </label>
          <label class="field compact-field">
            <span data-i18n="sourceFilter">Source address</span>
            <select id="source-filter">
              <option value="">All sources</option>
            </select>
          </label>
        </div>
      </div>
      <div id="finding-list" class="finding-list" role="list">
        <p class="empty-state">Run analysis to populate the queue.</p>
      </div>
      <div id="finding-pagination" class="pagination-controls" aria-label="Finding pagination"></div>
    </section>

    <aside class="panel detail-panel" aria-labelledby="evidence-detail-title">
      <div class="panel-heading">
        <h2 id="evidence-detail-title">Evidence detail</h2>
      </div>
      <article id="evidence-detail" class="evidence-detail">
        <p class="empty-state">Select a finding to inspect matched evidence.</p>
      </article>
      <div class="panel-section" aria-labelledby="investigation-insights-title">
        <div class="panel-heading compact">
          <h2 id="investigation-insights-title">Investigation insights</h2>
        </div>
        <ul id="insight-list" class="insight-list">
          <li class="empty-state">Insights appear after analysis.</li>
        </ul>
      </div>
    </aside>
  </section>

  <section class="panel visual-report-panel supporting-report" aria-labelledby="visual-report-title">
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
        <h3 id="time-chart-title" data-i18n="timeDistribution">Time distribution</h3>
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
      <article class="chart-card attacker-ip-card" aria-labelledby="attacker-ip-title">
        <h3 id="attacker-ip-title" data-i18n="attackerIpStatistics">Attacker IP statistics</h3>
        <div id="attacker-ip-stats" class="attacker-ip-table">
          <p class="empty-state">Run analysis to populate local charts.</p>
        </div>
      </article>
    </div>
  </section>
</section>
```

This makes the DOM order `Finding queue` -> `Evidence detail` -> `Visual report`, which is what the static adjacency test checks.

- [ ] **Step 2: Add language control in the topbar**

In `logcheck/web_static/index.html`, replace:

```html
<div class="run-state" id="run-state">Ready</div>
```

with:

```html
<div class="topbar-actions">
  <label class="language-control">
    <span data-i18n="languageLabel">Language</span>
    <select id="language-select" aria-label="Language">
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  </label>
  <div class="run-state" id="run-state">Ready</div>
</div>
```

- [ ] **Step 3: Replace the workspace CSS with an evidence-first grid and add new control styles**

In `logcheck/web_static/styles.css`, replace the current `.workspace` and `.main-grid` rules with:

```css
.workspace {
  display: grid;
  grid-template-columns: minmax(230px, 280px) minmax(0, 1fr);
  grid-template-areas:
    "source investigation"
    "report report";
  gap: 14px;
  max-width: 1480px;
  margin: 0 auto;
  align-items: start;
}

.source-rail {
  grid-area: source;
}

.investigation-lane {
  display: grid;
  grid-area: investigation;
  grid-template-columns: minmax(360px, 0.95fr) minmax(360px, 1.05fr);
  gap: 14px;
  min-width: 0;
  align-items: stretch;
}

.supporting-report {
  grid-area: report;
}

.main-grid {
  display: contents;
}
```

Append these rules before the media queries:

```css
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.language-control {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.language-control select {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  color: var(--ink);
  padding: 6px 8px;
}

.queue-toolbar {
  display: grid;
  gap: 10px;
  border-bottom: 1px solid var(--line);
  padding: 10px;
}

.compact-field {
  margin-bottom: 0;
}

.compact-field input,
.compact-field select {
  min-height: 36px;
}

.compact-field select {
  min-height: 36px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-top: 1px solid var(--line);
  padding: 10px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.pagination-controls button {
  min-height: 32px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fbfcfb;
  color: var(--ink);
  cursor: pointer;
  font-weight: 800;
}

.pagination-controls button:disabled {
  color: #9aa39c;
  cursor: not-allowed;
}

.attacker-ip-table {
  display: grid;
  gap: 8px;
  min-height: 112px;
}

.attacker-ip-row {
  display: grid;
  gap: 5px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fbfcfb;
  padding: 8px;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.attacker-ip-row strong,
.attacker-ip-row span {
  min-width: 0;
  overflow-wrap: anywhere;
}
```

Replace the current `@media (max-width: 1080px)` workspace override with:

```css
@media (max-width: 1080px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-areas:
      "source"
      "investigation"
      "report";
  }

  .investigation-lane {
    grid-template-columns: 1fr;
  }
}
```

Inside `@media (max-width: 760px)`, keep existing compact rules and add:

```css
.topbar-actions {
  align-items: stretch;
  flex-direction: column;
}

.filter-grid {
  grid-template-columns: 1fr;
}
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/test_webapp.py::test_dashboard_renders_language_filter_pagination_and_attacker_ip_regions tests/test_webapp.py::test_dashboard_places_queue_and_detail_in_primary_investigation_lane tests/test_webapp.py::test_dashboard_time_chart_title_is_explicit tests/test_webapp.py::test_dashboard_styles_include_filters_pagination_and_attacker_ip_rules -q
```

Expected: these tests pass. Helper tests can still fail until Task 3 and Task 4.

- [ ] **Step 5: Commit markup and styles**

```bash
git add logcheck/web_static/index.html logcheck/web_static/styles.css
git commit -m "feat: rebuild evidence-first workbench layout"
```

## Task 3: Add I18n, Filtering, And Pagination Helpers

**Files:**
- Modify: `logcheck/web_static/app.js`
- Test: `tests/test_webapp.py`

- [ ] **Step 1: Extend state and element references**

At the top of `logcheck/web_static/app.js`, replace:

```js
const state = {
  latestAnalysisId: "",
  findings: [],
};
```

with:

```js
const state = {
  latestAnalysisId: "",
  findings: [],
  selectedFindingIndex: null,
  language: localStorage.getItem("logcheckLanguage") || "en",
  filters: {
    keyword: "",
    severity: "",
    rule: "",
    source: "",
  },
  findingPage: 1,
  findingsPerPage: 10,
};
```

Add these element references after `const chartCount = ...`:

```js
const languageSelect = document.querySelector("#language-select");
const findingSearch = document.querySelector("#finding-search");
const severityFilter = document.querySelector("#severity-filter");
const ruleFilter = document.querySelector("#rule-filter");
const sourceFilter = document.querySelector("#source-filter");
const findingPagination = document.querySelector("#finding-pagination");
```

- [ ] **Step 2: Add translation dictionary and helper**

Add this after the `metrics` constant:

```js
const TRANSLATIONS = {
  en: {
    languageLabel: "Language",
    findingQueue: "Finding queue",
    timeDistribution: "Time distribution",
    attackerIpStatistics: "Attacker IP statistics",
    keywordFilter: "Keyword filter",
    severityFilter: "Severity",
    ruleFilter: "Rule",
    sourceFilter: "Source address",
    previousPage: "Previous",
    nextPage: "Next",
    allSeverities: "All severities",
    allRules: "All rules",
    allSources: "All sources",
    evidenceOrderDistribution: "Evidence order distribution",
    noFindingsQueue: "No findings in the queue.",
    noFilteredFindings: "No findings match the current filters.",
    noAttackerIps: "No source addresses were found in local findings.",
    runCharts: "Run analysis to populate local charts.",
    noTimeData: "No time or evidence-order data to chart.",
  },
  zh: {
    languageLabel: "\u8bed\u8a00",
    findingQueue: "\u53d1\u73b0\u961f\u5217",
    timeDistribution: "\u65f6\u95f4\u5206\u5e03",
    attackerIpStatistics: "\u653b\u51fb IP \u7edf\u8ba1",
    keywordFilter: "\u5173\u952e\u8bcd\u8fc7\u6ee4",
    severityFilter: "\u4e25\u91cd\u7ea7\u522b",
    ruleFilter: "\u89c4\u5219",
    sourceFilter: "\u6e90\u5730\u5740",
    previousPage: "\u4e0a\u4e00\u9875",
    nextPage: "\u4e0b\u4e00\u9875",
    allSeverities: "\u5168\u90e8\u7ea7\u522b",
    allRules: "\u5168\u90e8\u89c4\u5219",
    allSources: "\u5168\u90e8\u6765\u6e90",
    evidenceOrderDistribution: "\u8bc1\u636e\u987a\u5e8f\u5206\u5e03",
    noFindingsQueue: "\u961f\u5217\u4e2d\u6ca1\u6709\u53d1\u73b0",
    noFilteredFindings: "\u6ca1\u6709\u7b26\u5408\u5f53\u524d\u8fc7\u6ee4\u6761\u4ef6\u7684\u53d1\u73b0",
    noAttackerIps: "\u672c\u5730\u53d1\u73b0\u4e2d\u6ca1\u6709\u6e90\u5730\u5740",
    runCharts: "\u8fd0\u884c\u5206\u6790\u540e\u751f\u6210\u672c\u5730\u56fe\u8868",
    noTimeData: "\u6ca1\u6709\u53ef\u7528\u7684\u65f6\u95f4\u6216\u8bc1\u636e\u987a\u5e8f\u6570\u636e",
  },
};

function t(key) {
  return (TRANSLATIONS[state.language] && TRANSLATIONS[state.language][key]) || TRANSLATIONS.en[key] || key;
}
```

- [ ] **Step 3: Wire language and filter event handlers**

Inside `DOMContentLoaded`, replace:

```js
loadSamples();
```

with:

```js
languageSelect.value = state.language;
applyTranslations();
loadSamples();
```

After the export button handlers, add:

```js
languageSelect.addEventListener("change", () => {
  setLanguage(languageSelect.value);
});

findingSearch.addEventListener("input", () => {
  state.filters.keyword = findingSearch.value;
  state.findingPage = 1;
  renderFindings(state.findings);
});

for (const [element, key] of [
  [severityFilter, "severity"],
  [ruleFilter, "rule"],
  [sourceFilter, "source"],
]) {
  element.addEventListener("change", () => {
    state.filters[key] = element.value;
    state.findingPage = 1;
    renderFindings(state.findings);
  });
}

function setLanguage(language) {
  state.language = TRANSLATIONS[language] ? language : "en";
  localStorage.setItem("logcheckLanguage", state.language);
  languageSelect.value = state.language;
  applyTranslations();
  buildFilterOptions(state.findings);
  renderFindings(state.findings);
  renderCharts({ findings: state.findings, summary: {}, insights: {} });
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
}
```

- [ ] **Step 4: Add filtering and pagination helpers**

Add these helpers before `renderFindings`:

```js
function applyFindingFilters(findings) {
  const keyword = normalizeFilterText(state.filters.keyword);
  return findings.filter((finding) => {
    if (state.filters.severity && String(finding.severity || "").toLowerCase() !== state.filters.severity) {
      return false;
    }
    if (state.filters.rule && finding.rule_id !== state.filters.rule) {
      return false;
    }
    if (state.filters.source && finding.source_address !== state.filters.source) {
      return false;
    }
    if (!keyword) {
      return true;
    }
    return normalizeFilterText(findingSearchText(finding)).includes(keyword);
  });
}

function findingSearchText(finding) {
  return [
    finding.rule_id,
    finding.severity,
    finding.source_file,
    finding.source_address,
    finding.actor,
    finding.target,
    finding.matched_keyword,
    finding.explanation,
    ...(finding.evidence || []),
  ]
    .filter((value) => value !== null && value !== undefined)
    .join(" ");
}

function normalizeFilterText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\b\d{1,3}(?:\.\d{1,3}){3}\b/g, " ip ")
    .replace(/\b\d+\b/g, " number ")
    .replace(/\b[a-z]:\\[^\s]+/g, " path ")
    .replace(/\/[^\s]+/g, " path ")
    .replace(/\s+/g, " ")
    .trim();
}

function paginateFindings(findings) {
  const pageCount = Math.max(1, Math.ceil(findings.length / state.findingsPerPage));
  state.findingPage = Math.min(Math.max(state.findingPage, 1), pageCount);
  const start = (state.findingPage - 1) * state.findingsPerPage;
  return {
    pageCount,
    pageFindings: findings.slice(start, start + state.findingsPerPage),
    start,
  };
}
```

- [ ] **Step 5: Update renderFindings to filter first and paginate second**

Replace the existing `renderFindings` function with:

```js
function renderFindings(findings) {
  const filteredFindings = applyFindingFilters(findings);
  const { pageCount, pageFindings, start } = paginateFindings(filteredFindings);
  queueCount.textContent = `${filteredFindings.length} ${filteredFindings.length === 1 ? "item" : "items"}`;
  findingList.innerHTML = "";
  if (!findings.length) {
    findingList.innerHTML = `<p class="empty-state">${escapeHtml(t("noFindingsQueue"))}</p>`;
    renderPagination(pageCount, filteredFindings.length);
    return;
  }
  if (!filteredFindings.length) {
    findingList.innerHTML = `<p class="empty-state">${escapeHtml(t("noFilteredFindings"))}</p>`;
    clearSelectedAlert(t("noFilteredFindings"));
    renderPagination(pageCount, filteredFindings.length);
    return;
  }
  pageFindings.forEach((finding, pageIndex) => {
    const index = start + pageIndex;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `finding-card${pageIndex === 0 ? " active" : ""}`;
    button.setAttribute("role", "listitem");
    button.innerHTML = `
      <div class="finding-title">
        <span>${escapeHtml(finding.rule_id || "Finding")}</span>
        <span class="severity ${escapeHtml(String(finding.severity || "").toLowerCase())}">
          ${escapeHtml(finding.severity || "info")}
        </span>
      </div>
      <div class="finding-meta">${escapeHtml(finding.explanation || "Review evidence")} | ${escapeHtml(finding.source_file || "Local source")} | ${escapeHtml(String(finding.line_number || "line n/a"))}</div>
    `;
    button.addEventListener("click", () => {
      document.querySelectorAll(".finding-card").forEach((card) => card.classList.remove("active"));
      button.classList.add("active");
      state.selectedFindingIndex = index;
      renderSelectedAlert(finding, index);
    });
    findingList.append(button);
  });
  renderSelectedAlert(pageFindings[0], start);
  renderPagination(pageCount, filteredFindings.length);
}
```

- [ ] **Step 6: Add pagination rendering**

Add this helper after `renderFindings`:

```js
function renderPagination(pageCount, total) {
  findingPagination.innerHTML = "";
  const previous = document.createElement("button");
  previous.type = "button";
  previous.textContent = t("previousPage");
  previous.disabled = state.findingPage <= 1;
  previous.addEventListener("click", () => {
    state.findingPage -= 1;
    renderFindings(state.findings);
  });

  const next = document.createElement("button");
  next.type = "button";
  next.textContent = t("nextPage");
  next.disabled = state.findingPage >= pageCount || total === 0;
  next.addEventListener("click", () => {
    state.findingPage += 1;
    renderFindings(state.findings);
  });

  const status = document.createElement("span");
  status.textContent = `${state.findingPage} / ${pageCount}`;

  findingPagination.append(previous, status, next);
}
```

- [ ] **Step 7: Add filter option builder and call it after analysis**

Add this helper before `renderResult`:

```js
function buildFilterOptions(findings) {
  fillFilter(severityFilter, t("allSeverities"), uniqueValues(findings, (finding) => String(finding.severity || "").toLowerCase()));
  fillFilter(ruleFilter, t("allRules"), uniqueValues(findings, (finding) => finding.rule_id));
  fillFilter(sourceFilter, t("allSources"), uniqueValues(findings, (finding) => finding.source_address));
}

function uniqueValues(findings, getter) {
  return Array.from(new Set(findings.map(getter).filter(Boolean))).sort();
}

function fillFilter(element, emptyLabel, values) {
  const current = element.value;
  element.innerHTML = "";
  element.append(new Option(emptyLabel, ""));
  for (const value of values) {
    element.append(new Option(value, value));
  }
  element.value = values.includes(current) ? current : "";
}
```

Inside `renderResult`, before `renderFindings(state.findings);`, add:

```js
state.findingPage = 1;
buildFilterOptions(state.findings);
```

- [ ] **Step 8: Run focused tests**

Run:

```bash
pytest tests/test_webapp.py::test_dashboard_script_includes_pagination_filter_i18n_and_ip_helpers tests/test_webapp.py::test_dashboard_script_filters_before_paginating tests/test_webapp.py::test_dashboard_script_translation_keys_cover_english_and_chinese -q
```

Expected: i18n/filter/pagination helper tests pass. Attacker IP helper test may still fail until Task 4 if `aggregateAttackerIps` is not present yet.

- [ ] **Step 9: Commit i18n/filter/pagination helpers**

```bash
git add logcheck/web_static/app.js
git commit -m "feat: add local finding filters and pagination"
```

## Task 4: Add Time Fallback Labeling And Attacker IP Statistics

**Files:**
- Modify: `logcheck/web_static/app.js`
- Test: `tests/test_webapp.py`

- [ ] **Step 1: Add attacker IP chart element reference**

In the `charts` object, add:

```js
attackerIps: document.querySelector("#attacker-ip-stats"),
```

- [ ] **Step 2: Update renderCharts**

Replace `renderCharts` with:

```js
function renderCharts(payload) {
  const findings = payload.findings || [];
  const summary = payload.summary || {};
  const insights = payload.insights || {};
  const sourceRows = chartSourceDistribution(findings);
  const timeRows = chartTimeDistribution(findings, insights);
  const severityRows = chartSeverityDistribution(summary, findings);
  const attackerRows = aggregateAttackerIps(findings);

  chartCount.textContent = findings.length ? "4 charts" : "0 charts";
  renderBarChart(charts.source, sourceRows, { empty: "No source/entity findings to chart." });
  renderBarChart(charts.time, timeRows, { empty: t("noTimeData") });
  renderBarChart(charts.severity, severityRows, { empty: "No severity findings to chart." });
  renderAttackerIpStats(charts.attackerIps, attackerRows);
}
```

- [ ] **Step 3: Update resetCharts**

Replace the reset loop body with:

```js
container.innerHTML = `<p class="empty-state">${escapeHtml(t("runCharts"))}</p>`;
```

- [ ] **Step 4: Make time distribution fallback explicit**

Replace `chartTimeDistribution` with:

```js
function chartTimeDistribution(findings, insights) {
  const counts = new Map();
  const timeline = Array.isArray(insights.timeline) ? insights.timeline : [];
  findings.forEach((finding, index) => {
    const label =
      finding.timestamp ||
      (timeline[index] && timeline[index].label) ||
      `${t("evidenceOrderDistribution")} ${Math.floor(index / 5) + 1}`;
    counts.set(label, (counts.get(label) || 0) + 1);
  });
  return sortedChartRows(counts, false).slice(0, 6);
}
```

- [ ] **Step 5: Add attacker IP aggregation helper**

Add this before `chartSeverityDistribution`:

```js
function aggregateAttackerIps(findings) {
  const rows = new Map();
  findings.forEach((finding, index) => {
    if (!finding.source_address) {
      return;
    }
    const key = finding.source_address;
    if (!rows.has(key)) {
      rows.set(key, {
        source: key,
        count: 0,
        severities: new Map(),
        rules: new Set(),
        actors: new Map(),
        targets: new Map(),
        first: finding.timestamp || sourceReference(finding),
        last: finding.timestamp || sourceReference(finding),
        representativeIndex: index,
      });
    }
    const row = rows.get(key);
    row.count += 1;
    row.severities.set(finding.severity || "unknown", (row.severities.get(finding.severity || "unknown") || 0) + 1);
    if (finding.rule_id) {
      row.rules.add(finding.rule_id);
    }
    if (finding.actor) {
      row.actors.set(finding.actor, (row.actors.get(finding.actor) || 0) + 1);
    }
    if (finding.target) {
      row.targets.set(finding.target, (row.targets.get(finding.target) || 0) + 1);
    }
    row.last = finding.timestamp || sourceReference(finding);
  });
  return Array.from(rows.values()).sort((left, right) => right.count - left.count || left.source.localeCompare(right.source));
}

function sourceReference(finding) {
  if (finding.source_file && finding.line_number) {
    return `${finding.source_file}:${finding.line_number}`;
  }
  return finding.source_file || "local evidence";
}

function topMapValue(values) {
  const rows = Array.from(values, ([label, count]) => ({ label, count }));
  rows.sort((left, right) => right.count - left.count || left.label.localeCompare(right.label));
  return rows.length ? rows[0].label : "n/a";
}
```

- [ ] **Step 6: Add attacker IP renderer**

Add this helper after `renderBarChart`:

```js
function renderAttackerIpStats(container, rows) {
  container.innerHTML = "";
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">${escapeHtml(t("noAttackerIps"))}</p>`;
    return;
  }
  for (const row of rows.slice(0, 5)) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "attacker-ip-row";
    const severityMix = Array.from(row.severities, ([severity, count]) => `${severity}:${count}`).join(", ");
    item.innerHTML = `
      <strong>${escapeHtml(row.source)} (${escapeHtml(String(row.count))})</strong>
      <span>${escapeHtml(severityMix || "unknown")}</span>
      <span>${escapeHtml(Array.from(row.rules).slice(0, 3).join(", ") || "no rules")}</span>
      <span>${escapeHtml(topMapValue(row.targets))} | ${escapeHtml(topMapValue(row.actors))}</span>
      <span>${escapeHtml(row.first)} -> ${escapeHtml(row.last)}</span>
    `;
    item.addEventListener("click", () => {
      state.filters.source = row.source;
      sourceFilter.value = row.source;
      state.findingPage = 1;
      renderFindings(state.findings);
    });
    container.append(item);
  }
}
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
pytest tests/test_webapp.py::test_dashboard_script_includes_local_chart_helpers tests/test_webapp.py::test_dashboard_script_includes_pagination_filter_i18n_and_ip_helpers tests/test_webapp.py::test_dashboard_script_avoids_external_research_runtime_dependencies -q
```

Expected: all focused helper and safety tests pass.

- [ ] **Step 8: Commit chart and attacker IP changes**

```bash
git add logcheck/web_static/app.js
git commit -m "feat: add attacker ip stats and time distribution fallback"
```

## Task 5: Final Integration, Safety Checks, And Comet Task Updates

**Files:**
- Modify: `openspec/changes/enhance-finding-workbench-analytics/tasks.md`
- Optional Modify: `logcheck/web_static/app.js` if tests reveal integration defects.
- Optional Modify: `logcheck/web_static/styles.css` if browser layout reveals overlap.

- [ ] **Step 1: Run the web test suite**

Run:

```bash
pytest tests/test_webapp.py tests/test_web_serialization.py tests/test_insights.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run the broader Python suite**

Run:

```bash
pytest -q
```

Expected: all tests pass. If unrelated dirty-worktree changes cause failures, record the failing test names and inspect before changing unrelated files.

- [ ] **Step 3: Run JavaScript syntax check**

Run:

```bash
node --check logcheck/web_static/app.js
```

Expected: `node --check` exits with status 0 and prints no syntax errors.

- [ ] **Step 4: Start the local web dashboard for browser verification**

Run:

```bash
python -m logcheck.webapp
```

Expected: Flask serves `http://127.0.0.1:8765`.

- [ ] **Step 5: Verify in browser**

Open `http://127.0.0.1:8765` and verify:

- Language control switches labels between English and Chinese.
- Finding filters appear above the queue.
- Pagination controls appear below the queue.
- Visual report includes Source/entity frequency, Time distribution, Severity distribution, and Attacker IP statistics.
- No URL/domain input, remote fetch, scan, block, exploit, or external reporting controls are visible.
- At mobile width, filter controls, charts, attacker IP rows, and queue text do not overlap.

- [ ] **Step 6: Mark OpenSpec tasks complete**

In `openspec/changes/enhance-finding-workbench-analytics/tasks.md`, change each completed checkbox from `- [ ]` to `- [x]` only after the corresponding implementation and verification are complete.

- [ ] **Step 7: Commit verification and task updates**

```bash
git add openspec/changes/enhance-finding-workbench-analytics/tasks.md
git commit -m "chore: complete workbench analytics tasks"
```

## Self-Review

- Spec coverage: pagination is covered by Tasks 1 and 3; language switching by Tasks 1-3; time distribution by Tasks 1, 2, and 4; attacker IP statistics by Tasks 1, 2, and 4; keyword/facet filtering by Tasks 1 and 3; safety by Tasks 1 and 5.
- Placeholder scan: no task uses placeholder markers or unspecified implementation steps.
- Type consistency: helper names in tests match helper names in implementation snippets.
- Runtime dependency check: plan intentionally avoids LogAI, LogPAI, LogBERT, CDN, external URLs, and model dependencies.
