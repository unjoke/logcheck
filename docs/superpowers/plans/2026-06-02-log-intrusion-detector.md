---
change: build-log-intrusion-detector
design-doc: docs/superpowers/specs/2026-06-02-log-intrusion-detector-design.md
base-ref: none-not-a-git-repository
archived-with: 2026-06-02-build-log-intrusion-detector
---

# Log Intrusion Detector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python CLI that parses log files, detects intrusion indicators, and exports evidence-rich analysis reports for the course design.

**Architecture:** The CLI orchestrates parser, rule engine, config, and exporters. Parsers turn raw log lines into `Event` objects; rules turn events into `Finding` objects; exporters write JSON, CSV, and Markdown outputs.

**Tech Stack:** Python 3.11+, standard library (`argparse`, `csv`, `json`, `dataclasses`, `datetime`, `pathlib`, `re`, `tomllib`, `unittest`), no network calls.

archived-with: 2026-06-02-build-log-intrusion-detector
---

## File Structure

- Create `pyproject.toml`: package metadata and console script entry point.
- Create `logcheck/__init__.py`: package version.
- Create `logcheck/models.py`: `Event`, `Finding`, `AnalysisResult`, and config dataclasses.
- Create `logcheck/parsers.py`: file loading and log-line parsing.
- Create `logcheck/rules.py`: keyword rules, brute-force correlation, severity logic.
- Create `logcheck/config.py`: default rule config and optional TOML config loading.
- Create `logcheck/exporters.py`: JSON, CSV, and Markdown export functions.
- Create `logcheck/cli.py`: command-line interface and orchestration.
- Create `samples/auth.log`: deterministic Linux-auth-style sample logs.
- Create `samples/app.log`: deterministic application-style sample logs.
- Create `tests/__init__.py`: marks tests as a package for direct module runs.
- Create `tests/test_parsers.py`: parser unit tests.
- Create `tests/test_rules.py`: detection unit tests.
- Create `tests/test_exporters.py`: exporter unit tests.
- Create `tests/test_cli.py`: end-to-end CLI tests.
- Create `docs/course-report-notes.md`: report section notes and demo commands.

## Task 1: Project Scaffold and Data Models

**Files:**
- Create: `pyproject.toml`
- Create: `logcheck/__init__.py`
- Create: `logcheck/models.py`
- Create: `tests/__init__.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Create model tests**

Create `tests/__init__.py`:

```python
# Package marker for direct unittest module execution.
```

Create `tests/test_models.py`:

```python
import unittest

from logcheck.models import Event, Finding


class ModelTests(unittest.TestCase):
    def test_event_defaults_to_unknown_category(self):
        event = Event(source_file="auth.log", line_number=1, raw_line="raw")
        self.assertEqual(event.category, "unknown")
        self.assertEqual(event.message, "raw")


    def test_finding_exposes_exportable_dict(self):
        finding = Finding(
            rule_id="keyword.failed_login",
            severity="medium",
            explanation="Failed login detected",
            evidence=["failed password for root"],
            source_file="auth.log",
            line_number=12,
            source_address="192.0.2.10",
            actor="root",
        )
        data = finding.to_dict()
        self.assertEqual(data["rule_id"], "keyword.failed_login")
        self.assertEqual(data["severity"], "medium")
        self.assertEqual(data["source_address"], "192.0.2.10")
        self.assertEqual(data["evidence"], ["failed password for root"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run model tests and verify they fail**

Run:

```bash
python -m unittest tests.test_models -v
```

Expected: FAIL because `logcheck.models` does not exist yet.

- [ ] **Step 3: Create package metadata and models**

Create `pyproject.toml`:

```toml
[project]
name = "logcheck"
version = "0.1.0"
description = "Offline log intrusion behavior detector for course design"
requires-python = ">=3.11"

[project.scripts]
logcheck = "logcheck.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

Create `logcheck/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `logcheck/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Event:
    source_file: str
    line_number: int
    raw_line: str
    timestamp: datetime | None = None
    category: str = "unknown"
    actor: str | None = None
    target: str | None = None
    source_address: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.message is None:
            object.__setattr__(self, "message", self.raw_line)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    explanation: str
    evidence: list[str]
    source_file: str
    line_number: int
    timestamp: datetime | None = None
    source_address: str | None = None
    actor: str | None = None
    target: str | None = None
    matched_keyword: str | None = None
    count: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_address": self.source_address,
            "actor": self.actor,
            "target": self.target,
            "matched_keyword": self.matched_keyword,
            "count": self.count,
        }


@dataclass(frozen=True)
class DetectionConfig:
    keywords: dict[str, list[str]]
    brute_force_threshold: int = 5
    brute_force_window_minutes: int = 10


@dataclass
class AnalysisResult:
    events: list[Event] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
```

- [ ] **Step 4: Run model tests and verify they pass**

Run:

```bash
python -m unittest tests.test_models -v
```

Expected: PASS.

## Task 2: Log Parsing and Sample Logs

**Files:**
- Create: `logcheck/parsers.py`
- Create: `samples/auth.log`
- Create: `samples/app.log`
- Test: `tests/test_parsers.py`

- [ ] **Step 1: Create parser tests**

Create `tests/test_parsers.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logcheck.parsers import parse_line, parse_files


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
```

- [ ] **Step 2: Run parser tests and verify they fail**

Run:

```bash
python -m unittest tests.test_parsers -v
```

Expected: FAIL because parser functions do not exist.

- [ ] **Step 3: Implement parsers and sample logs**

Create `logcheck/parsers.py`:

```python
from __future__ import annotations

from pathlib import Path
import re

from .models import Event


IP_RE = r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
LINUX_AUTH_RE = re.compile(
    rf"^(?P<month>\w{{3}})\s+(?P<day>\d{{1,2}})\s+(?P<time>\d{{2}}:\d{{2}}:\d{{2}})\s+"
    rf"(?P<host>\S+)\s+(?P<service>\S+?):\s+(?P<message>.*?)(?:\s+from\s+{IP_RE})?(?:\s|$)",
    re.IGNORECASE,
)
APP_RE = re.compile(
    rf"^(?P<date>\d{{4}}-\d{{2}}-\d{{2}})\s+(?P<time>\d{{2}}:\d{{2}}:\d{{2}})\s+"
    rf"(?P<level>\w+)\s+(?P<message>.*?)(?:\s+ip={IP_RE})?(?:\s|$)",
    re.IGNORECASE,
)
USER_RE = re.compile(r"(?:invalid user|user=|for)\s+(?P<user>[A-Za-z0-9_.-]+)", re.IGNORECASE)


def _extract_actor(message: str) -> str | None:
    match = USER_RE.search(message)
    return match.group("user") if match else None


def parse_line(source_file: str, line_number: int, raw_line: str) -> Event:
    line = raw_line.rstrip("\n")

    linux_match = LINUX_AUTH_RE.match(line)
    if linux_match:
        message = linux_match.group("message")
        return Event(
            source_file=source_file,
            line_number=line_number,
            raw_line=line,
            category="auth",
            actor=_extract_actor(message),
            source_address=linux_match.groupdict().get("ip"),
            message=message,
        )

    app_match = APP_RE.match(line)
    if app_match:
        message = app_match.group("message")
        return Event(
            source_file=source_file,
            line_number=line_number,
            raw_line=line,
            category="application",
            actor=_extract_actor(message),
            source_address=app_match.groupdict().get("ip"),
            message=message,
        )

    return Event(source_file=source_file, line_number=line_number, raw_line=line)


def parse_files(paths: list[Path]) -> list[Event]:
    events: list[Event] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(str(path))
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                events.append(parse_line(str(path), line_number, line))
    return events
```

Create `samples/auth.log`:

```text
Jun  2 10:01:05 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51234 ssh2
Jun  2 10:01:15 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51235 ssh2
Jun  2 10:01:25 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51236 ssh2
Jun  2 10:01:35 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51237 ssh2
Jun  2 10:01:45 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51238 ssh2
Jun  2 10:03:01 ubuntu sudo: pam_unix(sudo:auth): authentication failure; user=root
this is a malformed line kept for robustness
```

Create `samples/app.log`:

```text
2026-06-02 10:02:00 WARN unauthorized access user=guest ip=198.51.100.7 path=/admin
2026-06-02 10:04:00 ERROR permission denied user=guest ip=198.51.100.7 path=/etc/shadow
2026-06-02 10:05:00 INFO normal request user=alice ip=203.0.113.4 path=/home
```

- [ ] **Step 4: Run parser tests and verify they pass**

Run:

```bash
python -m unittest tests.test_parsers -v
```

Expected: PASS.

## Task 3: Rule Engine and Config

**Files:**
- Create: `logcheck/config.py`
- Create: `logcheck/rules.py`
- Test: `tests/test_rules.py`

- [ ] **Step 1: Create rule tests**

Create `tests/test_rules.py`:

```python
import unittest

from logcheck.config import default_config
from logcheck.models import Event, DetectionConfig
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
            Event("auth.log", i, "Failed password", category="auth", source_address="192.0.2.10", message="Failed password")
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
            Event("auth.log", 1, "Failed password", category="auth", source_address="192.0.2.10", message="Failed password"),
            Event("auth.log", 2, "Failed password", category="auth", source_address="192.0.2.10", message="Failed password"),
        ]
        findings = detect_findings(events, config)
        self.assertTrue(any(f.rule_id == "correlation.brute_force" for f in findings))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run rule tests and verify they fail**

Run:

```bash
python -m unittest tests.test_rules -v
```

Expected: FAIL because config and rule modules do not exist.

- [ ] **Step 3: Implement config and rules**

Create `logcheck/config.py`:

```python
from __future__ import annotations

from pathlib import Path
import tomllib

from .models import DetectionConfig


def default_config() -> DetectionConfig:
    return DetectionConfig(
        keywords={
            "failed_login": ["failed password", "failed login", "authentication failure"],
            "invalid_user": ["invalid user"],
            "unauthorized_access": ["unauthorized access"],
            "permission_denied": ["permission denied"],
            "sudo_failure": ["sudo:auth", "sudo failure"],
            "suspicious_command": ["wget http", "curl http", "nc -e", "bash -i"],
        },
        brute_force_threshold=5,
        brute_force_window_minutes=10,
    )


def load_config(path: Path | None) -> DetectionConfig:
    if path is None:
        return default_config()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    base = default_config()
    keywords = data.get("keywords", base.keywords)
    brute_force = data.get("brute_force", {})
    return DetectionConfig(
        keywords=keywords,
        brute_force_threshold=int(brute_force.get("threshold", base.brute_force_threshold)),
        brute_force_window_minutes=int(brute_force.get("window_minutes", base.brute_force_window_minutes)),
    )
```

Create `logcheck/rules.py`:

```python
from __future__ import annotations

from collections import defaultdict

from .models import DetectionConfig, Event, Finding


SEVERITY_BY_RULE = {
    "failed_login": "medium",
    "invalid_user": "medium",
    "unauthorized_access": "high",
    "permission_denied": "medium",
    "sudo_failure": "high",
    "suspicious_command": "critical",
}


def detect_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_keyword_findings(events, config))
    findings.extend(_brute_force_findings(events, config))
    return findings


def _keyword_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = f"{event.raw_line}\n{event.message or ''}".lower()
        for rule_name, keywords in config.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    findings.append(
                        Finding(
                            rule_id=f"keyword.{rule_name}",
                            severity=SEVERITY_BY_RULE.get(rule_name, "low"),
                            explanation=f"Matched intrusion indicator keyword: {keyword}",
                            evidence=[event.raw_line],
                            source_file=event.source_file,
                            line_number=event.line_number,
                            timestamp=event.timestamp,
                            source_address=event.source_address,
                            actor=event.actor,
                            target=event.target,
                            matched_keyword=keyword,
                        )
                    )
                    break
    return findings


def _brute_force_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    buckets: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        text = f"{event.raw_line}\n{event.message or ''}".lower()
        if "failed password" in text or "failed login" in text or "authentication failure" in text:
            key = event.source_address or event.actor or "unknown"
            buckets[key].append(event)

    findings: list[Finding] = []
    for key, bucket in buckets.items():
        if len(bucket) >= config.brute_force_threshold:
            first = bucket[0]
            findings.append(
                Finding(
                    rule_id="correlation.brute_force",
                    severity="high",
                    explanation=(
                        f"{len(bucket)} failed authentication events from {key}; "
                        f"threshold is {config.brute_force_threshold}"
                    ),
                    evidence=[event.raw_line for event in bucket[:5]],
                    source_file=first.source_file,
                    line_number=first.line_number,
                    timestamp=first.timestamp,
                    source_address=first.source_address,
                    actor=first.actor,
                    count=len(bucket),
                )
            )
    return findings
```

- [ ] **Step 4: Run rule tests and verify they pass**

Run:

```bash
python -m unittest tests.test_rules -v
```

Expected: PASS.

## Task 4: Exporters

**Files:**
- Create: `logcheck/exporters.py`
- Test: `tests/test_exporters.py`

- [ ] **Step 1: Create exporter tests**

Create `tests/test_exporters.py`:

```python
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
```

- [ ] **Step 2: Run exporter tests and verify they fail**

Run:

```bash
python -m unittest tests.test_exporters -v
```

Expected: FAIL because exporter functions do not exist.

- [ ] **Step 3: Implement exporters**

Create `logcheck/exporters.py`:

```python
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

from .models import AnalysisResult


def _metadata(result: AnalysisResult) -> dict[str, object]:
    severities = Counter(finding.severity for finding in result.findings)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_events": len(result.events),
        "total_findings": len(result.findings),
        "findings_by_severity": dict(severities),
    }


def export_json(result: AnalysisResult, path: Path) -> None:
    payload = {
        **_metadata(result),
        "findings": [finding.to_dict() for finding in result.findings],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(result: AnalysisResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rule_id",
        "severity",
        "source_file",
        "line_number",
        "source_address",
        "actor",
        "matched_keyword",
        "count",
        "explanation",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for finding in result.findings:
            data = finding.to_dict()
            writer.writerow({field: data.get(field) for field in fields})


def export_markdown(result: AnalysisResult, path: Path) -> None:
    meta = _metadata(result)
    lines = [
        "# Log Intrusion Analysis Report",
        "",
        f"- Total events: {meta['total_events']}",
        f"- Total findings: {meta['total_findings']}",
        f"- Findings by severity: {meta['findings_by_severity']}",
        "",
        "## Findings",
        "",
    ]
    for finding in result.findings:
        lines.extend(
            [
                f"### {finding.rule_id} ({finding.severity})",
                "",
                f"- Source: {finding.source_file}:{finding.line_number}",
                f"- Address: {finding.source_address or 'unknown'}",
                f"- Explanation: {finding.explanation}",
                "- Evidence:",
            ]
        )
        lines.extend(f"  - `{line}`" for line in finding.evidence)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 4: Run exporter tests and verify they pass**

Run:

```bash
python -m unittest tests.test_exporters -v
```

Expected: PASS.

## Task 5: CLI and End-to-End Verification

**Files:**
- Create: `logcheck/cli.py`
- Test: `tests/test_cli.py`
- Modify: `docs/course-report-notes.md`

- [ ] **Step 1: Create CLI tests**

Create `tests/test_cli.py`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from logcheck.cli import main


class CliTests(unittest.TestCase):
    def test_cli_exports_requested_reports(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            code = main([
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
            ])
            self.assertEqual(code, 0)
            self.assertTrue((out / "analysis.json").exists())
            self.assertTrue((out / "analysis.csv").exists())
            self.assertTrue((out / "analysis.md").exists())

    def test_cli_missing_file_returns_nonzero(self):
        code = main(["missing.log"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run CLI tests and verify they fail**

Run:

```bash
python -m unittest tests.test_cli -v
```

Expected: FAIL because CLI module does not exist.

- [ ] **Step 3: Implement CLI**

Create `logcheck/cli.py`:

```python
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import sys

from .config import load_config
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
from .parsers import parse_files
from .rules import detect_findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze local logs for intrusion indicators.")
    parser.add_argument("logs", nargs="+", help="Local log files to analyze")
    parser.add_argument("--config", type=Path, help="Optional TOML rule configuration")
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"), help="Directory for exported reports")
    parser.add_argument(
        "--format",
        action="append",
        choices=["json", "csv", "markdown"],
        default=[],
        help="Export format; can be repeated",
    )
    return parser


def _print_summary(result: AnalysisResult) -> None:
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    print("Logcheck analysis summary")
    print(f"Events: {len(result.events)}")
    print(f"Findings: {len(result.findings)}")
    print(f"Severity counts: {dict(severities)}")
    print(f"Top suspicious sources: {sources.most_common(5)}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = [Path(log) for log in args.logs]
    try:
        config = load_config(args.config)
        events = parse_files(paths)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2

    result = AnalysisResult(events=events, findings=detect_findings(events, config))
    _print_summary(result)

    formats = args.format or ["json", "markdown"]
    if "json" in formats:
        export_json(result, args.out_dir / "analysis.json")
    if "csv" in formats:
        export_csv(result, args.out_dir / "analysis.csv")
    if "markdown" in formats:
        export_markdown(result, args.out_dir / "analysis.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Create course report notes**

Create `docs/course-report-notes.md`:

```markdown
# Course Report Notes

## Demo Commands

```bash
python -m logcheck.cli samples/auth.log samples/app.log --out-dir outputs --format json --format csv --format markdown
python -m unittest discover -s tests -v
```

## Report Mapping

- 绪论：说明日志分析在入侵检测中的意义，介绍暴力破解、未授权访问、权限失败等行为。
- 理论基础：说明 Linux auth/syslog 日志格式、关键词检测、阈值关联分析、严重等级分类。
- 系统总体设计：展示 CLI、Parser、Event、Rule Engine、Finding、Exporter 数据流。
- 详细设计与实现：描述 `Event` 和 `Finding` 数据结构、解析规则、关键词规则和暴力破解检测逻辑。
- 测试与结果：使用 `samples/auth.log` 和 `samples/app.log` 展示检测结果，并比较预期输出。
- 总结与展望：说明误报、日志格式覆盖不足，并展望 ELK 仪表盘和实时监控。
```

- [ ] **Step 5: Run full test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 6: Run sample demo command**

Run:

```bash
python -m logcheck.cli samples/auth.log samples/app.log --out-dir outputs --format json --format csv --format markdown
```

Expected: exit code 0 and files `outputs/analysis.json`, `outputs/analysis.csv`, and `outputs/analysis.md` exist.

## Self-Review

- Spec coverage: `log-ingestion` is covered by Task 2; `intrusion-detection-rules` is covered by Task 3; `report-export` is covered by Task 4 and Task 5; `course-deliverables` is covered by samples, tests, and `docs/course-report-notes.md`.
- Placeholder scan: no placeholder tasks are intentionally left for the implementer.
- Type consistency: `Event`, `Finding`, `DetectionConfig`, and `AnalysisResult` are introduced before parser, rules, exporters, and CLI use them.
