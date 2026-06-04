---
change: enhance-frontend-log-rules-workflow
design-doc: docs/superpowers/specs/2026-06-04-enhance-frontend-log-rules-workflow-design.md
base-ref: 6d4407c5cb341c29b6e13053b99311c46e4a5743
archived-with: 2026-06-04-enhance-frontend-log-rules-workflow
---

# Enhance Frontend Log Rules Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the desktop UI analyze selected log-source files, reuse that selection from Overview, import/download structured rule files, and keep overview details from covering export controls.

**Architecture:** Keep rule parsing and serialization in `logcheck/config.py`. Keep UI state, file dialogs, source-selection analysis, rule import/save actions, and layout changes in `logcheck/desktop.py`. Use the existing `analyze_logs(paths, config_path)` pipeline without changing parser, detector, or report exporter semantics.

**Tech Stack:** Python 3.11+, PyQt6, `unittest`, standard `json`/`tomllib`, optional PyYAML import for YAML files.

archived-with: 2026-06-04-enhance-frontend-log-rules-workflow
---

## File Map

- Modify `logcheck/config.py`: add JSON/YAML/TOML suffix dispatch, validation helpers, and `config_to_dict`.
- Modify `logcheck/desktop.py`: add active rule state, rule import/save controls, selected-source analysis action, overview source summary, stricter path resolution, and separated overview export layout.
- Modify `tests/test_rules.py`: add config file loading, serialization, invalid data, and optional YAML tests.
- Modify `tests/test_desktop.py`: add selected-source no-selection behavior, overview reuse summary, rule import/save behavior, and overview export layout checks.
- Modify `openspec/changes/enhance-frontend-log-rules-workflow/tasks.md`: mark implementation tasks complete as they are finished.

archived-with: 2026-06-04-enhance-frontend-log-rules-workflow
---

### Task 1: Config JSON Support and Validation

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/config.py`

- [ ] **Step 1: Write failing JSON load and validation tests**

Add imports near the top of `tests/test_rules.py`:

```python
import json
from tempfile import TemporaryDirectory
from pathlib import Path

from logcheck.config import config_to_dict, load_config
```

Add these tests inside `RuleTests`:

```python
    def test_json_rule_file_is_loaded(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "keywords": {"custom_rule": ["needle"]},
                        "brute_force": {"threshold": 3, "window_minutes": 7},
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.keywords, {"custom_rule": ["needle"]})
        self.assertEqual(config.brute_force_threshold, 3)
        self.assertEqual(config.brute_force_window_minutes, 7)

    def test_rule_config_rejects_invalid_keyword_shape(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps({"keywords": {"bad": "needle"}}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_config(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_rules.RuleTests.test_json_rule_file_is_loaded tests.test_rules.RuleTests.test_rule_config_rejects_invalid_keyword_shape -v`

Expected: FAIL or ERROR because `load_config` currently parses JSON as TOML and `config_to_dict` does not exist yet.

- [ ] **Step 3: Implement minimal config dispatch and validation**

Replace `logcheck/config.py` with this structure:

```python
from __future__ import annotations

from pathlib import Path
import json
import tomllib
from typing import Any

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

    data = _load_config_data(path)
    return _config_from_data(data)


def config_to_dict(config: DetectionConfig) -> dict[str, object]:
    return {
        "keywords": {name: list(keywords) for name, keywords in config.keywords.items()},
        "brute_force": {
            "threshold": config.brute_force_threshold,
            "window_minutes": config.brute_force_window_minutes,
        },
    }


def _load_config_data(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix == ".toml":
        data = tomllib.loads(text)
    elif suffix in {".yaml", ".yml"}:
        data = _load_yaml(text)
    else:
        raise ValueError(f"Unsupported rule file type: {suffix or path.name}")
    if not isinstance(data, dict):
        raise ValueError("Rule file must contain an object.")
    return data


def _load_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ValueError("YAML rule files require optional PyYAML support; JSON is supported.") from exc
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Rule file must contain an object.")
    return data


def _config_from_data(data: dict[str, Any]) -> DetectionConfig:
    base = default_config()
    raw_keywords = data.get("keywords", base.keywords)
    keywords = _validate_keywords(raw_keywords)
    raw_brute_force = data.get("brute_force", {})
    if raw_brute_force is None:
        raw_brute_force = {}
    if not isinstance(raw_brute_force, dict):
        raise ValueError("brute_force must be an object.")
    return DetectionConfig(
        keywords=keywords,
        brute_force_threshold=int(raw_brute_force.get("threshold", base.brute_force_threshold)),
        brute_force_window_minutes=int(
            raw_brute_force.get("window_minutes", base.brute_force_window_minutes)
        ),
    )


def _validate_keywords(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ValueError("keywords must be an object.")
    keywords: dict[str, list[str]] = {}
    for group, terms in value.items():
        if not isinstance(group, str):
            raise ValueError("keyword rule names must be strings.")
        if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
            raise ValueError("keyword rule values must be lists of strings.")
        keywords[group] = list(terms)
    return keywords
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_rules.RuleTests.test_json_rule_file_is_loaded tests.test_rules.RuleTests.test_rule_config_rejects_invalid_keyword_shape -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/config.py tests/test_rules.py
git commit -m "feat: load structured JSON rule files"
```

### Task 2: Rule Serialization and Optional YAML

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `logcheck/config.py`

- [ ] **Step 1: Write failing serialization and YAML tests**

Add this import near the top of `tests/test_rules.py`:

```python
import importlib.util
```

Add these tests inside `RuleTests`:

```python
    def test_config_to_dict_can_be_reloaded_from_json(self):
        original = DetectionConfig(
            keywords={"custom_rule": ["needle", "signal"]},
            brute_force_threshold=4,
            brute_force_window_minutes=12,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.json"
            path.write_text(json.dumps(config_to_dict(original)), encoding="utf-8")

            reloaded = load_config(path)

        self.assertEqual(reloaded, original)

    def test_yaml_rule_file_is_loaded_when_yaml_is_available(self):
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("PyYAML is not installed")
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.yaml"
            path.write_text(
                "keywords:\n  custom_rule:\n    - needle\nbrute_force:\n  threshold: 2\n  window_minutes: 6\n",
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.keywords, {"custom_rule": ["needle"]})
        self.assertEqual(config.brute_force_threshold, 2)
        self.assertEqual(config.brute_force_window_minutes, 6)
```

- [ ] **Step 2: Run tests to verify current state**

Run: `python -m unittest tests.test_rules.RuleTests.test_config_to_dict_can_be_reloaded_from_json tests.test_rules.RuleTests.test_yaml_rule_file_is_loaded_when_yaml_is_available -v`

Expected: serialization test passes if Task 1 already added `config_to_dict`; YAML test passes when PyYAML is installed or is skipped when unavailable. If either fails, continue with Step 3.

- [ ] **Step 3: Adjust implementation only if tests fail**

If serialization fails, ensure `config_to_dict` returns plain lists and integers exactly as shown in Task 1. If YAML fails with PyYAML installed, ensure `_load_yaml` calls `yaml.safe_load(text)` and returns `{}` for empty YAML files.

- [ ] **Step 4: Run focused rule tests**

Run: `python -m unittest tests.test_rules -v`

Expected: PASS, with the YAML test either passing or skipping depending on local parser availability.

- [ ] **Step 5: Commit**

```bash
git add logcheck/config.py tests/test_rules.py
git commit -m "feat: export and optionally load YAML rules"
```

### Task 3: Desktop Active Rule Import and Save

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`

- [ ] **Step 1: Write failing desktop rule import/save tests**

Add this import near the top of `tests/test_desktop.py`:

```python
import json
```

Add these tests inside `DesktopTests`:

```python
    def test_rule_import_updates_active_rules_display(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            rule_path = Path(tmp) / "rules.json"
            rule_path.write_text(
                json.dumps(
                    {
                        "keywords": {"custom_rule": ["needle"]},
                        "brute_force": {"threshold": 2, "window_minutes": 8},
                    }
                ),
                encoding="utf-8",
            )

            with patch("logcheck.desktop.QFileDialog.getOpenFileName", return_value=(str(rule_path), "")):
                window.import_rule_file()

        self.assertEqual(window.active_rule_path, rule_path)
        self.assertIn("custom_rule", window.rules_section_label.text())
        self.assertIn("needle", window.rules_section_label.text())
        self.assertIn("2", window.rules_section_label.text())
        self.assertIn("8", window.rules_section_label.text())
        window.close()

    def test_rule_import_failure_keeps_previous_rules(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        original_text = window.rules_section_label.text()
        with TemporaryDirectory() as tmp:
            rule_path = Path(tmp) / "bad.json"
            rule_path.write_text(json.dumps({"keywords": {"bad": "needle"}}), encoding="utf-8")

            with patch("logcheck.desktop.QFileDialog.getOpenFileName", return_value=(str(rule_path), "")):
                window.import_rule_file()

        self.assertIsNone(window.active_rule_path)
        self.assertEqual(window.rules_section_label.text(), original_text)
        self.assertIn("规则", window.status_label.text())
        window.close()

    def test_active_rules_can_be_saved_as_json(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "rules.json"

            with patch("logcheck.desktop.QFileDialog.getSaveFileName", return_value=(str(out_path), "")):
                window.save_active_rule_file()

            data = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertIn("keywords", data)
        self.assertIn("brute_force", data)
        self.assertIn("failed_login", data["keywords"])
        window.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_rule_import_updates_active_rules_display tests.test_desktop.DesktopTests.test_rule_import_failure_keeps_previous_rules tests.test_desktop.DesktopTests.test_active_rules_can_be_saved_as_json -v`

Expected: ERROR because `import_rule_file`, `save_active_rule_file`, and active rule attributes do not exist yet.

- [ ] **Step 3: Add desktop rule state and controls**

In `logcheck/desktop.py`, update imports:

```python
import json
```

Change config imports to:

```python
from .config import config_to_dict, default_config, load_config
```

In `LogcheckDesktop.__init__`, add before `_build_shell()`:

```python
        self.active_rule_path: Path | None = None
        self.active_config = default_config()
```

Replace `_rules_section` with a real section:

```python
    def _rules_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label(UI_TEXT["nav_rules"], "title", bold=True))
        layout.addWidget(self._label("查看并管理本地分析使用的检测规则。", "normal", MUTED))

        actions = QHBoxLayout()
        import_button = QPushButton("导入规则文件")
        import_button.clicked.connect(self.import_rule_file)
        save_button = QPushButton("下载当前规则")
        save_button.clicked.connect(self.save_active_rule_file)
        actions.addWidget(import_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        self.rules_section_label = self._label(self._format_rules_text(), "normal", MUTED)
        panel_layout.addWidget(self.rules_section_label)
        layout.addWidget(panel, 1)
        return section
```

Update `_format_rules_text` to use the active config:

```python
    def _format_rules_text(self) -> str:
        config = self.active_config
        source = self.active_rule_path.name if self.active_rule_path else "默认规则"
        lines = [f"当前规则：{source}", "关键词规则："]
        for group, keywords in sorted(config.keywords.items()):
            lines.append(f"- {group}: {', '.join(keywords)}")
        lines.append(
            f"重复失败登录：{config.brute_force_threshold} "
            f"次 / {config.brute_force_window_minutes} 分钟"
        )
        return "\n".join(lines)
```

Add helper methods near `_format_rules_text`:

```python
    def _refresh_rules_section(self) -> None:
        self.rules_section_label.setText(self._format_rules_text())

    def import_rule_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择本地规则文件",
            "",
            "Rule files (*.json *.yaml *.yml *.toml);;JSON files (*.json);;All files (*)",
        )
        if not selected:
            self.status_label.setText("已取消规则导入。")
            return
        path = Path(selected)
        try:
            config = load_config(path)
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"无法导入规则文件：{exc}")
            return
        self.active_rule_path = path
        self.active_config = config
        self._refresh_rules_section()
        self.status_label.setText(f"已导入规则文件：{path.name}")

    def save_active_rule_file(self) -> None:
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "保存当前规则",
            "rules.json",
            "JSON files (*.json);;All files (*)",
        )
        if not selected:
            self.status_label.setText("已取消规则保存。")
            return
        path = Path(selected)
        try:
            path.write_text(
                json.dumps(config_to_dict(self.active_config), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.status_label.setText(f"无法保存规则文件：{exc}")
            return
        self.status_label.setText(f"规则已保存到 {path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_rule_import_updates_active_rules_display tests.test_desktop.DesktopTests.test_rule_import_failure_keeps_previous_rules tests.test_desktop.DesktopTests.test_active_rules_can_be_saved_as_json -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "feat: manage rule files from desktop"
```

### Task 4: Analyze With Active Rule File

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`

- [ ] **Step 1: Write failing active-rule analysis test**

Add this test inside `DesktopTests`:

```python
    def test_run_analysis_passes_imported_rule_file(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(events=[Event("selected.log", 1, "needle")], findings=[])
        paths = [Path("selected.log")]
        rule_path = Path("rules.json")
        window.selected_source_paths = paths
        window.active_rule_path = rule_path

        with patch("logcheck.desktop.analyze_logs", return_value=result) as analyze_logs:
            window.run_analysis()

        analyze_logs.assert_called_once_with(paths, rule_path)
        window.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_run_analysis_passes_imported_rule_file -v`

Expected: FAIL because `run_analysis` currently calls `analyze_logs(paths)` without the imported config path.

- [ ] **Step 3: Pass active rule path into analysis**

Update `run_analysis` in `logcheck/desktop.py`:

```python
            self.latest_result = analyze_logs(paths, self.active_rule_path)
```

Update existing desktop tests that assert the old call signature:

```python
        analyze_logs.assert_called_once_with(paths, None)
```

and:

```python
        analyze_logs.assert_called_once_with(standalone, None)
```

- [ ] **Step 4: Run affected desktop tests**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_run_analysis_passes_imported_rule_file tests.test_desktop.DesktopTests.test_run_analysis_uses_selected_source_files tests.test_desktop.DesktopTests.test_standalone_local_files_can_be_analyzed_without_source_folder -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "feat: analyze with imported desktop rules"
```

### Task 5: Source Selection and Overview Reuse

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`

- [ ] **Step 1: Write failing source-selection behavior tests**

Add these tests inside `DesktopTests`:

```python
    def test_source_based_analysis_requires_selected_source_files(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        window.source_files = [Path("auth.log"), Path("app.log")]
        window.selected_source_paths = []
        window.standalone_paths = []
        window.selected_paths = []

        with patch("logcheck.desktop.analyze_logs") as analyze_logs:
            window.run_analysis()

        analyze_logs.assert_not_called()
        self.assertIn("至少", window.status_label.text())
        window.close()

    def test_overview_source_summary_updates_from_log_sources(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "auth.log"
            second = root / "app.log"
            first.write_text("auth", encoding="utf-8")
            second.write_text("app", encoding="utf-8")
            window.set_log_source_folder(root)

            window.source_file_checks[first].setChecked(False)

        self.assertIn("app.log", window.logs_label.text())
        self.assertNotIn("auth.log", window.logs_label.text())
        window.close()
```

- [ ] **Step 2: Run tests to verify expected failure**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_source_based_analysis_requires_selected_source_files tests.test_desktop.DesktopTests.test_overview_source_summary_updates_from_log_sources -v`

Expected: first test FAILS because `_resolve_analysis_paths` falls back to `source_files`; second test may already pass and should stay passing.

- [ ] **Step 3: Add explicit selected-source requirement and source analyze button**

Update `_sources_section` actions in `logcheck/desktop.py` after `standalone_button`:

```python
        analyze_source_button = QPushButton("分析选中日志")
        analyze_source_button.setObjectName("primary")
        analyze_source_button.clicked.connect(self.run_analysis)
```

Add it to the layout:

```python
        actions.addWidget(analyze_source_button)
```

Update `_resolve_analysis_paths`:

```python
    def _resolve_analysis_paths(self) -> list[Path]:
        if self.selected_source_paths:
            return list(self.selected_source_paths)
        if self.standalone_paths:
            return list(self.standalone_paths)
        return list(self.selected_paths)
```

Update `run_analysis` before the generic empty-path check:

```python
        if self.source_files and not self.selected_source_paths and not self.standalone_paths and not self.selected_paths:
            self.status_label.setText("请至少选择一个日志源文件再开始分析。")
            return
```

Ensure `_sync_selected_source_paths` keeps `logs_label` in sync. If it currently does not, update it to:

```python
    def _sync_selected_source_paths(self) -> None:
        self.selected_source_paths = [
            path for path, checkbox in self.source_file_checks.items() if checkbox.isChecked()
        ]
        self.logs_label.setText(
            "\n".join(path.name for path in self.selected_source_paths) or UI_TEXT["no_logs"]
        )
```

- [ ] **Step 4: Run affected tests**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_source_based_analysis_requires_selected_source_files tests.test_desktop.DesktopTests.test_overview_source_summary_updates_from_log_sources tests.test_desktop.DesktopTests.test_source_file_checkboxes_select_analysis_subset tests.test_desktop.DesktopTests.test_run_analysis_uses_selected_source_files -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "feat: analyze selected source files from overview"
```

### Task 6: Overview Layout Separation

**Files:**
- Modify: `tests/test_desktop.py`
- Modify: `logcheck/desktop.py`

- [ ] **Step 1: Write failing layout ownership test**

Add this test inside `DesktopTests`:

```python
    def test_overview_export_controls_are_separate_from_detail_scroll(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        self.assertIsNot(window.export_button.parentWidget(), window.detail_scroll)
        self.assertGreaterEqual(window.export_button.width(), 0)

        window.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_overview_export_controls_are_separate_from_detail_scroll -v`

Expected: ERROR because `window.export_button` does not exist yet.

- [ ] **Step 3: Make export controls named and separated**

In `_details_panel`, replace the local export button block:

```python
        export_button = QPushButton(UI_TEXT["export"])
        export_button.clicked.connect(self.export_reports)
        layout.addWidget(export_button)
```

with:

```python
        export_box = QFrame()
        export_box.setObjectName("row")
        export_layout = QVBoxLayout(export_box)
        export_layout.setContentsMargins(12, 10, 12, 10)
        export_layout.addWidget(self._label("导出", "bold", bold=True))
        self.export_button = QPushButton(UI_TEXT["export"])
        self.export_button.clicked.connect(self.export_reports)
        export_layout.addWidget(self.export_button)
        layout.addWidget(export_box)
```

Keep `detail_scroll` above the export box and avoid adding stretch before export controls.

- [ ] **Step 4: Run layout and detail tests**

Run: `python -m unittest tests.test_desktop.DesktopTests.test_overview_export_controls_are_separate_from_detail_scroll tests.test_desktop.DesktopTests.test_finding_detail_area_is_scrollable_for_long_evidence -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add logcheck/desktop.py tests/test_desktop.py
git commit -m "fix: keep overview export controls visible"
```

### Task 7: Final Verification and OpenSpec Task Updates

**Files:**
- Modify: `openspec/changes/enhance-frontend-log-rules-workflow/tasks.md`

- [ ] **Step 1: Run focused test suites**

Run: `python -m unittest tests.test_rules tests.test_desktop -v`

Expected: PASS, with optional YAML test skipped only when PyYAML is unavailable.

- [ ] **Step 2: Run full test suite**

Run: `python -m unittest discover -v`

Expected: PASS.

- [ ] **Step 3: Validate OpenSpec change**

Run: `openspec validate "enhance-frontend-log-rules-workflow" --strict`

Expected: `Change 'enhance-frontend-log-rules-workflow' is valid`.

- [ ] **Step 4: Update OpenSpec task checkboxes**

In `openspec/changes/enhance-frontend-log-rules-workflow/tasks.md`, change every completed task from `- [ ]` to `- [x]`.

- [ ] **Step 5: Commit final task update**

```bash
git add openspec/changes/enhance-frontend-log-rules-workflow/tasks.md
git commit -m "chore: mark log rules workflow tasks complete"
```

- [ ] **Step 6: Run build guard**

Run: `bash ".codex/skills/comet/scripts/comet-guard.sh" "enhance-frontend-log-rules-workflow" build --apply`

Expected: guard passes and updates `.comet.yaml` to `phase: verify`.
