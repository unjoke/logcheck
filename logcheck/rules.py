from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import unquote_plus

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
    findings.extend(_web_sql_injection_findings(events))
    findings.extend(_suspicious_command_findings(events, config))
    findings.extend(_privilege_escalation_findings(events))
    findings.extend(_brute_force_findings(events, config))
    findings.extend(_multi_signal_findings(findings))
    return findings


def _event_text(event: Event) -> str:
    return f"{event.raw_line}\n{event.message or ''}".lower()


def _decoded_event_text(event: Event) -> str:
    return unquote_plus(_event_text(event))


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


SQL_INJECTION_INDICATORS = (
    "information_schema",
    "select table_name",
    "select flag",
    "substr(",
    "database()",
    " and if(",
    " union select",
)
SQL_INJECTION_BURST_THRESHOLD = 5
SUBSTR_POSITION_RE = re.compile(r"substr\([^,]+,\s*(\d+)\s*,\s*1\s*\)", re.IGNORECASE)


def _access_request_text(event: Event) -> str:
    decoded = event.metadata.get("decoded_request") if event.metadata else None
    if isinstance(decoded, str):
        return decoded.lower()
    return _decoded_event_text(event)


def _access_group_key(event: Event) -> tuple[str, str]:
    source = event.source_address or event.actor or event.source_file or "unknown"
    path = event.target
    if not path and event.metadata:
        raw_path = event.metadata.get("path")
        path = raw_path if isinstance(raw_path, str) else None
    return source, path or "unknown"


def _sql_injection_indicators(text: str) -> set[str]:
    return {indicator for indicator in SQL_INJECTION_INDICATORS if indicator in text}


def _substr_positions(text: str) -> set[int]:
    return {int(match.group(1)) for match in SUBSTR_POSITION_RE.finditer(text)}


def _web_sql_injection_findings(events: list[Event]) -> list[Finding]:
    buckets: dict[tuple[str, str], list[Event]] = defaultdict(list)
    matched_indicators: dict[tuple[str, str], set[str]] = defaultdict(set)
    substr_positions: dict[tuple[str, str], set[int]] = defaultdict(set)
    response_sizes: dict[tuple[str, str], set[int]] = defaultdict(set)
    extraction_targets: dict[tuple[str, str], set[str]] = defaultdict(set)
    for event in events:
        text = _access_request_text(event)
        indicators = _sql_injection_indicators(text)
        if len(indicators) < 2:
            continue
        key = _access_group_key(event)
        buckets[key].append(event)
        matched_indicators[key].update(indicators)
        substr_positions[key].update(_substr_positions(text))
        if "information_schema" in indicators:
            extraction_targets[key].add("information_schema")
        if "select table_name" in indicators:
            extraction_targets[key].add("table names")
        if "select flag" in indicators:
            extraction_targets[key].add("flag")
        if event.metadata:
            response_size = event.metadata.get("response_size")
            if isinstance(response_size, int):
                response_sizes[key].add(response_size)

    findings: list[Finding] = []
    indicator_priority = (
        "substr(",
        " and if(",
        "information_schema",
        "select flag",
        "select table_name",
        "database()",
        " union select",
    )
    indicator_labels = {"substr(": "substr", " and if(": "and if("}
    for key, bucket in buckets.items():
        if len(bucket) < SQL_INJECTION_BURST_THRESHOLD:
            continue
        first = bucket[0]
        source, path = key
        indicators = [
            indicator
            for indicator in indicator_priority
            if indicator in matched_indicators[key]
        ]
        indicators.extend(
            sorted(matched_indicators[key].difference(indicators))
        )
        matched_keyword = ", ".join(
            indicator_labels.get(indicator, indicator) for indicator in indicators
        )
        positions = sorted(substr_positions[key])
        conditional_substr = "substr(" in matched_indicators[key] and " and if(" in matched_indicators[key]
        if positions or conditional_substr:
            traits = ["boolean-blind SQL injection enumeration"]
            if positions:
                traits.append(f"substr positions {positions[0]}-{positions[-1]}")
            if extraction_targets[key]:
                traits.append(f"targets {', '.join(sorted(extraction_targets[key]))}")
            if response_sizes[key]:
                sizes = sorted(response_sizes[key])
                traits.append(f"response sizes {sizes[0]}-{sizes[-1]}")
            confidence_reason = (
                "Grouped request traits indicate " + "; ".join(traits) + "."
            )
        else:
            confidence_reason = (
                "URL-decoded request text matched multiple SQL injection indicators across a burst."
            )
        findings.append(
            Finding(
                rule_id="behavior.web_sql_injection",
                severity="critical",
                explanation=(
                    f"{len(bucket)} URL-decoded web requests from {source} to {path} match SQL injection indicators."
                ),
                evidence=[event.raw_line for event in bucket[:5]],
                source_file=first.source_file,
                line_number=first.line_number,
                timestamp=first.timestamp,
                source_address=first.source_address,
                actor=first.actor,
                target=first.target or (path if path != "unknown" else None),
                matched_keyword=matched_keyword,
                count=len(bucket),
                severity_reason=(
                    "Repeated SQL injection indicators in access logs are critical attack behavior."
                ),
                confidence_reason=confidence_reason,
            )
        )
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
