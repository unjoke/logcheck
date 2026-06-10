from __future__ import annotations

from collections import defaultdict
import re

from .models import DetectionConfig, Event, Finding


SEVERITY_BY_RULE = {
    "failed_login": "medium",
    "invalid_user": "medium",
    "unauthorized_access": "high",
    "permission_denied": "medium",
    "sudo_failure": "high",
    "suspicious_command": "critical",
}
SUSPICIOUS_TEMPLATE_TERMS = (
    "failed password",
    "failed login",
    "authentication failure",
    "invalid user",
    "unauthorized access",
    "permission denied",
    "sudo",
    "su:",
    "/etc/shadow",
    "/root",
    "/admin",
    "curl http",
    "wget http",
    "nc -e",
    "bash -i",
)


def detect_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_keyword_findings(events, config))
    findings.extend(_suspicious_command_findings(events, config))
    findings.extend(_privilege_escalation_findings(events))
    findings.extend(_brute_force_findings(events, config))
    findings.extend(_template_burst_findings(events, config))
    findings.extend(_multi_signal_findings(findings))
    return findings


def _event_text(event: Event) -> str:
    return f"{event.raw_line}\n{event.message or ''}".lower()


def _normalize_template(text: str) -> str:
    template = text.lower()
    template = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<ip>", template)
    template = re.sub(r"\b[0-9a-f]{12,}\b", "<hex>", template)
    template = re.sub(r"(['\"])(?:(?=(\\?))\2.)*?\1", "<quoted>", template)
    template = re.sub(r"/[a-z0-9_./-]+", "<path>", template)
    template = re.sub(r"\b\d+\b", "<num>", template)
    template = re.sub(r"\s+", " ", template).strip()
    return template


def _is_suspicious_template(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in SUSPICIOUS_TEMPLATE_TERMS)


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


PRIVILEGE_ESCALATION_INDICATORS = (
    "sudo:auth",
    "sudo failure",
    "su:auth",
    "authentication failure; user=root",
    "/etc/shadow",
    "/root",
    "/admin",
)


def _privilege_escalation_findings(events: list[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        text = _event_text(event)
        matched = next(
            (
                indicator
                for indicator in PRIVILEGE_ESCALATION_INDICATORS
                if indicator.lower() in text
            ),
            None,
        )
        if matched is None:
            continue
        findings.append(
            Finding(
                rule_id="behavior.privilege_escalation",
                severity="high",
                explanation="Privilege escalation indicator observed in local log evidence.",
                evidence=[event.raw_line],
                source_file=event.source_file,
                line_number=event.line_number,
                timestamp=event.timestamp,
                source_address=event.source_address,
                actor=event.actor,
                target=event.target,
                matched_keyword=matched,
                severity_reason="Privilege escalation indicators are high priority for local review.",
                confidence_reason=(
                    "Exact configured privilege-escalation indicator matched the event text."
                ),
            )
        )
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


def _template_burst_findings(events: list[Event], config: DetectionConfig) -> list[Finding]:
    if not config.behavior_enabled:
        return []

    buckets: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for event in events:
        text = _event_text(event)
        if not _is_suspicious_template(text):
            continue
        entity = event.source_address or event.actor or "unknown"
        buckets[(entity, _normalize_template(text))].append(event)

    findings: list[Finding] = []
    for (entity, template), bucket in buckets.items():
        if len(bucket) < config.template_burst_threshold:
            continue
        first = bucket[0]
        findings.append(
            Finding(
                rule_id="behavior.template_burst",
                severity="high",
                explanation=(
                    f"{len(bucket)} suspicious local events matched normalized template "
                    f"`{template}` for {entity}."
                ),
                evidence=[event.raw_line for event in bucket[:5]],
                source_file=first.source_file,
                line_number=first.line_number,
                timestamp=first.timestamp,
                source_address=first.source_address,
                actor=first.actor,
                target=first.target,
                count=len(bucket),
                severity_reason=(
                    "Repeated suspicious template activity meets the configured burst threshold."
                ),
                confidence_reason=(
                    "Variable tokens were normalized and repeated raw local evidence matched "
                    "the same suspicious template."
                ),
            )
        )
    return findings


def _multi_signal_findings(findings: list[Finding]) -> list[Finding]:
    buckets: dict[tuple[str, str], list[Finding]] = defaultdict(list)
    for finding in findings:
        if finding.rule_id.startswith(("behavior.", "correlation.")):
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
