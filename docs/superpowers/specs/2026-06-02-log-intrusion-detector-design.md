---
comet_change: build-log-intrusion-detector
role: technical-design
canonical_spec: openspec
---

# Log Intrusion Detector Technical Design

## Context

This design implements the OpenSpec change `build-log-intrusion-detector` for the course topic "基于日志分析的入侵行为检测工具设计与实现". OpenSpec remains the canonical requirement source; this document records the technical implementation plan, boundaries, risks, and testing strategy.

The coursework requires a runnable tool, source code, executable or runnable artifact, demonstration material, report content, and exportable analysis logs. The selected implementation is a local Python command-line tool that analyzes Linux authentication/system logs and generic application logs.

## Architecture

The system is a small Python package with clear module boundaries:

```text
input log files
  -> logcheck.parsers
  -> normalized Event objects
  -> logcheck.rules
  -> Finding objects
  -> logcheck.exporters
  -> terminal summary + JSON/CSV/Markdown reports
```

The CLI is the orchestration layer. It validates input paths, loads optional rule configuration, calls the parser, runs the rule engine, prints a summary, and writes requested exports.

## Components

### CLI

The CLI accepts local file paths, an optional config file, an output directory, requested output formats, and verbosity. It returns a non-zero status for missing or unreadable files. It does not send data to any remote service.

### Parser

The parser reads text logs line by line and emits normalized events. It supports common Linux auth/syslog-style lines, simple timestamped application logs, and unknown or malformed lines. Unknown lines are preserved with the raw text so analysis remains transparent.

Each event should include source file, line number, raw line, timestamp when available, category, actor, target, source address, and message.

### Rule Engine

The rule engine applies two rule families:

- Keyword rules for indicators such as failed login, invalid user, unauthorized access, permission denied, sudo failure, and suspicious commands.
- Correlation rules for repeated failed-login behavior from the same source address or actor within a configurable time window.

Each finding includes a rule id, severity, explanation, matched event fields, evidence lines, and source metadata.

### Configuration

Default rules are bundled for the course demo. A local config file can override keywords, brute-force thresholds, and time windows. Defaults make the demo repeatable; configuration demonstrates extensibility.

### Exporters

Exporters write:

- JSON for complete structured analysis.
- CSV for tabular finding review.
- Markdown for course-report screenshots and demo narration.

All exports include metadata such as analyzed files, event counts, finding counts, and generation time.

## Key Decisions

### Python CLI Over ELK

Python CLI is selected because it is portable, testable, and easier to explain in a two-week course design. ELK is valuable for production log analysis but would shift effort toward deployment and dashboard setup. ELK can be discussed in future work.

### Offline Local Processing

All analysis is local and offline. This avoids unnecessary network exposure and keeps the project aligned with a defensive coursework tool rather than an operational monitoring service.

### Evidence-Rich Findings

Findings keep evidence lines and rule explanations. This helps with false-positive analysis, report writing, and demonstration.

### Small Focused Modules

Parser, rules, exporters, config, and CLI should be implemented as separate files. This keeps tests focused and maps neatly to the report's module-design section.

## Error Handling

Missing files, unreadable files, invalid output directories, and malformed config should produce clear CLI errors. Malformed log lines should not fail the whole run; they should be retained as unknown events.

## Testing Strategy

Tests cover:

- Parser behavior for Linux auth logs, application logs, unknown lines, and malformed lines.
- Rule behavior for keyword matches, brute-force threshold detection, severity classification, and custom config.
- Export behavior for JSON, CSV, and Markdown output files.
- CLI behavior for successful sample-log runs, missing files, and selected export formats.

Sample logs should be deterministic and include both normal and suspicious activity so the demo can be repeated.

## Course Report Mapping

- Background and significance: log analysis, intrusion detection, account attack behavior, audit evidence.
- Theory: syslog/auth log format, keyword matching, correlation thresholds, severity classification.
- Overall design: CLI, parser, normalized events, rule engine, exporters.
- Detailed design: event/finding data structures, parser regexes, rule algorithms, export formats.
- Testing: unit tests, end-to-end sample run, expected versus actual findings.
- Summary and future work: false positives, broader log formats, dashboard/ELK integration, real-time monitoring.

## Risks and Mitigations

- Log formats vary across systems -> Start with common formats and preserve unknown lines.
- Keyword rules can over-match -> Include evidence, severity, and explanation in each finding.
- CLI lacks visual dashboard impact -> Generate Markdown reports and terminal summaries for screenshots.
- Course document text has formatting noise around topic 11 -> Implement the clear mandatory requirements and defensible security extensions.

## Acceptance Notes

The implementation is acceptable when the sample logs can be analyzed from the CLI, suspicious events are detected, reports are exported in JSON/CSV/Markdown, automated tests pass, and documentation provides enough material for the course paper and demo video.
