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
