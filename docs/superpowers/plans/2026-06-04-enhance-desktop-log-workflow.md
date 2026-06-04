---
change: enhance-desktop-log-workflow
design-doc: docs/superpowers/specs/2026-06-04-enhance-desktop-log-workflow-design.md
base-ref: f753048e9343b7f41aba81318bd2012b9746991d
archived-with: 2026-06-04-enhance-desktop-log-workflow
---

# Enhanced Desktop Log Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the PyQt desktop workflow so log sources support folders, analysis can use selected source files or standalone files, rules are visible, history-based export works, and Course Demo is removed.

**Architecture:** Keep parser, analysis, and exporter modules unchanged. Add small desktop-only state objects and helper methods in `logcheck/desktop.py`, with focused regression tests in `tests/test_desktop.py`.

**Tech Stack:** Python 3.12, PyQt6, `unittest`.

archived-with: 2026-06-04-enhance-desktop-log-workflow
---

### Task 1: Source Discovery and Navigation Tests

**Files:**
- Modify: `tests/test_desktop.py`

- [x] **Step 1: Write failing folder source tests**

Add tests that create a temporary folder with two files and one subdirectory. Assert that folder discovery returns only direct files and updates desktop source state.

- [x] **Step 2: Write failing navigation removal test**

Assert that `desktop.NAV_ITEMS` and `window.nav_buttons` do not include `nav_demo`.

- [x] **Step 3: Run focused tests to verify failure**

Run:

```bash
python -m unittest tests.test_desktop -v
```

Expected before implementation: new tests fail because source discovery helpers and navigation removal are not implemented.

### Task 2: Source Selection Implementation

**Files:**
- Modify: `logcheck/desktop.py`

- [x] **Step 1: Add source state**

Add desktop fields for `source_folder`, `source_files`, `selected_source_paths`, and standalone selected paths.

- [x] **Step 2: Add folder discovery helper**

Implement a helper that returns sorted direct regular files for a folder.

- [x] **Step 3: Add selection resolution helper**

Implement a helper that returns selected source paths when present, otherwise standalone paths, otherwise all folder files when no narrower selection exists.

- [x] **Step 4: Remove Course Demo**

- [x] **Step 5: Add actionable source controls**

Add Log Sources page controls for choosing a source folder, choosing standalone files, and selecting folder files with checkboxes.

Remove `nav_demo` from navigation and section construction.

### Task 3: Analysis, Rules, and Export Tests

**Files:**
- Modify: `tests/test_desktop.py`

- [x] **Step 1: Write failing selected-source analysis test**

Patch `logcheck.desktop.analyze_logs`, configure selected source paths, call `run_analysis()`, and assert analysis uses those paths.

- [x] **Step 2: Write failing standalone analysis test**

Patch `QFileDialog.getOpenFileNames()` or the desktop helper, choose standalone files, run analysis, and assert the chosen paths are used.

- [x] **Step 3: Write failing rules display test**

Assert Detection Rules content includes configured keyword group names, indicator terms, brute-force threshold, and time window.

- [x] **Step 4: Write failing history export test**

Create two analysis runs, select the earlier one, patch exporters, call `export_reports()`, and assert exporters receive the selected historical result.

### Task 4: Analysis, Rules, and Export Implementation

**Files:**
- Modify: `logcheck/desktop.py`

- [x] **Step 1: Add `AnalysisRun` dataclass**

Store timestamp label, input paths, and `AnalysisResult`.

- [x] **Step 2: Update analysis flow**

Resolve input paths through the new helper, run existing `analyze_logs()`, append a timestamped `AnalysisRun`, and refresh UI/history labels.

- [x] **Step 3: Render rules from config**

Build rules section content from `default_config()` rather than static labels.

- [x] **Step 4: Update export flow**

- [x] **Step 5: Add export history selection control**

Add an export history selector so the chosen timestamped run drives report export.

Select an analysis history entry for export and pass that result to existing JSON/CSV/Markdown exporters.

### Task 5: Verification and Delivery

**Files:**
- Modify: `openspec/changes/enhance-desktop-log-workflow/tasks.md`
- Create: `docs/superpowers/reports/2026-06-04-enhance-desktop-log-workflow-verify.md`

- [x] **Step 1: Run focused desktop tests**

Run:

```bash
python -m unittest tests.test_desktop -v
```

Expected: all desktop tests pass.

- [x] **Step 2: Run full test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Complete Comet and PR delivery**

Run Comet build/verify/archive guards, commit changes, push `codex/enhance-desktop-log-workflow`, and create a PR against `unjoke/logcheck.git`.
