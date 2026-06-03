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
LOCAL_MODE_TEXT = "本地模式 - 仅分析本地文件"
FONT_SIZES = {
    "small": 10,
    "normal": 12,
    "bold": 12,
    "title": 28,
    "metric": 28,
}
UI_TEXT = {
    "window_title": "Logcheck 日志入侵检测",
    "brand": "  Logcheck",
    "menu_file": "文件",
    "menu_analyze": "分析",
    "menu_rules": "规则",
    "menu_reports": "报告",
    "menu_help": "帮助",
    "sidebar_title": "日志入侵检测",
    "sidebar_subtitle": "Logcheck 桌面版",
    "nav_overview": "总览",
    "nav_sources": "日志源",
    "nav_rules": "检测规则",
    "nav_suspicious": "可疑来源",
    "nav_export": "导出报告",
    "nav_demo": "课程演示",
    "recent": "最近分析",
    "settings": "设置",
    "main_title": "入侵行为分析总览",
    "main_subtitle": "解析本地日志，识别失败登录、越权访问和暴力破解迹象。",
    "select_logs": "选择日志",
    "run_analysis": "开始分析",
    "events": "事件",
    "events_hint": "已解析日志记录",
    "findings": "告警",
    "findings_hint": "检测规则命中",
    "high": "高危",
    "high_hint": "优先复核项目",
    "sources": "来源",
    "sources_hint": "可疑账号或地址",
    "finding_queue": "告警队列",
    "no_analysis": "尚未运行分析。",
    "current_logs": "当前日志",
    "no_logs": "未选择本地文件。",
    "rule_status": "规则状态",
    "rule_keyword": "关键词指标检测",
    "rule_repeated": "重复失败登录",
    "rule_severity": "严重等级分类",
    "finding_detail": "告警详情",
    "detail_empty": "选择一条告警查看证据。",
    "export": "导出 JSON / CSV / Markdown",
    "status_start": "请选择本地日志文件开始分析。",
}


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
        self.title(UI_TEXT["window_title"])
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.selected_paths: list[Path] = []
        self.latest_result: AnalysisResult | None = None

        self.ui = font.Font(family="Microsoft YaHei UI", size=FONT_SIZES["normal"])
        self.ui_small = font.Font(family="Microsoft YaHei UI", size=FONT_SIZES["small"])
        self.ui_bold = font.Font(family="Microsoft YaHei UI", size=FONT_SIZES["bold"], weight="bold")
        self.title_font = font.Font(family="Microsoft YaHei UI", size=FONT_SIZES["title"], weight="bold")
        self.metric_font = font.Font(family="Segoe UI", size=FONT_SIZES["metric"], weight="bold")

        self.status_var = tk.StringVar(value=UI_TEXT["status_start"])
        self.metric_vars = {
            "events": tk.StringVar(value="0"),
            "findings": tk.StringVar(value="0"),
            "high": tk.StringVar(value="0"),
            "sources": tk.StringVar(value="0"),
        }
        self.log_list_var = tk.StringVar(value=UI_TEXT["no_logs"])
        self.detail_var = tk.StringVar(value=UI_TEXT["detail_empty"])

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
        self._label(top, UI_TEXT["brand"], bg="#181818", font_obj=self.ui_bold, side="left", padx=(10, 22))
        for item in [
            UI_TEXT["menu_file"],
            UI_TEXT["menu_analyze"],
            UI_TEXT["menu_rules"],
            UI_TEXT["menu_reports"],
            UI_TEXT["menu_help"],
        ]:
            self._label(top, item, fg=MUTED, bg="#181818", side="left", padx=(0, 28))
        self._label(top, LOCAL_MODE_TEXT, fg=MUTED, bg="#181818", side="right", padx=18)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=PANEL, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._label(sidebar, UI_TEXT["sidebar_title"], bg=PANEL, font_obj=self.title_font, padx=20, pady=(28, 6))
        self._label(sidebar, UI_TEXT["sidebar_subtitle"], fg=MUTED, bg=PANEL, padx=22, pady=(0, 28))

        for text, active in [
            (UI_TEXT["nav_overview"], True),
            (UI_TEXT["nav_sources"], False),
            (UI_TEXT["nav_rules"], False),
            (UI_TEXT["nav_suspicious"], False),
            (UI_TEXT["nav_export"], False),
            (UI_TEXT["nav_demo"], False),
        ]:
            item = self._button_label(sidebar, text, active)
            item.pack(fill="x", padx=16, pady=4)

        tk.Frame(sidebar, bg=PANEL).pack(fill="both", expand=True)
        self._label(sidebar, UI_TEXT["recent"], fg=MUTED, bg=PANEL, font_obj=self.ui_bold, padx=22, pady=(8, 4))
        self._label(sidebar, "samples/auth.log + app.log", fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=22, pady=2)
        self._label(sidebar, f"  {UI_TEXT['settings']}", bg=PANEL, padx=20, pady=(20, 24))

        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        self._build_main(main)

    def _build_main(self, main):
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", padx=34, pady=(34, 18))
        title_block = tk.Frame(header, bg=BG)
        title_block.pack(side="left", fill="x", expand=True)
        self._label(title_block, UI_TEXT["main_title"], font_obj=self.title_font, pady=(0, 6))
        self._label(
            title_block,
            UI_TEXT["main_subtitle"],
            fg=MUTED,
        )
        select_button = self._button_label(header, UI_TEXT["select_logs"], False)
        select_button.bind("<Button-1>", lambda _event: self.choose_logs())
        select_button.pack(side="right", padx=(12, 0))
        run_button = self._button_label(header, UI_TEXT["run_analysis"], True)
        run_button.bind("<Button-1>", lambda _event: self.run_analysis())
        run_button.pack(side="right", padx=(12, 0))

        cards = tk.Frame(main, bg=BG)
        cards.pack(fill="x", padx=34, pady=(0, 20))
        for key, title, hint in [
            ("events", UI_TEXT["events"], UI_TEXT["events_hint"]),
            ("findings", UI_TEXT["findings"], UI_TEXT["findings_hint"]),
            ("high", UI_TEXT["high"], UI_TEXT["high_hint"]),
            ("sources", UI_TEXT["sources"], UI_TEXT["sources_hint"]),
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
        self._label(self.findings_frame, UI_TEXT["finding_queue"], bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self.finding_rows_frame = tk.Frame(self.findings_frame, bg=PANEL)
        self.finding_rows_frame.pack(fill="both", expand=True)
        self._render_empty_findings(UI_TEXT["no_analysis"])

        details = tk.Frame(content, bg=PANEL, width=315, highlightthickness=1, highlightbackground=BORDER)
        details.pack(side="right", fill="y")
        details.pack_propagate(False)
        self._label(details, UI_TEXT["current_logs"], bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(16, 10))
        self._label(details, textvariable=self.log_list_var, fg=MUTED, bg=PANEL, padx=18, pady=6)
        self._label(details, UI_TEXT["rule_status"], bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(22, 8))
        for rule in [UI_TEXT["rule_keyword"], UI_TEXT["rule_repeated"], UI_TEXT["rule_severity"]]:
            self._label(details, f"- {rule}", bg=PANEL, padx=20, pady=4)
        self._label(details, UI_TEXT["finding_detail"], bg=PANEL, font_obj=self.ui_bold, padx=18, pady=(22, 8))
        self._label(details, textvariable=self.detail_var, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=6)
        tk.Frame(details, bg=PANEL).pack(fill="both", expand=True)
        export_button = self._button_label(details, UI_TEXT["export"], False)
        export_button.bind("<Button-1>", lambda _event: self.export_reports())
        export_button.pack(fill="x", padx=16, pady=(8, 10))
        self._label(details, textvariable=self.status_var, fg=MUTED, bg=PANEL, font_obj=self.ui_small, padx=18, pady=(8, 18))

    def choose_logs(self):
        paths = filedialog.askopenfilenames(title="选择本地日志文件")
        if not paths:
            self.status_var.set("已取消日志选择。")
            return
        self.selected_paths = [Path(path) for path in paths]
        self.log_list_var.set("\n".join(path.name for path in self.selected_paths))
        self.status_var.set(f"已选择 {len(self.selected_paths)} 个本地日志文件。")

    def run_analysis(self):
        if not self.selected_paths:
            self.status_var.set("请先选择本地日志文件。")
            return
        try:
            self.latest_result = analyze_logs(self.selected_paths)
        except OSError as exc:
            self.status_var.set(f"无法分析日志：{exc}")
            return
        self._render_result(self.latest_result)
        self.status_var.set("分析完成。")

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
            self._render_empty_findings("未检测到告警。")
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
            f"严重等级：{finding.severity}\n"
            f"来源位置：{finding.source_file}:{finding.line_number}\n\n"
            f"{evidence}"
        )

    def export_reports(self):
        if self.latest_result is None:
            self.status_var.set("请先运行分析，再导出报告。")
            return
        selected = filedialog.askdirectory(title="选择本地报告输出目录")
        if not selected:
            self.status_var.set("已取消导出。")
            return
        out_dir = Path(selected)
        try:
            export_json(self.latest_result, out_dir / "analysis.json")
            export_csv(self.latest_result, out_dir / "analysis.csv")
            export_markdown(self.latest_result, out_dir / "analysis.md")
        except OSError as exc:
            self.status_var.set(f"无法导出报告：{exc}")
            return
        self.status_var.set(f"报告已导出到 {out_dir}")


def main() -> None:
    app = LogcheckDesktop()
    app.mainloop()


if __name__ == "__main__":
    main()
