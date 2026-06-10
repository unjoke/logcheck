from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Event:
    source_file: str
    line_number: int
    raw_line: str
    timestamp: datetime | None = None
    category: str = "unknown"
    actor: str | None = None
    target: str | None = None
    source_address: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.message is None:
            object.__setattr__(self, "message", self.raw_line)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    explanation: str
    evidence: list[str] = field(default_factory=list)
    source_file: str | None = None
    line_number: int | None = None
    timestamp: datetime | None = None
    source_address: str | None = None
    actor: str | None = None
    target: str | None = None
    matched_keyword: str | None = None
    count: int | None = None
    severity_reason: str | None = None
    confidence_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_address": self.source_address,
            "actor": self.actor,
            "target": self.target,
            "matched_keyword": self.matched_keyword,
            "count": self.count,
            "severity_reason": self.severity_reason,
            "confidence_reason": self.confidence_reason,
        }


@dataclass(frozen=True)
class DetectionConfig:
    keywords: dict[str, list[str]]
    brute_force_threshold: int = 5
    brute_force_window_minutes: int = 10
    behavior_enabled: bool = True
    template_burst_threshold: int = 4
    sequence_window_minutes: int = 10


@dataclass
class AnalysisResult:
    events: list[Event] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    insights: object | None = None
