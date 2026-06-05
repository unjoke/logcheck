from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logcheck.parsers import parse_files, parse_line


class ParserTests(unittest.TestCase):
    def test_parse_linux_failed_login_line(self):
        event = parse_line(
            "auth.log",
            1,
            "Jun  2 10:01:05 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51234 ssh2",
        )
        self.assertEqual(event.category, "auth")
        self.assertEqual(event.actor, "admin")
        self.assertEqual(event.source_address, "192.0.2.10")
        self.assertIn("Failed password", event.message)

    def test_parse_application_unauthorized_access_line(self):
        event = parse_line(
            "app.log",
            2,
            "2026-06-02 10:02:00 WARN unauthorized access user=guest ip=198.51.100.7 path=/admin",
        )
        self.assertEqual(event.category, "application")
        self.assertEqual(event.actor, "guest")
        self.assertEqual(event.source_address, "198.51.100.7")

    def test_unknown_line_is_preserved(self):
        event = parse_line("misc.log", 3, "not a known format")
        self.assertEqual(event.category, "unknown")
        self.assertEqual(event.raw_line, "not a known format")

    def test_empty_file_produces_no_events_without_crashing(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.log"
            path.write_text("", encoding="utf-8")

            events = parse_files([path])

        self.assertEqual(events, [])

    def test_unknown_lines_preserve_source_context(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.log"
            path.write_text("not a known auth line\n", encoding="utf-8")

            events = parse_files([path])

        self.assertEqual(events[0].source_file, str(path))
        self.assertEqual(events[0].line_number, 1)
        self.assertEqual(events[0].category, "unknown")
        self.assertEqual(events[0].raw_line, "not a known auth line")

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            parse_files([Path("missing.log")])

    def test_parse_file_reads_all_lines(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "auth.log"
            path.write_text("line one\nline two\n", encoding="utf-8")
            events = parse_files([path])
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0].line_number, 1)


if __name__ == "__main__":
    unittest.main()
