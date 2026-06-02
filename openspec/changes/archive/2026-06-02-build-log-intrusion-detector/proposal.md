## Why

The course design topic is "基于日志分析的入侵行为检测工具设计与实现". The project needs a clear, implementable scope that satisfies the course requirements: a runnable tool, source code, executable/demo artifact, report-ready design material, test evidence, and exportable analysis logs.

This change defines an offline log intrusion detection tool focused on Linux system logs and application-style logs. It keeps the implementation practical for a two-week course design while preserving enough security depth for the report, demo video, and possible defense.

## What Changes

- Build a Python-based command-line log analysis tool for local log files.
- Parse Linux authentication/system logs and generic application logs into normalized event records.
- Detect intrusion-related behavior through configurable keyword rules and lightweight correlation rules.
- Generate terminal summaries plus exportable JSON/CSV/Markdown analysis reports.
- Provide sample logs, test cases, and course-report material aligned with the provided template.
- Exclude live network monitoring, active blocking, production deployment, and ELK cluster setup from the first implementation scope.

## Capabilities

### New Capabilities

- `log-ingestion`: Parse and normalize input log files from Linux `/var/log`-style text logs and generic application logs.
- `intrusion-detection-rules`: Detect suspicious login, authorization, scanning, privilege, and abnormal-frequency events from normalized logs.
- `report-export`: Produce human-readable summaries and export detailed analysis logs for coursework submission and demo.
- `course-deliverables`: Support the course design report, tests, sample data, executable packaging, and demonstration workflow.

### Modified Capabilities

- None.

## Impact

- Adds a Python project structure for the log analysis CLI, detection engine, report exporter, tests, and sample data.
- Adds local-only processing of user-provided log files; no external domains, remote submission, or live defense actions are required.
- Adds documentation that maps the implementation to the course template sections: background, theory, architecture, module design, testing, results, and summary.
