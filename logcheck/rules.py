from __future__ import annotations

from collections import defaultdict

from .models import DetectionConfig, Event, Finding


SEVERITY_BY_RULE = {
    "failed_login": "medium",
    "invalid_user": "medium",
    "unauthorized_access": "high",
    "permission_denied": "medium",
    "sudo_failure": "high",
    "suspicious_command": "critical",
}


def detect_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_keyword_findings(events, config))
    findings.extend(_suspicious_command_findings(events, config))
    findings.extend(_brute_force_findings(events, config))
    findings.extend(_multi_signal_findings(findings))
    return findings


def _event_text(event: Event) -> str:
    return f"{event.raw_line}\n{event.message or ''}".lower()


def _keyword_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = _event_text(event)
        for rule_name, keywords in config.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    findings.append(
                        Finding(
                            rule_id=f"keyword.{rule_name}",
                            severity=SEVERITY_BY_RULE.get(rule_name, "low"),
                            explanation=f"Matched intrusion indicator keyword: {keyword}",
                            evidence=[event.raw_line],
                            source_file=event.source_file,
                            line_number=event.line_number,
                            timestamp=event.timestamp,
                            source_address=event.source_address,
                            actor=event.actor,
                            target=event.target,
                            matched_keyword=keyword,
                        )
                    )
                    break
    return findings


def _suspicious_command_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = _event_text(event)
        for keyword in config.keywords.get("suspicious_command", []):
            if keyword.lower() in text:
                findings.append(
                    Finding(
                        rule_id="behavior.suspicious_command",
                        severity="high",
                        explanation="Suspicious command execution indicator observed.",
                        evidence=[event.raw_line],
                        source_file=event.source_file,
                        line_number=event.line_number,
                        timestamp=event.timestamp,
                        source_address=event.source_address,
                        actor=event.actor,
                        target=event.target,
                        matched_keyword=keyword,
                        severity_reason="Suspicious command indicators are high priority for local review.",
                        confidence_reason=(
                            "Exact configured suspicious command indicator matched the event text."
                        ),
                    )
                )
                break
    return findings


def _brute_force_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    buckets: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        text = _event_text(event)
        if "failed password" in text or "failed login" in text or "authentication failure" in text:
            key = event.source_address or event.actor or "unknown"
            buckets[key].append(event)

    findings: list[Finding] = []
    for key, bucket in buckets.items():
        if len(bucket) >= config.brute_force_threshold:
            first = bucket[0]
            findings.append(
                Finding(
                    rule_id="correlation.brute_force",
                    severity="high",
                    explanation=(
                        f"{len(bucket)} failed authentication events from {key}; "
                        f"threshold is {config.brute_force_threshold}"
                    ),
                    evidence=[event.raw_line for event in bucket[:5]],
                    source_file=first.source_file,
                    line_number=first.line_number,
                    timestamp=first.timestamp,
                    source_address=first.source_address,
                    actor=first.actor,
                    count=len(bucket),
                )
            )
    return findings


def _multi_signal_findings(findings: list[Finding]) -> list[Finding]:
    buckets: dict[tuple[str, str], list[Finding]] = defaultdict(list)
    for finding in findings:
        if finding.rule_id.startswith("behavior."):
            continue
        if finding.source_address:
            buckets[("source", finding.source_address)].append(finding)
        if finding.actor:
            buckets[("actor", finding.actor)].append(finding)

    correlated: list[Finding] = []
    for (entity_type, entity), bucket in buckets.items():
        distinct_rule_ids = {finding.rule_id for finding in bucket}
        if len(distinct_rule_ids) < 2:
            continue

        first = bucket[0]
        evidence: list[str] = []
        for finding in bucket:
            for item in finding.evidence:
                if item not in evidence:
                    evidence.append(item)

        correlated.append(
            Finding(
                rule_id="behavior.multi_signal_source",
                severity="high",
                explanation=(
                    f"{entity_type.title()} {entity} triggered multiple detection signals."
                ),
                evidence=evidence[:5],
                source_file=first.source_file,
                line_number=first.line_number,
                timestamp=first.timestamp,
                source_address=entity if entity_type == "source" else first.source_address,
                actor=entity if entity_type == "actor" else first.actor,
                count=len(distinct_rule_ids),
                severity_reason="Multiple distinct detection signals raise review priority.",
                confidence_reason="Distinct rule IDs matched events tied to the same entity.",
            )
        )
    return correlated
