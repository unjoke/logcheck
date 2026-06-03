import unittest

from logcheck import desktop


class DesktopTests(unittest.TestCase):
    def test_theme_defines_black_and_white_shell(self):
        self.assertEqual(desktop.BG, "#111111")
        self.assertEqual(desktop.TEXT, "#f3f3f3")
        self.assertIn("local", desktop.LOCAL_MODE_TEXT.lower())


if __name__ == "__main__":
    unittest.main()
