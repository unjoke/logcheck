---
change: refactor-rules-scoring-model
design-doc: docs/superpowers/specs/2026-06-16-refactor-rules-scoring-model-design.md
base-ref: d7567743ec6216d03af3dfc33c41c7c237bda861
---

# Refactor Rules Scoring Model — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded severity detection rules with a three-tier (indicator→pattern→correlation) scoring engine driven entirely by `default_rules.toml`.

**Architecture:** `config.py` loads TOML rules into `RuleConfig` model. `rules.py` runs IndicatorScanner → PatternDetector → CorrelationEngine → ScoreCompiler pipeline. `Finding` model extended with `score`, `confidence`, `rule_tier`, `indicator_ids`. Score→severity mapping + confidence calculation determine final severity, with the defining fork: high score + low confidence → critical (human must decide).

**Tech Stack:** Python 3.11+ (tomllib stdlib), TOML for rules config, existing Flask/pytest stack.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `logcheck/default_rules.toml` | CREATE | All built-in detection rules as pure config |
| `logcheck/models.py` | MODIFY | Finding extension, RuleConfig, internal pipeline types |
| `logcheck/rules.py` | REWRITE | Engine only: Scanner, Detector, Correlator, Compiler, orchestration |
| `logcheck/config.py` | MODIFY | TOML rule loading, validation, merge, default fallback |
| `logcheck/analysis.py` | MODIFY | Wire new pipeline |
| `logcheck/insights.py` | MODIFY | Use score + confidence in profiles |
| `logcheck/web_serialization.py` | MODIFY | New Finding fields in JSON |
| `logcheck/exporters.py` | MODIFY | New Finding fields in JSON/CSV/Markdown export |
| `logcheck/cli.py` | MODIFY | Add `--rules` flag |
| `logcheck/web_static/app.js` | MODIFY | Score/confidence badges, filter |
| `tests/test_scoring_engine.py` | CREATE | Unit tests for engine components |
| `tests/test_rule_config.py` | CREATE | Config loading and validation tests |
| `tests/test_rules.py` | MODIFY | Update severity assertions |
| `tests/test_samples.py` | MODIFY | Update assertions |
| `tests/test_web_serialization.py` | MODIFY | New fields |
| `tests/test_exporters.py` | MODIFY | New fields |

---

## Task 1: Extend Data Models

**Files:**
- Modify: `logcheck/models.py` (entire file)
- No new test file yet (tested implicitly by engine tests)

### Step 1.1: Add new Finding fields

Edit `logcheck/models.py`, update the `Finding` dataclass to add `score`, `confidence`, `rule_tier`, `indicator_ids` with backward-compatible defaults:

```python
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
    # --- new fields (backward-compatible defaults) ---
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
```

### Step 1.2: Add internal pipeline types

Append to `logcheck/models.py`:

```python
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
```

### Step 1.3: Run existing tests to confirm backward compatibility

```bash
python -m pytest tests/ -x -q
```

All should pass (new fields have defaults, `to_dict()` returns extra keys which existing tests ignore).

### Step 1.4: Commit

```bash
git add logcheck/models.py
git commit -m "feat: extend Finding model and add rule config types for scoring engine"
```

---

## Task 2: Rule Configuration Loader

**Files:**
- Modify: `logcheck/config.py` (major rewrite)
- Test: `tests/test_rule_config.py` (new)

### Step 2.1: Write failing tests for config loading

Create `tests/test_rule_config.py`:

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from logcheck.config import load_rules
from logcheck.models import RuleConfig, IndicatorRule, PatternRule, CorrelationRule


class RuleConfigLoadingTests(unittest.TestCase):
    def _write_toml(self, tmp: Path, content: str) -> Path:
        path = tmp / "rules.toml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_indicator_rules_from_toml(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "test_indicator"
category = "test"
description = "A test indicator"
weight = 2
text_contains = ["needle"]
score = 15
""")
            config = load_rules(path)
            self.assertEqual(len(config.indicator_rules), 1)
            rule = config.indicator_rules[0]
            self.assertEqual(rule.id, "test_indicator")
            self.assertEqual(rule.score, 15)
            self.assertEqual(rule.text_contains, ["needle"])

    def test_loads_pattern_rules_from_toml(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "ind_a"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[pattern_rules]]
id = "test_pattern"
category = "test"
description = "A test pattern"
require_indicators = ["ind_a"]
min_events = 5
multiplier = 1.5
score = 30
""")
            config = load_rules(path)
            self.assertEqual(len(config.pattern_rules), 1)
            rule = config.pattern_rules[0]
            self.assertEqual(rule.id, "test_pattern")
            self.assertEqual(rule.require_indicators, ["ind_a"])
            self.assertEqual(rule.multiplier, 1.5)

    def test_loads_severity_thresholds(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[severity_thresholds]
low = 0
medium = 30
high = 60
critical = 85
""")
            config = load_rules(path)
            self.assertEqual(config.severity_thresholds["medium"], 30)
            self.assertEqual(config.severity_thresholds["critical"], 85)

    def test_default_thresholds_when_not_specified(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, "")
            config = load_rules(path)
            self.assertEqual(config.severity_thresholds, {
                "low": 0, "medium": 20, "high": 50, "critical": 80
            })

    def test_rejects_score_out_of_range(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "bad"
category = "test"
weight = 2
text_contains = ["x"]
score = 150
""")
            with self.assertRaises(ValueError):
                load_rules(path)

    def test_rejects_duplicate_rule_ids(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "same_id"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[indicator_rules]]
id = "same_id"
category = "test"
weight = 1
text_contains = ["b"]
score = 20
""")
            with self.assertRaises(ValueError):
                load_rules(path)

    def test_disabled_rule_is_excluded(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = self._write_toml(tmp, """
[[indicator_rules]]
id = "enabled_rule"
category = "test"
weight = 1
text_contains = ["a"]
score = 10

[[indicator_rules]]
id = "disabled_rule"
category = "test"
weight = 1
text_contains = ["b"]
score = 10
enabled = false
""")
            config = load_rules(path)
            ids = [r.id for r in config.indicator_rules]
            self.assertIn("enabled_rule", ids)
            self.assertNotIn("disabled_rule", ids)

    def test_loads_json_rules(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            path = tmp / "rules.json"
            path.write_text(json.dumps({
                "severity_thresholds": {"low": 0, "medium": 25, "high": 55, "critical": 85},
                "indicator_rules": [{
                    "id": "json_rule",
                    "category": "test",
                    "description": "from json",
                    "weight": 1,
                    "text_contains": ["json_needle"],
                    "score": 20
                }],
                "pattern_rules": [],
                "correlation_rules": []
            }), encoding="utf-8")
            config = load_rules(path)
            self.assertEqual(len(config.indicator_rules), 1)
            self.assertEqual(config.severity_thresholds["medium"], 25)
```

Run: `python -m pytest tests/test_rule_config.py -v`
Expected: All FAIL (load_rules not implemented yet)

### Step 2.2: Implement RuleConfig loading

Rewrite `logcheck/config.py`:

```python
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
    base_indicator_ids = {r.id for r in base.indicator_rules}
    base_pattern_ids = {r.id for r in base.pattern_rules}
    base_corr_ids = {r.id for r in base.correlation_rules}

    merged_indicators = [
        r for r in base.indicator_rules
        if r.id not in {o.id for o in overlay.indicator_rules}
    ] + list(overlay.indicator_rules)

    merged_patterns = [
        r for r in base.pattern_rules
        if r.id not in {o.id for o in overlay.pattern_rules}
    ] + list(overlay.pattern_rules)

    merged_corrs = [
        r for r in base.correlation_rules
        if r.id not in {o.id for o in overlay.correlation_rules}
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
```

### Step 2.3: Run config tests

```bash
python -m pytest tests/test_rule_config.py -v
```

Expected: All PASS

### Step 2.4: Commit

```bash
git add logcheck/config.py tests/test_rule_config.py
git commit -m "feat: add TOML rule config loader with validation and merge"
```

---

## Task 3: Default Rules TOML

**Files:**
- Create: `logcheck/default_rules.toml`

### Step 3.1: Create default rules file

Create `logcheck/default_rules.toml`:

```toml
[severity_thresholds]
low = 0
medium = 20
high = 50
critical = 80

# ── Auth Indicators ──────────────────────────────────────

[[indicator_rules]]
id = "failed_login"
category = "auth"
description = "Failed password or login attempt"
weight = 2
text_contains = ["failed password", "failed login", "authentication failure"]
score = 10

[[indicator_rules]]
id = "invalid_user"
category = "auth"
description = "Login attempt with non-existent username"
weight = 2
text_contains = ["invalid user"]
score = 10

[[indicator_rules]]
id = "sudo_failure"
category = "auth"
description = "Failed sudo authentication"
weight = 2
text_contains = ["sudo:auth", "sudo failure"]
score = 15

[[indicator_rules]]
id = "root_auth_failure"
category = "auth"
description = "Authentication failure for root user"
weight = 2
text_contains = ["authentication failure; user=root"]
score = 20

# ── Access Control Indicators ────────────────────────────

[[indicator_rules]]
id = "unauthorized_access"
category = "access_control"
description = "Unauthorized access attempt logged"
weight = 2
text_contains = ["unauthorized access"]
score = 15

[[indicator_rules]]
id = "permission_denied"
category = "access_control"
description = "Permission denied error"
weight = 1
text_contains = ["permission denied"]
score = 5

# ── Suspicious Commands ───────────────────────────────────

[[indicator_rules]]
id = "suspicious_download"
category = "command"
description = "Suspicious file download via wget or curl"
weight = 2
text_contains = ["wget http", "curl http"]
score = 15

[[indicator_rules]]
id = "reverse_shell"
category = "command"
description = "Potential reverse shell indicators"
weight = 3
text_contains = ["nc -e", "bash -i"]
score = 25

# ── Scanner/Probe Indicators ──────────────────────────────

[[indicator_rules]]
id = "scanner_probe"
category = "recon"
description = "Automated scanner or vulnerability probe"
weight = 1
text_contains = ["attack_case=scanner", "nikto"]
score = 5

# ── Privilege Escalation Indicators ───────────────────────

[[indicator_rules]]
id = "sensitive_path_access"
category = "privilege"
description = "Access to sensitive system paths"
weight = 2
text_contains = ["/etc/shadow", "/root", "/admin"]
score = 15

[[indicator_rules]]
id = "su_authentication"
category = "privilege"
description = "Switch user authentication attempt"
weight = 2
text_contains = ["su:auth"]
score = 15

# ── SQL Injection Indicators ──────────────────────────────

[[indicator_rules]]
id = "sqli_substr"
category = "web_attack"
description = "substr() call — common in blind SQL injection"
weight = 2
event_category = "access"
text_contains = ["substr("]
score = 15

[[indicator_rules]]
id = "sqli_information_schema"
category = "web_attack"
description = "information_schema access — schema enumeration"
weight = 2
event_category = "access"
text_contains = ["information_schema"]
score = 10

[[indicator_rules]]
id = "sqli_union_select"
category = "web_attack"
description = "UNION SELECT — classic SQL injection"
weight = 3
event_category = "access"
text_contains = ["union select"]
score = 20

[[indicator_rules]]
id = "sqli_and_if"
category = "web_attack"
description = "AND IF(...) — boolean-blind conditional"
weight = 3
event_category = "access"
text_contains = [" and if("]
score = 20

[[indicator_rules]]
id = "sqli_database_call"
category = "web_attack"
description = "database() call — DB name extraction"
weight = 2
event_category = "access"
text_contains = ["database()"]
score = 10

[[indicator_rules]]
id = "sqli_select_table_name"
category = "web_attack"
description = "SELECT table_name — table enumeration"
weight = 2
event_category = "access"
text_contains = ["select table_name"]
score = 10

[[indicator_rules]]
id = "sqli_select_flag"
category = "web_attack"
description = "SELECT flag — CTF flag extraction attempt"
weight = 2
event_category = "access"
text_contains = ["select flag"]
score = 10

# ── Pattern Rules ─────────────────────────────────────────

[[pattern_rules]]
id = "boolean_blind_enumeration"
category = "web_attack"
description = "Sustained boolean-blind SQL injection with character-by-character enumeration"
require_indicators = ["sqli_substr", "sqli_and_if"]
min_events = 5
multiplier = 1.8
score = 40
max_final_score = 85

[[pattern_rules]]
id = "schema_discovery"
category = "web_attack"
description = "Database schema enumeration via information_schema"
require_indicators = ["sqli_information_schema", "sqli_select_table_name"]
min_events = 3
multiplier = 1.5
score = 30
max_final_score = 70

[[pattern_rules]]
id = "data_extraction"
category = "web_attack"
description = "Direct data/flag extraction attempts"
require_indicators = ["sqli_select_flag", "sqli_database_call"]
min_events = 2
multiplier = 1.5
score = 30
max_final_score = 75

[[pattern_rules]]
id = "failed_auth_burst"
category = "auth"
description = "Sustained brute-force authentication attempts"
require_indicators = ["failed_login"]
min_events = 5
multiplier = 1.5
score = 30
max_final_score = 70

# ── Correlation Rules ─────────────────────────────────────

[[correlation_rules]]
id = "multi_category_source"
description = "Source triggers multiple distinct detection categories"
min_distinct_categories = 2
score = 20

[[correlation_rules]]
id = "public_source_cluster"
description = "Globally routable source with multiple findings"
require_source_global = true
min_findings = 2
score = 15
```

### Step 3.2: Verify TOML is loadable

```bash
python -c "from logcheck.config import load_rules; r = load_rules(); print(f'Loaded {len(r.indicator_rules)} indicators, {len(r.pattern_rules)} patterns, {len(r.correlation_rules)} correlations')"
```

Expected: `Loaded 16 indicators, 4 patterns, 2 correlations`

### Step 3.3: Commit

```bash
git add logcheck/default_rules.toml
git commit -m "feat: add default_rules.toml with all detection rules as config"
```

---

## Task 4: Scoring Engine — ScoreCompiler

**Files:**
- Modify: `logcheck/rules.py` (add ScoreCompiler class)
- Test: `tests/test_scoring_engine.py` (new)

### Step 4.1: Write ScoreCompiler tests

Create `tests/test_scoring_engine.py`:

```python
import unittest

from logcheck.rules import ScoreCompiler


class ScoreCompilerTests(unittest.TestCase):
    def setUp(self):
        self.thresholds = {"low": 0, "medium": 20, "high": 50, "critical": 80}
        self.compiler = ScoreCompiler(self.thresholds)

    def test_low_score_maps_to_low(self):
        self.assertEqual(self.compiler.score_to_severity(10, 80), "low")

    def test_medium_score_maps_to_medium(self):
        self.assertEqual(self.compiler.score_to_severity(35, 80), "medium")

    def test_high_score_high_confidence_maps_to_high(self):
        self.assertEqual(self.compiler.score_to_severity(65, 80), "high")

    def test_high_score_low_confidence_maps_to_critical(self):
        # The defining fork: high score + low confidence → critical
        self.assertEqual(self.compiler.score_to_severity(65, 30), "critical")

    def test_critical_score_always_critical(self):
        self.assertEqual(self.compiler.score_to_severity(85, 90), "critical")
        self.assertEqual(self.compiler.score_to_severity(85, 10), "critical")

    def test_confidence_diversity_driven(self):
        # 1 indicator → 15
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=1,
            indicator_ids=["a"],
            has_decoded=False,
            has_response_variance=False,
            substr_positions_count=0,
        )
        self.assertEqual(conf, 15)

        # 3 indicators → 45
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=3,
            indicator_ids=["a", "b", "c"],
            has_decoded=False,
            has_response_variance=False,
            substr_positions_count=0,
        )
        self.assertEqual(conf, 45)

    def test_confidence_evidence_bonuses(self):
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=2,
            indicator_ids=["a", "b"],
            has_decoded=True,
            has_response_variance=True,
            substr_positions_count=10,
        )
        # base 30 + decoded 5 + response_var 5 + substr 5 = 45
        self.assertEqual(conf, 45)

    def test_confidence_clamped_to_100(self):
        conf = self.compiler.calculate_confidence(
            distinct_indicator_count=10,
            indicator_ids=[str(i) for i in range(10)],
            has_decoded=True,
            has_response_variance=True,
            substr_positions_count=50,
        )
        self.assertLessEqual(conf, 100)

    def test_apply_cap_limits_score(self):
        self.assertEqual(self.compiler.apply_cap(90, 75), 75)
        self.assertEqual(self.compiler.apply_cap(60, 75), 60)

    def test_custom_thresholds(self):
        compiler = ScoreCompiler({"low": 0, "medium": 30, "high": 60, "critical": 90})
        self.assertEqual(compiler.score_to_severity(25, 80), "low")
        self.assertEqual(compiler.score_to_severity(55, 80), "medium")
        self.assertEqual(compiler.score_to_severity(75, 80), "high")
        self.assertEqual(compiler.score_to_severity(75, 30), "critical")
```

Run: `python -m pytest tests/test_scoring_engine.py -v`
Expected: All FAIL

### Step 4.2: Implement ScoreCompiler

In `logcheck/rules.py`, add the ScoreCompiler class at the top (before pipeline functions):

```python
from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import unquote_plus

from .ip_context import classify_ip_address
from .models import (
    CorrelationResult,
    CorrelationRule,
    DetectionConfig,
    Event,
    Finding,
    IndicatorMatch,
    IndicatorRule,
    PatternResult,
    PatternRule,
    RuleConfig,
)


class ScoreCompiler:
    """Maps scores to severity and calculates confidence."""

    def __init__(self, thresholds: dict[str, int]) -> None:
        self.thresholds = thresholds

    def score_to_severity(self, score: int, confidence: int) -> str:
        """Map score → severity, with critical override for disputed findings."""
        if score >= self.thresholds.get("critical", 80):
            return "critical"
        if score >= self.thresholds.get("high", 50) and confidence < 40:
            return "critical"  # high score, low confidence → human must decide
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
        """Diversity-driven confidence: 15 × distinct indicators + evidence bonuses."""
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
```

### Step 4.3: Run ScoreCompiler tests

```bash
python -m pytest tests/test_scoring_engine.py -v
```

Expected: All PASS

### Step 4.4: Commit

```bash
git add logcheck/rules.py tests/test_scoring_engine.py
git commit -m "feat: add ScoreCompiler with score→severity mapping and confidence calc"
```

---

## Task 5: Scoring Engine — IndicatorScanner

**Files:**
- Modify: `logcheck/rules.py` (add IndicatorScanner)
- Modify: `tests/test_scoring_engine.py` (add tests)

### Step 5.1: Write IndicatorScanner tests

Append to `tests/test_scoring_engine.py`:

```python
from logcheck.models import Event, IndicatorRule
from logcheck.rules import IndicatorScanner


class IndicatorScannerTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            IndicatorRule(
                id="test_keyword", category="test",
                description="test", weight=1,
                text_contains=["needle"], score=15,
            ),
            IndicatorRule(
                id="test_regex", category="test",
                description="test regex", weight=2,
                regex=r"id=(\d+)", score=20,
            ),
            IndicatorRule(
                id="access_only", category="test",
                description="access only", weight=1,
                event_category="access",
                text_contains=["secret"], score=25,
            ),
        ]
        self.scanner = IndicatorScanner(self.rules)

    def test_scanner_matches_keyword_in_event(self):
        event = Event("test.log", 1, "found a needle here", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].rule_id, "test_keyword")
        self.assertEqual(matches[0].score, 15)

    def test_scanner_matches_regex(self):
        event = Event("test.log", 1, "query?id=42&name=foo", category="access")
        matches = self.scanner.scan(event, 0)
        regex_match = [m for m in matches if m.rule_id == "test_regex"]
        self.assertEqual(len(regex_match), 1)
        self.assertEqual(regex_match[0].score, 20)

    def test_scanner_respects_event_category(self):
        event = Event("test.log", 1, "secret data", category="application")
        matches = self.scanner.scan(event, 0)
        ids = [m.rule_id for m in matches]
        self.assertNotIn("access_only", ids)

    def test_scanner_matches_category_when_correct(self):
        event = Event("test.log", 1, "secret data", category="access")
        matches = self.scanner.scan(event, 0)
        ids = [m.rule_id for m in matches]
        self.assertIn("access_only", ids)

    def test_scanner_no_matches(self):
        event = Event("test.log", 1, "completely benign", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertEqual(len(matches), 0)

    def test_scanner_multiple_matches_same_event(self):
        event = Event("test.log", 1, "needle and id=7", category="application")
        matches = self.scanner.scan(event, 0)
        self.assertGreaterEqual(len(matches), 2)
```

### Step 5.2: Implement IndicatorScanner

In `logcheck/rules.py`, add after ScoreCompiler:

```python
def _event_text(event: Event) -> str:
    return f"{event.raw_line}\n{event.message or ''}".lower()


def _decoded_event_text(event: Event) -> str:
    return unquote_plus(_event_text(event))


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
            matched_keyword = None

            # Try regex first
            if rule.id in self._compiled_regex:
                pattern = self._compiled_regex[rule.id]
                if pattern.search(text) or pattern.search(decoded):
                    matched_keyword = f"regex:{rule.regex}"
            # Then keyword matching
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
```

### Step 5.3: Run tests

```bash
python -m pytest tests/test_scoring_engine.py::IndicatorScannerTests -v
```

Expected: All PASS

### Step 5.4: Commit

```bash
git add logcheck/rules.py tests/test_scoring_engine.py
git commit -m "feat: add IndicatorScanner for per-event rule matching"
```

---

## Task 6: Scoring Engine — PatternDetector

**Files:**
- Modify: `logcheck/rules.py` (add PatternDetector)
- Modify: `tests/test_scoring_engine.py` (add tests)

### Step 6.1: Write PatternDetector tests

Append to `tests/test_scoring_engine.py`:

```python
from logcheck.models import PatternRule
from logcheck.rules import PatternDetector


class PatternDetectorTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            PatternRule(
                id="test_pattern", category="test",
                description="test pattern",
                require_indicators=["ind_a", "ind_b"],
                min_events=3, multiplier=1.5, score=30,
            ),
        ]
        self.detector = PatternDetector(self.rules)

    def _match(self, rule_id: str, source="1.2.3.4", target="/"):
        return IndicatorMatch(
            rule_id=rule_id, category="test", event_index=0,
            score=10, source_address=source, target=target,
        )

    def test_pattern_activates_when_requirements_met(self):
        matches = [
            self._match("ind_a"), self._match("ind_a"),
            self._match("ind_b"), self._match("ind_a"),
        ]
        results = self.detector.detect(matches, {i: None for i in range(4)})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "test_pattern")
        # indicator sum = 4×10 = 40, ×1.5 = 60, +30 pattern = 90
        self.assertEqual(results[0].indicator_score_sum, 40)
        self.assertEqual(results[0].final_score, 90)

    def test_pattern_does_not_activate_below_min_events(self):
        matches = [self._match("ind_a"), self._match("ind_b")]
        results = self.detector.detect(matches, {i: None for i in range(2)})
        self.assertEqual(len(results), 0)

    def test_pattern_requires_all_indicators(self):
        matches = [self._match("ind_a")] * 5  # only ind_a, missing ind_b
        results = self.detector.detect(matches, {i: None for i in range(5)})
        self.assertEqual(len(results), 0)

    def test_pattern_groups_by_source_target(self):
        matches = [
            self._match("ind_a", source="1.1.1.1", target="/a"),
            self._match("ind_a", source="1.1.1.1", target="/a"),
            self._match("ind_b", source="1.1.1.1", target="/a"),
            self._match("ind_a", source="2.2.2.2", target="/b"),
            self._match("ind_b", source="2.2.2.2", target="/b"),
            self._match("ind_a", source="2.2.2.2", target="/b"),
        ]
        results = self.detector.detect(matches, {i: None for i in range(6)})
        # Two groups: (1.1.1.1, /a) has 3 events with both indicators
        # (2.2.2.2, /b) has 3 events with both indicators
        self.assertEqual(len(results), 2)
```

### Step 6.2: Implement PatternDetector

In `logcheck/rules.py`, add after IndicatorScanner:

```python
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
        # Group matches by (source, target)
        groups: dict[tuple[str, str], list[IndicatorMatch]] = defaultdict(list)
        for match in matches:
            groups[_pattern_group_key(match)].append(match)

        results: list[PatternResult] = []
        for rule in self._rules:
            for key, group_matches in groups.items():
                if len(group_matches) < rule.min_events:
                    continue
                # Check required indicators are all present
                group_indicator_ids = {m.rule_id for m in group_matches}
                required = set(rule.require_indicators)
                if not required.issubset(group_indicator_ids):
                    continue

                indicator_sum = sum(m.score for m in group_matches)
                pattern_score = rule.score
                final_score = int(indicator_sum * rule.multiplier + pattern_score)
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
                    pattern_score=pattern_score,
                    final_score=final_score,
                    evidence_indices=[m.event_index for m in group_matches],
                ))

        return results
```

### Step 6.3: Run tests

```bash
python -m pytest tests/test_scoring_engine.py::PatternDetectorTests -v
```

Expected: All PASS

### Step 6.4: Commit

```bash
git add logcheck/rules.py tests/test_scoring_engine.py
git commit -m "feat: add PatternDetector for grouped behavior detection"
```

---

## Task 7: Scoring Engine — CorrelationEngine & Orchestrator

**Files:**
- Modify: `logcheck/rules.py` (add CorrelationEngine, compile_findings)
- Modify: `tests/test_scoring_engine.py` (add tests)

### Step 7.1: Write engine integration tests

Append to `tests/test_scoring_engine.py`:

```python
from logcheck.models import CorrelationRule, RuleConfig
from logcheck.rules import CorrelationEngine, compile_findings


class CorrelationEngineTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            CorrelationRule(
                id="multi_cat", description="multi category",
                min_distinct_categories=2, score=20,
            ),
        ]
        self.engine = CorrelationEngine(self.rules)

    def test_correlation_activates_multi_category(self):
        pattern_results = [
            PatternResult("p1", "web", ("1.2.3.4", "/"), ["a"], 5, 30, 1.5, 30, 75, []),
            PatternResult("p2", "auth", ("1.2.3.4", "/"), ["b"], 5, 20, 1.5, 30, 60, []),
        ]
        results = self.engine.detect(pattern_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].rule_id, "multi_cat")
        self.assertEqual(results[0].distinct_categories, 2)

    def test_correlation_does_not_activate_single_category(self):
        pattern_results = [
            PatternResult("p1", "web", ("1.2.3.4", "/"), ["a"], 5, 30, 1.5, 30, 75, []),
            PatternResult("p2", "web", ("1.2.3.4", "/"), ["b"], 5, 20, 1.5, 30, 60, []),
        ]
        results = self.engine.detect(pattern_results)
        self.assertEqual(len(results), 0)


class CompileFindingsTests(unittest.TestCase):
    def setUp(self):
        self.config = RuleConfig(
            indicator_rules=[
                IndicatorRule(id="ind_a", category="cat_a", description="a",
                              weight=1, text_contains=["a"], score=15),
                IndicatorRule(id="ind_b", category="cat_b", description="b",
                              weight=1, text_contains=["b"], score=15),
            ],
            pattern_rules=[
                PatternRule(id="pat_ab", category="cat_a",
                            description="ab pattern",
                            require_indicators=["ind_a", "ind_b"],
                            min_events=2, multiplier=1.5, score=30),
            ],
            correlation_rules=[
                CorrelationRule(id="corr_multi", description="multi",
                                min_distinct_categories=2, score=20),
            ],
            severity_thresholds={"low": 0, "medium": 20, "high": 50, "critical": 80},
        )

    def test_full_pipeline_produces_scored_findings(self):
        events = [
            Event("test.log", i, f"event with a and b #{i}",
                  category="application", source_address="1.2.3.4", target="/")
            for i in range(5)
        ]
        findings = compile_findings(events, self.config)
        self.assertTrue(len(findings) > 0)
        for f in findings:
            self.assertIsInstance(f.score, int)
            self.assertGreaterEqual(f.score, 0)
            self.assertLessEqual(f.score, 100)
            self.assertIsInstance(f.confidence, int)
            self.assertIn(f.rule_tier, ("indicator", "pattern", "correlation"))
```

### Step 7.2: Implement CorrelationEngine and compile_findings

In `logcheck/rules.py`, add after PatternDetector:

```python
class CorrelationEngine:
    """Detects cross-entity/cross-category correlations."""

    def __init__(self, rules: list[CorrelationRule]) -> None:
        self._rules = rules

    def detect(self, pattern_results: list[PatternResult]) -> list[CorrelationResult]:
        results: list[CorrelationResult] = []
        for rule in self._rules:
            if not rule.enabled:
                continue

            # Group pattern results by source
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

    # Emit pattern findings (primary output)
    for pr in pattern_results:
        # Collect evidence events
        evidence_events = [event_map[idx] for idx in pr.evidence_indices[:20]]
        source, target = pr.group_key

        # Check evidence quality
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

    # Emit unmatched indicator-only findings (for individual suspicious events
    # that didn't form a pattern)
    pattern_indices: set[int] = set()
    for pr in pattern_results:
        pattern_indices.update(pr.evidence_indices)

    indicator_matches_without_pattern = [
        m for m in all_matches if m.event_index not in pattern_indices
    ]
    for match in indicator_matches_without_pattern:
        event = event_map[match.event_index]
        confidence = compiler.calculate_confidence(
            distinct_indicator_count=1,
            indicator_ids=[match.rule_id],
        )
        severity = compiler.score_to_severity(match.score, confidence)
        findings.append(_event_to_finding(
            event, match, match.score, confidence, severity,
        ))

    return findings
```

### Step 7.3: Run all engine tests

```bash
python -m pytest tests/test_scoring_engine.py -v
```

Expected: All PASS

### Step 7.4: Commit

```bash
git add logcheck/rules.py tests/test_scoring_engine.py
git commit -m "feat: add CorrelationEngine and compile_findings pipeline orchestrator"
```

---

## Task 8: Rewire Analysis Pipeline

**Files:**
- Modify: `logcheck/analysis.py`
- Modify: `logcheck/cli.py`
- Modify: `logcheck/webapp.py` (if needed)

### Step 8.1: Update analysis.py

Edit `logcheck/analysis.py` to use new pipeline:

```python
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import load_rules
from .insights import generate_insights
from .models import AnalysisResult, RuleConfig
from .parsers import parse_files
from .rules import compile_findings


@dataclass(frozen=True)
class AnalysisSummary:
    total_events: int
    total_findings: int
    findings_by_severity: dict[str, int]
    top_suspicious_sources: list[tuple[str, int]]


def analyze_logs(
    paths: list[Path],
    config_path: Path | None = None,
) -> AnalysisResult:
    rules_config = load_rules(config_path)
    events = parse_files(paths)
    result = AnalysisResult(events=events, findings=compile_findings(events, rules_config))
    result.insights = generate_insights(result)
    return result


def summarize_result(result: AnalysisResult) -> AnalysisSummary:
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    return AnalysisSummary(
        total_events=len(result.events),
        total_findings=len(result.findings),
        findings_by_severity=dict(severities),
        top_suspicious_sources=sources.most_common(5),
    )
```

### Step 8.2: Update cli.py to accept --rules flag

Read the current cli.py to see exact structure, then add `--rules` argument to the `analyze` subcommand. The `--rules` flag takes a path to a TOML/JSON/YAML rules file.

### Step 8.3: Run quick smoke test

```bash
python -m logcheck.cli analyze samples/auth.log 2>&1 | head -20
```

Expected: Analysis runs, produces findings with new score/confidence fields.

### Step 8.4: Commit

```bash
git add logcheck/analysis.py logcheck/cli.py
git commit -m "feat: wire scoring pipeline into analysis and CLI"
```

---

## Task 9: Update Insights, Web Serialization, and Exporters

**Files:**
- Modify: `logcheck/insights.py`
- Modify: `logcheck/web_serialization.py`
- Modify: `logcheck/exporters.py`
- Modify: `logcheck/web_static/app.js`

### Step 9.1: Update insights.py

In `_entity_profiles()`, include `score` and `confidence` in entity assessment. In `EntityProfile`, add `avg_score` and `avg_confidence` fields.

### Step 9.2: Update exporters.py

In `export_csv()`, add `score`, `confidence`, `rule_tier` to CSV fields.
In `export_markdown()`, display score/confidence in finding sections.

### Step 9.3: Update web_static/app.js

Add score badge and confidence bar to finding cards. Add score range filter alongside severity filter.

### Step 9.4: Update tests and commit

Update `tests/test_web_serialization.py` and `tests/test_exporters.py` assertions to include new fields.

```bash
git add logcheck/insights.py logcheck/web_serialization.py logcheck/exporters.py logcheck/web_static/app.js tests/
git commit -m "feat: surface score/confidence in insights, exports and web UI"
```

---

## Task 10: Update Existing Tests

**Files:**
- Modify: `tests/test_rules.py`
- Modify: `tests/test_samples.py`
- Modify: `tests/test_analysis.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_webapp.py`

### Step 10.1: Update test_rules.py

Old tests use hardcoded severity checks like `self.assertEqual(sqli[0].severity, "critical")`. Update to match score-based output instead.

Since we moved from old `detect_findings()` to new `compile_findings()`, the tests need to use the new API. For each test:

- Replace `detect_findings(events, default_config())` with `compile_findings(events, load_rules())`
- Change severity assertions from exact match to range check: e.g. `self.assertIn(sqli[0].severity, {"high", "critical"})`
- Add score/confidence assertions

### Step 10.2: Update test_samples.py

Update `test_access1_sample_detects_encoded_sql_injection_attack_behavior`:
- Assert score > 50 (high+ range)
- Assert confidence reflects indicator diversity (2+ indicators → ≥30)
- Verify new Finding fields present

### Step 10.3: Run full test suite

```bash
python -m pytest tests/ -x -v
```

Fix any failures. Iterate until all green.

### Step 10.4: Commit

```bash
git add tests/
git commit -m "test: update all tests for scoring model"
```

---

## Task 11: Cleanup, README, and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `logcheck/rules.py` (remove dead code if any remains)

### Step 11.1: Remove dead code from rules.py

Delete old functions no longer called: `_keyword_findings`, `_web_sql_injection_findings`, `_suspicious_command_findings`, `_privilege_escalation_findings`, `_brute_force_findings`, `_multi_signal_findings`, `_public_source_cluster_findings`, old `detect_findings`, `SEVERITY_BY_RULE`, old `*_INDICATORS` tuples, `SQL_INJECTION_*` constants. Keep helper utilities if still used.

### Step 11.2: Update README

Add sections:
- **Rule Configuration**: Explain `--rules` flag, TOML format, default rules
- **Scoring Model**: Score→severity mapping, confidence calculation, critical override
- **Customizing Rules**: How to add/override/disable rules

### Step 11.3: Update pyproject.toml

Add `default_rules.toml` to package data:

```toml
[tool.setuptools.package-data]
logcheck = ["web_static/*", "default_rules.toml"]
```

### Step 11.4: Final test run

```bash
python -m pytest tests/ -v
python -m logcheck.cli analyze samples/auth.log samples/access1.log
```

### Step 11.5: Commit

```bash
git add README.md pyproject.toml logcheck/
git commit -m "docs: update README and final cleanup for scoring model"
```
