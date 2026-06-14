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
    assert finding["evidence"] == ["Failed password for root from 192.0.2.10"]
    assert finding["confidence_reason"] == "exact keyword match"


def test_serialize_result_includes_insights_when_present():
    payload = serialize_result(make_result())

    assert payload["insights"]["headline"]
    assert "entity_profiles" in payload["insights"]
    assert "timeline" in payload["insights"]
    assert "suggestions" in payload["insights"]
