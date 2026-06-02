import unittest

from logcheck.config import default_config
from logcheck.models import DetectionConfig, Event
from logcheck.rules import detect_findings


class RuleTests(unittest.TestCase):
    def test_keyword_rule_detects_failed_login(self):
        event = Event(
            source_file="auth.log",
            line_number=1,
            raw_line="Failed password for invalid user admin from 192.0.2.10",
            category="auth",
            actor="admin",
            source_address="192.0.2.10",
            message="Failed password for invalid user admin from 192.0.2.10",
        )
        findings = detect_findings([event], default_config())
        self.assertTrue(any(f.rule_id == "keyword.failed_login" for f in findings))

    def test_repeated_failed_login_detects_brute_force(self):
        events = [
            Event(
                "auth.log",
                i,
                "Failed password",
                category="auth",
                source_address="192.0.2.10",
                message="Failed password",
            )
            for i in range(1, 6)
        ]
        findings = detect_findings(events, default_config())
        brute_force = [f for f in findings if f.rule_id == "correlation.brute_force"]
        self.assertEqual(len(brute_force), 1)
        self.assertEqual(brute_force[0].severity, "high")
        self.assertEqual(brute_force[0].count, 5)

    def test_custom_threshold_is_applied(self):
        config = DetectionConfig(keywords=default_config().keywords, brute_force_threshold=2)
        events = [
            Event(
                "auth.log",
                1,
                "Failed password",
                category="auth",
                source_address="192.0.2.10",
                message="Failed password",
            ),
            Event(
                "auth.log",
                2,
                "Failed password",
                category="auth",
                source_address="192.0.2.10",
                message="Failed password",
            ),
        ]
        findings = detect_findings(events, config)
        self.assertTrue(any(f.rule_id == "correlation.brute_force" for f in findings))


if __name__ == "__main__":
    unittest.main()
