const state = {
  latestAnalysisId: "",
  findings: [],
};

const form = document.querySelector("#analysis-form");
const fileInput = document.querySelector("#log-files");
const sampleSelect = document.querySelector("#sample-select");
const runState = document.querySelector("#run-state");
const findingList = document.querySelector("#finding-list");
const queueCount = document.querySelector("#queue-count");
const evidenceDetail = document.querySelector("#evidence-detail");
const insightList = document.querySelector("#insight-list");
const exportButtons = Array.from(document.querySelectorAll(".export-button"));
const chartCount = document.querySelector("#chart-count");
const charts = {
  source: document.querySelector("#source-chart"),
  time: document.querySelector("#time-chart"),
  severity: document.querySelector("#severity-chart"),
};

const metrics = {
  events: document.querySelector("#metric-events"),
  findings: document.querySelector("#metric-findings"),
  sources: document.querySelector("#metric-sources"),
  high: document.querySelector("#metric-high"),
};

document.addEventListener("DOMContentLoaded", () => {
  loadSamples();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await runAnalysis();
});

exportButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (!state.latestAnalysisId) {
      return;
    }
    const format = button.dataset.format;
    const analysisId = encodeURIComponent(state.latestAnalysisId);
    window.location.assign(`/api/exports/${format}?analysis_id=${analysisId}`);
  });
});

async function loadSamples() {
  try {
    const response = await fetch("/api/samples");
    if (!response.ok) {
      throw new Error("Could not load samples.");
    }
    const payload = await response.json();
    renderSamples(payload.samples || []);
  } catch (error) {
    sampleSelect.innerHTML = "";
    sampleSelect.append(new Option("Samples not ready", ""));
    setRunState(error.message || "Samples not ready");
  }
}

function renderSamples(samples) {
  sampleSelect.innerHTML = "";
  if (!samples.length) {
    sampleSelect.append(new Option("No samples found", ""));
    return;
  }
  for (const sample of samples) {
    sampleSelect.append(new Option(sample.name, sample.id));
  }
}

async function runAnalysis() {
  const body = new FormData();
  for (const file of fileInput.files) {
    body.append("files", file);
  }
  for (const option of Array.from(sampleSelect.selectedOptions)) {
    if (option.value) {
      body.append("sample_ids", option.value);
    }
  }

  setRunState("Running");
  toggleExports(false);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Analysis failed.");
    }
    state.latestAnalysisId = payload.analysis_id || "";
    state.findings = payload.findings || [];
    renderResult(payload);
    toggleExports(Boolean(state.latestAnalysisId));
    setRunState("Complete");
  } catch (error) {
    state.latestAnalysisId = "";
    state.findings = [];
    renderError(error.message || "Analysis failed.");
    setRunState("Needs input");
  }
}

function renderResult(payload) {
  const summary = payload.summary || {};
  metrics.events.textContent = summary.total_events ?? 0;
  metrics.findings.textContent = summary.total_findings ?? state.findings.length;
  metrics.sources.textContent = Array.isArray(summary.analyzed_sources) ? summary.analyzed_sources.length : 0;
  metrics.high.textContent = countHighPriority(state.findings);
  renderFindings(state.findings);
  renderInsights(payload.insights || []);
  renderCharts(payload);
  if (state.findings.length) {
    renderSelectedAlert(state.findings[0], 0);
  } else {
    clearSelectedAlert("No findings were produced for the selected local material.");
  }
}

function renderFindings(findings) {
  queueCount.textContent = `${findings.length} ${findings.length === 1 ? "item" : "items"}`;
  findingList.innerHTML = "";
  if (!findings.length) {
    findingList.innerHTML = '<p class="empty-state">No findings in the queue.</p>';
    return;
  }
  findings.forEach((finding, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `finding-card${index === 0 ? " active" : ""}`;
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
      renderSelectedAlert(finding, index);
    });
    findingList.append(button);
  });
}

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

function sourceContextRows(finding) {
  const fields = [
    ["Line", finding.line_number],
    ["Actor", finding.actor],
    ["Target", finding.target],
    ["Source address", finding.source_address],
    ["Matched keyword", finding.matched_keyword],
  ];
  return fields
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
}

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

function renderInsights(insights) {
  insightList.innerHTML = "";
  const items = normalizeInsights(insights);
  if (!items.length) {
    insightList.innerHTML = '<li class="empty-state">No insights were produced.</li>';
    return;
  }
  for (const insight of items) {
    const item = document.createElement("li");
    item.textContent = insight;
    insightList.append(item);
  }
}

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
  for (const suggestion of insights.suggestions || []) {
    items.push(`${suggestion.title}: ${suggestion.detail}`);
  }
  for (const item of insights.timeline || []) {
    const context = [item.severity, item.rule_id, item.entity, item.source].filter(Boolean).join(" | ");
    items.push(context ? `${item.label || item.timestamp}: ${context}` : item.label || item.timestamp);
  }
  return items.filter(Boolean);
}

function renderError(message) {
  metrics.events.textContent = "0";
  metrics.findings.textContent = "0";
  metrics.sources.textContent = "0";
  metrics.high.textContent = "0";
  queueCount.textContent = "0 items";
  findingList.innerHTML = `<p class="empty-state">${escapeHtml(message)}</p>`;
  clearSelectedAlert("Select local material and run analysis.");
  insightList.innerHTML = '<li class="empty-state">Insights appear after analysis.</li>';
  resetCharts();
  toggleExports(false);
}

function toggleExports(enabled) {
  exportButtons.forEach((button) => {
    button.disabled = !enabled;
  });
}

function setRunState(message) {
  runState.textContent = message;
}

function countHighPriority(findings) {
  return findings.filter((finding) => {
    const severity = String(finding.severity || "").toLowerCase();
    return severity === "high" || severity === "critical";
  }).length;
}

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
    const label = finding.source_address || finding.actor || finding.source_file || "unknown";
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

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character];
  });
}
