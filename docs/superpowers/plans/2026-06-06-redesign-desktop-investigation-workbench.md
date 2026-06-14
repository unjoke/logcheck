---
change: redesign-desktop-investigation-workbench
design-doc: docs/superpowers/specs/2026-06-06-redesign-desktop-investigation-workbench-design.md
base-ref: a01dacff967709fcbf9fdb794ff0794ea88b0762
archived-with: 2026-06-07-redesign-desktop-investigation-workbench
---

# Redesign Desktop Investigation Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the PyQt desktop first screen into a local-only investigation workbench with source, log viewer, rule/context, and output regions.

**Architecture:** Keep the existing PyQt desktop entry point and analysis backend. Refactor `LogcheckDesktop` UI construction into pane-specific helpers while preserving existing methods for source selection, analysis, insights, history, and exports.

**Tech Stack:** Python 3.11+, PyQt6, unittest, existing `logcheck` modules.

archived-with: 2026-06-07-redesign-desktop-investigation-workbench
---

## File Structure

- Modify: `tests/test_desktop.py`
  - Add behavior-first tests for the workbench shell, local-only controls, source diagnostics, log viewer, finding detail, and export placement.
  - Update old navigation-specific assertions that conflict with the workbench-first layout.
- Modify: `logcheck/desktop.py`
  - Add workbench UI text keys and pane object names.
  - Replace the page-first shell with a top command bar plus four persistent workbench regions.
  - Preserve existing public methods used by tests and scripts: `choose_logs`, `choose_source_folder`, `set_log_source_folder`, `set_log_source_folders`, `run_analysis`, `import_rule_file`, `export_reports`, `_render_result`, `_show_finding_detail`.
  - Add focused helper methods such as `_build_workbench_shell`, `_build_source_pane`, `_build_log_viewer_pane`, `_build_rule_context_pane`, `_build_output_pane`, `_refresh_log_viewer`, and `_refresh_workbench_sources`.
- Optional Modify: `README.md`
  - Only update if the old desktop workflow instructions become misleading.

## Task 1: Lock The Workbench Layout Contract

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Add a failing first-screen region test**

Add this test to `DesktopTests`:

```python
def test_first_screen_exposes_investigation_workbench_regions(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()

    self.assertIsNotNone(window.findChild(QLabel, "sourcePaneTitle"))
    self.assertIsNotNone(window.findChild(QLabel, "logViewerPaneTitle"))
    self.assertIsNotNone(window.findChild(QLabel, "ruleContextPaneTitle"))
    self.assertIsNotNone(window.findChild(QLabel, "outputPaneTitle"))
    self.assertTrue(hasattr(window, "source_pane"))
    self.assertTrue(hasattr(window, "log_viewer_pane"))
    self.assertTrue(hasattr(window, "rule_context_pane"))
    self.assertTrue(hasattr(window, "output_pane"))

    window.close()
```

- [ ] **Step 2: Add a failing local-only safety test for the workbench**

Add or update the existing remote-control test so it reads the whole workbench:

```python
def test_workbench_omits_remote_or_destructive_controls(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()

    visible_text = " ".join(
        [button.text() for button in window.findChildren(QPushButton)]
        + [label.text() for label in window.findChildren(QLabel)]
    )

    for forbidden in ["URL", "域名", "上传", "扫描", "封禁", "利用", "远程"]:
        self.assertNotIn(forbidden, visible_text)

    window.close()
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
pytest tests/test_desktop.py -q
```

Expected: fail because the new pane attributes/object names do not exist yet.

- [ ] **Step 4: Mark task progress**

After the failing tests are committed or ready for the next implementation task, update:

```markdown
- [x] 1.1 Add or update desktop tests that assert the first screen exposes the workbench regions: local sources, log viewer, rule/context panel, and findings/evidence/history area.
- [x] 1.2 Add desktop tests that assert remote controls are absent, including URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, and external reporting controls.
```

in `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "test: lock desktop workbench layout contract"
```

## Task 2: Build The Workbench Shell

**Files:**
- Modify: `logcheck/desktop.py`
- Modify: `tests/test_desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Add UI text keys and pane names**

In `UI_TEXT`, add keys equivalent to:

```python
"workbench_tab": "调查",
"source_pane": "日志源",
"log_viewer_pane": "日志查看器",
"rule_context_pane": "规则上下文",
"output_pane": "分析输出",
"evidence_detail": "证据详情",
"analysis_history": "历史记录",
"local_export": "本地导出",
"empty_log_viewer": "选择本地日志并运行分析后查看事件证据。",
```

- [ ] **Step 2: Replace the shell composition with a workbench builder**

Update `_build_shell()` so the central widget is a workbench layout. Preserve existing menu/action setup if present, but route the primary visible UI through:

```python
def _build_shell(self) -> None:
    root = QWidget()
    root_layout = QVBoxLayout(root)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    root_layout.addWidget(self._build_workbench_topbar())
    root_layout.addWidget(self._build_workbench_body(), 1)

    self.setCentralWidget(root)
    self.status_label = QLabel(UI_TEXT["status_start"])
    root_layout.addWidget(self.status_label)
```

Keep compatibility attributes that existing methods use, such as `status_label`, `logs_label`, `rules_section_label`, `detail_label`, `detail_scroll`, `export_history_combo`, and `source_file_checks`.

- [ ] **Step 3: Implement the four persistent pane helpers**

Create helper methods with stable attributes and object names:

```python
def _build_workbench_body(self) -> QWidget:
    body = QWidget()
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(12, 12, 12, 12)
    body_layout.setSpacing(10)

    upper = QHBoxLayout()
    self.source_pane = self._build_source_pane()
    self.log_viewer_pane = self._build_log_viewer_pane()
    self.rule_context_pane = self._build_rule_context_pane()
    upper.addWidget(self.source_pane, 2)
    upper.addWidget(self.log_viewer_pane, 5)
    upper.addWidget(self.rule_context_pane, 2)

    self.output_pane = self._build_output_pane()
    body_layout.addLayout(upper, 4)
    body_layout.addWidget(self.output_pane, 2)
    return body
```

Each pane title label must set the object name used by tests:

```python
title = QLabel(UI_TEXT["source_pane"])
title.setObjectName("sourcePaneTitle")
```

- [ ] **Step 4: Run layout tests**

Run:

```bash
pytest tests/test_desktop.py::DesktopTests::test_first_screen_exposes_investigation_workbench_regions -q
pytest tests/test_desktop.py::DesktopTests::test_workbench_omits_remote_or_destructive_controls -q
```

Expected: pass.

- [ ] **Step 5: Mark task progress**

Update `tasks.md`:

```markdown
- [x] 2.1 Replace the current primary desktop shell composition with a workbench layout using stable left, center, right, and bottom regions.
```

- [ ] **Step 6: Commit**

```bash
git add logcheck/desktop.py tests/test_desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "feat: introduce desktop investigation workbench shell"
```

## Task 3: Move Source And Rule Workflows Into Panes

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Add a source diagnostics test**

Add a test that drives existing source setup and checks the left pane:

```python
def test_workbench_source_pane_updates_selected_sources(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "auth.log"
        second = root / "app.log"
        first.write_text("auth", encoding="utf-8")
        second.write_text("app", encoding="utf-8")

        window.set_log_source_folder(root)

        self.assertIn("auth.log", window.sources_section_label.text())
        self.assertIn("app.log", window.sources_section_label.text())
        self.assertEqual(len(window.source_file_checks), 2)

    window.close()
```

- [ ] **Step 2: Ensure source controls live in the source pane**

Build source import buttons, source summary label, diagnostics label, and checkbox container inside `_build_source_pane()`. Keep `sources_section_label` as the summary label so existing tests and methods keep working.

- [ ] **Step 3: Ensure rule controls live in the right pane**

Build `rules_section_label`, import-rule button, and save-rule button inside `_build_rule_context_pane()`. Keep `import_rule_file()` and `save_active_rule_file()` unchanged unless wiring needs a target refresh.

- [ ] **Step 4: Refresh source and rule pane content**

Update methods that currently refresh old section labels:

```python
def _refresh_source_display(self) -> None:
    # keep existing path resolution behavior
    # update self.logs_label and self.sources_section_label
    # rebuild self.source_file_checks in the source pane
```

Ensure `set_log_source_folder`, `set_log_source_folders`, `choose_logs`, and checkbox toggles still call the refresh path.

- [ ] **Step 5: Run focused tests**

Run:

```bash
pytest tests/test_desktop.py -q
```

Expected: source/rule tests pass or expose old navigation assumptions to update.

- [ ] **Step 6: Mark task progress**

Update `tasks.md`:

```markdown
- [x] 1.3 Add tests for source diagnostics remaining visible while readable files stay analyzable.
- [x] 2.2 Move source selection, selected source state, and source diagnostics into the left source region.
- [x] 2.4 Move local rule status, rule file state, and local threshold/context controls into the right region.
- [x] 3.1 Wire existing import-folder and import-file actions into the workbench source region.
```

- [ ] **Step 7: Commit**

```bash
git add tests/test_desktop.py logcheck/desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "feat: move source and rule workflows into workbench panes"
```

## Task 4: Add Log Viewer And Evidence Output Wiring

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Add a failing log viewer refresh test**

Add:

```python
def test_workbench_log_viewer_renders_analysis_events(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()
    result = AnalysisResult(
        events=[Event("auth.log", 7, "Failed password for root", source_address="192.0.2.10")],
        findings=[],
    )

    window._render_result(result)

    self.assertIn("auth.log", window.log_viewer_label.text())
    self.assertIn("Failed password", window.log_viewer_label.text())

    window.close()
```

- [ ] **Step 2: Add a failing finding-detail linkage test**

Add:

```python
def test_workbench_finding_selection_updates_evidence_detail(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()
    finding = Finding(
        rule_id="keyword.failed_login",
        severity="high",
        explanation="Repeated failed login",
        evidence=["Failed password for root from 192.0.2.10"],
        source_file="auth.log",
        line_number=7,
        source_address="192.0.2.10",
    )

    window._show_finding_detail(finding)

    self.assertIn("Repeated failed login", window.detail_label.text())
    self.assertIn("auth.log", window.detail_label.text())
    self.assertIn("Failed password", window.detail_label.text())

    window.close()
```

- [ ] **Step 3: Implement central log viewer state**

In `_build_log_viewer_pane()`, create:

```python
self.log_viewer_label = QLabel(UI_TEXT["empty_log_viewer"])
self.log_viewer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
self.log_viewer_label.setWordWrap(True)
```

Wrap it in a `QScrollArea` so large result sets do not resize the shell.

- [ ] **Step 4: Implement `_refresh_log_viewer`**

Add:

```python
def _refresh_log_viewer(self, result: AnalysisResult | None = None) -> None:
    if result is None or not result.events:
        self.log_viewer_label.setText(UI_TEXT["empty_log_viewer"])
        return

    finding_locations = {
        (finding.source_file, finding.line_number)
        for finding in result.findings
        if finding.source_file and finding.line_number is not None
    }
    lines = []
    for event in result.events[:200]:
        marker = "!" if (event.source_file, event.line_number) in finding_locations else " "
        lines.append(f"{marker} {event.source_file}:{event.line_number}  {event.message}")
    self.log_viewer_label.setText("\n".join(lines))
```

Call it from `_render_result(result)`.

- [ ] **Step 5: Keep detail output in the bottom pane**

Ensure `_show_finding_detail()` writes to the existing `detail_label` inside `_build_output_pane()`. Include severity, rule, source location, actor/source address when present, and all evidence lines.

- [ ] **Step 6: Run focused tests**

Run:

```bash
pytest tests/test_desktop.py::DesktopTests::test_workbench_log_viewer_renders_analysis_events -q
pytest tests/test_desktop.py::DesktopTests::test_workbench_finding_selection_updates_evidence_detail -q
pytest tests/test_desktop.py::DesktopTests::test_finding_detail_area_is_scrollable_for_long_evidence -q
```

Expected: pass.

- [ ] **Step 7: Mark task progress**

Update `tasks.md`:

```markdown
- [x] 1.4 Add tests for finding selection driving evidence detail in the workbench output area.
- [x] 2.3 Add the central log viewer surface with stable row styling, empty state, and room for highlighted finding rows.
- [x] 2.5 Move findings, selected evidence detail, analysis history, and local export actions into the bottom output region.
- [x] 3.3 Refresh source counts, diagnostics, log viewer rows, findings, insights, history, and export availability after analysis completes.
- [x] 3.4 Link finding selection to highlighted log evidence and detail content where parsed event data is available.
```

- [ ] **Step 8: Commit**

```bash
git add tests/test_desktop.py logcheck/desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "feat: add workbench log viewer and evidence output"
```

## Task 5: Preserve Analysis, History, And Export Behavior

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Update export placement test**

Replace old overview/export page assumptions with bottom output expectations:

```python
def test_workbench_output_region_contains_local_export_action(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()

    output_buttons = window.output_pane.findChildren(QPushButton)
    self.assertIn(desktop.UI_TEXT["export"], [button.text() for button in output_buttons])

    window.close()
```

- [ ] **Step 2: Keep export history combo in output pane**

In `_build_output_pane()`, create or move:

```python
self.export_history_combo = QComboBox()
export_button = QPushButton(UI_TEXT["export"])
export_button.clicked.connect(self.export_reports)
```

Ensure `_record_analysis_run()` still updates `export_history_combo` and `selected_history_index`.

- [ ] **Step 3: Preserve run-analysis wiring**

Connect the primary run button to `run_analysis`:

```python
run_button = QPushButton(UI_TEXT["run_analysis"])
run_button.setObjectName("primary")
run_button.clicked.connect(self.run_analysis)
```

Keep `run_analysis()` calling:

```python
analyze_logs(paths, self.active_rule_path)
```

- [ ] **Step 4: Run export and analysis tests**

Run:

```bash
pytest tests/test_desktop.py::DesktopTests::test_run_analysis_uses_selected_source_files -q
pytest tests/test_desktop.py::DesktopTests::test_export_reports_uses_selected_analysis_history_entry -q
pytest tests/test_desktop.py::DesktopTests::test_export_history_is_selectable_by_combo -q
pytest tests/test_desktop.py::DesktopTests::test_workbench_output_region_contains_local_export_action -q
```

Expected: pass.

- [ ] **Step 5: Mark task progress**

Update `tasks.md`:

```markdown
- [x] 3.2 Wire existing analysis execution into the workbench top or source-adjacent action area.
- [x] 3.5 Preserve existing JSON, CSV, and Markdown export behavior from the new bottom output region.
```

- [ ] **Step 6: Commit**

```bash
git add tests/test_desktop.py logcheck/desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "feat: preserve analysis history and exports in workbench"
```

## Task 6: Polish Styling And Remove Obsolete Navigation Assumptions

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Update styling tests**

Adjust existing stylesheet tests to assert pane and row surfaces used by the workbench:

```python
def test_stylesheet_preserves_workbench_pane_and_row_surfaces(self):
    app = QApplication.instance() or QApplication([])
    window = desktop.LogcheckDesktop()

    stylesheet = window.styleSheet()

    self.assertIn("QFrame#pane", stylesheet)
    self.assertIn("QFrame#row", stylesheet)
    self.assertIn("QScrollArea", stylesheet)

    window.close()
```

- [ ] **Step 2: Remove brittle sidebar navigation tests**

Delete or rewrite tests that require `workspace_stack`, `section_widgets["nav_overview"]`, or sidebar-only navigation if those widgets no longer exist. Preserve tests that assert user-visible behavior.

- [ ] **Step 3: Tune stylesheet**

Update `_stylesheet()` so panes and rows have consistent contrast:

```python
QFrame#pane { background: PANEL; border: 1px solid BORDER; border-radius: 6px; }
QFrame#row { background: PANEL_2; border: 1px solid BORDER; border-radius: 4px; }
QScrollArea { border: 1px solid BORDER; background: PANEL; }
QLabel#paneTitle { font-weight: 700; }
```

Use the existing color constants unless a small additional neutral or accent constant is needed.

- [ ] **Step 4: Check small-window behavior**

Keep `setMinimumSize(980, 620)` or raise it only if necessary. Ensure the center log viewer remains visible when the window is at minimum size.

- [ ] **Step 5: Run desktop tests**

Run:

```bash
pytest tests/test_desktop.py -q
```

Expected: pass.

- [ ] **Step 6: Mark task progress**

Update `tasks.md`:

```markdown
- [x] 4.1 Update the stylesheet for a restrained investigation-tool look with readable contrast, consistent borders, and compact controls.
- [x] 4.2 Ensure monospaced log rows, severity indicators, buttons, labels, and scroll areas do not overlap or resize unpredictably.
- [x] 4.3 Define minimum dimensions or collapse behavior so the center log viewer remains usable on smaller windows.
- [x] 4.4 Remove duplicated or obsolete section controls that conflict with the workbench-first flow.
- [x] 5.1 Run the desktop-focused tests and fix regressions.
```

- [ ] **Step 7: Commit**

```bash
git add tests/test_desktop.py logcheck/desktop.py openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "style: polish desktop workbench surfaces"
```

## Task 7: Final Verification And Documentation Check

**Files:**
- Modify: `README.md` only if needed
- Modify: `openspec/changes/redesign-desktop-investigation-workbench/tasks.md`

- [ ] **Step 1: Run the full test suite**

Run:

```bash
pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Launch the desktop app for visual verification**

Run:

```bash
python -m logcheck.desktop
```

Expected: the app opens to the workbench with left source pane, central log viewer, right rule/context pane, and bottom output pane. No remote controls are visible.

- [ ] **Step 3: Check README workflow accuracy**

Search for desktop instructions:

```bash
rg "desktop|桌面|logcheck-desktop|导出|规则" README.md docs
```

If the README still describes a page-first workflow that is now misleading, update only that section with the workbench flow.

- [ ] **Step 4: Mark final tasks complete**

Update `tasks.md`:

```markdown
- [x] 5.2 Run the full test suite.
- [x] 5.3 Launch the desktop app and visually verify the workbench layout, source flow, analysis flow, finding detail, local exports, and absence of remote controls.
- [x] 5.4 Update README or course-facing documentation only if the user workflow changes enough to make current instructions misleading.
```

- [ ] **Step 5: Commit**

```bash
git add README.md openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "docs: finalize desktop workbench verification"
```

If README did not need changes:

```bash
git add openspec/changes/redesign-desktop-investigation-workbench/tasks.md
git commit -m "chore: finalize desktop workbench verification"
```

## Self-Review

- Spec coverage: Tasks cover the first-screen workbench shell, local source diagnostics, highlighted evidence/log viewer, local-only rule controls, bottom findings/evidence/history/export output, and verification.
- Completion marker scan: The plan avoids unfinished markers and gives concrete tests, implementation targets, and commands.
- Type consistency: The plan preserves existing model names (`AnalysisResult`, `Event`, `Finding`) and existing desktop method names while adding pane-specific attributes.
