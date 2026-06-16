from pathlib import Path

from logcheck.analysis import analyze_logs


def test_incident_sample_exercises_course_demo_findings():
    result = analyze_logs([Path("samples/incident.log")])
    rule_ids = {finding.rule_id for finding in result.findings}
    severities = {finding.severity for finding in result.findings}
    sources = {
        finding.source_address for finding in result.findings if finding.source_address
    }

    # Check for new rule ID patterns (indicator.*, pattern.*, correlation.*)
    assert any("failed_auth" in rid for rid in rule_ids)
    assert any("sudo_failure" in rid or "root_auth" in rid or "sensitive_path" in rid
               for rid in rule_ids)
    assert any("suspicious_download" in rid or "reverse_shell" in rid
               for rid in rule_ids)
    assert any("unauthorized" in rid for rid in rule_ids)
    assert len(severities) >= 2, f"Expected at least 2 severity levels, got {severities}"
    assert len(sources) >= 2
    assert result.insights is not None
    assert result.insights.entity_profiles


def test_access1_sample_detects_encoded_sql_injection_attack_behavior():
    result = analyze_logs([Path("samples/access1.log")])
    sql_injection_findings = [
        finding
        for finding in result.findings
        if any("sqli" in iid.lower() for iid in (finding.indicator_ids or []))
        or "sqli" in (finding.matched_keyword or "").lower()
    ]

    assert sql_injection_findings
    assert sql_injection_findings[0].severity in {"high", "critical", "medium"}
    assert sql_injection_findings[0].source_address == "172.17.0.1"
    assert sql_injection_findings[0].count is not None
    assert sql_injection_findings[0].count >= 5
    assert sql_injection_findings[0].severity_reason
    assert sql_injection_findings[0].confidence_reason
    # New fields from scoring model
    assert sql_injection_findings[0].score is not None
    assert sql_injection_findings[0].score > 0
    assert sql_injection_findings[0].confidence is not None
    assert sql_injection_findings[0].confidence > 0


def test_visual_access_sample_has_source_and_time_diversity():
    result = analyze_logs([Path("samples/access-visual-diverse.log")])
    findings = result.findings
    sources = {finding.source_address for finding in findings if finding.source_address}
    timestamps = {finding.timestamp for finding in findings if finding.timestamp}

    assert len(findings) >= 3
    assert len(sources) >= 3
    assert len(timestamps) >= 3
    # Check for SQL-injection related findings using new rule ID pattern
    assert any(
        "sqli" in (finding.matched_keyword or "").lower()
        or any("sqli" in iid.lower() for iid in (finding.indicator_ids or []))
        for finding in findings
    )
