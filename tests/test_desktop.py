import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel, QPushButton, QScrollArea

from logcheck import desktop
from logcheck.insights import EntityProfile, generate_insights
from logcheck.models import AnalysisResult, Event, Finding


class DesktopTests(unittest.TestCase):
    def test_desktop_uses_qt_toolkit(self):
        self.assertEqual(desktop.UI_TOOLKIT, "PyQt6/Qt")

    def test_theme_defines_black_and_white_shell(self):
        self.assertEqual(desktop.BG, "#111111")
        self.assertEqual(desktop.TEXT, "#f3f3f3")
        self.assertIn("\u672c\u5730", desktop.LOCAL_MODE_TEXT)

    def test_interface_copy_is_chinese(self):
        visible_text = " ".join(desktop.UI_TEXT.values())

        for phrase in [
            "\u6587\u4ef6",
            "\u5206\u6790",
            "\u68c0\u6d4b\u89c4\u5219",
            "\u544a\u8b66\u961f\u5217",
            "\u5bfc\u51fa\u62a5\u544a",
            "\u672c\u5730\u6587\u4ef6",
        ]:
            self.assertIn(phrase, visible_text)

    def test_font_sizes_are_clear_for_demo(self):
        self.assertGreaterEqual(desktop.FONT_SIZES["normal"], 12)
        self.assertGreaterEqual(desktop.FONT_SIZES["small"], 10)
        self.assertGreaterEqual(desktop.FONT_SIZES["title"], 26)
        self.assertGreaterEqual(desktop.FONT_SIZES["metric"], 26)

    def test_qt_window_can_be_created(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        self.assertEqual(window.windowTitle(), desktop.UI_TEXT["window_title"])
        self.assertGreaterEqual(window.minimumWidth(), 980)
        self.assertGreaterEqual(window.minimumHeight(), 620)

        window.close()

    def test_new_window_starts_with_empty_source_folders(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        self.assertEqual(window.source_folders, [])

        window.close()

    def test_first_screen_exposes_investigation_workbench_regions(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        self.assertIsNotNone(window.findChild(QLabel, "sourcePaneTitle"))
        self.assertIsNotNone(window.findChild(QLabel, "logViewerPaneTitle"))
        self.assertIsNotNone(window.findChild(QLabel, "ruleContextPaneTitle"))
        self.assertIsNotNone(window.findChild(QLabel, "outputPaneTitle"))

        window.close()

    def test_sidebar_navigation_buttons_are_clickable(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        window.nav_buttons["nav_rules"].click()
        app.processEvents()

        self.assertEqual(window.current_section, desktop.UI_TEXT["nav_rules"])
        self.assertIn(desktop.UI_TEXT["nav_rules"], window.status_label.text())
        self.assertEqual(window.nav_buttons["nav_rules"].objectName(), "primary")
        self.assertEqual(window.nav_buttons["nav_overview"].objectName(), "")
        self.assertEqual(window.workspace_stack.currentWidget(), window.section_widgets["nav_rules"])

        window.close()

    def test_folder_log_source_discovers_direct_files_only(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "auth.log"
            second = root / "app.log"
            nested = root / "archive"
            nested.mkdir()
            nested_file = nested / "old.log"
            first.write_text("auth", encoding="utf-8")
            second.write_text("app", encoding="utf-8")
            nested_file.write_text("old", encoding="utf-8")

            window.set_log_source_folder(root)

            self.assertEqual(window.source_folder, root)
            self.assertEqual(window.source_files, [second, first])
            self.assertEqual(window.selected_source_paths, [second, first])
            self.assertIn("2", window.sources_section_label.text())
            self.assertNotIn("old.log", window.sources_section_label.text())
            self.assertEqual(len(window.source_file_checks), 2)
            self.assertTrue(all(check.isChecked() for check in window.source_file_checks.values()))

        window.close()

    def test_multiple_source_folders_combine_direct_files_only(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            first_root = base / "one"
            second_root = base / "two"
            first_root.mkdir()
            second_root.mkdir()
            first = first_root / "auth.log"
            second = second_root / "app.log"
            nested = second_root / "archive"
            nested.mkdir()
            nested_file = nested / "old.log"
            first.write_text("auth", encoding="utf-8")
            second.write_text("app", encoding="utf-8")
            nested_file.write_text("old", encoding="utf-8")

            window.set_log_source_folders([first_root, second_root])

            self.assertEqual(window.source_files, [first, second])
            self.assertEqual(window.selected_source_paths, [first, second])
            self.assertIn("2", window.sources_section_label.text())
            self.assertNotIn("old.log", window.sources_section_label.text())
            self.assertEqual(len(window.source_file_checks), 2)

        window.close()

    def test_source_folder_dialog_loads_multiple_folder_files(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            first_root = base / "one"
            second_root = base / "two"
            first_root.mkdir()
            second_root.mkdir()
            first = first_root / "auth.log"
            second = second_root / "app.log"
            nested = second_root / "archive"
            nested.mkdir()
            nested_file = nested / "old.log"
            first.write_text("auth", encoding="utf-8")
            second.write_text("app", encoding="utf-8")
            nested_file.write_text("old", encoding="utf-8")

            with patch.object(window, "choose_source_folders", return_value=[first_root, second_root]):
                window.choose_source_folder()

            self.assertIsNone(window.source_folder)
            self.assertEqual(window.selected_source_paths, [first, second])
            self.assertIn("2", window.sources_section_label.text())
            self.assertNotIn("old.log", window.sources_section_label.text())

        window.close()

    def test_source_file_checkboxes_select_analysis_subset(self):
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

            self.assertEqual(window.selected_source_paths, [second])
            self.assertEqual(window._resolve_analysis_paths(), [second])
            self.assertIn("app.log", window.logs_label.text())
            self.assertNotIn("auth.log", window.logs_label.text())

        window.close()

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
        self.assertIn("\u81f3\u5c11", window.status_label.text())
        window.close()

    def test_empty_source_folder_does_not_analyze_stale_standalone_paths(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with patch.object(window, "choose_standalone_logs", return_value=[Path("old.log")]):
            window.choose_logs()

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            window.set_log_source_folder(root)

            with patch("logcheck.desktop.analyze_logs") as analyze_logs:
                window.run_analysis()

        analyze_logs.assert_not_called()
        self.assertIn("\u672c\u5730\u65e5\u5fd7", window.status_label.text())
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

    def test_course_demo_navigation_is_removed(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        self.assertNotIn("nav_demo", desktop.NAV_ITEMS)
        self.assertNotIn("nav_demo", window.nav_buttons)
        self.assertNotIn("nav_demo", window.section_widgets)

        window.close()

    def test_run_analysis_uses_selected_source_files(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(events=[Event("selected.log", 1, "failed")], findings=[])
        paths = [Path("selected.log")]
        window.source_files = [Path("ignored.log"), *paths]
        window.selected_source_paths = paths

        with patch("logcheck.desktop.analyze_logs", return_value=result) as analyze_logs:
            window.run_analysis()

        analyze_logs.assert_called_once_with(paths, None)
        self.assertEqual(window.latest_result, result)
        self.assertEqual(window.analysis_history[-1].paths, paths)

        window.close()

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

    def test_standalone_local_files_can_be_analyzed_without_source_folder(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(events=[Event("standalone.log", 1, "failed")], findings=[])
        standalone = [Path("standalone.log")]

        with patch.object(window, "choose_standalone_logs", return_value=standalone):
            window.choose_logs()
        with patch("logcheck.desktop.analyze_logs", return_value=result) as analyze_logs:
            window.run_analysis()

        analyze_logs.assert_called_once_with(standalone, None)
        self.assertEqual(window.standalone_paths, standalone)
        self.assertEqual(window.analysis_history[-1].paths, standalone)

        window.close()

    def test_standalone_logs_clear_previous_source_folder_state(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "source.log"
            standalone = root / "standalone.log"
            source_file.write_text("source", encoding="utf-8")
            standalone.write_text("standalone", encoding="utf-8")
            window.set_log_source_folder(root)

            with patch.object(window, "choose_standalone_logs", return_value=[standalone]):
                window.choose_logs()

            self.assertIsNone(window.source_folder)
            self.assertEqual(window.source_folders, [])
            self.assertEqual(window.source_files, [])
            self.assertEqual(window.standalone_paths, [standalone])
            self.assertEqual(window.selected_paths, [standalone])

        window.close()

    def test_standalone_log_dialog_selects_multiple_files_together(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "auth.log"
            second = root / "app.log"
            first.write_text("auth", encoding="utf-8")
            second.write_text("app", encoding="utf-8")

            with patch(
                "logcheck.desktop.QFileDialog.getOpenFileNames",
                return_value=([str(first), str(second)], ""),
            ):
                window.choose_logs()

            self.assertEqual(window.standalone_paths, [first, second])
            self.assertEqual(window.selected_paths, [first, second])
            self.assertIn("auth.log", window.logs_label.text())
            self.assertIn("app.log", window.logs_label.text())

        window.close()

    def test_rules_section_displays_configured_detection_rules(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        text = window.rules_section_label.text()

        self.assertIn("failed_login", text)
        self.assertIn("failed password", text)
        self.assertIn("5", text)
        self.assertIn("10", text)

        window.close()

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

    def test_malformed_yaml_rule_import_failure_keeps_previous_rules(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        original_text = window.rules_section_label.text()
        with TemporaryDirectory() as tmp:
            rule_path = Path(tmp) / "bad.yaml"
            rule_path.write_text("keywords:\n  custom_rule:\n    - [needle\n", encoding="utf-8")

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

    def test_export_reports_uses_selected_analysis_history_entry(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        first = AnalysisResult(events=[Event("first.log", 1, "first")], findings=[])
        second = AnalysisResult(events=[Event("second.log", 1, "second")], findings=[])
        window._record_analysis_run([Path("first.log")], first)
        window._record_analysis_run([Path("second.log")], second)
        window.export_history_combo.setCurrentIndex(0)

        with TemporaryDirectory() as tmp:
            with patch("logcheck.desktop.QFileDialog.getExistingDirectory", return_value=tmp):
                with patch("logcheck.desktop.export_json") as export_json, patch(
                    "logcheck.desktop.export_csv"
                ) as export_csv, patch("logcheck.desktop.export_markdown") as export_markdown:
                    window.export_reports()

        export_json.assert_called_once()
        export_csv.assert_called_once()
        export_markdown.assert_called_once()
        self.assertIs(export_json.call_args.args[0], first)
        self.assertIs(export_csv.call_args.args[0], first)
        self.assertIs(export_markdown.call_args.args[0], first)

        window.close()

    def test_export_history_is_selectable_by_combo(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        first = AnalysisResult(events=[Event("first.log", 1, "first")], findings=[])
        second = AnalysisResult(events=[Event("second.log", 1, "second")], findings=[])

        window._record_analysis_run([Path("first.log")], first)
        window._record_analysis_run([Path("second.log")], second)
        window.export_history_combo.setCurrentIndex(0)

        self.assertIsInstance(window.export_history_combo, QComboBox)
        self.assertEqual(window.export_history_combo.count(), 2)
        self.assertEqual(window.selected_history_index, 0)
        self.assertIs(window._selected_analysis_run().result, first)

        window.close()

    def test_source_section_renders_file_checkboxes(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_file = root / "auth.log"
            log_file.write_text("auth", encoding="utf-8")

            window.set_log_source_folder(root)

            checks = window.source_pane.findChildren(QCheckBox)
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0].text(), "auth.log")

        window.close()

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

    def test_finding_detail_area_is_scrollable_for_long_evidence(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        window.show()
        finding = Finding(
            rule_id="keyword.long_evidence",
            severity="high",
            explanation="\u591a\u884c\u8bc1\u636e\u9700\u8981\u5b8c\u6574\u9605\u8bfb",
            evidence=[f"\u7b2c {index} \u884c\u8bc1\u636e\uff1aFailed password from 192.0.2.{index}" for index in range(1, 31)],
            source_file="samples/auth.log",
            line_number=12,
            source_address="192.0.2.9",
            actor="root",
        )

        window._show_finding_detail(finding)
        app.processEvents()

        self.assertIsInstance(window.detail_scroll, QScrollArea)
        self.assertTrue(window.detail_scroll.widgetResizable())
        self.assertIn("\u7b2c 30 \u884c\u8bc1\u636e", window.detail_label.text())
        self.assertTrue(window.detail_label.wordWrap())
        self.assertTrue(
            window.detail_label.textInteractionFlags()
            & Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.assertGreater(window.detail_scroll.verticalScrollBar().maximum(), 0)

        window.close()

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

    def test_overview_renders_analysis_insight_summary(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(
            events=[Event("auth.log", 1, "Failed password", source_address="192.0.2.10")],
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Failed login",
                    evidence=["Failed password"],
                    source_address="192.0.2.10",
                )
            ],
        )
        result.insights = generate_insights(result)

        window._render_result(result)

        self.assertIn(result.insights.risk_level, window.insight_summary_label.text())
        self.assertIn("192.0.2.10", window.insight_summary_label.text())

        window.close()

    def test_suspicious_sources_render_entity_profiles_with_evidence(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(
            events=[Event("auth.log", 1, "Failed password", source_address="192.0.2.10")],
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="high",
                    explanation="Failed login",
                    evidence=["Failed password for root from 192.0.2.10"],
                    source_address="192.0.2.10",
                )
            ],
        )
        result.insights = type(
            "Insights",
            (),
            {
                "risk_level": "high",
                "headline": "1 suspicious source requires review.",
                "evidence_count": 1,
                "entity_profiles": [
                    EntityProfile(
                        kind="source_address",
                        value="192.0.2.10",
                        finding_count=1,
                        severity_counts={"high": 1},
                        related_rules=["keyword.failed_login"],
                        evidence=["Failed password for root from 192.0.2.10"],
                    )
                ],
            },
        )()

        window._render_result(result)

        text = window.suspicious_sources_label.text()
        self.assertIn("192.0.2.10", text)
        self.assertIn("source_address", text)
        self.assertIn("high", text)
        self.assertIn("keyword.failed_login", text)
        self.assertIn("Failed password for root", text)

        window.close()

    def test_overview_does_not_duplicate_export_button(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        overview_buttons = window.section_widgets["nav_overview"].findChildren(QPushButton)
        export_buttons = window.section_widgets["nav_export"].findChildren(QPushButton)

        self.assertNotIn(desktop.UI_TEXT["export"], [button.text() for button in overview_buttons])
        self.assertIn(desktop.UI_TEXT["export"], [button.text() for button in export_buttons])

        window.close()

    def test_sidebar_does_not_show_settings_shortcut_label(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        visible_labels = [label.text() for label in window.findChildren(QLabel)]

        self.assertNotIn(desktop.UI_TEXT["settings"], visible_labels)

        window.close()

    def test_stylesheet_preserves_panel_scroll_and_row_surfaces(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        stylesheet = window.styleSheet()

        self.assertIn("QFrame#panel", stylesheet)
        self.assertIn("QScrollArea", stylesheet)
        self.assertIn("QFrame#row", stylesheet)
        self.assertIn(f"QFrame#row {{ background: {desktop.PANEL_2};", stylesheet)

        window.close()

    def test_sources_action_uses_concise_file_button_text(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        buttons = window.section_widgets["nav_sources"].findChildren(QPushButton)
        button_texts = [button.text() for button in buttons]

        self.assertIn("选择日志文件", button_texts)
        self.assertNotIn("选择单独日志文件", button_texts)

        window.close()

    def test_workbench_omits_remote_or_destructive_controls(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        visible_text = " ".join(
            [button.text() for button in window.findChildren(QPushButton)]
            + [label.text() for label in window.findChildren(QLabel)]
        )

        for forbidden in ["URL", "域名", "上传", "扫描", "封禁", "利用", "远程", "report", "外部", "上报", "报送"]:
            self.assertNotIn(forbidden, visible_text)

        window.close()


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


if __name__ == "__main__":
    unittest.main()
