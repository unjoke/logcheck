# Logcheck

Logcheck 是一个基于日志分析的入侵行为检测工具，课程设计题目为“基于日志分析的入侵行为检测工具设计与实现”。工具使用 Python 实现，支持读取本地日志文件，解析常见 Linux 认证日志和应用日志，通过关键词规则和简单关联规则识别可疑行为，并导出分析报告。

## 功能概览

- 解析 Linux `/var/log/auth.log` 风格日志和通用应用日志
- 检测 failed login、invalid user、unauthorized access、permission denied、sudo failure 等关键词
- 检测同一来源多次失败登录的暴力破解行为
- 输出终端摘要，包括事件数、告警数、严重等级统计和可疑来源
- 导出 JSON、CSV、Markdown 三种分析结果
- 提供样例日志和自动化测试，方便课程演示、录屏和报告撰写

## 环境要求

- Python 3.11 或更高版本
- 不需要额外第三方依赖

在项目根目录运行命令：

```bash
cd E:\学校文件\大三下\信息安全基础\Logcheck
```

## 快速运行

使用内置样例日志运行检测：

```bash
python -m logcheck.cli samples/auth.log samples/app.log --out-dir outputs --format json --format csv --format markdown
```

运行后终端会输出类似摘要：

```text
Logcheck analysis summary
Events: 10
Findings: 15
Severity counts: {'medium': 12, 'high': 3}
Top suspicious sources: [('192.0.2.10', 11), ('unknown', 2), ('198.51.100.7', 2)]
```

导出文件位于 `outputs/`：

- `outputs/analysis.json`：完整结构化分析结果
- `outputs/analysis.csv`：表格形式告警结果
- `outputs/analysis.md`：适合截图和写入课程报告的 Markdown 报告

## 分析自己的日志

可以把自己的日志文件路径作为参数传入：

```bash
python -m logcheck.cli C:\path\to\auth.log --out-dir outputs --format markdown
```

也可以同时分析多个日志文件：

```bash
python -m logcheck.cli logs\auth.log logs\app.log --out-dir outputs --format json --format csv
```

如果不指定 `--format`，默认导出 JSON 和 Markdown：

```bash
python -m logcheck.cli samples/auth.log samples/app.log
```

## 命令参数

```text
logs                  本地日志文件路径，可传入一个或多个
--config CONFIG       可选 TOML 规则配置文件
--out-dir OUT_DIR     导出目录，默认 outputs
--format FORMAT       导出格式，可重复使用：json、csv、markdown
```

查看帮助：

```bash
python -m logcheck.cli --help
```

## 运行测试

```bash
python -m unittest discover -s tests -v
```

当前测试覆盖：

- 日志解析
- 未知或畸形日志行保留
- 关键词检测
- 暴力破解阈值检测
- JSON/CSV/Markdown 导出
- CLI 端到端运行

## 项目结构

```text
Logcheck/
  logcheck/
    cli.py          命令行入口
    parsers.py      日志解析与规范化
    rules.py        检测规则与严重等级
    exporters.py    JSON/CSV/Markdown 导出
    models.py       Event、Finding 等数据结构
    config.py       默认规则与配置加载
  samples/
    auth.log        Linux 认证日志样例
    app.log         应用日志样例
  tests/            自动化测试
  docs/             课程报告 notes、设计文档、验证报告
  openspec/         OpenSpec/Comet 规格与归档记录
```

## 课程报告写作提示

报告中可以按以下思路组织：

- 绪论：说明日志审计、入侵检测和账号安全的背景意义
- 理论基础：介绍系统日志格式、关键词匹配、阈值关联分析、严重等级划分
- 总体设计：展示 CLI -> Parser -> Event -> Rule Engine -> Finding -> Exporter 数据流
- 详细设计：说明 `Event`、`Finding` 数据结构，以及解析规则和检测规则
- 测试结果：使用 `samples/auth.log` 和 `samples/app.log` 展示检测结果和导出文件
- 总结展望：说明误报、日志格式覆盖有限，并展望 ELK 仪表盘、实时监控等扩展

## 注意事项

- 本工具只分析本地日志文件，不进行网络扫描、攻击、阻断或远程上报。
- 关键词规则可能产生误报，报告中应结合 evidence 字段解释判断依据。
- `outputs/` 是运行生成目录，已加入 `.gitignore`，可按需删除后重新生成。
