from __future__ import annotations

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

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    base = default_config()
    keywords = data.get("keywords", base.keywords)
    brute_force = data.get("brute_force", {})
    return DetectionConfig(
        keywords=keywords,
        brute_force_threshold=int(brute_force.get("threshold", base.brute_force_threshold)),
        brute_force_window_minutes=int(brute_force.get("window_minutes", base.brute_force_window_minutes)),
    )
