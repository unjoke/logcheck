## Context

`LogcheckDesktop` is a PyQt6 local desktop UI that currently lets users choose local files, run analysis, view summary/finding details, and export JSON/CSV/Markdown for the latest result. The left navigation includes a Course Demo section from earlier course-oriented work, a basic Log Sources section, and a Detection Rules section that only displays static labels. Export always uses `latest_result`, so previous runs cannot be selected by time.

## Goals / Non-Goals

**Goals:**

- Make Log Sources useful for folder-backed local logs and per-file selection.
- Let users analyze either selected source files or ad hoc standalone files from the computer.
- Remove the Course Demo section from navigation and workspace setup.
- Present detection rule details from the existing local `DetectionConfig`.
- Store timestamped analysis runs in the desktop session and export a selected run.
- Keep all actions local-only.

**Non-Goals:**

- Change parser behavior, detection logic, exporter formats, or CLI behavior.
- Persist analysis history across app restarts.
- Recursively crawl folders by default.
- Add remote sources, URLs, uploads, monitoring daemons, or network behavior.

## Decisions

### Model UI Log Sources as Local Path Entries

The desktop window will track a folder source and a derived list of regular files under that folder. Folder selection uses `QFileDialog.getExistingDirectory()`. The default folder mode includes all files directly inside the folder and excludes subdirectories.

Alternative considered: recursive folder crawling. This was rejected for the default behavior because it can unexpectedly include too much data and complicates course/demo expectations.

### Keep Analysis Selection in the UI Layer

Analysis will still call `analyze_logs(paths)`. The desktop UI decides which `Path` list to pass:

- selected files from the configured folder source
- standalone files chosen from the computer

This keeps the analysis pipeline stable and makes the change frontend-scoped.

### Store Session Analysis History In Memory

Add a small session history list on `LogcheckDesktop`, storing timestamp label, selected paths, and `AnalysisResult`. Each successful analysis appends one entry and updates export controls. Export chooses the selected history entry instead of implicitly using only `latest_result`.

Alternative considered: write history metadata to disk. Rejected because the request only needs choosing among runs in the current UI flow and persistent history would expand scope.

### Render Rule Details from Existing Config

The Detection Rules section should read from `default_config()` or `load_config(None)` and display keyword groups plus brute-force threshold/window. This avoids duplicating rule definitions in UI text.

### Remove Course Demo Navigation

`nav_demo` will be removed from `NAV_ITEMS`, UI copy, and section construction. Course demo text is no longer part of the production desktop workflow.

## Risks / Trade-offs

- Large folder selection -> Display file count and keep non-recursive default to avoid surprise.
- Empty folders -> Show an empty-state message and prevent analysis until files are selected.
- Multiple report runs -> Use stable timestamp labels and default the export selector to the latest successful run.
- Tests around dialogs -> Patch dialog functions in tests and test helper methods directly where possible.
