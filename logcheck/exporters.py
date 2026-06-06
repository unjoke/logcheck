from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

from .models import AnalysisResult


def _metadata(result: AnalysisResult) -> dict[str, object]:
    severities = Counter(finding.severity for finding in result.findings)
    analyzed_sources = sorted(
        {event.source_file for event in result.events if event.source_file}
        or {finding.source_file for finding in result.findings if finding.source_file}
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_events": len(result.events),
        "total_findings": len(result.findings),
        "findings_by_severity": dict(severities),
        "analyzed_sources": analyzed_sources,
        "active_rule_source": getattr(result, "rule_source", None),
    }


def _insights_to_dict(insights: object | None) -> dict[str, object] | None:
    if insights is None:
        return None
    return {
        "risk_level": insights.risk_level,
        "headline": insights.headline,
        "evidence_count": insights.evidence_count,
        "entity_profiles": [profile.__dict__ for profile in insights.entity_profiles],
        "timeline": [item.__dict__ for item in insights.timeline],
        "suggestions": [suggestion.__dict__ for suggestion in insights.suggestions],
    }


def export_json(result: AnalysisResult, path: Path) -> None:
    payload = {
        **_metadata(result),
        "findings": [finding.to_dict() for finding in result.findings],
    }
    insights = _insights_to_dict(result.insights)
    if insights is not None:
        payload["insights"] = insights
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
    ]
    if result.insights is not None:
        insights = result.insights
        lines.extend(
            [
                "## Investigation Insights",
                "",
                f"- Risk level: {insights.risk_level}",
                f"- Summary: {insights.headline}",
                f"- Evidence count: {insights.evidence_count}",
                "",
            ]
        )
        if insights.entity_profiles:
            lines.extend(["### Top Entities", ""])
            for profile in insights.entity_profiles:
                lines.append(
                    f"- {profile.kind} `{profile.value}`: {profile.finding_count} findings, "
                    f"severities {profile.severity_counts}, rules {', '.join(profile.related_rules)}"
                )
                lines.extend(f"  - Evidence: `{line}`" for line in profile.evidence)
            lines.append("")
        if insights.timeline:
            lines.extend(["### Timeline", ""])
            for item in insights.timeline:
                lines.append(f"- {item.label}: {item.severity} {item.rule_id} for {item.entity} in {item.source}")
            lines.append("")
        if insights.suggestions:
            lines.extend(["### Suggestions", ""])
            for suggestion in insights.suggestions:
                lines.append(f"- {suggestion.title}: {suggestion.detail}")
                lines.extend(f"  - Evidence: `{line}`" for line in suggestion.evidence)
            lines.append("")
    lines.extend(
        [
        "## Findings",
        "",
        ]
    )
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
