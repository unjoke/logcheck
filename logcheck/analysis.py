from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import load_config
from .models import AnalysisResult
from .parsers import parse_files
from .rules import detect_findings


@dataclass(frozen=True)
class AnalysisSummary:
    total_events: int
    total_findings: int
    findings_by_severity: dict[str, int]
    top_suspicious_sources: list[tuple[str, int]]


def analyze_logs(paths: list[Path], config_path: Path | None = None) -> AnalysisResult:
    config = load_config(config_path)
    events = parse_files(paths)
    return AnalysisResult(events=events, findings=detect_findings(events, config))


def summarize_result(result: AnalysisResult) -> AnalysisSummary:
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    return AnalysisSummary(
        total_events=len(result.events),
        total_findings=len(result.findings),
        findings_by_severity=dict(severities),
        top_suspicious_sources=sources.most_common(5),
    )
