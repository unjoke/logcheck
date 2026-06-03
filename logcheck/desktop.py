from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .analysis import analyze_logs, summarize_result
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult, Finding


UI_TOOLKIT = "PyQt6/Qt"
BG = "#111111"
PANEL = "#1b1b1b"
PANEL_2 = "#242424"
TEXT = "#f3f3f3"
MUTED = "#a8a8a8"
BORDER = "#3a3a3a"
ACCENT = "#f5f5f5"
LOCAL_MODE_TEXT = "\u672c\u5730\u6a21\u5f0f - \u4ec5\u5206\u6790\u672c\u5730\u6587\u4ef6"
FONT_SIZES = {
    "small": 10,
    "normal": 12,
    "bold": 12,
    "title": 28,
    "metric": 28,
}
UI_TEXT = {
    "window_title": "Logcheck \u65e5\u5fd7\u5165\u4fb5\u68c0\u6d4b",
    "brand": "Logcheck",
    "menu_file": "\u6587\u4ef6",
    "menu_analyze": "\u5206\u6790",
    "menu_rules": "\u89c4\u5219",
    "menu_reports": "\u62a5\u544a",
    "menu_help": "\u5e2e\u52a9",
    "sidebar_title": "\u65e5\u5fd7\u5165\u4fb5\u68c0\u6d4b",
    "sidebar_subtitle": "Logcheck \u684c\u9762\u7248",
    "nav_overview": "\u603b\u89c8",
    "nav_sources": "\u65e5\u5fd7\u6e90",
    "nav_rules": "\u68c0\u6d4b\u89c4\u5219",
    "nav_suspicious": "\u53ef\u7591\u6765\u6e90",
    "nav_export": "\u5bfc\u51fa\u62a5\u544a",
    "nav_demo": "\u8bfe\u7a0b\u6f14\u793a",
    "recent": "\u6700\u8fd1\u5206\u6790",
    "settings": "\u8bbe\u7f6e",
    "main_title": "\u5165\u4fb5\u884c\u4e3a\u5206\u6790\u603b\u89c8",
    "main_subtitle": "\u89e3\u6790\u672c\u5730\u65e5\u5fd7\uff0c\u8bc6\u522b\u5931\u8d25\u767b\u5f55\u3001\u8d8a\u6743\u8bbf\u95ee\u548c\u66b4\u529b\u7834\u89e3\u8ff9\u8c61\u3002",
    "select_logs": "\u9009\u62e9\u65e5\u5fd7",
    "run_analysis": "\u5f00\u59cb\u5206\u6790",
    "events": "\u4e8b\u4ef6",
    "events_hint": "\u5df2\u89e3\u6790\u65e5\u5fd7\u8bb0\u5f55",
    "findings": "\u544a\u8b66",
    "findings_hint": "\u68c0\u6d4b\u89c4\u5219\u547d\u4e2d",
    "high": "\u9ad8\u5371",
    "high_hint": "\u4f18\u5148\u590d\u6838\u9879\u76ee",
    "sources": "\u6765\u6e90",
    "sources_hint": "\u53ef\u7591\u8d26\u53f7\u6216\u5730\u5740",
    "finding_queue": "\u544a\u8b66\u961f\u5217",
    "no_analysis": "\u5c1a\u672a\u8fd0\u884c\u5206\u6790\u3002",
    "current_logs": "\u5f53\u524d\u65e5\u5fd7",
    "no_logs": "\u672a\u9009\u62e9\u672c\u5730\u6587\u4ef6\u3002",
    "rule_status": "\u89c4\u5219\u72b6\u6001",
    "rule_keyword": "\u5173\u952e\u8bcd\u6307\u6807\u68c0\u6d4b",
    "rule_repeated": "\u91cd\u590d\u5931\u8d25\u767b\u5f55",
    "rule_severity": "\u4e25\u91cd\u7b49\u7ea7\u5206\u7c7b",
    "finding_detail": "\u544a\u8b66\u8be6\u60c5",
    "detail_empty": "\u9009\u62e9\u4e00\u6761\u544a\u8b66\u67e5\u770b\u8bc1\u636e\u3002",
    "export": "\u5bfc\u51fa JSON / CSV / Markdown",
    "status_start": "\u8bf7\u9009\u62e9\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u5f00\u59cb\u5206\u6790\u3002",
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


def _font(size_key: str, *, bold: bool = False) -> QFont:
    font = QFont("Microsoft YaHei UI", FONT_SIZES[size_key])
    font.setBold(bold)
    return font


class LogcheckDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_paths: list[Path] = []
        self.latest_result: AnalysisResult | None = None
        self.metric_labels: dict[str, QLabel] = {}

        self.setWindowTitle(UI_TEXT["window_title"])
        self.resize(1180, 720)
        self.setMinimumSize(980, 620)
        self.setStyleSheet(self._stylesheet())
        self._build_shell()

    def _stylesheet(self) -> str:
        return f"""
            QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; }}
            QLabel {{ color: {TEXT}; }}
            QPushButton {{
                background: {PANEL_2};
                color: {TEXT};
                border: 1px solid {BORDER};
                padding: 9px 16px;
                font-size: {FONT_SIZES["normal"]}pt;
            }}
            QPushButton#primary {{
                background: {ACCENT};
                color: {BG};
                font-weight: 700;
            }}
            QFrame#panel, QFrame#card, QFrame#row {{
                background: {PANEL};
                border: 1px solid {BORDER};
            }}
            QFrame#row {{ background: {PANEL_2}; }}
            QScrollArea {{ border: none; background: {PANEL}; }}
        """

    def _label(self, text: str, size_key: str = "normal", color: str = TEXT, *, bold: bool = False) -> QLabel:
        label = QLabel(text)
        label.setFont(_font(size_key, bold=bold))
        label.setStyleSheet(f"color: {color};")
        label.setWordWrap(True)
        return label

    def _build_shell(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        body.addWidget(self._main_area(), 1)
        root.addLayout(body, 1)
        self.setCentralWidget(central)

    def _top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(28)
        layout.addWidget(self._label(UI_TEXT["brand"], "bold", bold=True))
        for key in ["menu_file", "menu_analyze", "menu_rules", "menu_reports", "menu_help"]:
            layout.addWidget(self._label(UI_TEXT[key], "normal", MUTED))
        layout.addStretch(1)
        layout.addWidget(self._label(LOCAL_MODE_TEXT, "normal", MUTED))
        return bar

    def _sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("panel")
        side.setFixedWidth(270)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(20, 28, 20, 24)
        layout.setSpacing(8)
        layout.addWidget(self._label(UI_TEXT["sidebar_title"], "title", bold=True))
        layout.addWidget(self._label(UI_TEXT["sidebar_subtitle"], "normal", MUTED))
        layout.addSpacing(18)
        for index, key in enumerate(
            ["nav_overview", "nav_sources", "nav_rules", "nav_suspicious", "nav_export", "nav_demo"]
        ):
            button = QPushButton(UI_TEXT[key])
            button.setObjectName("primary" if index == 0 else "")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)
        layout.addStretch(1)
        layout.addWidget(self._label(UI_TEXT["recent"], "bold", MUTED, bold=True))
        layout.addWidget(self._label("samples/auth.log + app.log", "small", MUTED))
        layout.addSpacing(16)
        layout.addWidget(self._label(UI_TEXT["settings"], "normal"))
        return side

    def _main_area(self) -> QWidget:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(self._label(UI_TEXT["main_title"], "title", bold=True))
        title_box.addWidget(self._label(UI_TEXT["main_subtitle"], "normal", MUTED))
        header.addLayout(title_box, 1)
        select_button = QPushButton(UI_TEXT["select_logs"])
        select_button.clicked.connect(self.choose_logs)
        run_button = QPushButton(UI_TEXT["run_analysis"])
        run_button.setObjectName("primary")
        run_button.clicked.connect(self.run_analysis)
        header.addWidget(select_button)
        header.addWidget(run_button)
        layout.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        for column, (key, title_key, hint_key) in enumerate(
            [
                ("events", "events", "events_hint"),
                ("findings", "findings", "findings_hint"),
                ("high", "high", "high_hint"),
                ("sources", "sources", "sources_hint"),
            ]
        ):
            cards.addWidget(self._metric_card(key, UI_TEXT[title_key], UI_TEXT[hint_key]), 0, column)
        layout.addLayout(cards)

        content = QHBoxLayout()
        content.setSpacing(16)
        content.addWidget(self._finding_panel(), 1)
        content.addWidget(self._details_panel())
        layout.addLayout(content, 1)
        return main

    def _metric_card(self, key: str, title: str, hint: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.addWidget(self._label(title, "small", MUTED))
        value = self._label("0", "metric", bold=True)
        self.metric_labels[key] = value
        box.addWidget(value)
        box.addWidget(self._label(hint, "small", MUTED))
        return card

    def _finding_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(self._label(UI_TEXT["finding_queue"], "bold", bold=True))
        self.finding_rows = QVBoxLayout()
        self.finding_rows.addWidget(self._label(UI_TEXT["no_analysis"], "normal", MUTED))
        self.finding_rows.addStretch(1)
        rows_widget = QWidget()
        rows_widget.setLayout(self.finding_rows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(rows_widget)
        layout.addWidget(scroll, 1)
        return panel

    def _details_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(330)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(self._label(UI_TEXT["current_logs"], "bold", bold=True))
        self.logs_label = self._label(UI_TEXT["no_logs"], "normal", MUTED)
        layout.addWidget(self.logs_label)
        layout.addWidget(self._label(UI_TEXT["rule_status"], "bold", bold=True))
        for key in ["rule_keyword", "rule_repeated", "rule_severity"]:
            layout.addWidget(self._label(f"- {UI_TEXT[key]}", "normal"))
        layout.addWidget(self._label(UI_TEXT["finding_detail"], "bold", bold=True))
        self.detail_label = self._label(UI_TEXT["detail_empty"], "small", MUTED)
        layout.addWidget(self.detail_label)
        layout.addStretch(1)
        export_button = QPushButton(UI_TEXT["export"])
        export_button.clicked.connect(self.export_reports)
        layout.addWidget(export_button)
        self.status_label = self._label(UI_TEXT["status_start"], "small", MUTED)
        layout.addWidget(self.status_label)
        return panel

    def choose_logs(self) -> None:
        paths, _selected_filter = QFileDialog.getOpenFileNames(self, "\u9009\u62e9\u672c\u5730\u65e5\u5fd7\u6587\u4ef6")
        if not paths:
            self.status_label.setText("\u5df2\u53d6\u6d88\u65e5\u5fd7\u9009\u62e9\u3002")
            return
        self.selected_paths = [Path(path) for path in paths]
        self.logs_label.setText("\n".join(path.name for path in self.selected_paths))
        self.status_label.setText(f"\u5df2\u9009\u62e9 {len(self.selected_paths)} \u4e2a\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u3002")

    def run_analysis(self) -> None:
        if not self.selected_paths:
            self.status_label.setText("\u8bf7\u5148\u9009\u62e9\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u3002")
            return
        try:
            self.latest_result = analyze_logs(self.selected_paths)
        except OSError as exc:
            self.status_label.setText(f"\u65e0\u6cd5\u5206\u6790\u65e5\u5fd7\uff1a{exc}")
            return
        self._render_result(self.latest_result)
        self.status_label.setText("\u5206\u6790\u5b8c\u6210\u3002")

    def _render_result(self, result: AnalysisResult) -> None:
        summary = summarize_result(result)
        high_count = sum(
            count
            for severity, count in summary.findings_by_severity.items()
            if severity in {"high", "critical"}
        )
        self.metric_labels["events"].setText(str(summary.total_events))
        self.metric_labels["findings"].setText(str(summary.total_findings))
        self.metric_labels["high"].setText(str(high_count))
        self.metric_labels["sources"].setText(str(len(summary.top_suspicious_sources)))
        self._render_findings(result.findings)

    def _clear_findings(self) -> None:
        while self.finding_rows.count():
            item = self.finding_rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_findings(self, findings: list[Finding]) -> None:
        self._clear_findings()
        if not findings:
            self.finding_rows.addWidget(self._label("\u672a\u68c0\u6d4b\u5230\u544a\u8b66\u3002", "normal", MUTED))
            self.finding_rows.addStretch(1)
            return
        for finding in findings:
            row = format_finding_row(finding)
            frame = QFrame()
            frame.setObjectName("row")
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            box = QHBoxLayout(frame)
            box.setContentsMargins(12, 10, 12, 10)
            severity = self._label(row.severity, "small", BG, bold=True)
            severity.setAlignment(Qt.AlignmentFlag.AlignCenter)
            severity.setFixedWidth(86)
            severity.setStyleSheet(f"background: {TEXT}; color: {BG}; padding: 6px;")
            text_box = QVBoxLayout()
            text_box.addWidget(self._label(row.title, "bold", bold=True))
            text_box.addWidget(self._label(f"{row.subtitle}  |  {row.location}", "small", MUTED))
            box.addWidget(severity)
            box.addLayout(text_box, 1)
            frame.mousePressEvent = lambda _event, item=finding: self._show_finding_detail(item)
            self.finding_rows.addWidget(frame)
        self.finding_rows.addStretch(1)

    def _show_finding_detail(self, finding: Finding) -> None:
        evidence = "\n".join(finding.evidence[:4])
        self.detail_label.setText(
            f"{finding.rule_id}\n"
            f"\u4e25\u91cd\u7b49\u7ea7\uff1a{finding.severity}\n"
            f"\u6765\u6e90\u4f4d\u7f6e\uff1a{finding.source_file}:{finding.line_number}\n\n"
            f"{evidence}"
        )

    def export_reports(self) -> None:
        if self.latest_result is None:
            self.status_label.setText("\u8bf7\u5148\u8fd0\u884c\u5206\u6790\uff0c\u518d\u5bfc\u51fa\u62a5\u544a\u3002")
            return
        selected = QFileDialog.getExistingDirectory(self, "\u9009\u62e9\u672c\u5730\u62a5\u544a\u8f93\u51fa\u76ee\u5f55")
        if not selected:
            self.status_label.setText("\u5df2\u53d6\u6d88\u5bfc\u51fa\u3002")
            return
        out_dir = Path(selected)
        try:
            export_json(self.latest_result, out_dir / "analysis.json")
            export_csv(self.latest_result, out_dir / "analysis.csv")
            export_markdown(self.latest_result, out_dir / "analysis.md")
        except OSError as exc:
            self.status_label.setText(f"\u65e0\u6cd5\u5bfc\u51fa\u62a5\u544a\uff1a{exc}")
            return
        self.status_label.setText(f"\u62a5\u544a\u5df2\u5bfc\u51fa\u5230 {out_dir}")


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = LogcheckDesktop()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
