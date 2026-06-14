from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from io import StringIO
import unittest

from logcheck.cli import main


class CliTests(unittest.TestCase):
    def test_cli_exports_requested_reports(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            code = main(
                [
                    "samples/auth.log",
                    "samples/app.log",
                    "--out-dir",
                    str(out),
                    "--format",
                    "json",
                    "--format",
                    "csv",
                    "--format",
                    "markdown",
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((out / "analysis.json").exists())
            self.assertTrue((out / "analysis.csv").exists())
            self.assertTrue((out / "analysis.md").exists())

    def test_cli_missing_file_returns_nonzero(self):
        code = main(["missing.log"])
        self.assertEqual(code, 2)

    def test_cli_prints_local_insight_summary(self):
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "auth.log"
            log.write_text(
                "Jan  1 00:00:01 host sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2\n",
                encoding="utf-8",
            )
            out = Path(tmp) / "out"
            stdout = StringIO()

            with redirect_stdout(stdout):
                code = main([str(log), "--out-dir", str(out), "--format", "json"])

        self.assertEqual(code, 0)
        self.assertIn("Insight", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
