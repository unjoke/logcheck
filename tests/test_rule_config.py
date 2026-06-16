import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from logcheck.config import load_rules
from logcheck.models import RuleConfig, IndicatorRule, PatternRule, CorrelationRule


class RuleConfigLoadingTests(unittest.TestCase):
    def _write_toml(self, tmp: Path, content: str) -> Path:
        path = tmp / "rules.toml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_indicator_rules_from_toml(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "test_indicator"
category = "test"
description = "A test indicator"
weight = 2
text_contains = ["needle"]
score = 15
""")
            config = load_rules(path)
            # load_rules() merges with defaults, so we check at least the user rule is present
            self.assertGreaterEqual(len(config.indicator_rules), 1)
            rule_ids = [r.id for r in config.indicator_rules]
            self.assertIn("test_indicator", rule_ids)
            rule = next(r for r in config.indicator_rules if r.id == "test_indicator")
            self.assertEqual(rule.score, 15)
            self.assertEqual(rule.text_contains, ["needle"])

    def test_loads_pattern_rules_from_toml(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "ind_a"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[pattern_rules]]
id = "test_pattern"
category = "test"
description = "A test pattern"
require_indicators = ["ind_a"]
min_events = 5
multiplier = 1.5
score = 30
""")
            config = load_rules(path)
            # load_rules() merges with defaults, so check user pattern is present
            self.assertGreaterEqual(len(config.pattern_rules), 1)
            pattern_ids = [r.id for r in config.pattern_rules]
            self.assertIn("test_pattern", pattern_ids)
            rule = next(r for r in config.pattern_rules if r.id == "test_pattern")
            self.assertEqual(rule.require_indicators, ["ind_a"])
            self.assertEqual(rule.multiplier, 1.5)

    def test_loads_severity_thresholds(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[severity_thresholds]
low = 0
medium = 30
high = 60
critical = 85
""")
            config = load_rules(path)
            self.assertEqual(config.severity_thresholds["medium"], 30)
            self.assertEqual(config.severity_thresholds["critical"], 85)

    def test_default_thresholds_when_not_specified(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, "")
            config = load_rules(path)
            self.assertEqual(config.severity_thresholds, {
                "low": 0, "medium": 20, "high": 50, "critical": 80
            })

    def test_rejects_score_out_of_range(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "bad"
category = "test"
weight = 2
text_contains = ["x"]
score = 150
""")
            with self.assertRaises(ValueError):
                load_rules(path)

    def test_rejects_duplicate_rule_ids(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "same_id"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[indicator_rules]]
id = "same_id"
category = "test"
weight = 1
text_contains = ["b"]
score = 20
""")
            with self.assertRaises(ValueError):
                load_rules(path)

    def test_disabled_rule_is_excluded(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "enabled_rule"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[indicator_rules]]
id = "disabled_rule"
category = "test"
weight = 1
text_contains = ["b"]
score = 10
enabled = false
""")
            config = load_rules(path)
            ids = [r.id for r in config.indicator_rules]
            self.assertIn("enabled_rule", ids)
            self.assertNotIn("disabled_rule", ids)

    def test_loads_json_rules(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = tmp / "rules.json"
            path.write_text(json.dumps({
                "severity_thresholds": {"low": 0, "medium": 25, "high": 55, "critical": 85},
                "indicator_rules": [{
                    "id": "json_rule",
                    "category": "test",
                    "description": "from json",
                    "weight": 1,
                    "text_contains": ["json_needle"],
                    "score": 20
                }],
                "pattern_rules": [],
                "correlation_rules": []
            }), encoding="utf-8")
            config = load_rules(path)
            # Merged with defaults — check user rule is present
            self.assertGreaterEqual(len(config.indicator_rules), 1)
            rule_ids = [r.id for r in config.indicator_rules]
            self.assertIn("json_rule", rule_ids)
            self.assertEqual(config.severity_thresholds["medium"], 25)
