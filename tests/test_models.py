import unittest

from logcheck.models import Event, Finding


class ModelTests(unittest.TestCase):
    def test_event_defaults_to_unknown_category(self):
        event = Event(source_file="auth.log", line_number=1, raw_line="raw")
        self.assertEqual(event.category, "unknown")
        self.assertEqual(event.message, "raw")

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


if __name__ == "__main__":
    unittest.main()
