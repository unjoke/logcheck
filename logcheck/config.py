from __future__ import annotations

import json
from pathlib import Path
import tomllib

from .models import DetectionConfig


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
    else:
        raise ValueError(f"Unsupported config file type: {path.suffix}")

    if not isinstance(data, dict):
        raise ValueError("Rule config must be an object")

    base = default_config()
    keywords = data.get("keywords", base.keywords)
    _validate_keywords(keywords)
    brute_force = data.get("brute_force", {})
    return DetectionConfig(
        keywords=keywords,
        brute_force_threshold=int(brute_force.get("threshold", base.brute_force_threshold)),
        brute_force_window_minutes=int(brute_force.get("window_minutes", base.brute_force_window_minutes)),
    )


def _validate_keywords(keywords: object) -> None:
    if not isinstance(keywords, dict):
        raise ValueError("keywords must be an object")

    for rule_id, terms in keywords.items():
        if not isinstance(rule_id, str):
            raise ValueError("keyword rule IDs must be strings")
        if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
            raise ValueError("keyword rules must be lists of strings")


def config_to_dict(config: DetectionConfig) -> dict[str, object]:
    return {
        "keywords": config.keywords,
        "brute_force": {
            "threshold": config.brute_force_threshold,
            "window_minutes": config.brute_force_window_minutes,
        },
    }
