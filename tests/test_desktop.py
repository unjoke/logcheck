import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QScrollArea

from logcheck import desktop
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

    def test_sidebar_action_buttons_dispatch_existing_local_functions(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()

        with patch.object(window, "choose_logs") as choose_logs:
            window.nav_buttons["nav_sources"].click()
            app.processEvents()

        choose_logs.assert_called_once_with()
        self.assertEqual(window.workspace_stack.currentWidget(), window.section_widgets["nav_sources"])

        with patch.object(window, "export_reports") as export_reports:
            window.nav_buttons["nav_export"].click()
            app.processEvents()

        export_reports.assert_called_once_with()
        self.assertEqual(window.workspace_stack.currentWidget(), window.section_widgets["nav_export"])

        window.close()

    def test_sidebar_suspicious_sources_section_reflects_latest_analysis(self):
        app = QApplication.instance() or QApplication([])
        window = desktop.LogcheckDesktop()
        result = AnalysisResult(
            events=[Event(source_file="samples/auth.log", line_number=1, raw_line="login failed")],
            findings=[
                Finding(
                    rule_id="keyword.failed_login",
                    severity="medium",
                    explanation="Matched intrusion indicator keyword",
                    evidence=["Failed password from 192.0.2.10"],
                    source_file="samples/auth.log",
                    line_number=1,
                    source_address="192.0.2.10",
                )
            ],
        )

        window._render_result(result)
        window.nav_buttons["nav_suspicious"].click()
        app.processEvents()

        self.assertEqual(window.workspace_stack.currentWidget(), window.section_widgets["nav_suspicious"])
        self.assertIn("192.0.2.10", window.suspicious_sources_label.text())
        self.assertIn("1", window.suspicious_sources_label.text())

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
