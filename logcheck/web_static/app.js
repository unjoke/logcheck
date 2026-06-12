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
const languageSelect = document.querySelector("#language-select");
const findingSearch = document.querySelector("#finding-search");
const severityFilter = document.querySelector("#severity-filter");
const ruleFilter = document.querySelector("#rule-filter");
const sourceFilter = document.querySelector("#source-filter");
const findingPagination = document.querySelector("#finding-pagination");
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
    runCharts: "Run analysis to populate local charts.",
  },
  zh: {
    languageLabel: "语言",
    findingQueue: "发现队列",
    timeDistribution: "时间分布",
    attackerIpStatistics: "攻击 IP 统计",
    keywordFilter: "关键词过滤",
    severityFilter: "严重级别",
    ruleFilter: "规则",
    sourceFilter: "源地址",
    previousPage: "上一页",
    nextPage: "下一页",
    allSeverities: "全部级别",
    allRules: "全部规则",
    allSources: "全部来源",
    evidenceOrderDistribution: "证据顺序分布",
    noFindingsQueue: "队列中没有发现。",
    noFilteredFindings: "没有符合当前过滤条件的发现。",
    runCharts: "运行分析后生成本地图表。",
  },
};

document.addEventListener("DOMContentLoaded", () => {
  languageSelect.value = state.language;
  applyTranslations();
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

function setLanguage(language) {
  state.language = TRANSLATIONS[language] ? language : "en";
  localStorage.setItem("logcheckLanguage", state.language);
  languageSelect.value = state.language;
  applyTranslations();
  buildFilterOptions(state.findings);
  renderFindings(state.findings);
}

function t(key) {
  return (TRANSLATIONS[state.language] && TRANSLATIONS[state.language][key]) || TRANSLATIONS.en[key] || key;
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
}

function renderResult(payload) {
  const summary = payload.summary || {};
  metrics.events.textContent = summary.total_events ?? 0;
  metrics.findings.textContent = summary.total_findings ?? state.findings.length;
  metrics.sources.textContent = Array.isArray(summary.analyzed_sources) ? summary.analyzed_sources.length : 0;
  metrics.high.textContent = countHighPriority(state.findings);
  state.findingPage = 1;
  buildFilterOptions(state.findings);
  renderFindings(state.findings);
  renderInsights(payload.insights || []);
  renderCharts(payload);
  if (!state.findings.length) {
    clearSelectedAlert("No findings were produced for the selected local material.");
  }
}

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
      renderSelectedAlert(finding, index);
    });
    findingList.append(button);
  });
  state.selectedFindingIndex = start;
  renderSelectedAlert(pageFindings[0], start);
  renderPagination(pageCount, filteredFindings.length);
}

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
