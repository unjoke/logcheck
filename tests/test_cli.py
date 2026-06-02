from pathlib import Path
from tempfile import TemporaryDirectory
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


if __name__ == "__main__":
    unittest.main()
