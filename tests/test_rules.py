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
