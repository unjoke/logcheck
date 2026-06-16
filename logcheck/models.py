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
    metadata: dict[str, object] = field(default_factory=dict)

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
    score: int = 0
    confidence: int = 0
    rule_tier: str = "indicator"
    indicator_ids: list[str] = field(default_factory=list)

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
            "score": self.score,
            "confidence": self.confidence,
            "rule_tier": self.rule_tier,
            "indicator_ids": self.indicator_ids,
        }


@dataclass(frozen=True)
class DetectionConfig:
    keywords: dict[str, list[str]]
    brute_force_threshold: int = 5
    brute_force_window_minutes: int = 10


@dataclass
class AnalysisResult:
    events: list[Event] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    insights: object | None = None


@dataclass(frozen=True)
class IndicatorMatch:
    rule_id: str
    category: str
    event_index: int
    score: int
    source_address: str | None = None
    target: str | None = None
    matched_keyword: str | None = None


@dataclass(frozen=True)
class PatternResult:
    rule_id: str
    category: str
    group_key: tuple[str, str]
    indicator_ids: list[str]
    event_count: int
    indicator_score_sum: int
    multiplier: float
    pattern_score: int
    final_score: int
    evidence_indices: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class CorrelationResult:
    rule_id: str
    entity: str
    distinct_categories: int
    bonus_score: int


@dataclass(frozen=True)
class IndicatorRule:
    id: str
    category: str
    description: str
    weight: int
    score: int
    event_category: str | None = None
    text_contains: list[str] = field(default_factory=list)
    regex: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class PatternRule:
    id: str
    category: str
    description: str
    require_indicators: list[str] = field(default_factory=list)
    min_events: int = 2
    multiplier: float = 1.0
    score: int = 0
    max_final_score: int = 100
    enabled: bool = True


@dataclass(frozen=True)
class CorrelationRule:
    id: str
    description: str
    min_distinct_categories: int = 2
    require_source_global: bool = False
    min_findings: int = 2
    score: int = 0
    enabled: bool = True


@dataclass(frozen=True)
class RuleConfig:
    indicator_rules: list[IndicatorRule] = field(default_factory=list)
    pattern_rules: list[PatternRule] = field(default_factory=list)
    correlation_rules: list[CorrelationRule] = field(default_factory=list)
    severity_thresholds: dict[str, int] = field(default_factory=lambda: {
        "low": 0, "medium": 20, "high": 50, "critical": 80
    })
    brute_force_threshold: int = 5
    brute_force_window_minutes: int = 10
