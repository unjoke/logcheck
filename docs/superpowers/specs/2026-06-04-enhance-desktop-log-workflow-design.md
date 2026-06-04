---
comet_change: enhance-desktop-log-workflow
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-04-enhance-desktop-log-workflow
status: final
---

# Enhanced Desktop Log Workflow Design

## Context

The canonical requirements are in `openspec/changes/enhance-desktop-log-workflow/specs/desktop-frontend/spec.md`. The current PyQt6 desktop UI supports local file selection, local analysis, result display, and exporting the latest result. It does not yet support folder-backed log sources, per-file source selection, timestamped analysis history, choosing which run to export, or rule details rendered from the local detection configuration. The Course Demo section is now out of scope and should be removed.

## Architecture

Keep the change inside the desktop UI layer. `LogcheckDesktop` will continue to call the existing `analyze_logs(paths)` function and the existing JSON/CSV/Markdown exporters. The UI will own only source discovery, selected file state, session analysis history, and the chosen export target.

The desktop state will expand with:

- `source_folder: Path | None`
- `source_files: list[Path]`
- `selected_source_paths: list[Path]`
- `analysis_history: list[AnalysisRun]`
- `selected_history_index: int | None`

`AnalysisRun` will be a small dataclass containing a timestamp label, input paths, and `AnalysisResult`. It is session-only and is not persisted to disk.

## Data Flow

Folder-backed source analysis:

1. User chooses a local folder.
2. UI lists all regular files directly inside that folder.
3. User selects one or more listed files, or the UI defaults to all listed files when no finer selection is made.
4. `run_analysis()` resolves the selected paths and calls `analyze_logs(paths)`.
5. Successful result is rendered and appended to `analysis_history`.

Standalone file analysis:

1. User chooses one or more local files from the computer.
2. UI sets those paths as the immediate analysis selection.
3. `run_analysis()` calls the same `analyze_logs(paths)` pipeline.

Export:

1. Export section lists timestamped successful analysis runs.
2. User selects a run.
3. `export_reports()` exports JSON, CSV, and Markdown from that selected run.

## UI Decisions

- Remove `nav_demo` from `NAV_ITEMS`, `UI_TEXT`, and section construction.
- Replace the simple Log Sources section with controls for choosing a folder, choosing standalone files, selecting files from the folder source, and displaying current selected paths.
- Replace the static Detection Rules section with text rendered from `default_config()`: keyword groups and brute-force threshold/window.
- Keep export output directory selection local-only, but select the `AnalysisRun` before writing files.

## Risks and Mitigations

- Large folders may create noisy source lists. Mitigation: only include direct regular files by default and show counts/status.
- Empty folders can lead to confusing analysis attempts. Mitigation: show an empty state and block analysis with a clear message.
- In-memory history disappears after restart. This is intentional and matches the requested “choose which run by time” workflow without adding persistence.
- PyQt dialog behavior is hard to test directly. Mitigation: test path resolution and state updates directly, and patch `QFileDialog`/methods in focused tests.

## Test Strategy

- Add failing desktop tests for:
  - folder source discovery includes direct files and excludes subdirectories
  - selected folder files are used for analysis
  - standalone local files can be analyzed without a folder source
  - Course Demo navigation is absent
  - Detection Rules section displays keyword and brute-force configuration
  - successful analysis appends a timestamped history entry
  - export uses a selected historical run
- Run focused desktop tests and then the full `unittest` suite.
