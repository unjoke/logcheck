# Logcheck

Logcheck 是一个面向课程设计的本地日志入侵行为检测工具。它使用 Python 实现，支持读取本地日志文件，解析常见 Linux 认证日志和应用日志，通过关键词规则与简单关联规则识别可疑行为，并导出分析报告。

项目现在提供命令行界面和本地 Web 前端。Web 前端已经集成在主项目目录中，运行在本机回环地址，适合课堂演示、截图和人工复核。

## 功能概览

- 解析 Linux `/var/log/auth.log` 风格日志和通用应用日志。
- 检测 `failed login`、`invalid user`、`unauthorized access`、`permission denied`、`sudo failure` 等可疑关键词。
- 检测同一来源多次失败登录的暴力破解迹象。
- 输出事件数量、告警数量、严重等级统计和可疑来源摘要。
- 在 Web 页面中选择内置样例日志或上传本地日志文件进行分析。
- 展示分析摘要、告警队列、证据详情、调查洞察和源文件上下文。
- 导出 JSON、CSV、Markdown 三种分析报告。
- 保持本地分析边界，不提供域名扫描、远程上传、阻断、漏洞利用或外部上报功能。

## 环境要求

- Python 3.11 或更高版本
- Flask 3.0 或更高版本

安装依赖：

```bash
python -m pip install -e .
```

## Web 前端运行

在项目根目录启动本地 Web 前端：

```bash
cd "E:\学校文件\大三下\信息安全基础\Logcheck"
python -m logcheck.webapp
```

也可以在安装项目后使用脚本入口：

```bash
logcheck-web
```

默认打开地址：

```text
http://127.0.0.1:8765
```

如果 `8765` 已被本机其他服务占用，可以使用当前预览脚本启动 `8767`：

```bash
python worktmp/run_webapp_8767.py
```

然后打开：

```text
http://127.0.0.1:8767
```

Web 页面支持：

- 选择 `samples/` 中的内置样例日志。
- 上传一个或多个本地日志文件。
- 点击 `Run analysis` 运行现有检测流程。
- 查看事件数、告警数、来源数和高危项统计。
- 点击告警查看证据详情，包括源文件、行号、账号、来源地址和匹配关键词。
- 查看调查洞察和时间线摘要。
- 导出 `analysis.json`、`analysis.csv`、`analysis.md`。

## 命令行运行

使用内置样例日志运行检测：

```bash
python -m logcheck.cli samples/auth.log samples/app.log --out-dir outputs --format json --format csv --format markdown
```

终端会输出类似摘要：

```text
Logcheck analysis summary
Events: 10
Findings: 15
Severity counts: {'medium': 12, 'high': 3}
Top suspicious sources: [('192.0.2.10', 11), ('unknown', 2), ('198.51.100.7', 2)]
```

导出文件位于 `outputs/`：

- `analysis.json`：完整结构化分析结果
- `analysis.csv`：表格形式告警结果
- `analysis.md`：适合课程报告引用的 Markdown 报告

分析自己的日志：

```bash
python -m logcheck.cli C:\path\to\auth.log --out-dir outputs --format markdown
```

同时分析多个日志：

```bash
python -m logcheck.cli logs\auth.log logs\app.log --out-dir outputs --format json --format csv
```

如果不指定 `--format`，默认导出 JSON 和 Markdown。

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

## 测试

运行完整测试：

```bash
python -m pytest tests -q
```

检查前端脚本语法：

```bash
node --check logcheck/web_static/app.js
```

当前测试覆盖：

- 日志解析
- 未知或畸形日志行保留
- 关键词检测
- 暴力破解阈值检测
- JSON、CSV、Markdown 导出
- CLI 端到端运行
- Web API 健康检查、样例日志、上传分析和导出
- Web 前端静态资源与本地安全边界

## 项目结构

```text
Logcheck/
  logcheck/
    analysis.py              本地分析流程与摘要统计
    cli.py                   命令行入口
    webapp.py                Flask Web 前端入口
    web_serialization.py     Web API 结果序列化
    web_static/              Web 页面、样式和脚本
    parsers.py               日志解析与规范化
    rules.py                 检测规则与严重等级
    exporters.py             JSON/CSV/Markdown 导出
    models.py                Event、Finding 等数据结构
    config.py                默认规则与配置加载
  samples/
    auth.log                 Linux 认证日志样例
    app.log                  应用日志样例
  tests/                     自动化测试
  docs/                      设计文档、计划和验证报告
  openspec/                  OpenSpec/Comet 规格与变更记录
  worktmp/                   本地临时运行文件
```

## 安全边界

Logcheck 只分析本地日志文件，并只向本地目录导出报告。项目不提供网络扫描、远程上传、域名访问、漏洞利用、阻断封禁或外部上报功能。

检测规则可能产生误报。课程报告中建议结合 `evidence` 字段、源文件和行号解释判断依据。
