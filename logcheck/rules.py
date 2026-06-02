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
    findings.extend(_brute_force_findings(events, config))
    return findings


def _keyword_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = f"{event.raw_line}\n{event.message or ''}".lower()
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


def _brute_force_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    buckets: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        text = f"{event.raw_line}\n{event.message or ''}".lower()
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
