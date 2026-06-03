from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, font

from .analysis import analyze_logs, summarize_result
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
from .models import Finding


BG = "#111111"
PANEL = "#1b1b1b"
PANEL_2 = "#242424"
TEXT = "#f3f3f3"
MUTED = "#9a9a9a"
BORDER = "#333333"
ACCENT = "#f5f5f5"
LOCAL_MODE_TEXT = "Local mode - local files only"


@dataclass(frozen=True)
class FindingRow:
    severity: str
    title: str
    subtitle: str
    location: str


def format_finding_row(finding: Finding) -> FindingRow:
    source = finding.source_address or finding.actor or "unknown"
    return FindingRow(
        severity=finding.severity.upper(),
        title=f"{source} - {finding.rule_id}",
        subtitle=finding.explanation,
        location=f"{finding.source_file}:{finding.line_number}",
    )


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
        self.log_list_var = tk.StringVar(value="No local files selected.")
        self.detail_var = tk.StringVar(value="Select a finding to inspect evidence.")

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
        select_button = self._button_label(header, "Select Logs", False)
        select_button.bind("<Button-1>", lambda _event: self.choose_logs())
        select_button.pack(side="right", padx=(12, 0))
        run_button = self._button_label(header, "Run Analysis", True)
        run_button.bind("<Button-1>", lambda _event: self.run_analysis())
        run_button.pack(side="right", padx=(12, 0))

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
        self.findings_frame = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        self.findings_frame.pack(side="left", fill="both", expand=True, padx=(0, 16))
        self._label(self.findings_frame, "Finding Queue", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self.finding_rows_frame = tk.Frame(self.findings_frame, bg=PANEL)
        self.finding_rows_frame.pack(fill="both", expand=True)
        self._render_empty_findings("No analysis has been run.")

        details = tk.Frame(content, bg=PANEL, width=315, highlightthickness=1, highlightbackground=BORDER)
        details.pack(side="right", fill="y")
        details.pack_propagate(False)
        self._label(details, "Current Logs", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self._label(details, textvariable=self.log_list_var, fg=MUTED, bg=PANEL, padx=18, pady=6)
        self._label(details, "Rule Status", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(22, 8))
        for rule in ["Keyword indicators", "Repeated failed login", "Severity classification"]:
            self._label(details, f"- {rule}", bg=PANEL, padx=20, pady=4)
        self._label(details, "Finding Detail", bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(22, 8))
        self._label(details, textvariable=self.detail_var, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=6)
        tk.Frame(details, bg=PANEL).pack(fill="both", expand=True)
        self._label(details, textvariable=self.status_var, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=(8, 18))

    def choose_logs(self):
        paths = filedialog.askopenfilenames(title="Select local log files")
        if not paths:
            self.status_var.set("Log selection cancelled.")
            return
        self.selected_paths = [Path(path) for path in paths]
        self.log_list_var.set("\n".join(path.name for path in self.selected_paths))
        self.status_var.set(f"{len(self.selected_paths)} local log file(s) selected.")

    def run_analysis(self):
        if not self.selected_paths:
            self.status_var.set("Select local log files before analysis.")
            return
        try:
            self.latest_result = analyze_logs(self.selected_paths)
        except OSError as exc:
            self.status_var.set(f"Could not analyze logs: {exc}")
            return
        self._render_result(self.latest_result)
        self.status_var.set("Analysis complete.")

    def _render_result(self, result: AnalysisResult):
        summary = summarize_result(result)
        high_count = sum(
            count
            for severity, count in summary.findings_by_severity.items()
            if severity in {"high", "critical"}
        )
        self.metric_vars["events"].set(str(summary.total_events))
        self.metric_vars["findings"].set(str(summary.total_findings))
        self.metric_vars["high"].set(str(high_count))
        self.metric_vars["sources"].set(str(len(summary.top_suspicious_sources)))
        self._render_findings(result.findings)

    def _render_empty_findings(self, message: str):
        for child in self.finding_rows_frame.winfo_children():
            child.destroy()
        self._label(self.finding_rows_frame, message, fg=MUTED, bg=PANEL, padx=18, pady=8)

    def _render_findings(self, findings: list[Finding]):
        for child in self.finding_rows_frame.winfo_children():
            child.destroy()
        if not findings:
            self._render_empty_findings("No findings detected.")
            return
        for finding in findings:
            row = format_finding_row(finding)
            frame = tk.Frame(self.finding_rows_frame, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
            frame.pack(fill="x", padx=16, pady=5)
            sev = tk.Label(frame, text=row.severity, fg=BG, bg=TEXT, font=self.ui_small, width=8, pady=5)
            sev.pack(side="left", padx=(10, 12), pady=10)
            text_box = tk.Frame(frame, bg=PANEL_2)
            text_box.pack(side="left", fill="x", expand=True, pady=8)
            self._label(text_box, row.title, bg=PANEL_2, font_obj=self.ui_bold)
            self._label(text_box, f"{row.subtitle}  |  {row.location}", fg=MUTED, bg=PANEL_2, font_obj=self.ui_small)
            frame.bind("<Button-1>", lambda _event, item=finding: self._show_finding_detail(item))

    def _show_finding_detail(self, finding: Finding):
        evidence = "\n".join(finding.evidence[:4])
        self.detail_var.set(
            f"{finding.rule_id}\n"
            f"Severity: {finding.severity}\n"
            f"Source: {finding.source_file}:{finding.line_number}\n\n"
            f"{evidence}"
        )


def main() -> None:
    app = LogcheckDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()
