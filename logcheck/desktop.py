from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .analysis import analyze_logs, summarize_result
from .config import config_to_dict, default_config, load_config
from .exporters import export_csv, export_json, export_markdown
from .insights import generate_insights
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
NAV_ITEMS = (
    "nav_overview",
    "nav_sources",
    "nav_rules",
    "nav_suspicious",
    "nav_export",
)


@dataclass(frozen=True)
class FindingRow:
    severity: str
    title: str
    subtitle: str
    location: str


@dataclass(frozen=True)
class AnalysisRun:
    label: str
    paths: list[Path]
    result: AnalysisResult


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
        self.source_folder: Path | None = None
        self.source_files: list[Path] = []
        self.selected_source_paths: list[Path] = []
        self.standalone_paths: list[Path] = []
        self.analysis_history: list[AnalysisRun] = []
        self.selected_history_index: int | None = None
        self.latest_result: AnalysisResult | None = None
        self.metric_labels: dict[str, QLabel] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.section_widgets: dict[str, QWidget] = {}
        self.source_file_checks: dict[Path, QCheckBox] = {}
        self.active_rule_path: Path | None = None
        self.active_config = default_config()
        self.current_section = UI_TEXT["nav_overview"]

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
            QPushButton:hover {{
                background: #303030;
                border-color: #666666;
            }}
            QPushButton:pressed {{
                background: #f5f5f5;
                color: #111111;
                padding-top: 11px;
                padding-bottom: 7px;
            }}
            QPushButton#primary {{
                background: {ACCENT};
                color: {BG};
                font-weight: 700;
            }}
            QPushButton#primary:hover, QPushButton#primary:pressed {{
                background: #ffffff;
                color: {BG};
                border-color: #ffffff;
            }}
            QFrame#panel, QFrame#card, QFrame#row {{
                background: {PANEL};
                border: 1px solid {BORDER};
            }}
            QFrame#row {{ background: {PANEL_2}; }}
            QScrollArea {{ border: none; background: {PANEL}; }}
            QScrollArea QWidget {{ background: {PANEL}; color: {TEXT}; }}
            QComboBox {{
                background: {PANEL_2};
                color: {TEXT};
                border: 1px solid {BORDER};
                padding: 8px 10px;
                font-size: {FONT_SIZES["normal"]}pt;
            }}
            QCheckBox {{
                color: {TEXT};
                spacing: 10px;
                font-size: {FONT_SIZES["normal"]}pt;
            }}
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
        for index, key in enumerate(NAV_ITEMS):
            button = QPushButton(UI_TEXT[key])
            button.setObjectName("primary" if index == 0 else "")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, item=key: self._activate_nav(item))
            self.nav_buttons[key] = button
            layout.addWidget(button)
        layout.addStretch(1)
        layout.addWidget(self._label(UI_TEXT["recent"], "bold", MUTED, bold=True))
        layout.addWidget(self._label("samples/auth.log + app.log", "small", MUTED))
        return side

    def _main_area(self) -> QWidget:
        self.workspace_stack = QStackedWidget()
        self.section_widgets["nav_overview"] = self._overview_section()
        self.section_widgets["nav_sources"] = self._sources_section()
        self.section_widgets["nav_rules"] = self._rules_section()
        self.section_widgets["nav_suspicious"] = self._suspicious_section()
        self.section_widgets["nav_export"] = self._export_section()
        for key in NAV_ITEMS:
            self.workspace_stack.addWidget(self.section_widgets[key])
        return self.workspace_stack

    def _overview_section(self) -> QWidget:
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

    def _simple_section(self, title: str, subtitle: str, lines: list[str]) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label(title, "title", bold=True))
        layout.addWidget(self._label(subtitle, "normal", MUTED))
        panel = QFrame()
        panel.setObjectName("panel")
        panel_box = QVBoxLayout(panel)
        panel_box.setContentsMargins(20, 18, 20, 18)
        panel_box.setSpacing(10)
        for line in lines:
            panel_box.addWidget(self._label(line, "normal", MUTED))
        panel_box.addStretch(1)
        layout.addWidget(panel, 1)
        return section

    def _sources_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label(UI_TEXT["nav_sources"], "title", bold=True))
        layout.addWidget(self._label("\u7ba1\u7406\u5f85\u5206\u6790\u7684\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u3002", "normal", MUTED))

        actions = QHBoxLayout()
        folder_button = QPushButton("\u9009\u62e9\u65e5\u5fd7\u6e90\u6587\u4ef6\u5939")
        folder_button.clicked.connect(self.choose_source_folder)
        standalone_button = QPushButton("\u9009\u62e9\u65e5\u5fd7\u6587\u4ef6")
        standalone_button.clicked.connect(self.choose_logs)
        analyze_selected_button = QPushButton("\u5206\u6790\u9009\u4e2d\u65e5\u5fd7")
        analyze_selected_button.setObjectName("primary")
        analyze_selected_button.clicked.connect(self.run_analysis)
        actions.addWidget(folder_button)
        actions.addWidget(standalone_button)
        actions.addWidget(analyze_selected_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_box = QVBoxLayout(panel)
        panel_box.setContentsMargins(20, 18, 20, 18)
        panel_box.setSpacing(10)
        self.sources_section_label = self._label("\u5f53\u524d\u672a\u9009\u62e9\u65e5\u5fd7\u6587\u4ef6\u3002", "normal", MUTED)
        panel_box.addWidget(self.sources_section_label)

        self.source_file_list = QWidget()
        self.source_file_list_layout = QVBoxLayout(self.source_file_list)
        self.source_file_list_layout.setContentsMargins(0, 0, 0, 0)
        self.source_file_list_layout.setSpacing(6)
        self.source_file_list_layout.addStretch(1)
        source_scroll = QScrollArea()
        source_scroll.setWidgetResizable(True)
        source_scroll.setWidget(self.source_file_list)
        panel_box.addWidget(source_scroll, 1)
        layout.addWidget(panel, 1)
        return section

    def _rules_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label(UI_TEXT["nav_rules"], "title", bold=True))
        layout.addWidget(
            self._label("\u67e5\u770b\u6216\u66f4\u6362\u672c\u5730\u5206\u6790\u4f7f\u7528\u7684\u68c0\u6d4b\u89c4\u5219\u3002", "normal", MUTED)
        )

        actions = QHBoxLayout()
        import_button = QPushButton("\u5bfc\u5165\u89c4\u5219\u6587\u4ef6")
        import_button.clicked.connect(self.import_rule_file)
        save_button = QPushButton("\u4fdd\u5b58\u5f53\u524d\u89c4\u5219")
        save_button.clicked.connect(self.save_active_rule_file)
        actions.addWidget(import_button)
        actions.addWidget(save_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_box = QVBoxLayout(panel)
        panel_box.setContentsMargins(20, 18, 20, 18)
        panel_box.setSpacing(10)
        self.rules_section_label = self._label(self._format_rules_text(), "normal", MUTED)
        panel_box.addWidget(self.rules_section_label)
        panel_box.addStretch(1)
        layout.addWidget(panel, 1)
        return section

    def _suspicious_section(self) -> QWidget:
        section = self._simple_section(
            UI_TEXT["nav_suspicious"],
            "\u6839\u636e\u6700\u8fd1\u4e00\u6b21\u672c\u5730\u5206\u6790\u6c47\u603b\u53ef\u7591\u8d26\u53f7\u6216\u5730\u5740\u3002",
            ["\u5c1a\u672a\u8fd0\u884c\u5206\u6790\uff0c\u6682\u65e0\u53ef\u7591\u6765\u6e90\u3002"],
        )
        self.suspicious_sources_label = section.findChildren(QLabel)[-1]
        return section

    def _export_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(14)
        layout.addWidget(self._label(UI_TEXT["nav_export"], "title", bold=True))
        layout.addWidget(
            self._label("\u9009\u62e9\u672c\u6b21\u4f1a\u8bdd\u4e2d\u67d0\u4e00\u6b21\u5206\u6790\u7ed3\u679c\u5bfc\u51fa\u62a5\u544a\u3002", "normal", MUTED)
        )
        panel = QFrame()
        panel.setObjectName("panel")
        panel_box = QVBoxLayout(panel)
        panel_box.setContentsMargins(20, 18, 20, 18)
        panel_box.setSpacing(12)
        self.export_history_combo = QComboBox()
        self.export_history_combo.currentIndexChanged.connect(self._select_history_index)
        panel_box.addWidget(self.export_history_combo)
        export_button = QPushButton(UI_TEXT["export"])
        export_button.setObjectName("primary")
        export_button.clicked.connect(self.export_reports)
        panel_box.addWidget(export_button)
        self.export_history_label = self._label("\u5c1a\u65e0\u53ef\u5bfc\u51fa\u7684\u5206\u6790\u5386\u53f2\u3002", "normal", MUTED)
        panel_box.addWidget(self.export_history_label)
        panel_box.addStretch(1)
        layout.addWidget(panel, 1)
        return section

    def _format_rules_text(self) -> str:
        config = self.active_config
        source = self.active_rule_path.name if self.active_rule_path else "\u9ed8\u8ba4\u89c4\u5219"
        lines = [f"\u89c4\u5219\u6765\u6e90\uff1a{source}", "\u5173\u952e\u8bcd\u89c4\u5219\uff1a"]
        for group, keywords in sorted(config.keywords.items()):
            lines.append(f"- {group}: {', '.join(keywords)}")
        lines.append(
            f"\u91cd\u590d\u5931\u8d25\u767b\u5f55\uff1a{config.brute_force_threshold} "
            f"\u6b21 / {config.brute_force_window_minutes} \u5206\u949f"
        )
        return "\n".join(lines)

    def _refresh_rules_section(self) -> None:
        self.rules_section_label.setText(self._format_rules_text())

    def import_rule_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "\u5bfc\u5165\u68c0\u6d4b\u89c4\u5219",
            "",
            "\u89c4\u5219\u6587\u4ef6 (*.json *.yaml *.yml *.toml);;\u6240\u6709\u6587\u4ef6 (*)",
        )
        if not selected:
            self.status_label.setText("\u5df2\u53d6\u6d88\u89c4\u5219\u5bfc\u5165\u3002")
            return

        rule_path = Path(selected)
        try:
            config = load_config(rule_path)
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"\u89c4\u5219\u5bfc\u5165\u5931\u8d25\uff1a{exc}")
            return

        self.active_rule_path = rule_path
        self.active_config = config
        self._refresh_rules_section()
        self.status_label.setText(f"\u5df2\u5bfc\u5165\u89c4\u5219\u6587\u4ef6\uff1a{rule_path}")

    def save_active_rule_file(self) -> None:
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "\u4fdd\u5b58\u5f53\u524d\u89c4\u5219",
            "rules.json",
            "JSON (*.json);;\u6240\u6709\u6587\u4ef6 (*)",
        )
        if not selected:
            self.status_label.setText("\u5df2\u53d6\u6d88\u89c4\u5219\u4fdd\u5b58\u3002")
            return

        out_path = Path(selected)
        try:
            out_path.write_text(
                json.dumps(config_to_dict(self.active_config), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.status_label.setText(f"\u89c4\u5219\u4fdd\u5b58\u5931\u8d25\uff1a{exc}")
            return
        self.status_label.setText(f"\u89c4\u5219\u5df2\u4fdd\u5b58\u5230 {out_path}")

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
        layout.addWidget(self._label("\u5206\u6790\u6d1e\u5bdf", "bold", bold=True))
        self.insight_summary_label = self._label("\u5c1a\u672a\u751f\u6210\u6d1e\u5bdf\u6458\u8981\u3002", "small", MUTED)
        layout.addWidget(self.insight_summary_label)
        layout.addWidget(self._label(UI_TEXT["finding_detail"], "bold", bold=True))
        self.detail_label = self._label(UI_TEXT["detail_empty"], "small", MUTED)
        self.detail_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(self.detail_label)
        detail_layout.addStretch(1)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setMinimumHeight(150)
        self.detail_scroll.setWidget(detail_widget)
        layout.addWidget(self.detail_scroll, 1)
        self.status_label = self._label(UI_TEXT["status_start"], "small", MUTED)
        layout.addWidget(self.status_label)
        return panel

    def _activate_nav(self, key: str) -> None:
        self._select_nav(key)

    def _select_nav(self, key: str) -> None:
        self.current_section = UI_TEXT[key]
        self.workspace_stack.setCurrentWidget(self.section_widgets[key])
        for nav_key, button in self.nav_buttons.items():
            button.setObjectName("primary" if nav_key == key else "")
            button.style().unpolish(button)
            button.style().polish(button)
        self.status_label.setText(f"\u5df2\u5207\u6362\u5230\uff1a{self.current_section}")

    def choose_logs(self) -> None:
        paths = self.choose_standalone_logs()
        if not paths:
            self.status_label.setText("\u5df2\u53d6\u6d88\u65e5\u5fd7\u9009\u62e9\u3002")
            return
        self.standalone_paths = paths
        self.selected_paths = paths
        self.selected_source_paths = []
        self.logs_label.setText("\n".join(path.name for path in self.selected_paths))
        self.sources_section_label.setText("\n".join(str(path) for path in self.selected_paths))
        self._clear_source_file_checks()
        self.status_label.setText(f"\u5df2\u9009\u62e9 {len(self.selected_paths)} \u4e2a\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u3002")

    def choose_source_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "\u9009\u62e9\u65e5\u5fd7\u6e90\u6587\u4ef6\u5939")
        if not selected:
            self.status_label.setText("\u5df2\u53d6\u6d88\u65e5\u5fd7\u6e90\u9009\u62e9\u3002")
            return
        self.set_log_source_folder(Path(selected))

    def choose_source_folders(self) -> None:
        dialog = QFileDialog(self, "\u9009\u62e9\u65e5\u5fd7\u6e90\u6587\u4ef6\u5939")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        if not dialog.exec():
            self.status_label.setText("\u5df2\u53d6\u6d88\u65e5\u5fd7\u6e90\u9009\u62e9\u3002")
            return
        self.set_log_source_folders([Path(path) for path in dialog.selectedFiles()])

    def choose_standalone_logs(self) -> list[Path]:
        paths, _selected_filter = QFileDialog.getOpenFileNames(self, "\u9009\u62e9\u672c\u5730\u65e5\u5fd7\u6587\u4ef6")
        return [Path(path) for path in paths]

    def discover_source_files(self, folder: Path) -> list[Path]:
        return sorted(path for path in folder.iterdir() if path.is_file())

    def set_log_source_folder(self, folder: Path) -> None:
        self.set_log_source_folders([folder])

    def set_log_source_folders(self, folders: list[Path]) -> None:
        self.source_folder = folders[0] if len(folders) == 1 else None
        self.source_files = [
            file_path
            for folder in folders
            for file_path in self.discover_source_files(folder)
        ]
        self.selected_source_paths = list(self.source_files)
        self.standalone_paths = []
        self.selected_paths = list(self.selected_source_paths)
        folder_text = "\n".join(str(folder) for folder in folders)
        if not self.source_files:
            text = f"{folder_text}\n\u672a\u53d1\u73b0\u53ef\u7528\u65e5\u5fd7\u6587\u4ef6\u3002"
        else:
            text = f"{folder_text}\n{len(self.source_files)} \u4e2a\u6587\u4ef6"
        self.sources_section_label.setText(text)
        self._refresh_source_file_checks()
        self.logs_label.setText("\n".join(path.name for path in self.selected_source_paths) or UI_TEXT["no_logs"])
        self.status_label.setText(f"\u5df2\u8f7d\u5165\u65e5\u5fd7\u6e90\uff1a{len(self.source_files)} \u4e2a\u6587\u4ef6\u3002")

    def _clear_source_file_checks(self) -> None:
        self.source_file_checks = {}
        while self.source_file_list_layout.count():
            item = self.source_file_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_source_file_checks(self) -> None:
        self._clear_source_file_checks()
        if not self.source_files:
            self.source_file_list_layout.addWidget(self._label("\u6682\u65e0\u53ef\u9009\u6587\u4ef6\u3002", "normal", MUTED))
            self.source_file_list_layout.addStretch(1)
            return
        selected = set(self.selected_source_paths)
        for path in self.source_files:
            checkbox = QCheckBox(path.name)
            checkbox.setChecked(path in selected)
            checkbox.stateChanged.connect(self._sync_selected_source_paths)
            self.source_file_checks[path] = checkbox
            self.source_file_list_layout.addWidget(checkbox)
        self.source_file_list_layout.addStretch(1)

    def _sync_selected_source_paths(self) -> None:
        self.selected_source_paths = [
            path for path in self.source_files if self.source_file_checks[path].isChecked()
        ]
        self.selected_paths = list(self.selected_source_paths)
        self.logs_label.setText("\n".join(path.name for path in self.selected_source_paths) or UI_TEXT["no_logs"])

    def _resolve_analysis_paths(self) -> list[Path]:
        if self.selected_source_paths:
            return list(self.selected_source_paths)
        if self.standalone_paths:
            return list(self.standalone_paths)
        return list(self.selected_paths)

    def run_analysis(self) -> None:
        paths = self._resolve_analysis_paths()
        if not paths:
            if self.source_files and not self.selected_source_paths and not self.standalone_paths and not self.selected_paths:
                self.status_label.setText("\u8bf7\u81f3\u5c11\u9009\u62e9\u4e00\u4e2a\u65e5\u5fd7\u6e90\u6587\u4ef6\u518d\u5f00\u59cb\u5206\u6790\u3002")
                return
            self.status_label.setText("\u8bf7\u5148\u9009\u62e9\u672c\u5730\u65e5\u5fd7\u6587\u4ef6\u3002")
            return
        try:
            self.latest_result = analyze_logs(paths, self.active_rule_path)
        except OSError as exc:
            self.status_label.setText(f"\u65e0\u6cd5\u5206\u6790\u65e5\u5fd7\uff1a{exc}")
            return
        self.selected_paths = paths
        self._record_analysis_run(paths, self.latest_result)
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
        self._refresh_suspicious_sources(summary.top_suspicious_sources)
        self._refresh_insight_summary(result)
        self._render_findings(result.findings)

    def _refresh_insight_summary(self, result: AnalysisResult) -> None:
        insights = getattr(result, "insights", None) or generate_insights(result)
        entities = ", ".join(profile.value for profile in insights.entity_profiles[:3])
        if not entities:
            entities = "\u6682\u65e0\u53ef\u7591\u5b9e\u4f53"
        self.insight_summary_label.setText(
            f"\u98ce\u9669\uff1a{insights.risk_level}\n"
            f"{insights.headline}\n"
            f"\u53ef\u7591\u5b9e\u4f53\uff1a{entities}\n"
            f"\u8bc1\u636e\uff1a{insights.evidence_count} \u6761"
        )

    def _refresh_suspicious_sources(self, sources: list[tuple[str, int]]) -> None:
        if not sources:
            self.suspicious_sources_label.setText("\u672a\u68c0\u6d4b\u5230\u53ef\u7591\u6765\u6e90\u3002")
            return
        self.suspicious_sources_label.setText("\n".join(f"{source} - {count}" for source, count in sources))

    def _record_analysis_run(self, paths: list[Path], result: AnalysisResult) -> None:
        label = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.analysis_history.append(AnalysisRun(label=label, paths=list(paths), result=result))
        self.selected_history_index = len(self.analysis_history) - 1
        self._refresh_export_history()

    def _selected_analysis_run(self) -> AnalysisRun | None:
        if self.selected_history_index is None:
            return None
        if not 0 <= self.selected_history_index < len(self.analysis_history):
            return None
        return self.analysis_history[self.selected_history_index]

    def _refresh_export_history(self) -> None:
        self.export_history_combo.blockSignals(True)
        self.export_history_combo.clear()
        if not self.analysis_history:
            self.export_history_label.setText("\u5c1a\u65e0\u53ef\u5bfc\u51fa\u7684\u5206\u6790\u5386\u53f2\u3002")
            self.export_history_combo.addItem("\u5c1a\u65e0\u5206\u6790\u5386\u53f2", None)
            self.export_history_combo.setEnabled(False)
            self.export_history_combo.blockSignals(False)
            return
        self.export_history_combo.setEnabled(True)
        lines = []
        for index, run in enumerate(self.analysis_history):
            marker = "*" if index == self.selected_history_index else "-"
            lines.append(f"{marker} {run.label} ({len(run.paths)} \u4e2a\u6587\u4ef6)")
            self.export_history_combo.addItem(f"{run.label} - {len(run.paths)} \u4e2a\u6587\u4ef6", index)
        if self.selected_history_index is not None:
            self.export_history_combo.setCurrentIndex(self.selected_history_index)
        self.export_history_label.setText("\n".join(lines))
        self.export_history_combo.blockSignals(False)

    def _select_history_index(self, index: int) -> None:
        value = self.export_history_combo.itemData(index)
        if value is None:
            return
        self.selected_history_index = int(value)
        self._refresh_export_history()

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
        evidence = "\n".join(finding.evidence)
        self.detail_label.setText(
            f"{finding.rule_id}\n"
            f"\u4e25\u91cd\u7b49\u7ea7\uff1a{finding.severity}\n"
            f"\u6765\u6e90\u4f4d\u7f6e\uff1a{finding.source_file}:{finding.line_number}\n\n"
            f"{evidence}"
        )

    def export_reports(self) -> None:
        run = self._selected_analysis_run()
        if run is None:
            self.status_label.setText("\u8bf7\u5148\u8fd0\u884c\u5206\u6790\uff0c\u518d\u5bfc\u51fa\u62a5\u544a\u3002")
            return
        selected = QFileDialog.getExistingDirectory(self, "\u9009\u62e9\u672c\u5730\u62a5\u544a\u8f93\u51fa\u76ee\u5f55")
        if not selected:
            self.status_label.setText("\u5df2\u53d6\u6d88\u5bfc\u51fa\u3002")
            return
        out_dir = Path(selected)
        try:
            export_json(run.result, out_dir / "analysis.json")
            export_csv(run.result, out_dir / "analysis.csv")
            export_markdown(run.result, out_dir / "analysis.md")
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
