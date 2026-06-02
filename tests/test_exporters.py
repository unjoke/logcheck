from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from logcheck.exporters import export_csv, export_json, export_markdown
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


if __name__ == "__main__":
    unittest.main()
