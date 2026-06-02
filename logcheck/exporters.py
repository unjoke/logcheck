from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

from .models import AnalysisResult


def _metadata(result: AnalysisResult) -> dict[str, object]:
    severities = Counter(finding.severity for finding in result.findings)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_events": len(result.events),
        "total_findings": len(result.findings),
        "findings_by_severity": dict(severities),
    }


def export_json(result: AnalysisResult, path: Path) -> None:
    payload = {
        **_metadata(result),
        "findings": [finding.to_dict() for finding in result.findings],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_csv(result: AnalysisResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rule_id",
        "severity",
        "source_file",
        "line_number",
        "source_address",
        "actor",
        "matched_keyword",
        "count",
        "explanation",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for finding in result.findings:
            data = finding.to_dict()
            writer.writerow({field: data.get(field) for field in fields})


def export_markdown(result: AnalysisResult, path: Path) -> None:
    meta = _metadata(result)
    lines = [
        "# Log Intrusion Analysis Report",
        "",
        f"- Total events: {meta['total_events']}",
        f"- Total findings: {meta['total_findings']}",
        f"- Findings by severity: {meta['findings_by_severity']}",
        "",
        "## Findings",
        "",
    ]
    for finding in result.findings:
        lines.extend(
            [
                f"### {finding.rule_id} ({finding.severity})",
                "",
                f"- Source: {finding.source_file}:{finding.line_number}",
                f"- Address: {finding.source_address or 'unknown'}",
                f"- Explanation: {finding.explanation}",
                "- Evidence:",
            ]
        )
        lines.extend(f"  - `{line}`" for line in finding.evidence)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
