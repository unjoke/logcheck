---
change: design-logcheck-desktop-frontend
design-doc: docs/superpowers/specs/2026-06-03-logcheck-desktop-frontend-design.md
base-ref: ba51ebe18f0cf9342e6adfc739131757b8d2ee34
---

# Logcheck Desktop Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Tkinter desktop front end for Logcheck with a black-and-white Codex-inspired workspace.

**Architecture:** Extract reusable analysis orchestration into `logcheck.analysis`, keep `logcheck.cli` behavior-compatible, and add `logcheck.desktop` as a thin Tkinter UI over existing parsers, rules, models, and exporters.

**Tech Stack:** Python 3.11+, standard library `tkinter`, existing Logcheck modules, `unittest`.

---

## File Structure

- Create `logcheck/analysis.py`: reusable analysis orchestration and summary helpers.
- Modify `logcheck/cli.py`: delegate parsing/rule orchestration to `analysis.py` while preserving CLI output and export behavior.
- Create `logcheck/desktop.py`: Tkinter window, file selection, analysis action, findings rendering, and report export actions.
- Modify `pyproject.toml`: add optional `logcheck-desktop` script entry point.
- Create `tests/test_analysis.py`: unit tests for reusable analysis and summary.
- Create `tests/test_desktop.py`: import/smoke tests for desktop constants/helpers without starting `mainloop`.

### Task 1: Extract Reusable Analysis Logic

**Files:**
- Create: `logcheck/analysis.py`
- Modify: `logcheck/cli.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: Write failing analysis tests**

Create `tests/test_analysis.py`:

```python
from pathlib import Path
import unittest

from logcheck.analysis import analyze_logs, summarize_result


class AnalysisTests(unittest.TestCase):
    def test_analyze_logs_returns_events_and_findings(self):
        result = analyze_logs([Path("samples/auth.log"), Path("samples/app.log")])

        self.assertGreater(len(result.events), 0)
        self.assertGreater(len(result.findings), 0)

    def test_summarize_result_counts_findings(self):
        result = analyze_logs([Path("samples/auth.log"), Path("samples/app.log")])
        summary = summarize_result(result)

        self.assertEqual(summary.total_events, len(result.events))
        self.assertEqual(summary.total_findings, len(result.findings))
        self.assertIn("high", summary.findings_by_severity)
        self.assertGreaterEqual(len(summary.top_suspicious_sources), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_analysis -v
```

Expected: FAIL because `logcheck.analysis` does not exist yet.

- [ ] **Step 3: Implement analysis helper**

Create `logcheck/analysis.py`:

```python
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import load_config
from .models import AnalysisResult
from .parsers import parse_files
from .rules import detect_findings


@dataclass(frozen=True)
class AnalysisSummary:
    total_events: int
    total_findings: int
    findings_by_severity: dict[str, int]
    top_suspicious_sources: list[tuple[str, int]]


def analyze_logs(paths: list[Path], config_path: Path | None = None) -> AnalysisResult:
    config = load_config(config_path)
    events = parse_files(paths)
    return AnalysisResult(events=events, findings=detect_findings(events, config))


def summarize_result(result: AnalysisResult) -> AnalysisSummary:
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    return AnalysisSummary(
        total_events=len(result.events),
        total_findings=len(result.findings),
        findings_by_severity=dict(severities),
        top_suspicious_sources=sources.most_common(5),
    )
```

- [ ] **Step 4: Update CLI to use helper**

Modify `logcheck/cli.py` imports and logic:

```python
from .analysis import analyze_logs, summarize_result
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
```

Update `_print_summary`:

```python
def _print_summary(result: AnalysisResult) -> None:
    summary = summarize_result(result)
    print("Logcheck analysis summary")
    print(f"Events: {summary.total_events}")
    print(f"Findings: {summary.total_findings}")
    print(f"Severity counts: {summary.findings_by_severity}")
    print(f"Top suspicious sources: {summary.top_suspicious_sources}")
```

Update `main()`:

```python
    try:
        result = analyze_logs(paths, args.config)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2
```

Remove now-unused imports from `cli.py`: `Counter`, `load_config`, `parse_files`, and `detect_findings`.

- [ ] **Step 5: Run focused and existing tests**

Run:

```powershell
python -m unittest tests.test_analysis tests.test_cli -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```powershell
git add logcheck/analysis.py logcheck/cli.py tests/test_analysis.py
git commit -m "refactor: extract reusable log analysis flow"
```

### Task 2: Add Desktop UI Skeleton and Smoke Test

**Files:**
- Create: `logcheck/desktop.py`
- Modify: `pyproject.toml`
- Test: `tests/test_desktop.py`

- [ ] **Step 1: Write desktop smoke test**

Create `tests/test_desktop.py`:

```python
import unittest

from logcheck import desktop


class DesktopTests(unittest.TestCase):
    def test_theme_defines_black_and_white_shell(self):
        self.assertEqual(desktop.BG, "#111111")
        self.assertEqual(desktop.TEXT, "#f3f3f3")
        self.assertIn("local", desktop.LOCAL_MODE_TEXT.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_desktop -v
```

Expected: FAIL because `logcheck.desktop` does not exist yet.

- [ ] **Step 3: Create desktop skeleton**

Create `logcheck/desktop.py` with a Tkinter app class, theme constants, top bar, sidebar, main workspace, status label, and empty result panels. Include:

```python
BG = "#111111"
PANEL = "#1b1b1b"
PANEL_2 = "#242424"
TEXT = "#f3f3f3"
MUTED = "#9a9a9a"
BORDER = "#333333"
ACCENT = "#f5f5f5"
LOCAL_MODE_TEXT = "Local mode - local files only"
```

Define:

```python
class LogcheckDesktop(tk.Tk):
    ...

def main() -> None:
    app = LogcheckDesktop()
    app.mainloop()
```

Use the layout in `worktmp/logcheck_desktop_mockup.py` as the baseline, but write clean UTF-8 English or Chinese strings.

- [ ] **Step 4: Add script entry point**

Modify `pyproject.toml`:

```toml
[project.scripts]
logcheck = "logcheck.cli:main"
logcheck-desktop = "logcheck.desktop:main"
```

- [ ] **Step 5: Run desktop smoke test**

Run:

```powershell
python -m unittest tests.test_desktop -v
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```powershell
git add logcheck/desktop.py pyproject.toml tests/test_desktop.py
git commit -m "feat: add desktop window skeleton"
```

### Task 3: Wire File Selection and Analysis Rendering

**Files:**
- Modify: `logcheck/desktop.py`
- Test: `tests/test_desktop.py`

- [ ] **Step 1: Add row formatting tests**

Append to `tests/test_desktop.py`:

```python
from logcheck.models import Finding


class DesktopFormattingTests(unittest.TestCase):
    def test_format_finding_row_includes_core_fields(self):
        finding = Finding(
            rule_id="keyword.failed_login",
            severity="medium",
            explanation="Matched intrusion indicator keyword: failed password",
            evidence=["Failed password for root"],
            source_file="samples/auth.log",
            line_number=4,
            source_address="192.0.2.10",
            actor="root",
        )

        row = desktop.format_finding_row(finding)

        self.assertEqual(row.severity, "MEDIUM")
        self.assertIn("192.0.2.10", row.title)
        self.assertIn("failed password", row.subtitle.lower())
        self.assertEqual(row.location, "samples/auth.log:4")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest tests.test_desktop -v
```

Expected: FAIL because `format_finding_row` does not exist yet.

- [ ] **Step 3: Add formatting helper and UI state**

In `logcheck/desktop.py`, add:

```python
@dataclass(frozen=True)
class FindingRow:
    severity: str
    title: str
    subtitle: str
    location: str


def format_finding_row(finding: Finding) -> FindingRow:
    source = finding.source_address or finding.actor or "unknown"
    return FindingRow(
        severity=finding.severity.upper(),
        title=f"{source} - {finding.rule_id}",
        subtitle=finding.explanation,
        location=f"{finding.source_file}:{finding.line_number}",
    )
```

Add instance fields for selected paths and latest result:

```python
self.selected_paths: list[Path] = []
self.latest_result: AnalysisResult | None = None
```

- [ ] **Step 4: Add file picker and run action**

In `LogcheckDesktop`, add buttons for selecting local files and running analysis. Use `tkinter.filedialog.askopenfilenames()` and call `analyze_logs(self.selected_paths)`. Catch `OSError` and show the error in the status label.

- [ ] **Step 5: Render summary and findings**

After successful analysis, use `summarize_result()` to update card labels and rebuild finding rows using `format_finding_row()`.

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m unittest tests.test_desktop tests.test_analysis tests.test_cli -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```powershell
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "feat: render desktop analysis results"
```

### Task 4: Add Desktop Export Controls

**Files:**
- Modify: `logcheck/desktop.py`

- [ ] **Step 1: Add export state behavior**

In `LogcheckDesktop`, keep export buttons disabled or status-blocked until `self.latest_result` is not `None`.

- [ ] **Step 2: Add output directory chooser**

Use `tkinter.filedialog.askdirectory()` to choose a local output directory. If the user cancels, keep the window open and set status text to `Export cancelled`.

- [ ] **Step 3: Reuse existing exporters**

When export is requested, call:

```python
export_json(self.latest_result, out_dir / "analysis.json")
export_csv(self.latest_result, out_dir / "analysis.csv")
export_markdown(self.latest_result, out_dir / "analysis.md")
```

Show status text containing the output directory.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```powershell
git add logcheck/desktop.py
git commit -m "feat: export reports from desktop UI"
```

### Task 5: Manual Verification and Task Closure

**Files:**
- Modify: `openspec/changes/design-logcheck-desktop-frontend/tasks.md`

- [ ] **Step 1: Launch desktop window**

Run:

```powershell
python -m logcheck.desktop
```

Expected: A native desktop window opens with black-and-white Logcheck layout and local-mode status.

- [ ] **Step 2: Analyze sample logs**

In the window, select:

```text
samples/auth.log
samples/app.log
```

Run analysis. Expected: summary metrics and finding rows update with real results.

- [ ] **Step 3: Export reports**

Export reports to a temporary output directory. Expected: `analysis.json`, `analysis.csv`, and `analysis.md` are created.

- [ ] **Step 4: Run full test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 5: Mark OpenSpec tasks complete**

Update `openspec/changes/design-logcheck-desktop-frontend/tasks.md` by changing each implemented checkbox from `- [ ]` to `- [x]`.

- [ ] **Step 6: Commit Task 5**

```powershell
git add openspec/changes/design-logcheck-desktop-frontend/tasks.md
git commit -m "chore: complete desktop frontend tasks"
```

## Self-Review

- Spec coverage: desktop window, black-and-white visual style, local file analysis, summary display, finding details, report export, and local-only safety boundary are all covered.
- Placeholder scan: no placeholder-only steps remain.
- Type consistency: `AnalysisSummary`, `FindingRow`, `analyze_logs`, `summarize_result`, and `LogcheckDesktop` are consistently named across tasks.
