import unittest

from logcheck.models import (
    CorrelationRule,
    Event,
    IndicatorRule,
    IndicatorMatch,
    PatternResult,
    PatternRule,
    RuleConfig,
)
from logcheck.rules import (
    ScoreCompiler,
    IndicatorScanner,
    PatternDetector,
    CorrelationEngine,
    compile_findings,
)


class ScoreCompilerTests(unittest.TestCase):
    def setUp(self):
        self.thresholds = {"low": 0, "medium": 20, "high": 50, "critical": 80}
        self.compiler = ScoreCompiler(self.thresholds)

    def test_low_score_maps_to_low(self):
        self.assertEqual(self.compiler.score_to_severity(10, 80), "low")

    def test_medium_score_maps_to_medium(self):
        self.assertEqual(self.compiler.score_to_severity(35, 80), "medium")

    def test_high_score_high_confidence_maps_to_high(self):
        self.assertEqual(self.compiler.score_to_severity(65, 80), "high")

    def test_high_score_low_confidence_maps_to_critical(self):
        self.assertEqual(self.compiler.score_to_severity(65, 30), "critical")

    def test_critical_score_always_critical(self):
        self.assertEqual(self.compiler.score_to_severity(85, 90), "critical")
        self.assertEqual(self.compiler.score_to_severity(85, 10), "critical")

    def test_confidence_diversity_driven(self):
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=1, indicator_ids=["a"],
            has_decoded=False, has_response_variance=False,
            substr_positions_count=0,
        )
        self.assertEqual(conf, 15)

        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=3, indicator_ids=["a", "b", "c"],
            has_decoded=False, has_response_variance=False,
            substr_positions_count=0,
        )
        self.assertEqual(conf, 45)

    def test_confidence_evidence_bonuses(self):
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=2, indicator_ids=["a", "b"],
            has_decoded=True, has_response_variance=True,
            substr_positions_count=10,
        )
        self.assertEqual(conf, 45)

    def test_confidence_clamped_to_100(self):
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=10,
            indicator_ids=[str(i) for i in range(10)],
            has_decoded=True, has_response_variance=True,
            substr_positions_count=50,
        )
        self.assertLessEqual(conf, 100)

    def test_apply_cap_limits_score(self):
        self.assertEqual(self.compiler.apply_cap(90, 75), 75)
        self.assertEqual(self.compiler.apply_cap(60, 75), 60)

    def test_custom_thresholds(self):
        compiler = ScoreCompiler({"low": 0, "medium": 30, "high": 60, "critical": 90})
        self.assertEqual(compiler.score_to_severity(25, 80), "low")
        self.assertEqual(compiler.score_to_severity(55, 80), "medium")
        self.assertEqual(compiler.score_to_severity(75, 80), "high")
        self.assertEqual(compiler.score_to_severity(75, 30), "critical")


class IndicatorScannerTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            IndicatorRule(
                id="test_keyword", category="test",
                description="test", weight=1,
                text_contains=["needle"], score=15,
            ),
            IndicatorRule(
                id="test_regex", category="test",
                description="test regex", weight=2,
                regex=r"id=(\d+)", score=20,
            ),
            IndicatorRule(
                id="access_only", category="test",
                description="access only", weight=1,
                event_category="access",
                text_contains=["secret"], score=25,
            ),
        ]
        self.scanner = IndicatorScanner(self.rules)

    def test_scanner_matches_keyword_in_event(self):
        event = Event("test.log", 1, "found a needle here", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].rule_id, "test_keyword")
        self.assertEqual(matches[0].score, 15)

    def test_scanner_matches_regex(self):
        event = Event("test.log", 1, "query?id=42&name=foo", category="access")
        matches = self.scanner.scan(event, 0)
        regex_match = [m for m in matches if m.rule_id == "test_regex"]
        self.assertEqual(len(regex_match), 1)
        self.assertEqual(regex_match[0].score, 20)

    def test_scanner_respects_event_category(self):
        event = Event("test.log", 1, "secret data", category="application")
        matches = self.scanner.scan(event, 0)
        ids = [m.rule_id for m in matches]
        self.assertNotIn("access_only", ids)

    def test_scanner_matches_category_when_correct(self):
        event = Event("test.log", 1, "secret data", category="access")
        matches = self.scanner.scan(event, 0)
        ids = [m.rule_id for m in matches]
        self.assertIn("access_only", ids)

    def test_scanner_no_matches(self):
        event = Event("test.log", 1, "completely benign", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertEqual(len(matches), 0)

    def test_scanner_multiple_matches_same_event(self):
        event = Event("test.log", 1, "needle and id=7", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertGreaterEqual(len(matches), 2)


class PatternDetectorTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            PatternRule(
                id="test_pattern", category="test",
                description="test pattern",
                require_indicators=["ind_a", "ind_b"],
                min_events=3, multiplier=1.5, score=30,
            ),
        ]
        self.detector = PatternDetector(self.rules)

    def _match(self, rule_id: str, source="1.2.3.4", target="/"):
        return IndicatorMatch(
            rule_id=rule_id, category="test", event_index=0,
            score=10, source_address=source, target=target,
        )

    def test_pattern_activates_when_requirements_met(self):
        matches = [
            self._match("ind_a"), self._match("ind_a"),
            self._match("ind_b"), self._match("ind_a"),
        ]
        results = self.detector.detect(matches, {i: None for i in range(4)})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "test_pattern")
        self.assertEqual(results[0].indicator_score_sum, 40)
        # 40 * 1.5 + 30 = 90
        self.assertEqual(results[0].final_score, 90)

    def test_pattern_does_not_activate_below_min_events(self):
        matches = [self._match("ind_a"), self._match("ind_b")]
        results = self.detector.detect(matches, {i: None for i in range(2)})
        self.assertEqual(len(results), 0)

    def test_pattern_requires_all_indicators(self):
        matches = [self._match("ind_a")] * 5
        results = self.detector.detect(matches, {i: None for i in range(5)})
        self.assertEqual(len(results), 0)

    def test_pattern_groups_by_source_target(self):
        matches = [
            self._match("ind_a", source="1.1.1.1", target="/a"),
            self._match("ind_a", source="1.1.1.1", target="/a"),
            self._match("ind_b", source="1.1.1.1", target="/a"),
            self._match("ind_a", source="2.2.2.2", target="/b"),
            self._match("ind_b", source="2.2.2.2", target="/b"),
            self._match("ind_a", source="2.2.2.2", target="/b"),
        ]
        results = self.detector.detect(matches, {i: None for i in range(6)})
        self.assertEqual(len(results), 2)


class CorrelationEngineTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            CorrelationRule(
                id="multi_cat", description="multi category",
                min_distinct_categories=2, score=20,
            ),
        ]
        self.engine = CorrelationEngine(self.rules)

    def test_correlation_activates_multi_category(self):
        pattern_results = [
            PatternResult("p1", "web", ("1.2.3.4", "/"), ["a"], 5, 30, 1.5, 30, 75, []),
            PatternResult("p2", "auth", ("1.2.3.4", "/"), ["b"], 5, 20, 1.5, 30, 60, []),
        ]
        results = self.engine.detect(pattern_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "multi_cat")
        self.assertEqual(results[0].distinct_categories, 2)

    def test_correlation_does_not_activate_single_category(self):
        pattern_results = [
            PatternResult("p1", "web", ("1.2.3.4", "/"), ["a"], 5, 30, 1.5, 30, 75, []),
            PatternResult("p2", "web", ("1.2.3.4", "/"), ["b"], 5, 20, 1.5, 30, 60, []),
        ]
        results = self.engine.detect(pattern_results)
        self.assertEqual(len(results), 0)


class CompileFindingsTests(unittest.TestCase):
    def setUp(self):
        self.config = RuleConfig(
            indicator_rules=[
                IndicatorRule(id="ind_a", category="cat_a", description="a",
                              weight=1, text_contains=["a"], score=15),
                IndicatorRule(id="ind_b", category="cat_b", description="b",
                              weight=1, text_contains=["b"], score=15),
            ],
            pattern_rules=[
                PatternRule(id="pat_ab", category="cat_a",
                            description="ab pattern",
                            require_indicators=["ind_a", "ind_b"],
                            min_events=2, multiplier=1.5, score=30),
            ],
            correlation_rules=[
                CorrelationRule(id="corr_multi", description="multi",
                                min_distinct_categories=2, score=20),
            ],
            severity_thresholds={"low": 0, "medium": 20, "high": 50, "critical": 80},
        )

    def test_full_pipeline_produces_scored_findings(self):
        events = [
            Event("test.log", i, f"event with a and b #{i}",
                  category="application", source_address="1.2.3.4", target="/")
            for i in range(5)
        ]
        findings = compile_findings(events, self.config)
        self.assertTrue(len(findings) > 0)
        for f in findings:
            self.assertIsInstance(f.score, int)
            self.assertGreaterEqual(f.score, 0)
            self.assertLessEqual(f.score, 100)
            self.assertIsInstance(f.confidence, int)
            self.assertIn(f.rule_tier, ("indicator", "pattern", "correlation"))
