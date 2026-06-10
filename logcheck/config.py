from __future__ import annotations

import json
from pathlib import Path
import tomllib

from .models import DetectionConfig


SUPPORTED_BEHAVIOR_FIELDS = {
    "enabled",
    "template_burst_threshold",
    "sequence_window_minutes",
}


def default_config() -> DetectionConfig:
    return DetectionConfig(
        keywords={
            "failed_login": ["failed password", "failed login", "authentication failure"],
            "invalid_user": ["invalid user"],
            "unauthorized_access": ["unauthorized access"],
            "permission_denied": ["permission denied"],
            "sudo_failure": ["sudo:auth", "sudo failure"],
            "suspicious_command": ["wget http", "curl http", "nc -e", "bash -i"],
        },
        brute_force_threshold=5,
        brute_force_window_minutes=10,
    )


def load_config(path: Path | None) -> DetectionConfig:
    if path is None:
        return default_config()

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    elif path.suffix == ".toml":
        data = tomllib.loads(text)
    elif path.suffix in {".yaml", ".yml"}:
        data = _load_yaml(text)
    else:
        raise ValueError(f"Unsupported config file type: {path.suffix}")

    if not isinstance(data, dict):
        raise ValueError("Rule config must be an object")

    base = default_config()
    keywords = data.get("keywords", base.keywords)
    _validate_keywords(keywords)
    brute_force = data.get("brute_force", {})
    _validate_brute_force(brute_force)
    behavior = data.get("behavior", {})
    _validate_behavior(behavior)
    return DetectionConfig(
        keywords=keywords,
        brute_force_threshold=_parse_int(
            brute_force.get("threshold", base.brute_force_threshold), "brute_force.threshold"
        ),
        brute_force_window_minutes=_parse_int(
            brute_force.get("window_minutes", base.brute_force_window_minutes),
            "brute_force.window_minutes",
        ),
        behavior_enabled=_parse_bool(
            behavior.get("enabled", base.behavior_enabled), "behavior.enabled"
        ),
        template_burst_threshold=_parse_positive_int(
            behavior.get("template_burst_threshold", base.template_burst_threshold),
            "behavior.template_burst_threshold",
        ),
        sequence_window_minutes=_parse_positive_int(
            behavior.get("sequence_window_minutes", base.sequence_window_minutes),
            "behavior.sequence_window_minutes",
        ),
    )


def _validate_keywords(keywords: object) -> None:
    if not isinstance(keywords, dict):
        raise ValueError("keywords must be an object")

    for rule_id, terms in keywords.items():
        if not isinstance(rule_id, str):
            raise ValueError("keyword rule IDs must be strings")
        if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
            raise ValueError("keyword rules must be lists of strings")


def _load_yaml(text: str) -> object:
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("YAML requires optional parser; JSON is supported") from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("YAML rule config could not be parsed") from exc
    return {} if data is None else data


def _validate_brute_force(brute_force: object) -> None:
    if not isinstance(brute_force, dict):
        raise ValueError("brute_force must be an object")


def _validate_behavior(behavior: object) -> None:
    if not isinstance(behavior, dict):
        raise ValueError("behavior must be an object")
    unsupported = set(behavior) - SUPPORTED_BEHAVIOR_FIELDS
    if unsupported:
        raise ValueError(f"Unsupported behavior config field: {sorted(unsupported)[0]}")


def _parse_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _parse_positive_int(value: object, field_name: str) -> int:
    parsed = _parse_int(value, field_name)
    if parsed <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return parsed


def _parse_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def config_to_dict(config: DetectionConfig) -> dict[str, object]:
    return {
        "keywords": config.keywords,
        "brute_force": {
            "threshold": config.brute_force_threshold,
            "window_minutes": config.brute_force_window_minutes,
        },
        "behavior": {
            "enabled": config.behavior_enabled,
            "template_burst_threshold": config.template_burst_threshold,
            "sequence_window_minutes": config.sequence_window_minutes,
        },
    }
