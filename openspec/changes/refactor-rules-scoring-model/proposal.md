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
