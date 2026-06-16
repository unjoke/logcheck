from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import unquote_plus

from .ip_context import classify_ip_address
from .models import (
    CorrelationResult,
    CorrelationRule,
    Event,
    Finding,
    IndicatorMatch,
    IndicatorRule,
    PatternResult,
    PatternRule,
    RuleConfig,
)


# ── Helper functions (kept from old rules.py) ─────────────

def _event_text(event: Event) -> str:
    return f"{event.raw_line}\n{event.message or ''}".lower()


def _decoded_event_text(event: Event) -> str:
    return unquote_plus(_event_text(event))


def _representative_evidence(events: list[Event], limit: int = 6) -> list[str]:
    evidence: list[str] = []
    seen: set[str] = set()
    for event in events:
        if event.raw_line in seen:
            continue
        evidence.append(event.raw_line)
        seen.add(event.raw_line)
        if len(evidence) >= limit:
            break
    return evidence


# ── ScoreCompiler ────────────────────────────────────────

class ScoreCompiler:
    """Maps scores to severity and calculates confidence."""

    def __init__(self, thresholds: dict[str, int]) -> None:
        self.thresholds = thresholds

    def score_to_severity(self, score: int, confidence: int) -> str:
        if score >= self.thresholds.get("critical", 80):
            return "critical"
        if score >= self.thresholds.get("high", 50) and confidence < 40:
            return "critical"
        if score >= self.thresholds.get("high", 50):
            return "high"
        if score >= self.thresholds.get("medium", 20):
            return "medium"
        return "low"

    def calculate_confidence(
        self,
        distinct_indicator_count: int,
        indicator_ids: list[str],
        has_decoded: bool = False,
        has_response_variance: bool = False,
        substr_positions_count: int = 0,
    ) -> int:
        base = 15 * distinct_indicator_count
        bonuses = 0
        if has_decoded:
            bonuses += 5
        if has_response_variance:
            bonuses += 5
        if substr_positions_count >= 5:
            bonuses += 5
        return min(base + bonuses, 100)

    def apply_cap(self, score: int, cap: int) -> int:
        return min(score, cap)


# ── IndicatorScanner ─────────────────────────────────────

class IndicatorScanner:
    """Scans individual events against indicator rules."""

    def __init__(self, rules: list[IndicatorRule]) -> None:
        self._rules = rules
        self._compiled_regex: dict[str, re.Pattern] = {}
        for rule in rules:
            if rule.regex:
                self._compiled_regex[rule.id] = re.compile(rule.regex, re.IGNORECASE)

    def scan(self, event: Event, event_index: int) -> list[IndicatorMatch]:
        text = _event_text(event)
        decoded = _decoded_event_text(event)
        matches: list[IndicatorMatch] = []

        for rule in self._rules:
            if rule.event_category and event.category != rule.event_category:
                continue

            # Status code filtering
            if rule.status_codes or rule.status_not:
                status_code = event.metadata.get("status_code") if event.metadata else None
                if isinstance(status_code, int):
                    if rule.status_not and status_code in rule.status_not:
                        continue
                    if rule.status_codes and status_code not in rule.status_codes:
                        continue

            matched_keyword = None

            if rule.id in self._compiled_regex:
                pattern = self._compiled_regex[rule.id]
                if pattern.search(text) or pattern.search(decoded):
                    matched_keyword = f"regex:{rule.regex}"
            elif rule.text_contains:
                for keyword in rule.text_contains:
                    kw = keyword.lower()
                    if kw in text or kw in decoded:
                        matched_keyword = keyword
                        break

            if matched_keyword is not None:
                matches.append(IndicatorMatch(
                    rule_id=rule.id,
                    category=rule.category,
                    event_index=event_index,
                    score=rule.score,
                    source_address=event.source_address,
                    target=event.target,
                    matched_keyword=matched_keyword,
                ))

        return matches


# ── PatternDetector ──────────────────────────────────────

def _pattern_group_key(match: IndicatorMatch) -> tuple[str, str]:
    source = match.source_address or "unknown"
    target = match.target or "unknown"
    return source, target


class PatternDetector:
    """Detects multi-event behavior patterns from indicator matches."""

    def __init__(self, rules: list[PatternRule]) -> None:
        self._rules = rules

    def detect(
        self,
        matches: list[IndicatorMatch],
        events: dict[int, Event],
    ) -> list[PatternResult]:
        groups: dict[tuple[str, str], list[IndicatorMatch]] = defaultdict(list)
        for match in matches:
            groups[_pattern_group_key(match)].append(match)

        results: list[PatternResult] = []
        for rule in self._rules:
            for key, group_matches in groups.items():
                if len(group_matches) < rule.min_events:
                    continue
                group_indicator_ids = {m.rule_id for m in group_matches}
                required = set(rule.require_indicators)
                if not required.issubset(group_indicator_ids):
                    continue

                indicator_sum = sum(m.score for m in group_matches)
                final_score = int(indicator_sum * rule.multiplier + rule.score)
                final_score = min(final_score, rule.max_final_score)
                final_score = min(final_score, 100)

                results.append(PatternResult(
                    rule_id=rule.id,
                    category=rule.category,
                    group_key=key,
                    indicator_ids=sorted(required),
                    event_count=len(group_matches),
                    indicator_score_sum=indicator_sum,
                    multiplier=rule.multiplier,
                    pattern_score=rule.score,
                    final_score=final_score,
                    evidence_indices=[m.event_index for m in group_matches],
                ))

        return results


# ── CorrelationEngine ────────────────────────────────────

class CorrelationEngine:
    """Detects cross-entity/cross-category correlations."""

    def __init__(self, rules: list[CorrelationRule]) -> None:
        self._rules = rules

    def detect(self, pattern_results: list[PatternResult]) -> list[CorrelationResult]:
        results: list[CorrelationResult] = []
        for rule in self._rules:
            if not rule.enabled:
                continue

            source_categories: dict[str, set[str]] = defaultdict(set)
            for pr in pattern_results:
                source = pr.group_key[0]
                source_categories[source].add(pr.category)

            for source, categories in source_categories.items():
                if len(categories) >= rule.min_distinct_categories:
                    results.append(CorrelationResult(
                        rule_id=rule.id,
                        entity=source,
                        distinct_categories=len(categories),
                        bonus_score=rule.score,
                    ))
        return results


# ── Pipeline Orchestrator ────────────────────────────────

def _event_to_finding(
    event: Event,
    match: IndicatorMatch,
    score: int,
    confidence: int,
    severity: str,
) -> Finding:
    return Finding(
        rule_id=f"indicator.{match.rule_id}",
        severity=severity,
        score=score,
        confidence=confidence,
        rule_tier="indicator",
        indicator_ids=[match.rule_id],
        explanation=f"Matched indicator: {match.matched_keyword}",
        evidence=[event.raw_line],
        source_file=event.source_file,
        line_number=event.line_number,
        timestamp=event.timestamp,
        source_address=event.source_address,
        actor=event.actor,
        target=event.target,
        matched_keyword=match.matched_keyword,
        severity_reason=f"Score {score}/100 from indicator '{match.rule_id}'",
        confidence_reason=f"Single indicator match ({match.rule_id})",
    )


def compile_findings(events: list[Event], config: RuleConfig) -> list[Finding]:
    """Run full scoring pipeline and return compiled findings."""
    compiler = ScoreCompiler(config.severity_thresholds)
    scanner = IndicatorScanner(config.indicator_rules)
    pattern_detector = PatternDetector(config.pattern_rules)
    correlation_engine = CorrelationEngine(config.correlation_rules)

    # Phase 1: Scan all events
    event_map: dict[int, Event] = {i: e for i, e in enumerate(events)}
    all_matches: list[IndicatorMatch] = []
    for i, event in enumerate(events):
        all_matches.extend(scanner.scan(event, i))

    # Phase 2: Detect patterns
    pattern_results = pattern_detector.detect(all_matches, event_map)

    # Phase 3: Correlation
    correlation_results = correlation_engine.detect(pattern_results)

    findings: list[Finding] = []

    # Collect indices used in patterns
    pattern_indices: set[int] = set()
    for pr in pattern_results:
        pattern_indices.update(pr.evidence_indices)

    # Emit pattern findings
    for pr in pattern_results:
        evidence_events = [event_map[idx] for idx in pr.evidence_indices[:20]]
        source, target = pr.group_key

        has_decoded = any(
            e.metadata and e.metadata.get("decoded_request")
            for e in evidence_events
        )
        response_sizes = {
            e.metadata.get("response_size")
            for e in evidence_events
            if e.metadata and isinstance(e.metadata.get("response_size"), int)
        }
        has_response_variance = len(response_sizes) > 1

        confidence = compiler.calculate_confidence(
            distinct_indicator_count=len(pr.indicator_ids),
            indicator_ids=pr.indicator_ids,
            has_decoded=has_decoded,
            has_response_variance=has_response_variance,
        )

        final_score = pr.final_score
        for cr in correlation_results:
            if cr.entity == source:
                final_score = min(final_score + cr.bonus_score, 100)

        severity = compiler.score_to_severity(final_score, confidence)

        first_event = evidence_events[0] if evidence_events else None
        conf_reason = (
            f"Confidence {confidence}/100: {len(pr.indicator_ids)} distinct indicators"
            + (" + decoded evidence" if has_decoded else "")
            + (" + response variance" if has_response_variance else "")
        )

        findings.append(Finding(
            rule_id=f"pattern.{pr.rule_id}",
            severity=severity,
            score=final_score,
            confidence=confidence,
            rule_tier="pattern",
            indicator_ids=pr.indicator_ids,
            explanation=(
                f"{pr.event_count} events from {source} to {target} "
                f"matched indicators: {', '.join(pr.indicator_ids)}"
            ),
            evidence=_representative_evidence(evidence_events),
            source_file=first_event.source_file if first_event else None,
            line_number=first_event.line_number if first_event else None,
            timestamp=first_event.timestamp if first_event else None,
            source_address=first_event.source_address if first_event else None,
            actor=first_event.actor if first_event else None,
            target=target if target != "unknown" else None,
            matched_keyword=", ".join(pr.indicator_ids),
            count=pr.event_count,
            severity_reason=(
                f"Score {final_score}/100: pattern '{pr.rule_id}' with "
                f"{pr.event_count} events"
            ),
            confidence_reason=conf_reason,
        ))

    # Emit unmatched indicator-only findings
    for match in all_matches:
        if match.event_index in pattern_indices:
            continue
        event = event_map[match.event_index]
        confidence = compiler.calculate_confidence(
            distinct_indicator_count=1,
            indicator_ids=[match.rule_id],
        )
        severity = compiler.score_to_severity(match.score, confidence)
        findings.append(_event_to_finding(event, match, match.score, confidence, severity))

    return findings
