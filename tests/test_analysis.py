from pathlib import Path
import unittest

from logcheck.analysis import analyze_logs, summarize_result


class AnalysisTests(unittest.TestCase):
    def test_analyze_logs_returns_events_and_findings(self):
        result = analyze_logs([Path("samples/auth.log"), Path("samples/app.log")])

        self.assertGreater(len(result.events), 0)
        self.assertGreater(len(result.findings), 0)
        self.assertIsNotNone(result.insights)

    def test_summarize_result_counts_findings(self):
        result = analyze_logs([Path("samples/auth.log"), Path("samples/app.log")])
        summary = summarize_result(result)

        self.assertEqual(summary.total_events, len(result.events))
        self.assertEqual(summary.total_findings, len(result.findings))
        # With new scoring model, the severity may be any of medium/high/critical
        self.assertTrue(
            any(sev in summary.findings_by_severity for sev in ("high", "critical", "medium"))
        )
        self.assertGreaterEqual(len(summary.top_suspicious_sources), 1)


if __name__ == "__main__":
    unittest.main()
