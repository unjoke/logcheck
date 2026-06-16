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
─────────────────────────
 0 - 19      → low        (informational / unlikely attack)
20 - 49      → medium     (suspicious, needs review)
50 - 79      → high       (likely attack, prioritize)
80 - 100     → critical   (confirmed active attack)
```

阈值可通过规则配置文件自定义。这个分布确保：
- 单个低权重 indicator（如 scanner_probe）落在 low
- 重复 indicator 或单个 pattern 命中落在 medium/high
- 多个 pattern + correlation 叠加才达到 critical

### Decision 3: 置信度计算

置信度与严重级别独立计算：

```
confidence = base_confidence
           × indicator_diversity_factor   (0.5-1.5, 匹配的 distinct indicator 数)
           × evidence_quality_factor      (0.5-1.5, 是否有 decoded/structured evidence)
           × false_positive_correction    (0.3-1.0, 基于规则已知误报率)
```

- `base_confidence`: 由最匹配的规则定义
- 最终 clamp 到 [0, 100]
- < 30: "低可信度 — 可能为误报"
- 30-60: "中等可信度 — 需要人工确认"
- > 60: "高可信度 — 明确攻击特征"

### Decision 4: 规则文件格式

默认规则嵌入代码（`default_rules.toml` 字符串），用户可覆盖。格式：

```toml
[severity_thresholds]
low = 0
medium = 20
high = 50
critical = 80

[[indicator_rules]]
id = "sql_injection_substr"
category = "web_attack"
description = "URL-decoded request contains substr() call"
weight = 2
event_category = "access"
text_contains = ["substr("]
score = 15

[[pattern_rules]]
id = "boolean_blind_enumeration"
category = "web_attack"
description = "Repeated boolean-blind SQL injection with substr position enumeration"
weight = 6
require_indicators = ["sql_injection_substr", "sql_injection_if"]
min_events = 3
min_distinct_positions = 3
score = 45
max_final_score = 90

[[correlation_rules]]
id = "multi_signal_source"
description = "Source triggers multiple distinct detection categories"
weight = 7
min_distinct_categories = 2
score = 25
```

**Alternatives considered:**
- Sigma 规则格式：太重，需要 YAML + 复杂 parser
- 纯 JSON Schema：对课程项目来说太繁琐
- TOML：Python 3.11+ 内置 `tomllib`，零额外依赖，可读性好 → 选用为默认格式，同时保留 JSON/YAML 支持

### Decision 5: Finding 模型扩展（非破坏性）

```python
@dataclass(frozen=True)
class Finding:
    # ... existing fields preserved ...
    
    # New fields (all with defaults for backward compat)
    score: int = 0                    # 0-100 numerical score
    confidence: int = 0               # 0-100 confidence rating
    rule_tier: str = "indicator"      # "indicator" | "pattern" | "correlation"
    indicator_ids: list[str] = field(default_factory=list)  # contributing indicators
    severity_reason: str | None = None
    confidence_reason: str | None = None
```

## Risks / Trade-offs

- **[Risk] 评分阈值难以调优** → 提供合理的默认值（基于 access1.log 等真实样本校准），并支持配置文件覆盖
- **[Risk] 重构可能引入回归** → 保留所有现有测试，逐个更新 severity 断言；新增评分专项测试
- **[Risk] TOML 格式在 Python 3.10 不可用** → `tomllib` 是 3.11+ 新增；对 3.10 提供 JSON 回退，或在 `pyproject.toml` 中声明 `requires-python >= 3.11`
- **[Trade-off] 评分模型增加复杂度** → 但消除了硬编码 severity 带来的更大问题（告警失真）；规则配置可选，默认值即开即用
