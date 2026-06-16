import unittest

from logcheck.models import AnalysisResult, Event, Finding


class ModelTests(unittest.TestCase):
    def test_event_defaults_to_unknown_category(self):
        event = Event(source_file="auth.log", line_number=1, raw_line="raw")
        self.assertEqual(event.category, "unknown")
        self.assertEqual(event.message, "raw")

    def test_event_metadata_defaults_to_empty_dict(self):
        event = Event(source_file="access.log", line_number=1, raw_line="raw")

        self.assertEqual(event.metadata, {})

    def test_finding_exposes_exportable_dict(self):
        finding = Finding(
            rule_id="keyword.failed_login",
            severity="medium",
            explanation="Failed login detected",
            evidence=["failed password for root"],
            source_file="auth.log",
            line_number=12,
            source_address="192.0.2.10",
            actor="root",
        )
        data = finding.to_dict()
        self.assertEqual(data["rule_id"], "keyword.failed_login")
        self.assertEqual(data["severity"], "medium")
        self.assertEqual(data["source_address"], "192.0.2.10")
        self.assertEqual(data["evidence"], ["failed password for root"])

    def test_analysis_result_can_carry_diagnostics_and_insights(self):
        result = AnalysisResult()

        self.assertEqual(result.diagnostics, [])
        self.assertIsNone(result.insights)

    def test_finding_exports_reason_fields_when_present(self):
        finding = Finding(
            rule_id="behavior.suspicious_command",
            severity="high",
            explanation="Suspicious command execution",
            evidence=["curl http://example.invalid"],
            severity_reason="Suspicious command matched high-risk indicator",
            confidence_reason="Exact command keyword match",
        )

        data = finding.to_dict()

        self.assertEqual(data["severity_reason"], "Suspicious command matched high-risk indicator")
        self.assertEqual(data["confidence_reason"], "Exact command keyword match")


if __name__ == "__main__":
    unittest.main()
