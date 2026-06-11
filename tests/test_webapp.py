from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from logcheck.webapp import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def script_function_body(script: str, function_name: str) -> str:
    match = re.search(rf"function {function_name}\([^)]*\) \{{", script)
    assert match is not None
    start = match.end()
    depth = 1
    for index in range(start, len(script)):
        if script[index] == "{":
            depth += 1
        elif script[index] == "}":
            depth -= 1
            if depth == 0:
                return script[start:index]
    raise AssertionError(f"{function_name} function body was not closed")


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


def test_dashboard_renders_local_investigation_regions(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for region in [
        "Logcheck",
        "Source intake",
        "Analysis summary",
        "Finding queue",
        "Evidence detail",
        "Investigation insights",
        "Exports",
    ]:
        assert region in html


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


def test_dashboard_excludes_forbidden_remote_control_terms(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True).lower()
    for forbidden in [
        "url",
        "domain",
        "remote upload",
        "network scan",
        "scan target",
        "exploit",
        "block ip",
        "external report",
    ]:
        assert forbidden not in html


def test_dashboard_script_includes_evidence_detail_fields():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    for field in [
        "line_number",
        "actor",
        "target",
        "source_address",
        "matched_keyword",
        "confidence_reason",
    ]:
        assert field in script


def test_dashboard_script_keeps_insights_separate_from_alert_evidence():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "entity_profiles" in script
    assert "timeline" not in script_function_body(script, "normalizeInsights")


def test_dashboard_script_omits_empty_optional_detail_fields():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert 'value !== null && value !== undefined && value !== ""' in script
    assert "Severity reason" in script
    assert "Confidence reason" in script


def test_dashboard_script_uses_ascii_separators():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert "\u00b7" not in script
    assert "\u8def" not in script


def test_dashboard_script_renders_structured_selected_alert_detail():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert re.search(
        r"if \(state\.findings\.length\) {\s*renderSelectedAlert\(state\.findings\[0\], 0\);",
        script,
    )
    assert re.search(
        r'button\.addEventListener\("click", \(\) => {\s*'
        r'document\.querySelectorAll\("\.finding-card"\).*?'
        r"button\.classList\.add\(\"active\"\);\s*"
        r"renderSelectedAlert\(finding, index\);",
        script,
        re.DOTALL,
    )

    for expected in [
        "alert-detail-section",
        "alert-log-detail",
        "Severity reason",
        "Confidence reason",
        "Selected alert",
    ]:
        assert expected in script

    source_context_rows = re.search(r"function sourceContextRows\(finding\) {(?P<body>.*?)^}", script, re.DOTALL | re.MULTILINE)
    assert source_context_rows is not None
    assert '["Confidence", finding.confidence_reason]' not in source_context_rows.group("body")
    assert "No evidence lines were attached to this finding." not in script


def test_dashboard_script_clears_stale_selected_alert_when_no_findings():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    assert re.search(
        r"else {\s*"
        r'clearSelectedAlert\("No findings were produced for the selected local material\."\);\s*'
        r"}",
        script,
    )
    assert re.search(
        r"function renderError\(message\) {.*?"
        r'clearSelectedAlert\("Select local material and run analysis\."\);',
        script,
        re.DOTALL,
    )


def test_dashboard_script_keeps_timeline_fields_out_of_concise_insights():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    normalize_insights = script_function_body(script, "normalizeInsights")
    assert "item.detail" not in normalize_insights
    assert "item.summary" not in normalize_insights
    for field in ["item.severity", "item.rule_id", "item.entity", "item.source"]:
        assert field not in normalize_insights
    assert "timeline[index] && timeline[index].label" in script


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


def test_dashboard_script_fetches_only_local_api_inputs():
    script = (PROJECT_ROOT / "logcheck" / "web_static" / "app.js").read_text(encoding="utf-8")

    fetch_targets = re.findall(r"fetch\(\s*([\"'`])([^\"'`]+)\1", script)
    assert {target for _, target in fetch_targets} == {"/api/samples", "/api/analyze"}

    export_target = re.search(r"window\.location\.assign\(\s*`([^`]+)`\s*\)", script)
    assert export_target is not None
    assert export_target.group(1).startswith("/api/exports/")
    assert "analysis_id=${analysisId}" in export_target.group(1)


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
        "cdn.",
        "http://",
        "https://",
        "geolocation",
        "dns",
        "threat-intelligence",
        "threat intelligence",
    ]:
        assert forbidden not in script


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


def test_analyze_uploaded_file(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={
            "files": (
                BytesIO(
                    b"Jun  1 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.11 port 22 ssh2\n"
                ),
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


def test_analyze_ignores_unknown_sample_id_while_valid_sample_runs(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={"sample_ids": ["missing.log", "auth.log"]},
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["summary"]["total_events"] == 1
    assert payload["events"][0]["source_file"].endswith("auth.log")


def test_analyze_requires_local_input(tmp_path):
    client = make_app(tmp_path)

    response = client.post("/api/analyze", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert "local log" in response.get_json()["error"].lower()


def test_analyze_rejects_url_and_domain_fields_without_local_input(tmp_path):
    client = make_app(tmp_path)

    response = client.post(
        "/api/analyze",
        data={"url": "http://example.invalid/log", "domain": "example.invalid"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "local log" in response.get_json()["error"].lower()


def test_export_requires_analysis_first(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/json")

    assert response.status_code == 400
    assert "analysis must run" in response.get_json()["error"].lower()


def test_export_json_after_analysis(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/json?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert b"findings" in response.data


def test_export_csv_after_analysis_with_analysis_id(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/csv?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "rule_id,severity" in response.get_data(as_text=True)


def test_export_markdown_after_analysis_with_analysis_id(tmp_path):
    client = make_app(tmp_path)
    analyze = client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")
    analysis_id = analyze.get_json()["analysis_id"]

    response = client.get(f"/api/exports/markdown?analysis_id={analysis_id}")

    assert response.status_code == 200
    assert response.mimetype == "text/markdown"
    assert "Log Intrusion Analysis Report" in response.get_data(as_text=True)


def test_export_requires_analysis_id_after_analysis(tmp_path):
    client = make_app(tmp_path)
    client.post("/api/analyze", data={"sample_ids": "auth.log"}, content_type="multipart/form-data")

    export = client.get("/api/exports/json")

    assert export.status_code == 400
    assert "analysis id" in export.get_json()["error"].lower()


def test_export_rejects_unknown_analysis_id(tmp_path):
    client = make_app(tmp_path)

    response = client.get("/api/exports/json?analysis_id=missing")

    assert response.status_code == 400
    assert "analysis must run" in response.get_json()["error"].lower()


def test_analyze_rejects_more_than_configured_uploaded_files(tmp_path):
    client = make_app(tmp_path)
    client.application.config["MAX_UPLOAD_FILES"] = 1

    response = client.post(
        "/api/analyze",
        data={
            "files": [
                (BytesIO(b"first failed password line\n"), "first.log"),
                (BytesIO(b"second failed password line\n"), "second.log"),
            ]
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "too many" in response.get_json()["error"].lower()


def test_uploaded_files_are_cleaned_after_analysis(tmp_path):
    upload_dir = tmp_path / "uploads"
    client = create_app(sample_dir=tmp_path / "samples", upload_dir=upload_dir).test_client()

    response = client.post(
        "/api/analyze",
        data={
            "files": (
                BytesIO(
                    b"Jun  1 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.11 port 22 ssh2\n"
                ),
                "upload.log",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert not list(upload_dir.glob("*upload.log"))


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


def test_dashboard_styles_include_filters_pagination_and_attacker_ip_rules():
    styles = (PROJECT_ROOT / "logcheck" / "web_static" / "styles.css").read_text(encoding="utf-8")

    for selector in [
        ".language-control",
        ".filter-grid",
        ".queue-toolbar",
        ".pagination-controls",
        ".attacker-ip-table",
        ".attacker-ip-row",
    ]:
        assert selector in styles
    assert "overflow-wrap: anywhere" in styles
