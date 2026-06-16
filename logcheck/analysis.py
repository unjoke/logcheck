from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import load_rules
from .insights import generate_insights
from .models import AnalysisResult
from .parsers import parse_files
from .rules import compile_findings


@dataclass(frozen=True)
class AnalysisSummary:
    total_events: int
    total_findings: int
    findings_by_severity: dict[str, int]
    top_suspicious_sources: list[tuple[str, int]]


def analyze_logs(
    paths: list[Path],
    rules_path: Path | None = None,
) -> AnalysisResult:
    rules_config = load_rules(rules_path)
    events = parse_files(paths)
    result = AnalysisResult(events=events, findings=compile_findings(events, rules_config))
    result.insights = generate_insights(result)
    return result


def summarize_result(result: AnalysisResult) -> AnalysisSummary:
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    return AnalysisSummary(
        total_events=len(result.events),
        total_findings=len(result.findings),
        findings_by_severity=dict(severities),
        top_suspicious_sources=sources.most_common(5),
    )
