from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from logcheck.exporters import export_csv, export_json, export_markdown
from logcheck.insights import generate_insights
from logcheck.models import AnalysisResult, Event, Finding


def sample_result():
    return AnalysisResult(
        events=[Event("auth.log", 1, "Failed password", category="auth")],
        findings=[
            Finding(
                "keyword.failed_login",
                "medium",
                "Matched failed login",
                ["Failed password"],
                "auth.log",
                1,
                source_address="192.0.2.10",
            )
        ],
    )


class ExporterTests(unittest.TestCase):
    def test_export_json_writes_findings(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            export_json(sample_result(), path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["total_events"], 1)
            self.assertEqual(data["findings"][0]["rule_id"], "keyword.failed_login")

    def test_export_json_includes_source_context_metadata(self):
        result = sample_result()
        result.rule_source = "rules/custom.yml"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"

            export_json(result, path)

            data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["analyzed_sources"], ["auth.log"])
        self.assertEqual(data["active_rule_source"], "rules/custom.yml")

    def test_export_json_includes_insights_when_available(self):
        result = sample_result()
        result.insights = generate_insights(result)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "analysis.json"

            export_json(result, path)

            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("insights", payload)
        self.assertIn("entity_profiles", payload["insights"])

    def test_export_csv_writes_header_and_row(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.csv"
            export_csv(sample_result(), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("rule_id,severity", text)
            self.assertIn("keyword.failed_login,medium", text)

    def test_export_markdown_writes_summary(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            export_markdown(sample_result(), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("# Log Intrusion Analysis Report", text)
            self.assertIn("keyword.failed_login", text)

    def test_export_markdown_includes_insight_section(self):
        result = sample_result()
        result.insights = generate_insights(result)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "analysis.md"

            export_markdown(result, path)

            text = path.read_text(encoding="utf-8")
        self.assertIn("## Investigation Insights", text)
        self.assertIn(result.insights.headline, text)

    def test_export_markdown_includes_insight_evidence(self):
        result = sample_result()
        result.insights = generate_insights(result)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "analysis.md"

            export_markdown(result, path)

            text = path.read_text(encoding="utf-8")
        insights_section = text.split("## Investigation Insights", 1)[1].split("## Findings", 1)[0]
        self.assertIn("Failed password", insights_section)


if __name__ == "__main__":
    unittest.main()
