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
    setRunState(error.message || "Samples not ready", "error");
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

  setRunState("Running", "busy");
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
    setRunState("Complete", "ready");
  } catch (error) {
    state.latestAnalysisId = "";
    state.findings = [];
    renderError(error.message || "Analysis failed.");
    setRunState("Needs input", "error");
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
  if (state.findings.length) {
    renderEvidence(state.findings[0], 0);
  } else {
    evidenceDetail.innerHTML = '<p class="empty-state">No findings were produced for the selected local material.</p>';
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
      <div class="finding-meta">${escapeHtml(finding.explanation || "Review evidence")} · ${escapeHtml(finding.source_file || "Local source")} · ${escapeHtml(String(finding.line_number || "line n/a"))}</div>
    `;
    button.addEventListener("click", () => {
      document.querySelectorAll(".finding-card").forEach((card) => card.classList.remove("active"));
      button.classList.add("active");
      renderEvidence(finding, index);
    });
    findingList.append(button);
  });
}

function renderEvidence(finding, index) {
  const lines = finding.evidence || finding.matched_lines || [];
  const lineMarkup = lines.length
    ? lines.map((line) => `<div class="evidence-line">${escapeHtml(String(line))}</div>`).join("")
    : '<p class="empty-state">No evidence lines were attached to this finding.</p>';
  evidenceDetail.innerHTML = `
    <h3>${escapeHtml(finding.rule_id || `Finding ${index + 1}`)}</h3>
    <div class="detail-meta">
      ${escapeHtml(finding.explanation || "Review evidence")} · ${escapeHtml(finding.source_file || "Local source")} · ${escapeHtml(finding.severity || "info")}
    </div>
    <div class="evidence-lines">${lineMarkup}</div>
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
    items.push(`${item.label || item.timestamp}: ${item.detail || item.summary}`);
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
  evidenceDetail.innerHTML = '<p class="empty-state">Select local material and run analysis.</p>';
  insightList.innerHTML = '<li class="empty-state">Insights appear after analysis.</li>';
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
