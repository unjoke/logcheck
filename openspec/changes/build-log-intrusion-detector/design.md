## Context

The selected course topic requires an intrusion behavior detection tool based on log analysis. The requirement document allows Python or ELK and mentions Linux `/var/log` or application logs, keyword filtering such as "failed login" and "unauthorized access", and an interface that can be command-line or graphical with detailed analysis-log export.

For a two-week course design, a Python CLI is the most reliable first implementation. It is easier to explain in the report, easier to test, easier to package, and avoids the operational weight of deploying Elasticsearch, Logstash, and Kibana. ELK can still be discussed as an alternative in the report's future work or comparison section.

## Goals / Non-Goals

**Goals:**

- Implement a local, offline Python CLI that analyzes one or more log files.
- Parse common Linux authentication/system log patterns and preserve unknown lines.
- Detect intrusion indicators through keyword rules and simple correlation rules.
- Export analysis details for course submission, demonstration video, and screenshots.
- Provide tests, sample logs, and documentation that map cleanly to the course template.

**Non-Goals:**

- No live network monitoring, firewall blocking, remote collection, or production SIEM deployment.
- No attack execution, exploit automation, credential guessing, or intrusive scanning.
- No required ELK cluster setup in the initial implementation.
- No attempt to fully parse every Linux distribution or application log format.

## Decisions

### Use Python CLI Instead of ELK

Use Python as the implementation platform and expose the tool through a command-line interface. Python keeps the system portable and lets the report focus on parsing, detection rules, algorithms, and test evidence. ELK is powerful but would make deployment and screenshots dominate the coursework.

Alternative considered: ELK-based dashboard. It offers richer visualization but requires more environment setup, heavier dependencies, and less original detection logic for a small course project.

### Separate Parser, Detection Engine, Exporter, and CLI

Organize the tool into four core modules:

- Parser: reads files and converts raw lines into normalized events.
- Rule engine: applies keyword and correlation rules to events.
- Exporter: writes JSON, CSV, and Markdown outputs.
- CLI: handles arguments, error reporting, and orchestration.

This keeps each module explainable in the report and independently testable.

### Use Local Rule Configuration With Defaults

Provide a default rule set for course demonstration and optionally load a local config file for keywords, thresholds, and time windows. Defaults ensure the demo works immediately, while configuration shows extensibility.

### Export Evidence-Rich Findings

Every finding should include rule id, severity, explanation, source file, timestamp where available, suspicious actor/source address where available, and evidence lines. This supports both technical validation and report writing.

## Risks / Trade-offs

- Ambiguous Word requirement text for topic 11 -> Treat the clear parts as mandatory and implement defensible security-relevant additions: repeated failed-login detection, severity classification, and exportable evidence.
- Log formats vary widely -> Support common Linux auth/syslog patterns first and preserve unknown lines for transparency.
- Keyword rules can create false positives -> Include evidence, severity, and rule explanations; document limitations in the report.
- CLI is less visual than a dashboard -> Generate Markdown/CSV/JSON reports that can be shown in screenshots and demo video.
- Course template text appears adapted from operating-system coursework -> Map sections to information-security theory and log-analysis concepts while preserving the provided structure.

## Data Flow

```text
input log files
  -> parser
  -> normalized events
  -> keyword rules + correlation rules
  -> findings
  -> terminal summary + JSON/CSV/Markdown exports
```

## Testing Approach

Tests should cover successful parsing, missing files, malformed lines, keyword matching, brute-force threshold detection, severity classification, output file creation, and CLI exit behavior. Sample logs should include normal lines and malicious-looking lines so the demo can be repeated without external systems.
