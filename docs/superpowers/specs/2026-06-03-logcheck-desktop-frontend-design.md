---
comet_change: design-logcheck-desktop-frontend
role: technical-design
canonical_spec: openspec
---

# Logcheck Desktop Frontend Technical Design

## Context

This design implements the OpenSpec change `design-logcheck-desktop-frontend`. OpenSpec remains the canonical requirement source; this document records the implementation approach for a local desktop front end with a black-and-white Codex-inspired visual style.

Logcheck currently works as a Python CLI. The core flow is:

```text
local log paths
  -> logcheck.parsers.parse_files()
  -> logcheck.rules.detect_findings()
  -> logcheck.models.AnalysisResult
  -> logcheck.exporters
```

The desktop front end should reuse that flow. It should not duplicate parsing or detection logic, and it must not introduce any URL, domain scan, remote upload, blocking, or exploitation controls.

## Architecture

The implementation should split analysis orchestration from UI rendering:

```text
logcheck.analysis
  owns reusable local analysis and summary helpers

logcheck.cli
  parses command-line args and calls logcheck.analysis

logcheck.desktop
  owns Qt window, local file selection, run action, result rendering, and export actions
```

The desktop UI remains a thin local shell. It calls reusable analysis functions, stores the latest `AnalysisResult` in memory, renders summary metrics and finding rows, and calls existing exporters for JSON/CSV/Markdown output.

## Components

### Analysis Module

Create `logcheck.analysis` to hold reusable orchestration that currently lives in `cli.py`.

It should expose:

- `analyze_logs(paths, config_path=None) -> AnalysisResult`
- `summarize_result(result) -> AnalysisSummary`

`AnalysisSummary` should include total events, total findings, findings by severity, and top suspicious sources. CLI and desktop should both use this helper so displayed counts stay consistent.

### CLI

`logcheck.cli.main()` should remain behavior-compatible. It should parse arguments, call `analyze_logs()`, print the same summary, and call the existing exporters. Existing CLI tests should continue to pass.

### Desktop UI

Create `logcheck.desktop` as a PyQt6/Qt app. The production version should favor Qt because the user requested a clearer, more polished Chinese desktop window than the first Tkinter implementation could comfortably provide.

The window should refine `worktmp/logcheck_desktop_mockup.py`:

- top menu with Logcheck identity and local-mode status
- left navigation for overview, log sources, detection rules, suspicious sources, export report, and course demo
- main overview title, selected local files, and run action
- summary cards for events, findings, high/critical count, and suspicious sources
- finding queue with severity, source, rule/explanation, evidence location
- right-side detail panel for selected finding, loaded logs, rule status, and export actions

The UI should not use a browser or local web server.

### Export Flow

Desktop export controls should reuse `export_json`, `export_csv`, and `export_markdown`. If no analysis has been run, export controls should show a clear in-window status instead of writing empty reports.

### Error Handling

Missing files, unreadable files, and exporter errors should be shown in the UI status area. The window should remain open after errors. Malformed log lines remain the parser's responsibility and should continue to be represented as unknown events.

## Key Decisions

### PyQt6/Qt for the Production Version

PyQt6 is selected because it provides sharper widgets, better layout control, richer styling, and a more professional native desktop feel. This introduces one third-party dependency, but it directly supports the requested clarity improvement and keeps the application local-only. PySide6 was considered first, but installation repeatedly timed out in this environment; PyQt6 installed successfully and still satisfies the Qt requirement.

### Reusable Analysis Helper Before UI Work

The CLI currently owns orchestration. Extracting a small analysis helper first prevents UI code from importing CLI argument parsing and keeps analysis behavior consistent across CLI and desktop.

### Black-and-White Functional Workspace

The UI should be dense and work-focused. The first screen is the actual analysis workspace, not a landing page or tutorial. Visual polish should come from spacing, typography, dark panels, and light contrast rather than gradients, decorative imagery, or colorful dashboards.

### Local-Only Safety Boundary

The front end must make local mode visible and expose only local file and local report actions. There should be no text input for remote hosts, URLs, domains, or upload endpoints.

## Testing Strategy

Tests should cover analysis reuse without testing Qt internals heavily:

- `tests/test_analysis.py` verifies `analyze_logs()` returns events/findings for sample logs.
- `tests/test_analysis.py` verifies `summarize_result()` returns stable counts and top sources.
- Existing CLI tests verify the extraction did not break command-line behavior.
- A desktop smoke test can import `logcheck.desktop` without launching `mainloop`.
- Manual verification launches the desktop window, runs sample log analysis, checks readable black-and-white layout, and exports reports.

## Risks and Mitigations

- Qt dependency size -> Keep the dependency explicit in `pyproject.toml` and preserve the CLI so the core tool still runs independently.
- Encoding problems in the temporary mockup -> Treat it as layout reference and write production source as UTF-8.
- CLI regression during extraction -> Add analysis helper tests before changing CLI.
- UI logic grows too large -> Keep data summarization in `analysis.py` and small formatting helpers; keep Qt event handlers thin.
- Safety boundary drift -> Add tests or manual checks that UI labels/actions only reference local files and local exports.

## Acceptance Notes

The design is complete when a local desktop window can be launched, sample logs can be selected and analyzed, summary cards and finding rows update from real `AnalysisResult` data, JSON/CSV/Markdown exports work, existing tests pass, and the UI contains no remote-target or network-action controls.
