---
comet_change: rebuild-web-frontend
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-09-rebuild-web-frontend
status: final
---

# Rebuild Web Frontend Technical Design

## Context

Logcheck is moving from a GUI frontend direction to a browser-based local web application. OpenSpec remains the canonical requirement source for this change. The selected application shape is **Local Investigation Dashboard**.

The current backend already has a useful boundary for the web layer:
- `logcheck.analysis.analyze_logs(paths, config_path)` accepts local paths and returns `AnalysisResult`.
- `AnalysisResult` contains events, findings, diagnostics, and generated insights.
- `logcheck.exporters.export_json`, `export_csv`, and `export_markdown` write supported reports from an `AnalysisResult`.
- CLI behavior already proves the local analysis and export pipeline can run without GUI coupling.

The private CTF environment redirects domains to `192.168.2.1`, so the web frontend must remain a local file analysis surface. It must not introduce domain, URL, scan, blocking, exploitation, remote upload, or external reporting workflows.

## Selected UX

The first implementation will be a single-page **Local Investigation Dashboard**. The first screen is the working product surface, not a landing page.

Primary dashboard regions:
- **Source intake:** upload local log files and select bundled sample logs.
- **Analysis summary:** total events, findings, severity distribution, risk headline, and top suspicious sources.
- **Finding queue:** sortable or filterable list of findings with severity, rule id, source, and actor/address when available.
- **Evidence detail:** selected finding with raw evidence, source file, line number, actor, target, source address, matched keyword, and explanation.
- **Insights:** risk headline, entity profiles, timeline, and suggestions from the local insight layer.
- **Exports:** JSON, CSV, and Markdown export actions for the latest analysis result.

The layout should be dense and operational rather than decorative. It should use restrained color, clear table/list hierarchy, compact panels, and stable regions that remain readable on desktop and mobile-width verification viewports.

## Architecture

Use a small local web server plus a browser UI.

The server responsibilities:
- Serve the dashboard assets.
- Accept uploaded local log files into a temporary local workspace.
- List bundled sample logs from an approved project directory.
- Run `analyze_logs()` with selected local paths and optional local rule config support if retained.
- Serialize `AnalysisResult` into web-friendly JSON.
- Invoke existing exporters for report download or local report generation.

The frontend responsibilities:
- Maintain dashboard state: selected inputs, analysis status, latest result, selected finding, and export state.
- Render analysis results without duplicating detection logic.
- Keep all controls local-only.
- Avoid any browser behavior that fetches external URLs for analysis.

Suggested data flow:

```text
User selects local files or samples
        |
        v
Local web API validates local inputs
        |
        v
analyze_logs(paths, config_path)
        |
        v
AnalysisResult + insights
        |
        v
Dashboard JSON response
        |
        v
Summary, findings, evidence, insights, exports
```

## API Shape

The implementation can choose exact routes during build, but the design expects these boundaries:
- `GET /api/samples`: list approved bundled sample logs.
- `POST /api/analyze`: accept uploaded files and/or sample ids, run local analysis, return result JSON.
- `GET /api/exports/<format>` or `POST /api/export`: export the latest or addressed analysis result in `json`, `csv`, or `markdown`.
- `GET /api/health`: support dev server and smoke-test checks.

Server responses should expose only the fields needed by the dashboard: metadata, diagnostics, findings, insights, events when needed for source context, and export availability. Internal paths should be displayed carefully; prefer user-facing filenames unless full local paths are necessary for diagnostics.

## Safety Rules

The dashboard must not include:
- URL or domain inputs.
- Remote upload destinations.
- Network scan or fetch buttons.
- Blocking, exploitation, or external reporting controls.
- Any dependency on internet access for analysis.

Tests should assert these forbidden controls are absent by visible text, labels, and common placeholder strings.

## Testing Strategy

Backend/API tests:
- Analyze uploaded local logs.
- Analyze bundled sample logs.
- Analyze a mixed uploaded plus sample selection.
- Report pre-analysis export errors.
- Export JSON, CSV, and Markdown from an existing result.
- Reject missing, invalid, or empty local inputs with clear diagnostics.

Frontend tests:
- First screen renders the dashboard, not a landing page.
- Source intake, summary, finding queue, evidence detail, insights, and export regions are present.
- Analysis result rendering includes source context fields when available.
- Forbidden remote controls are absent.

Browser verification:
- Run the local web app.
- Capture desktop and mobile-width views.
- Confirm the dashboard is nonblank, non-overlapping, readable, and uses the selected Local Investigation Dashboard layout.

Regression coverage:
- Keep existing parser, rule, analysis, insight, exporter, and CLI tests.
- Replace desktop-focused tests with web/API-focused tests during implementation.

## Migration Plan

1. Add web server and dashboard structure.
2. Add uploaded-file and sample-log input handling.
3. Connect analysis and result serialization.
4. Connect export actions.
5. Add API, frontend, safety, and browser verification tests.
6. Remove or deprecate PyQt dependency, `logcheck.desktop`, `tests/test_desktop.py`, and the `logcheck-desktop` entry point once replacement coverage is in place.

Rollback is straightforward: remove the web entry point and restore the GUI entry point/dependency if the web direction is abandoned before archive.

## Edge Cases

- No inputs selected: show a clear local input error.
- Uploaded file is empty or unreadable: preserve backend diagnostics and keep readable inputs usable.
- Sample log path is missing: return a local sample diagnostic instead of failing the whole page.
- Analysis produces no findings: show an empty finding queue with event counts and export availability.
- Export requested before analysis: show an export-disabled state or explicit pre-analysis error.

## Spec Patch

No additional delta spec patch is needed. The current OpenSpec delta already covers the selected Dashboard direction, local analysis workflow, local-only safety boundary, exports, and web verification.
