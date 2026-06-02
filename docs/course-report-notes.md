# Course Report Notes

## Demo Commands

```bash
python -m logcheck.cli samples/auth.log samples/app.log --out-dir outputs --format json --format csv --format markdown
python -m unittest discover -s tests -v
```

## Report Mapping

- 绪论：说明日志分析在入侵检测中的意义，介绍暴力破解、未授权访问、权限失败等行为。
- 理论基础：说明 Linux auth/syslog 日志格式、关键词检测、阈值关联分析、严重等级分类。
- 系统总体设计：展示 CLI、Parser、Event、Rule Engine、Finding、Exporter 数据流。
- 详细设计与实现：描述 `Event` 和 `Finding` 数据结构、解析规则、关键词规则和暴力破解检测逻辑。
- 测试与结果：使用 `samples/auth.log` 和 `samples/app.log` 展示检测结果，并比较预期输出。
- 总结与展望：说明误报、日志格式覆盖不足，并展望 ELK 仪表盘和实时监控。
