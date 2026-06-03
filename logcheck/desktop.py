from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import font

from .models import AnalysisResult


BG = "#111111"
PANEL = "#1b1b1b"
PANEL_2 = "#242424"
TEXT = "#f3f3f3"
MUTED = "#9a9a9a"
BORDER = "#333333"
ACCENT = "#f5f5f5"
LOCAL_MODE_TEXT = "Local mode - local files only"


class LogcheckDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Logcheck Desktop")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.selected_paths: list[Path] = []
        self.latest_result: AnalysisResult | None = None

        self.ui = font.Font(family="Microsoft YaHei UI", size=11)
        self.ui_small = font.Font(family="Microsoft YaHei UI", size=9)
        self.ui_bold = font.Font(family="Microsoft YaHei UI", size=11, weight="bold")
        self.title_font = font.Font(family="Microsoft YaHei UI", size=23, weight="bold")
        self.metric_font = font.Font(family="Segoe UI", size=22, weight="bold")

        self.status_var = tk.StringVar(value="Select local logs to begin.")
        self.metric_vars = {
            "events": tk.StringVar(value="0"),
            "findings": tk.StringVar(value="0"),
            "high": tk.StringVar(value="0"),
            "sources": tk.StringVar(value="0"),
        }

        self._build_shell()

    def _label(self, parent, text=None, *, textvariable=None, fg=TEXT, bg=None, font_obj=None, **pack):
        label = tk.Label(
            parent,
            text=text,
            textvariable=textvariable,
            fg=fg,
            bg=bg or parent["bg"],
            font=font_obj or self.ui,
            anchor="w",
            justify="left",
        )
        label.pack(**pack)
        return label

    def _button_label(self, parent, text, active=False):
        return tk.Label(
            parent,
            text=text,
            fg=BG if active else TEXT,
            bg=ACCENT if active else PANEL_2,
            font=self.ui_bold if active else self.ui,
            padx=14,
            pady=8,
            anchor="center",
        )

    def _build_shell(self):
        top = tk.Frame(self, bg="#181818", height=44)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)
        self._label(top, "  Logcheck", bg="#181818", font_obj=self.ui_bold, side="left", padx=(10, 22))
        for item in ["File", "Analyze", "Rules", "Reports", "Help"]:
            self._label(top, item, fg=MUTED, bg="#181818", side="left", padx=(0, 28))
        self._label(top, LOCAL_MODE_TEXT, fg=MUTED, bg="#181818", side="right", padx=18)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=PANEL, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._label(sidebar, "Log Intrusion", bg=PANEL, font_obj=self.title_font, padx=20, pady=(28, 6))
        self._label(sidebar, "Logcheck Desktop", fg=MUTED, bg=PANEL, padx=22, pady=(0, 28))

        for text, active in [
            ("Overview", True),
            ("Log Sources", False),
            ("Detection Rules", False),
            ("Suspicious Sources", False),
            ("Export Report", False),
            ("Course Demo", False),
        ]:
            item = self._button_label(sidebar, text, active)
            item.pack(fill="x", padx=16, pady=4)

        tk.Frame(sidebar, bg=PANEL).pack(fill="both", expand=True)
        self._label(sidebar, "Recent analysis", fg=MUTED, bg=PANEL, font_obj=self.ui_bold, padx=22, pady=(8, 4))
        self._label(sidebar, "samples/auth.log + app.log", fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=22, pady=2)
        self._label(sidebar, "  Settings", bg=PANEL, padx=20, pady=(20, 24))

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self._build_main(main)

    def _build_main(self, main):
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", padx=34, pady=(34, 18))
        title_block = tk.Frame(header, bg=BG)
        title_block.pack(side="left", fill="x", expand=True)
        self._label(title_block, "Intrusion Behavior Overview", font_obj=self.title_font, pady=(0, 6))
        self._label(
            title_block,
            "Analyze local logs for failed logins, unauthorized access, and brute-force indicators.",
            fg=MUTED,
        )
        self._button_label(header, "Select Logs", False).pack(side="right", padx=(12, 0))
        self._button_label(header, "Run Analysis", True).pack(side="right", padx=(12, 0))

        cards = tk.Frame(main, bg=BG)
        cards.pack(fill="x", padx=34, pady=(0, 20))
        for key, title, hint in [
            ("events", "Events", "Parsed log records"),
            ("findings", "Findings", "Detection hits"),
            ("high", "High Risk", "Priority review"),
            ("sources", "Sources", "Suspicious actors"),
        ]:
            card = tk.Frame(cards, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12))
            self._label(card, title, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=(16, 0))
            self._label(card, textvariable=self.metric_vars[key], bg=PANEL, font_obj=self.metric_font, padx=18, pady=(2, 0))
            self._label(card, hint, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=(0, 16))

        content = tk.Frame(main, bg=BG)
        content.pack(fill="both", expand=True, padx=34, pady=(0, 34))
        findings = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        findings.pack(side="left", fill="both", expand=True, padx=(0, 16))
        self._label(findings, "Finding Queue", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self._label(findings, "No analysis has been run.", fg=MUTED, bg=PANEL, padx=18, pady=8)

        details = tk.Frame(content, bg=PANEL, width=315, highlightthickness=1, highlightbackground=BORDER)
        details.pack(side="right", fill="y")
        details.pack_propagate(False)
        self._label(details, "Current Logs", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self._label(details, "No local files selected.", fg=MUTED, bg=PANEL, padx=18, pady=6)
        self._label(details, "Rule Status", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(22, 8))
        for rule in ["Keyword indicators", "Repeated failed login", "Severity classification"]:
            self._label(details, f"- {rule}", bg=PANEL, padx=20, pady=4)
        tk.Frame(details, bg=PANEL).pack(fill="both", expand=True)
        self._label(details, textvariable=self.status_var, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=(8, 18))


def main() -> None:
    app = LogcheckDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()
