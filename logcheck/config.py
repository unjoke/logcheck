from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .models import (
    CorrelationRule,
    IndicatorRule,
    PatternRule,
    RuleConfig,
)


DEFAULT_SEVERITY_THRESHOLDS = {"low": 0, "medium": 20, "high": 50, "critical": 80}


def _validate_score_range(value: int, field: str, rule_id: str) -> None:
    if not (0 <= value <= 100):
        raise ValueError(
            f"Rule '{rule_id}': {field} must be 0-100, got {value}"
        )


def _validate_indicator_rule(data: dict) -> IndicatorRule:
    rule_id = data.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        raise ValueError("indicator_rules: 'id' is required and must be a string")
    category = data.get("category", "general")
    description = data.get("description", "")
    weight = data.get("weight", 1)
    score = data.get("score", 0)
    _validate_score_range(score, "score", rule_id)
    return IndicatorRule(
        id=rule_id,
        category=str(category),
        description=str(description),
        weight=int(weight),
        score=int(score),
        event_category=data.get("event_category"),
        text_contains=data.get("text_contains", []),
        regex=data.get("regex"),
        enabled=data.get("enabled", True),
    )


def _validate_pattern_rule(data: dict) -> PatternRule:
    rule_id = data.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        raise ValueError("pattern_rules: 'id' is required and must be a string")
    score = data.get("score", 0)
    _validate_score_range(score, "score", rule_id)
    max_score = data.get("max_final_score", 100)
    _validate_score_range(max_score, "max_final_score", rule_id)
    return PatternRule(
        id=rule_id,
        category=str(data.get("category", "general")),
        description=str(data.get("description", "")),
        require_indicators=data.get("require_indicators", []),
        min_events=int(data.get("min_events", 2)),
        multiplier=float(data.get("multiplier", 1.0)),
        score=int(score),
        max_final_score=int(max_score),
        enabled=data.get("enabled", True),
    )


def _validate_correlation_rule(data: dict) -> CorrelationRule:
    rule_id = data.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        raise ValueError("correlation_rules: 'id' is required and must be a string")
    score = data.get("score", 0)
    _validate_score_range(score, "score", rule_id)
    return CorrelationRule(
        id=rule_id,
        description=str(data.get("description", "")),
        min_distinct_categories=int(data.get("min_distinct_categories", 2)),
        require_source_global=data.get("require_source_global", False),
        min_findings=int(data.get("min_findings", 2)),
        score=int(score),
        enabled=data.get("enabled", True),
    )


def _merge_configs(base: RuleConfig, overlay: RuleConfig) -> RuleConfig:
    """Merge overlay into base. Same-ID rules in overlay replace base."""
    overlay_indicator_ids = {r.id for r in overlay.indicator_rules}
    overlay_pattern_ids = {r.id for r in overlay.pattern_rules}
    overlay_corr_ids = {r.id for r in overlay.correlation_rules}

    merged_indicators = [
        r for r in base.indicator_rules
        if r.id not in overlay_indicator_ids
    ] + list(overlay.indicator_rules)

    merged_patterns = [
        r for r in base.pattern_rules
        if r.id not in overlay_pattern_ids
    ] + list(overlay.pattern_rules)

    merged_corrs = [
        r for r in base.correlation_rules
        if r.id not in overlay_corr_ids
    ] + list(overlay.correlation_rules)

    merged_thresholds = {**base.severity_thresholds, **overlay.severity_thresholds}

    return RuleConfig(
        indicator_rules=merged_indicators,
        pattern_rules=merged_patterns,
        correlation_rules=merged_corrs,
        severity_thresholds=merged_thresholds,
    )


def load_rules(path: Path | None = None) -> RuleConfig:
    """Load rules from a TOML/JSON/YAML file, or return default rules."""
    config = _default_rules()
    if path is None:
        return config
    overlay = _parse_rules_file(path)
    return _merge_configs(config, overlay)


def _default_rules() -> RuleConfig:
    """Load built-in default_rules.toml from package directory."""
    rules_path = Path(__file__).parent / "default_rules.toml"
    if rules_path.exists():
        return _parse_rules_file(rules_path)
    return RuleConfig()


def _parse_rules_file(path: Path) -> RuleConfig:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".toml":
        data = tomllib.loads(text)
    elif suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
            data = yaml.safe_load(text) or {}
        except ImportError:
            raise ValueError("YAML requires PyYAML; use JSON or TOML instead")
    else:
        raise ValueError(f"Unsupported rules file type: {suffix}")

    if not isinstance(data, dict):
        raise ValueError("Rules file must contain a top-level object")

    thresholds = data.get("severity_thresholds", {})
    if isinstance(thresholds, dict):
        merged_thresholds = {
            **DEFAULT_SEVERITY_THRESHOLDS,
            **{k: int(v) for k, v in thresholds.items()},
        }
    else:
        merged_thresholds = dict(DEFAULT_SEVERITY_THRESHOLDS)

    indicator_data = data.get("indicator_rules", [])
    pattern_data = data.get("pattern_rules", [])
    correlation_data = data.get("correlation_rules", [])

    if not isinstance(indicator_data, list):
        raise ValueError("indicator_rules must be a list")
    if not isinstance(pattern_data, list):
        raise ValueError("pattern_rules must be a list")
    if not isinstance(correlation_data, list):
        raise ValueError("correlation_rules must be a list")

    indicator_rules = [_validate_indicator_rule(r) for r in indicator_data]
    pattern_rules = [_validate_pattern_rule(r) for r in pattern_data]
    correlation_rules = [_validate_correlation_rule(r) for r in correlation_data]

    # Check for duplicate IDs
    all_ids = [r.id for r in indicator_rules + pattern_rules + correlation_rules]
    if len(all_ids) != len(set(all_ids)):
        seen = set()
        for rid in all_ids:
            if rid in seen:
                raise ValueError(f"Duplicate rule ID: {rid}")
            seen.add(rid)

    enabled_indicators = [r for r in indicator_rules if r.enabled]
    enabled_patterns = [r for r in pattern_rules if r.enabled]
    enabled_corrs = [r for r in correlation_rules if r.enabled]

    return RuleConfig(
        indicator_rules=enabled_indicators,
        pattern_rules=enabled_patterns,
        correlation_rules=enabled_corrs,
        severity_thresholds=merged_thresholds,
    )
