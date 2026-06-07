from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from typing import Any

from .models import AnalysisResult


def _serialize_insights(insights: object | None) -> dict[str, Any] | None:
    if insights is None:
        return None
    if is_dataclass(insights):
        return asdict(insights)
    return {
        "risk_level": getattr(insights, "risk_level", None),
        "headline": getattr(insights, "headline", None),
        "evidence_count": getattr(insights, "evidence_count", None),
        "entity_profiles": [
            asdict(profile) if is_dataclass(profile) else dict(profile)
            for profile in getattr(insights, "entity_profiles", [])
        ],
        "timeline": [
            asdict(item) if is_dataclass(item) else dict(item)
            for item in getattr(insights, "timeline", [])
        ],
        "suggestions": [
            asdict(suggestion) if is_dataclass(suggestion) else dict(suggestion)
            for suggestion in getattr(insights, "suggestions", [])
        ],
    }


def serialize_result(result: AnalysisResult) -> dict[str, Any]:
    severities = Counter(finding.severity for finding in result.findings)
    sources = sorted(
        {event.source_file for event in result.events if event.source_file}
        or {finding.source_file for finding in result.findings if finding.source_file}
    )
    payload: dict[str, Any] = {
        "summary": {
            "total_events": len(result.events),
            "total_findings": len(result.findings),
            "findings_by_severity": dict(severities),
            "analyzed_sources": sources,
        },
        "diagnostics": list(result.diagnostics),
        "findings": [finding.to_dict() for finding in result.findings],
        "events": [
            {
                "source_file": event.source_file,
                "line_number": event.line_number,
                "raw_line": event.raw_line,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "category": event.category,
                "actor": event.actor,
                "target": event.target,
                "source_address": event.source_address,
                "message": event.message,
            }
            for event in result.events[:200]
        ],
    }
    insights = _serialize_insights(result.insights)
    if insights is not None:
        payload["insights"] = insights
    return payload
