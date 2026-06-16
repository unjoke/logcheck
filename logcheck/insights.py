from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .models import AnalysisResult, Finding


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class EntityProfile:
    kind: str
    value: str
    finding_count: int
    severity_counts: dict[str, int]
    related_rules: list[str]
    evidence: list[str] = field(default_factory=list)
    avg_score: float = 0.0
    avg_confidence: float = 0.0


@dataclass(frozen=True)
class TimelineHighlight:
    label: str
    severity: str
    rule_id: str
    entity: str
    source: str


@dataclass(frozen=True)
class RemediationSuggestion:
    title: str
    detail: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisInsights:
    risk_level: str
    headline: str
    evidence_count: int
    entity_profiles: list[EntityProfile] = field(default_factory=list)
    timeline: list[TimelineHighlight] = field(default_factory=list)
    suggestions: list[RemediationSuggestion] = field(default_factory=list)


def generate_insights(result: AnalysisResult) -> AnalysisInsights:
    if not result.findings:
        return AnalysisInsights(
            risk_level="low",
            headline="No configured rule patterns were detected in the analyzed local logs.",
            evidence_count=0,
            suggestions=[
                RemediationSuggestion(
                    title="Review coverage",
                    detail="Confirm the selected local logs and active rules cover the activity you intended to inspect.",
                )
            ],
        )

    risk_level = max(
        (finding.severity for finding in result.findings),
        key=lambda severity: SEVERITY_ORDER.get(severity, 0),
    )
    profiles = _entity_profiles(result.findings)
    return AnalysisInsights(
        risk_level=risk_level,
        headline=f"{len(result.findings)} local findings require review; highest severity is {risk_level}.",
        evidence_count=sum(len(finding.evidence) for finding in result.findings),
        entity_profiles=profiles,
        timeline=_timeline(result.findings),
        suggestions=_suggestions(risk_level, profiles),
    )


def _entity_profiles(findings: list[Finding]) -> list[EntityProfile]:
    grouped: dict[tuple[str, str], list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[_entity_key(finding)].append(finding)

    profiles: list[EntityProfile] = []
    for (kind, value), entity_findings in grouped.items():
        severity_counts = Counter(finding.severity for finding in entity_findings)
        evidence: list[str] = []
        for finding in entity_findings:
            evidence.extend(finding.evidence)
        scores = [f.score for f in entity_findings]
        confidences = [f.confidence for f in entity_findings]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        profiles.append(
            EntityProfile(
                kind=kind,
                value=value,
                finding_count=len(entity_findings),
                severity_counts=dict(severity_counts),
                related_rules=sorted({finding.rule_id for finding in entity_findings}),
                evidence=evidence[:5],
                avg_score=round(avg_score, 1),
                avg_confidence=round(avg_confidence, 1),
            )
        )

    return sorted(
        profiles,
        key=lambda profile: (
            -profile.finding_count,
            -max(SEVERITY_ORDER.get(severity, 0) for severity in profile.severity_counts),
            profile.kind,
            profile.value,
        ),
    )


def _timeline(findings: list[Finding]) -> list[TimelineHighlight]:
    ordered = sorted(
        enumerate(findings),
        key=lambda item: (
            item[1].timestamp is None,
            item[1].timestamp.isoformat() if item[1].timestamp else "",
            item[1].source_file or "",
            item[1].line_number or 0,
            item[0],
        ),
    )
    return [
        TimelineHighlight(
            label=_timeline_label(finding),
            severity=finding.severity,
            rule_id=finding.rule_id,
            entity=_entity_key(finding)[1],
            source=_source_label(finding),
        )
        for _, finding in ordered
    ]


def _suggestions(risk_level: str, profiles: list[EntityProfile]) -> list[RemediationSuggestion]:
    evidence = profiles[0].evidence[:3] if profiles else []
    top_score = profiles[0].avg_score if profiles else 0.0
    score_hint = f" (top entity avg score: {top_score})" if top_score > 0 else ""
    return [
        RemediationSuggestion(
            title="Review highlighted evidence",
            detail=f"Manually compare the {risk_level} findings with nearby local log entries and documented maintenance activity.{score_hint}",
            evidence=evidence,
        ),
        RemediationSuggestion(
            title="Audit affected accounts and sources",
            detail="Check whether named accounts, addresses, and files match expected activity for the reviewed time period.",
            evidence=evidence,
        ),
        RemediationSuggestion(
            title="Tune local rules",
            detail="Adjust configured rule patterns after review so recurring benign events are documented and future findings stay focused.",
        ),
    ]


def _entity_key(finding: Finding) -> tuple[str, str]:
    if finding.source_address:
        return ("source_address", finding.source_address)
    if finding.actor:
        return ("actor", finding.actor)
    if finding.source_file:
        return ("source_file", finding.source_file)
    return ("unknown", "unknown")


def _timeline_label(finding: Finding) -> str:
    if finding.timestamp:
        return finding.timestamp.isoformat()
    return _source_label(finding)


def _source_label(finding: Finding) -> str:
    if finding.source_file and finding.line_number is not None:
        return f"{finding.source_file}:{finding.line_number}"
    if finding.source_file:
        return finding.source_file
    return "unknown"
