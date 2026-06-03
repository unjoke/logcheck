## Context

Logcheck is currently a Python-based local log analysis tool. It reads local log files, normalizes events, detects intrusion indicators, and exports JSON/CSV/Markdown reports. The requested front end is a desktop software window, not a web application. The visual direction is a restrained black-and-white interface inspired by the Codex desktop screenshot and the existing `worktmp/logcheck_desktop_mockup.py` prototype.

The front end is primarily for course demonstration, screenshots, and easier review of analysis results. It must preserve the project's safety boundary: analyze local logs only, with no network scanning, blocking, exploitation, or remote reporting.

## Goals / Non-Goals

**Goals:**

- Provide a desktop application window that feels like a real Logcheck software interface.
- Use a black-and-white visual system with subtle gray panels, compact spacing, and clear information hierarchy.
- Let users select local log files, start analysis, inspect summary metrics, review findings, see evidence references, and export reports.
- Make the UI suitable for course screenshots and live demonstrations.
- Keep the future implementation compatible with the existing Python analysis pipeline.

**Non-Goals:**

- Build a web app or browser-based dashboard.
- Add real-time monitoring, remote telemetry, network scanning, exploit execution, or automated blocking.
- Redesign the core parser, rule engine, or exporter behavior.
- Replace the CLI; the desktop UI should complement it.

## Decisions

### Use a Desktop Shell Instead of a Web Front End

The interface SHALL be implemented as a local desktop window. A future implementation may use Python desktop tooling such as Tkinter, PySide, or CustomTkinter, but the product surface must remain a native window rather than a browser page.

Alternative considered: a web dashboard. This was rejected because the user explicitly asked for a software window and because local-only desktop presentation better matches the project's security constraints.

### Use the Mockup as the Visual Baseline

`worktmp/logcheck_desktop_mockup.py` establishes the first acceptable visual direction: dark shell, left navigation, top menu, overview cards, alert list, and right-side log/rule/export panel. The production UI should refine that structure rather than restart from an unrelated layout.

Alternative considered: a terminal-like single pane. This would be simpler, but it would not communicate the tool's workflow as clearly in screenshots.

### Keep the UI Information-Dense and Demonstration-Friendly

The UI should avoid landing-page composition. The first screen is the actual analysis workspace: file inputs, run action, metrics, findings, and export actions. Text should be concise and functional, with no in-app tutorial copy.

Alternative considered: a wizard flow. This can help beginners, but it hides the summary and findings behind steps, which is weaker for classroom demonstration.

### Bind UI State to Existing Analysis Results

The desktop UI should call the existing local analysis path, then render structured output from the result model or JSON export. It should show:

- total parsed events
- finding counts by severity
- top suspicious sources
- findings with rule, severity, source, target, evidence, and source file reference
- export status for JSON, CSV, and Markdown

This keeps the front end thin and reduces the chance of diverging from CLI behavior.

### Preserve Local-Only Safety Constraints

The UI SHALL make local mode visible and SHALL NOT provide fields or actions for URLs, remote hosts, domain scans, attack actions, or remote upload. Any future file picker should accept local files only.

## Risks / Trade-offs

- UI toolkit mismatch -> Choose the toolkit after confirming packaging needs; keep the spec focused on behavior and layout.
- Mockup encoding issues -> Treat the mockup as layout reference, and write production UI strings in UTF-8 source files.
- Overbuilding visual polish -> Prioritize a stable demo window, readable results, and export workflow before animations or advanced theming.
- Divergence from CLI analysis -> Render data returned by existing analysis/export modules instead of duplicating detection logic in the UI.

## Migration Plan

1. Keep the CLI unchanged.
2. Add the desktop front end as a separate entry point or module.
3. Use sample logs for initial demo data and screenshots.
4. Wire the UI to existing analysis functions.
5. Validate with unit tests for data mapping and manual screenshot checks for visual layout.

Rollback is straightforward: remove or ignore the desktop entry point while retaining the existing CLI.

## Open Questions

- Which desktop toolkit should be used for the production version: Tkinter for zero dependencies, or a richer toolkit for more polished controls?
- Should the production front end be packaged as a standalone executable, or is running through Python acceptable for the course demo?
