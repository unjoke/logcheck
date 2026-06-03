import unittest

from logcheck import desktop
from logcheck.models import Finding


class DesktopTests(unittest.TestCase):
    def test_theme_defines_black_and_white_shell(self):
        self.assertEqual(desktop.BG, "#111111")
        self.assertEqual(desktop.TEXT, "#f3f3f3")
        self.assertIn("本地", desktop.LOCAL_MODE_TEXT)

    def test_interface_copy_is_chinese(self):
        visible_text = " ".join(desktop.UI_TEXT.values())

        for phrase in ["文件", "分析", "检测规则", "告警队列", "导出报告", "本地文件"]:
            self.assertIn(phrase, visible_text)

    def test_font_sizes_are_clear_for_demo(self):
        self.assertGreaterEqual(desktop.FONT_SIZES["normal"], 12)
        self.assertGreaterEqual(desktop.FONT_SIZES["small"], 10)
        self.assertGreaterEqual(desktop.FONT_SIZES["title"], 26)
        self.assertGreaterEqual(desktop.FONT_SIZES["metric"], 26)


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
