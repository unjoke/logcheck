# Comet Design Handoff

- Change: refactor-rules-scoring-model
- Phase: design
- Mode: compact
- Context hash: 1deb9cc0552d5cad4a0bede6dee545369d5f81930a2d87940a3664659aa0c424

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/refactor-rules-scoring-model/proposal.md

- Source: openspec/changes/refactor-rules-scoring-model/proposal.md
- Lines: 1-34
- SHA256: 04edd768e0ecd1a7be16ce6a3f4225a05e629ed7c80265059d3615c3c98d8885

```md
## Why

当前规则引擎使用硬编码的二元匹配+静态严重级别：每个检测函数将 severity 写死（如 SQL 注入永远 `critical`，暴力破解永远 `high`），无评分模型、无置信度量化、无上下文区分。结果是显而易见的 CTF 课程 SQL 注入练习日志也被标记为 critical——告警要么没有，要么最高级，完全丧失分级意义。参考 FastWLAT 的 OWASP 累积评分模型和 MaaLogAnalyzer 的结构化事件流水线，需要全面重构为基于证据累积的分层评分系统。

## What Changes

- **引入评分模型（Scoring Model）**：每个检测维度产生数值分数，最终严重级别由累积分数映射决定，替代硬编码 severity
- **引入置信度评分**：区分"低置信度-可疑"与"高置信度-确认攻击"，confidence 变为 0-100 的量化值
- **分层规则结构**：规则分为 indicator（单事件指示器）→ pattern（行为模式）→ correlation（多源关联）三个层级，每层权重可配置
- **上下文感知严重级别**：根据攻击特征（单次探测 vs 持续枚举 vs 数据窃取）动态调整，而非一刀切
- **SQL 注入检测重构**：基于评分累积而非简单的"≥2 指示器 + ≥5 事件 → critical"，区分 CTF/课程练习与真实攻击
- **可配置规则定义**：将规则定义从代码中移到可配置的规则文件（JSON/TOML/YAML），支持自定义评分权重和阈值
- **结构化事件流水线**：参考 MaaLogAnalyzer，规范化事件→索引→统计→检测的数据流
- **保持安全边界**：纯本地分析，不引入网络依赖、扫描、利用或外部报告能力
- Breaking changes: Finding 模型增加 `score`、`confidence`（数值）、`rule_tier` 字段；SEVERITY_BY_RULE 移除

## Capabilities

### New Capabilities

- `scoring-engine`: 可配置的评分引擎，支持 indicator/pattern/correlation 三层规则，数值分数累积，分数到严重级别的可配置映射
- `rule-config-format`: 规则文件格式定义，支持 JSON/TOML/YAML，包含关键字、正则、评分权重、阈值、严重级别映射

### Modified Capabilities

- `intrusion-detection-rules`: 所有检测规则从硬编码改为基于评分引擎的可配置规则；Finding 模型增加 score/confidence/rule_tier 字段；严重级别由评分映射决定而非硬编码

## Impact

- **核心重构**: `logcheck/rules.py`（完全重写）、`logcheck/models.py`（Finding 模型扩展）、`logcheck/config.py`（规则加载扩展）
- **级联影响**: `logcheck/analysis.py`、`logcheck/insights.py`、`logcheck/web_serialization.py`、`logcheck/exporters.py`、`logcheck/webapp.py`、`logcheck/cli.py`、`logcheck/web_static/app.js`
- **测试更新**: 所有现有测试的 severity 断言需更新以匹配评分模型输出
- **规则文件**: 新增默认规则配置（替代代码中硬编码的 SEVERITY_BY_RULE 和各类 INDICATORS）
- **不变**: `logcheck/parsers.py` 核心解析逻辑保持；本地安全边界不变
```

## openspec/changes/refactor-rules-scoring-model/design.md

- Source: openspec/changes/refactor-rules-scoring-model/design.md
- Lines: 1-175
- SHA256: c09e4553d31cfd44de1ecff2e7f3a81b54b662e42cb83b9e989aebec86a78a6b

[TRUNCATED]

```md
## Context

当前 `logcheck/rules.py` 中的检测规则全部采用硬编码：severity 在代码中写死（如 `_web_sql_injection_findings` 永远返回 `severity="critical"`），无评分模型，无置信度量化。现有架构：

```
Events → detect_findings()
  ├── _keyword_findings()           → substring match, SEVERITY_BY_RULE static
  ├── _web_sql_injection_findings() → burst detection, severity="critical" hardcoded
  ├── _suspicious_command_findings() → substring match, severity="high" hardcoded
  ├── _privilege_escalation_findings() → substring match, severity="high" hardcoded
  ├── _brute_force_findings()       → threshold correlation, severity="high" hardcoded
  ├── _multi_signal_findings()      → multi-rule correlation, severity="high" hardcoded
  └── _public_source_cluster_findings() → source IP clustering, severity="medium" hardcoded
```

参考项目：
- **FastWLAT**: OWASP ModSecurity 风格的累积评分，每个攻击类别独立计分，可配置阈值映射严重级别
- **MaaLogAnalyzer**: 事件→索引→统计→检测的结构化流水线，原始行溯源与结构化数据分离

## Goals / Non-Goals

**Goals:**
- 引入三层评分引擎：Indicator（单事件指示器）→ Pattern（行为模式）→ Correlation（关联分析）
- 严重级别由数值分数映射决定，不再硬编码
- 置信度独立量化（0-100），与严重级别解耦
- 规则从代码中移至可配置文件，支持 JSON/TOML/YAML
- SQL 注入检测基于评分累积：单次探测 ≠ critical，持续盲注枚举 ≈ critical
- 保持向后兼容：现有 Finding 模型扩展字段（非破坏性增加），旧测试可适应新输出

**Non-Goals:**
- 不引入外部规则源（如 Sigma 规则、WAF 规则集）
- 不实现 ML/统计异常检测
- 不引入数据库或外部依赖
- 不改变 parsers.py 的解析逻辑
- 不添加网络能力

## Decisions

### Decision 1: 三层评分架构

选择三层（indicator → pattern → correlation）而非单层或更复杂的多层：

```
┌─────────────────────────────────────────────────────────┐
│                    Scoring Pipeline                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Events ──▶ Indicator Scanner ──▶ IndicatorMatches     │
│                  (weight 1-3)          │                │
│                                        ▼                │
│                              Pattern Detector           │
│                              (multiplier 1.5-3x)        │
│                                        │                │
│                                        ▼                │
│                              Correlation Engine         │
│                              (bonus +10-30)             │
│                                        │                │
│                                        ▼                │
│                              Score Compiler             │
│                              score → severity map       │
│                              confidence calc            │
│                                        │                │
│                                        ▼                │
│                              Final Findings             │
└─────────────────────────────────────────────────────────┘
```

- **Indicator**: 单事件匹配（关键字、正则、参数特征），base_score 1-30
- **Pattern**: 事件组特征（频率、组合、时序），对组内 indicator 分数的加权乘数
- **Correlation**: 跨实体关联（同源多规则命中、攻击链），固定 bonus 叠加

**Alternatives considered:**
- 单层评分：太粗糙，无法区分"一次可疑请求"和"持续攻击"
- 5+ 层（如 MITRE ATT&CK 战术映射）：过度工程，课程项目不需要
- 纯 OWASP CRS 风格（paranoia level 1-4）：不适合本地日志分析场景

### Decision 2: 严重级别映射（可配置阈值）

```
Score Range  → Severity
```

Full source: openspec/changes/refactor-rules-scoring-model/design.md

## openspec/changes/refactor-rules-scoring-model/tasks.md

- Source: openspec/changes/refactor-rules-scoring-model/tasks.md
- Lines: 1-60
- SHA256: 8efe851aa3b8242b1bbc4b9c1f28e60869c336281201f81a75a2749f5abb4f56

```md
## 1. Models & Data Structures

- [ ] 1.1 Extend Finding dataclass with `score: int`, `confidence: int`, `rule_tier: str`, `indicator_ids: list[str]` fields, all with backward-compatible defaults
- [ ] 1.2 Add `IndicatorMatch`, `PatternResult`, `CorrelationResult` internal dataclasses to `logcheck/rules.py` for pipeline stages
- [ ] 1.3 Add `RuleConfig` dataclass to `logcheck/models.py` holding parsed rules: indicator_rules, pattern_rules, correlation_rules, severity_thresholds

## 2. Default Rule Configuration

- [ ] 2.1 Create `logcheck/default_rules.toml` with all current detection rules expressed as indicator/pattern/correlation rules with appropriate scores
- [ ] 2.2 Port existing keyword rules (failed_login, invalid_user, unauthorized_access, permission_denied, sudo_failure, suspicious_command, scanner_probe) to indicator_rules with scores 2-20
- [ ] 2.3 Port SQL injection detection to indicator_rules (substr, information_schema, union_select, etc.) plus pattern_rules (boolean_blind_enumeration, schema_discovery, data_extraction)
- [ ] 2.4 Port brute-force to pattern_rules (failed_auth_burst) with configurable threshold
- [ ] 2.5 Port privilege escalation indicators as indicator_rules with appropriate scores
- [ ] 2.6 Port multi-signal and public-source-cluster as correlation_rules
- [ ] 2.7 Define default severity_thresholds: low=0, medium=20, high=50, critical=80

## 3. Scoring Engine Core

- [ ] 3.1 Implement `ScoreCompiler`: score-to-severity mapping using configurable thresholds, score capping, confidence calculation
- [ ] 3.2 Implement `IndicatorScanner`: iterate events, match against indicator_rules, emit IndicatorMatch list with per-match scores
- [ ] 3.3 Implement `PatternDetector`: group IndicatorMatches by (source, target), evaluate pattern_rules against groups, compute pattern-tier findings with accumulated scores
- [ ] 3.4 Implement `CorrelationEngine`: aggregate all findings, evaluate correlation_rules, add correlation bonuses and emit correlation-tier findings
- [ ] 3.5 Implement `compile_findings()` pipeline orchestrator: IndicatorScanner → PatternDetector → CorrelationEngine → deduplicate → final Finding list
- [ ] 3.6 Implement rule-level `max_final_score` capping to prevent single-rule score inflation

## 4. Rule Configuration Loader

- [ ] 4.1 Extend `logcheck/config.py` `load_config()` to parse `[[indicator_rules]]`, `[[pattern_rules]]`, `[[correlation_rules]]`, and `[severity_thresholds]` from TOML/JSON/YAML
- [ ] 4.2 Add validation: reject scores outside 0-100, duplicate rule IDs, missing required fields, invalid regex patterns
- [ ] 4.3 Add `load_rules()` to read embedded `default_rules.toml` when no user config provided
- [ ] 4.4 Merge user-provided rules with defaults (user additions override/extend, not replace entirely)

## 5. Detection Pipeline Integration

- [ ] 5.1 Rewrite `detect_findings()` in `logcheck/rules.py` to use the new scoring pipeline instead of hardcoded detection functions
- [ ] 5.2 Remove `SEVERITY_BY_RULE`, hardcoded `*_INDICATORS` tuples, and standalone detection functions replaced by config
- [ ] 5.3 Update `AnalysisResult` or analysis flow to carry rule configuration through the pipeline
- [ ] 5.4 Update `logcheck/insights.py` to use `finding.score` and `finding.confidence` in entity profiles and risk assessment

## 6. Web & Export Updates

- [ ] 6.1 Update `logcheck/web_serialization.py` to include score, confidence, rule_tier, indicator_ids in Finding JSON
- [ ] 6.2 Update `logcheck/web_static/app.js` to display score/confidence badges and filter by score range
- [ ] 6.3 Update `logcheck/exporters.py` (JSON, CSV, Markdown) to include new Finding fields

## 7. Tests

- [ ] 7.1 Add `tests/test_scoring_engine.py`: unit tests for ScoreCompiler, IndicatorScanner, PatternDetector, CorrelationEngine
- [ ] 7.2 Add `tests/test_rule_config.py`: unit tests for TOML rule loading, validation, error cases, default rules
- [ ] 7.3 Update `tests/test_rules.py`: update all severity assertions to match score-based output; add tests for score accumulation and confidence calculation
- [ ] 7.4 Update `tests/test_samples.py`: verify access1.log SQL injection now produces high (not critical) score under default config, or add pattern rules to push it to critical based on enumeration depth
- [ ] 7.5 Update `tests/test_web_serialization.py` and `tests/test_exporters.py` for new Finding fields
- [ ] 7.6 Run full test suite and verify all tests pass with new scoring model

## 8. Documentation & Cleanup

- [ ] 8.1 Update `pyproject.toml` if `requires-python >= 3.11` is needed for `tomllib`
- [ ] 8.2 Remove all dead code: old hardcoded detection functions, SEVERITY_BY_RULE, *_INDICATORS tuples
- [ ] 8.3 Verify all CLI commands (`analyze`, `serve`, `export`) work correctly with new rule system
- [ ] 8.4 Run `openspec validate` to confirm change integrity
```

## openspec/changes/refactor-rules-scoring-model/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/refactor-rules-scoring-model/specs/intrusion-detection-rules/spec.md
- Lines: 1-56
- SHA256: f8df85ad25d68c7a7faf738ca23996b796eeedcc7571737cfb2478136680707a

```md
## MODIFIED Requirements

### Requirement: Detect configurable behavior patterns
The intrusion detection rules capability SHALL detect configurable behavior patterns through a three-tier scoring pipeline (indicator → pattern → correlation) with numerical score accumulation, replacing hardcoded severity assignments.

#### Scenario: Suspicious command pattern
- **WHEN** parsed events contain suspicious command execution indicators
- **THEN** the system emits a pattern-tier finding with rule identifier, numerical score, confidence, severity (mapped from score), matched evidence, and explanation

#### Scenario: Multi-signal suspicious actor
- **WHEN** one actor or source address triggers multiple lower-severity indicators in a local analysis run
- **THEN** the system SHALL emit a correlation-tier finding with cumulative score reflecting all contributing indicators and a correlation bonus

#### Scenario: SQL injection severity reflects attack characteristics
- **WHEN** a single URL-encoded request contains one SQL injection indicator
- **THEN** the finding severity SHALL be "low" or "medium" (based on the single indicator score)
- **AND** SHALL NOT be "critical" unless multiple indicators, sustained enumeration, or data extraction patterns are detected

#### Scenario: Sustained SQL injection enumeration maps to critical
- **WHEN** a source sends 50+ requests with boolean-blind SQL injection indicators across 10+ distinct character positions
- **AND** the requests span information_schema enumeration and data extraction attempts
- **THEN** the cumulative score SHALL map to "critical" severity

### Requirement: Explain severity and confidence
The intrusion detection rules capability SHALL explain why each finding received its numerical score, severity, and confidence through both human-readable reasons and quantifiable metrics.

#### Scenario: Severity explanation
- **WHEN** the system emits a finding
- **THEN** the finding includes a numerical score (0-100), a severity label mapped from that score, and a human-readable severity reason

#### Scenario: Confidence explanation
- **WHEN** the system emits a finding from a behavior pattern
- **THEN** the finding includes a numerical confidence value (0-100), and a human-readable confidence reason that distinguishes exact matches, repeated behavior diversity, and correlated signals

#### Scenario: Score breakdown available
- **WHEN** a finding results from multiple contributing rules
- **THEN** the finding SHALL include the list of contributing indicator rule IDs

### Requirement: Validate enhanced rule configuration safely
The intrusion detection rules capability SHALL validate enhanced local rule configuration before applying it.

#### Scenario: Reject unsafe or malformed enhanced rules
- **WHEN** a local rule file contains malformed behavior patterns, invalid thresholds, or unsupported rule fields
- **THEN** the system rejects the file with a clear error
- **AND** it does not silently apply partial unsafe configuration

#### Scenario: Validate score ranges
- **WHEN** a rule file specifies indicator scores or severity thresholds outside the valid 0-100 range
- **THEN** the system SHALL reject the configuration with an error describing the invalid range

## REMOVED Requirements

### Requirement: Static SEVERITY_BY_RULE mapping
**Reason**: Replaced by the configurable score-to-severity mapping in the scoring engine. The old static mapping (SEVERITY_BY_RULE dict in rules.py) could not express context-dependent severity and forced all matches of a given rule name to the same severity regardless of attack characteristics.

**Migration**: Severity is now determined by the cumulative numerical score crossing configurable thresholds. Existing rule names map to indicator/pattern rules in the default rule configuration file, each with appropriate score contributions.
```

## openspec/changes/refactor-rules-scoring-model/specs/rule-config-format/spec.md

- Source: openspec/changes/refactor-rules-scoring-model/specs/rule-config-format/spec.md
- Lines: 1-66
- SHA256: a61bcd20fa41ebc108b49cc0cee5aced3b4028de0c7dd2d8d4602b00d7abd48c

```md
## ADDED Requirements

### Requirement: TOML as default rule configuration format
The rule configuration SHALL use TOML as the default format, with JSON and YAML as supported alternatives.

#### Scenario: Load valid TOML rule file
- **WHEN** a `.toml` rule file defines indicator_rules, pattern_rules, correlation_rules, and severity_thresholds sections
- **THEN** the system parses and applies all rule definitions without error

#### Scenario: Reject malformed TOML rule file
- **WHEN** a `.toml` rule file contains invalid syntax
- **THEN** the system raises a clear error indicating the parse failure location

#### Scenario: JSON rule file loads as alternative
- **WHEN** a `.json` rule file defines equivalent rule structure
- **THEN** the system parses and applies the rules identically to TOML

### Requirement: Indicator rule definition
Each indicator rule SHALL define a single-event detection condition with a configurable score contribution.

#### Scenario: Keyword indicator rule
- **WHEN** an indicator rule specifies text_contains with one or more keywords
- **AND** an event's text contains any of those keywords
- **THEN** the rule matches and contributes its score to the finding

#### Scenario: Category-scoped indicator rule
- **WHEN** an indicator rule specifies event_category
- **AND** the event does not match that category
- **THEN** the rule SHALL NOT match

#### Scenario: Regex indicator rule
- **WHEN** an indicator rule specifies a regex pattern
- **AND** the event text matches the regex
- **THEN** the rule matches and extracts named capture groups as match metadata

### Requirement: Pattern rule definition
Each pattern rule SHALL define multi-event behavior detection with required indicators, minimum events, and score contribution.

#### Scenario: Pattern activates when indicator and event thresholds met
- **WHEN** a pattern rule requires indicators ["sql_injection_substr", "sql_injection_if"]
- **AND** a grouped set of events has at least min_events matching those indicators
- **THEN** the pattern rule activates and contributes its score

#### Scenario: Pattern does not activate below event threshold
- **WHEN** a pattern rule has min_events set to 5
- **AND** only 3 grouped events match the required indicators
- **THEN** the pattern rule SHALL NOT activate

### Requirement: Correlation rule definition
Each correlation rule SHALL define cross-entity or cross-category detection with minimum diversity requirements.

#### Scenario: Correlation activates across detection categories
- **WHEN** a correlation rule requires min_distinct_categories of 2
- **AND** a source entity has findings in two different categories
- **THEN** the correlation rule activates and adds its score bonus

### Requirement: Severity threshold configuration
The severity_thresholds section SHALL define the score ranges for each severity level.

#### Scenario: Custom severity thresholds override defaults
- **WHEN** a rule file defines severity_thresholds with low=0, medium=30, high=60, critical=85
- **THEN** score 25 maps to "low" (below custom medium=30)

#### Scenario: Missing threshold defaults to built-in value
- **WHEN** a rule file omits the severity_thresholds section
- **THEN** the system SHALL use default thresholds: low=0, medium=20, high=50, critical=80
```

## openspec/changes/refactor-rules-scoring-model/specs/scoring-engine/spec.md

- Source: openspec/changes/refactor-rules-scoring-model/specs/scoring-engine/spec.md
- Lines: 1-56
- SHA256: b97ea1a223fe366b03fe85b8469b1a3d641e60a82fa129bf0b6a02914772b0fb

```md
## ADDED Requirements

### Requirement: Three-tier scoring pipeline
The scoring engine SHALL process events through a three-tier pipeline: indicator scanning, pattern detection, and correlation analysis.

#### Scenario: Single indicator match produces low-score finding
- **WHEN** a single event matches exactly one indicator rule with weight 2 and score 15
- **THEN** the engine emits a finding with score 15, tier "indicator", and severity mapped from the score

#### Scenario: Multiple indicators accumulate to higher score
- **WHEN** multiple events from the same source match two different indicator rules (scores 15 and 20 respectively)
- **AND** a pattern rule activates with score 40
- **THEN** the engine emits a pattern-tier finding whose score reflects the accumulated indicator scores plus the pattern score

#### Scenario: Correlation bonus raises severity tier
- **WHEN** a source triggers findings in two distinct detection categories
- **AND** a correlation rule with score 25 activates
- **THEN** the final finding's score includes the correlation bonus, potentially raising the severity to a higher tier

### Requirement: Score-to-severity mapping
The scoring engine SHALL map numerical scores (0-100) to severity labels using configurable thresholds.

#### Scenario: Score below medium threshold maps to low
- **WHEN** a finding has a cumulative score of 10
- **AND** the medium threshold is configured at 20
- **THEN** the finding severity is "low"

#### Scenario: Score above critical threshold maps to critical
- **WHEN** a finding has a cumulative score of 85
- **AND** the critical threshold is configured at 80
- **THEN** the finding severity is "critical"

#### Scenario: Default thresholds apply when not configured
- **WHEN** no severity thresholds are specified in the rule configuration
- **THEN** the engine SHALL use default thresholds: low=0, medium=20, high=50, critical=80

### Requirement: Independent confidence calculation
The scoring engine SHALL calculate confidence (0-100) independently from severity, based on indicator diversity, evidence quality, and rule-specific base confidence.

#### Scenario: High confidence from multiple diverse indicators
- **WHEN** a finding is supported by three distinct indicator types
- **AND** each indicator has decoded evidence available
- **THEN** the confidence score SHALL be at least 60

#### Scenario: Low confidence from single weak indicator
- **WHEN** a finding is supported by only one generic keyword match
- **AND** no structured evidence is available
- **THEN** the confidence score SHALL be below 40

### Requirement: Per-rule score capping
The scoring engine SHALL support optional maximum score limits per rule to prevent individual rules from inflating severity disproportionately.

#### Scenario: Rule score capped at configured maximum
- **WHEN** a pattern rule has max_final_score set to 75
- **AND** accumulated indicator scores plus pattern score would reach 90
- **THEN** the final finding score is capped at 75
```

