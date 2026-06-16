---
comet_change: refactor-rules-scoring-model
role: technical-design
canonical_spec: openspec
---

# Refactor Rules: Scoring Model & Config-Driven Detection

## 1. Overview

Replace hardcoded, flat-severity detection rules with a three-tier scoring engine
driven entirely by configuration files. Severity reflects *review urgency*, not attack
certainty. Confidence quantifies *match reliability*, independent from severity.

### Core Insight

```
                    Confidence →
                    Low              High
          ┌─────┬──────────────┬──────────────┐
          │ Low │  Low         │  Low         │  noise / informational
Score     │     │ (ignore)     │ (record)     │
(severity)├─────┼──────────────┼──────────────┤
          │ Med │  Medium      │  Medium      │  worth a look
          │     │ (suspicious) │ (notable)    │
          ├─────┼──────────────┼──────────────┤
          │ High│  CRITICAL    │  High        │  ← the key fork
          │     │ (human must  │ (confirmed   │
          │     │  decide)     │  attack)     │
          └─────┴──────────────┴──────────────┘
```

- **High severity + High confidence** → **High**: machine is confident this is an attack
- **High severity + Low confidence** → **Critical**: attack indicators exist but evidence is ambiguous — human judgment required
- Medium/Low score → Medium/Low regardless of confidence

## 2. Architecture

### 2.1 Pipeline

```
                          ┌───────────────────┐
  Events ────────────────▶│ Indicator Scanner │
                          │   per-event match │
                          │   weight 1-3      │
                          └────────┬──────────┘
                                   │ IndicatorMatch[]
                                   ▼
                          ┌───────────────────┐
                          │ Pattern Detector  │
                          │   group by source │
                          │   × multiplier    │
                          └────────┬──────────┘
                                   │ PatternResult[]
                                   ▼
                          ┌───────────────────┐
                          │ Correlation Eng.  │
                          │   cross-entity    │
                          │   + bonus score   │
                          └────────┬──────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │  Score Compiler   │
                          │  score→severity   │
                          │  confidence calc  │
                          │  dedup + cap      │
                          └────────┬──────────┘
                                   │
                                   ▼
                             Final Findings
```

### 2.2 Component Responsibilities

| Component | Input | Output | Key Logic |
|-----------|-------|--------|-----------|
| `IndicatorScanner` | Events, indicator_rules | `list[IndicatorMatch]` | Substring/regex match per event; each match has rule_id, score, event ref |
| `PatternDetector` | IndicatorMatch[], pattern_rules | `list[PatternResult]` | Group matches by (source, target); evaluate require_indicators, min_events; apply multiplier |
| `CorrelationEngine` | All findings, correlation_rules | `list[CorrelationResult]` | Cross-category detection; min_distinct_categories; flat bonus |
| `ScoreCompiler` | All results, severity_thresholds | `list[Finding]` | Compute final_score = Σindicator × multiplier + correlation; score→severity map; confidence calc; dedup |

## 3. Data Models

### 3.1 Rule Definitions (TOML)

```toml
[severity_thresholds]
low = 0
medium = 20
high = 50
critical = 80

[[indicator_rules]]
id = "sql_injection_substr"
category = "web_attack"
description = "Request contains substr() — common in blind SQL injection"
weight = 2
event_category = "access"
text_contains = ["substr("]
score = 15

[[indicator_rules]]
id = "sql_injection_information_schema"
category = "web_attack"
event_category = "access"
text_contains = ["information_schema"]
score = 10

[[indicator_rules]]
id = "sql_injection_union_select"
category = "web_attack"
event_category = "access"
text_contains = ["union select"]
score = 20

[[pattern_rules]]
id = "boolean_blind_enumeration"
category = "web_attack"
description = "Sustained boolean-blind SQL injection with character-by-character enumeration"
require_indicators = ["sql_injection_substr", "sql_injection_information_schema"]
min_events = 5
multiplier = 1.8
score = 40
max_final_score = 85

[[pattern_rules]]
id = "failed_auth_burst"
category = "auth_attack"
require_indicators = ["failed_login"]
min_events = 5
multiplier = 1.5
score = 30
max_final_score = 70

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

### 3.2 Finding Model Extension

```python
@dataclass(frozen=True)
class Finding:
    # --- existing fields preserved ---
    rule_id: str
    severity: str                    # now: mapped from score+confidence
    explanation: str
    evidence: list[str]
    source_file: str | None
    line_number: int | None
    timestamp: datetime | None
    source_address: str | None
    actor: str | None
    target: str | None
    matched_keyword: str | None
    count: int | None
    severity_reason: str | None
    confidence_reason: str | None

    # --- new fields (backward-compatible defaults) ---
    score: int = 0                   # 0-100
    confidence: int = 0              # 0-100
    rule_tier: str = "indicator"     # indicator | pattern | correlation
    indicator_ids: list[str] = field(default_factory=list)
```

### 3.3 Internal Pipeline Types

```python
@dataclass(frozen=True)
class IndicatorMatch:
    rule_id: str
    category: str
    event_index: int
    score: int
    source_address: str | None
    target: str | None
    matched_keyword: str | None

@dataclass(frozen=True)
class PatternResult:
    rule_id: str
    category: str
    group_key: tuple[str, str]       # (source, target)
    indicator_ids: list[str]
    event_count: int
    indicator_score_sum: int
    multiplier: float
    pattern_score: int
    final_score: int                 # capped

@dataclass(frozen=True)
class CorrelationResult:
    rule_id: str
    entity: str
    distinct_categories: int
    bonus_score: int
```

## 4. Scoring Formulas

### 4.1 Final Score

```
final_score = clamp(
    (Σ indicator_scores) × pattern_multiplier + Σ correlation_bonuses,
    0, 100
)
```

Per-rule `max_final_score` caps apply before the clamp.

### 4.2 Severity Mapping

```python
def score_to_severity(score: int, confidence: int, thresholds: dict) -> str:
    if score >= thresholds["high"] and confidence < 40:
        return "critical"            # high score, low confidence → human must decide
    if score >= thresholds["critical"]:
        return "critical"            # score alone above critical threshold
    if score >= thresholds["high"]:
        return "high"                # high score + high confidence → confirmed attack
    if score >= thresholds["medium"]:
        return "medium"
    return "low"
```

The defining fork: **score ≥ high threshold but confidence < 40** → Critical.
This means "strong attack indicators exist, but evidence diversity is too low
to be certain — a human must look at it."

### 4.3 Confidence (Diversity-Driven)

```
confidence = clamp(
    15 × distinct_indicator_count + evidence_bonus,
    0, 100
)

evidence_bonus:
    +5  if any matching event has decoded_request metadata
    +5  if response_size variance > 0 in the group
    +5  if substr position range >= 5
```

- 1 indicator → 15-25% (low confidence)
- 2 indicators → 30-45% (moderate)
- 3 indicators → 45-60% (solid)
- 5+ indicators with all evidence bonuses → 75-90% (high confidence)

## 5. File Layout

```
logcheck/
├── rules.py              # Engine only: Scanner, Detector, Correlator, Compiler
├── models.py             # Finding extension, internal types, RuleConfig
├── config.py             # TOML/JSON/YAML loader, validation, merge strategy
├── default_rules.toml    # All built-in rules (pure config, no code)
├── parsers.py            # UNCHANGED
├── analysis.py           # Wire new pipeline into analyze_logs()
├── insights.py           # Use score + confidence in EntityProfile
├── exporters.py          # Include new Finding fields
├── web_serialization.py  # Include new Finding fields
├── webapp.py             # No logic changes
├── cli.py                # Accept --rules flag for custom config
└── web_static/
    └── app.js            # Display score/confidence badges, filter by range
```

## 6. Config Merge Strategy

User provides `--rules my-rules.toml`:

1. Load `default_rules.toml` as base
2. Load user file
3. Merge per section:
   - `severity_thresholds`: user overrides key-by-key
   - `indicator_rules`: user entries with same `id` replace default; new `id`s appended
   - `pattern_rules`: same merge-by-id
   - `correlation_rules`: same merge-by-id
   - User can set `enabled = false` on any rule to disable it
4. Validate complete merged config
5. No rule removal without explicit `enabled = false`

## 7. Implementation Order

### Phase A: Foundation (tasks 1.x, 3.x, 4.x)
- Extend Finding model with new fields (backward-compat defaults)
- Add internal pipeline types to rules.py
- Implement ScoreCompiler (score→severity map, confidence calc)
- Extend config.py to parse new TOML sections with validation

### Phase B: Engine (tasks 3.x)
- Implement IndicatorScanner, PatternDetector, CorrelationEngine
- Implement compile_findings() orchestrator
- Build default_rules.toml with all current detection coverage

### Phase C: Integration (tasks 5.x)
- Rewrite detect_findings() to use new pipeline
- Remove SEVERITY_BY_RULE, hardcoded INDICATORS, old detection functions
- Wire into analysis.py, insights.py

### Phase D: Web & Export (tasks 6.x)
- Update serialization, frontend display, export formats

### Phase E: Tests & Docs (tasks 7.x, 8.x)
- New unit tests for each engine component
- Update existing test assertions
- Update README with rule configuration guide

## 8. Testing Strategy

| Layer | What to Test | File |
|-------|-------------|------|
| Unit: ScoreCompiler | score→severity for all thresholds, confidence calc with varying indicator counts, critical override logic | `test_scoring_engine.py` |
| Unit: IndicatorScanner | Single-event keyword match, regex match, category filtering, score accumulation | `test_scoring_engine.py` |
| Unit: PatternDetector | Group formation, require_indicators logic, min_events threshold, multiplier application, score capping | `test_scoring_engine.py` |
| Unit: CorrelationEngine | Cross-category detection, min_distinct_categories counting, source_global filter | `test_scoring_engine.py` |
| Unit: Config | TOML parsing, validation (bad scores, missing fields, dupe IDs), merge logic, default rules load | `test_rule_config.py` |
| Integration: Rules | Full pipeline on access1.log: score in critical/high range, confidence reflects indicator diversity | `test_rules.py` (updated) |
| Integration: Samples | All sample files produce expected findings with score-based severity | `test_samples.py` (updated) |
| Integration: Web/Export | New Finding fields serialize correctly | `test_web_serialization.py`, `test_exporters.py` |

### access1.log Calibration Target

With default_rules.toml, access1.log (2764 boolean-blind SQLi requests, 43 substr positions, information_schema + flag extraction) should produce:
- Score: 75-85 (High, possibly Critical if confidence < 40)
- Confidence: depends on distinct indicator count in the matched group
- At minimum: `sql_injection_substr`, `sql_injection_information_schema`, `sql_injection_if`, plus any additional matched indicators

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Score thresholds mis-calibrated for real-world logs | Default thresholds derived from access1.log (known CTF attack) and auth.log (normal activity); user-configurable |
| TOML unavailable on Python < 3.11 | `pyproject.toml` already requires `>= 3.11`; verify |
| Confidence formula too simplistic | Start simple (diversity-count based), tune after real usage; formula is a single pure function, easy to adjust |
| Old test assertions break | Update tests in Phase E after engine is stable; don't edit tests mid-implementation |
| Rule ID naming collisions between user and default | Merge-by-id: user intentionally overrides when same ID used |

## 10. README Updates Needed

- Document `--rules` CLI flag
- Show example `rules.toml` with indicator/pattern/correlation sections
- Explain scoring model: score → severity mapping, confidence calculation
- Explain critical vs high distinction (human judgment gate)
- Document rule config merge behavior
- Add `default_rules.toml` reference (or pointer to it)
