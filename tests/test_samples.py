from pathlib import Path

from logcheck.analysis import analyze_logs


def test_incident_sample_exercises_course_demo_findings():
    result = analyze_logs([Path("samples/incident.log")])
    rule_ids = {finding.rule_id for finding in result.findings}
    severities = {finding.severity for finding in result.findings}
    sources = {
        finding.source_address for finding in result.findings if finding.source_address
    }

    assert "correlation.brute_force" in rule_ids
    assert "behavior.privilege_escalation" in rule_ids
    assert "behavior.suspicious_command" in rule_ids
    assert "keyword.invalid_user" in rule_ids
    assert "keyword.unauthorized_access" in rule_ids
    assert {"medium", "high"}.issubset(severities)
    assert len(sources) >= 2
    assert result.insights is not None
    assert result.insights.entity_profiles


def test_access1_sample_detects_encoded_sql_injection_attack_behavior():
    result = analyze_logs([Path("samples/access1.log")])
    sql_injection_findings = [
        finding
        for finding in result.findings
        if finding.rule_id == "behavior.web_sql_injection"
    ]

    assert sql_injection_findings
    assert sql_injection_findings[0].severity in {"high", "critical"}
    assert sql_injection_findings[0].source_address == "172.17.0.1"
    assert sql_injection_findings[0].count is not None
    assert sql_injection_findings[0].count >= 5
    assert sql_injection_findings[0].severity_reason
    assert sql_injection_findings[0].confidence_reason


def test_visual_access_sample_has_source_and_time_diversity():
    result = analyze_logs([Path("samples/access-visual-diverse.log")])
    findings = result.findings
    sources = {finding.source_address for finding in findings if finding.source_address}
    timestamps = {finding.timestamp for finding in findings if finding.timestamp}

    assert len(findings) >= 3
    assert len(sources) >= 3
    assert len(timestamps) >= 3
    assert any(finding.rule_id == "behavior.web_sql_injection" for finding in findings)
