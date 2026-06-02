# Comet Design Handoff

- Change: build-log-intrusion-detector
- Phase: design
- Mode: compact
- Context hash: 3e73258346cdd6c9b3511d059c32f16ec4b1cedf61eb4363c0ef2bf63957cdbf

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/build-log-intrusion-detector/proposal.md

- Source: openspec/changes/build-log-intrusion-detector/proposal.md
- Lines: 1-33
- SHA256: 5e2b5f49e57f0e8f33857517dbbb91bfcb1ff4f3c4e556a90ddbfd59fe2046c7

```md
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
```

## openspec/changes/build-log-intrusion-detector/design.md

- Source: openspec/changes/build-log-intrusion-detector/design.md
- Lines: 1-72
- SHA256: 38ff43faf76b561abd6cad2aace581ec42a2abd050f21fb16b7fb55e0443edff

```md
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
```

## openspec/changes/build-log-intrusion-detector/tasks.md

- Source: openspec/changes/build-log-intrusion-detector/tasks.md
- Lines: 1-34
- SHA256: 4a1b36b869e7cb77665bd0d378363de0b72948a3ccd8212ea7f58c799a5d2ce7

```md
## 1. Project Setup

- [ ] 1.1 Create Python package structure for CLI, parser, rules, exporter, config, and tests.
- [ ] 1.2 Add project metadata, dependency list, and a runnable command entry point.
- [ ] 1.3 Add sample log files covering normal behavior, failed login, unauthorized access, brute force, sudo failure, and malformed lines.

## 2. Log Ingestion

- [ ] 2.1 Implement local file loading with clear errors for missing or unreadable files.
- [ ] 2.2 Implement parsers for Linux auth/syslog-style lines and generic application log lines.
- [ ] 2.3 Normalize parsed lines into event objects and preserve unknown or malformed lines.
- [ ] 2.4 Add parser unit tests for known formats, unknown lines, and malformed input.

## 3. Detection Rules

- [ ] 3.1 Implement default keyword rules for failed login, invalid user, unauthorized access, permission denied, sudo failure, and suspicious commands.
- [ ] 3.2 Implement repeated failed-login or brute-force detection using configurable thresholds and time windows.
- [ ] 3.3 Implement severity classification and evidence-rich finding objects.
- [ ] 3.4 Add rule-engine tests for keyword matches, threshold matches, defaults, and custom config.

## 4. Report Export and CLI

- [ ] 4.1 Implement terminal summary output with event counts, finding counts by severity, and top suspicious sources.
- [ ] 4.2 Implement JSON export with metadata, counts, findings, and evidence.
- [ ] 4.3 Implement CSV export with one row per finding.
- [ ] 4.4 Implement Markdown report export for course paper screenshots and demo narration.
- [ ] 4.5 Implement CLI options for input files, config path, output directory, output formats, and verbosity.

## 5. Verification and Course Materials

- [ ] 5.1 Add end-to-end CLI tests using sample logs.
- [ ] 5.2 Add documentation for setup, demo commands, test commands, export examples, and packaging.
- [ ] 5.3 Add course-report notes that map the implementation to the provided template sections.
- [ ] 5.4 Run the full verification command and record sample outputs for the final report/demo.
```

## openspec/changes/build-log-intrusion-detector/specs/course-deliverables/spec.md

- Source: openspec/changes/build-log-intrusion-detector/specs/course-deliverables/spec.md
- Lines: 1-29
- SHA256: e28d4bd1343af1d64a572ff75d3838fb7ee8fcdcd3aa3593c168de67efd4e199

```md
## ADDED Requirements

### Requirement: Provide reproducible sample data
The project SHALL include sample log files that demonstrate normal behavior, keyword detections, brute-force detections, and malformed-line handling.

#### Scenario: Run demo sample
- **WHEN** the user runs the documented demo command against the sample logs
- **THEN** the system produces findings that cover the major detection rules

### Requirement: Provide verification coverage
The project SHALL include tests for parsing, detection, export, and CLI behavior.

#### Scenario: Run automated tests
- **WHEN** the user runs the documented test command
- **THEN** parser, rule engine, exporter, and CLI tests execute successfully

### Requirement: Support course submission package
The project SHALL provide documentation and build commands for producing source code, executable or runnable script, sample outputs, and report material.

#### Scenario: Prepare submission artifacts
- **WHEN** the user follows the packaging instructions
- **THEN** the resulting package contains source code, runnable entry point, sample logs, exported analysis result, and report notes

### Requirement: Align with course report template
The documentation SHALL map implementation details to the course report sections, including background, theory, architecture, module design, tests, results, limitations, and future work.

#### Scenario: Write course report
- **WHEN** the user writes the course design paper
- **THEN** the project documentation provides section-level material matching the provided template
```

## openspec/changes/build-log-intrusion-detector/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/build-log-intrusion-detector/specs/intrusion-detection-rules/spec.md
- Lines: 1-33
- SHA256: ce8cb61f3a3a86597c286f689ae1ed53e452ff747a934f6aba70737a511a3287

```md
## ADDED Requirements

### Requirement: Detect keyword indicators
The system SHALL detect intrusion-related keywords such as failed login, unauthorized access, invalid user, authentication failure, permission denied, sudo failure, and suspicious command execution.

#### Scenario: Failed login keyword match
- **WHEN** a parsed log event contains a failed-login indicator
- **THEN** the system emits a finding with a rule identifier, severity, matched keyword, evidence line, and explanation

### Requirement: Detect repeated suspicious behavior
The system SHALL detect repeated suspicious behavior from the same actor or source address within a configurable time window.

#### Scenario: Brute force threshold exceeded
- **WHEN** one source address produces failed-login events at or above the configured threshold within the time window
- **THEN** the system emits a brute-force finding with the source address, count, window, severity, and supporting evidence

### Requirement: Support configurable rules
The system SHALL load detection rules and thresholds from a local configuration file while providing secure defaults when no configuration is supplied.

#### Scenario: Use default rules
- **WHEN** the user runs analysis without a custom rule file
- **THEN** the system applies the default course-demo rule set

#### Scenario: Use custom threshold
- **WHEN** the user supplies a configuration file with a changed brute-force threshold
- **THEN** the system applies that threshold in the repeated-behavior analysis

### Requirement: Classify finding severity
The system SHALL classify each finding as low, medium, high, or critical based on rule type, event count, and confidence.

#### Scenario: Severity appears in result
- **WHEN** the system emits a finding
- **THEN** the finding includes a severity value suitable for terminal display and report export
```

## openspec/changes/build-log-intrusion-detector/specs/log-ingestion/spec.md

- Source: openspec/changes/build-log-intrusion-detector/specs/log-ingestion/spec.md
- Lines: 1-30
- SHA256: eef6da1d1e31ce7aa0ccc0344ebeef5f7d458fee23973fa7811f104484ffedeb

```md
## ADDED Requirements

### Requirement: Accept local log files
The system SHALL accept one or more local log file paths as analysis input.

#### Scenario: Analyze a single readable log file
- **WHEN** the user provides a readable local log file path
- **THEN** the system parses the file and includes its records in the analysis result

#### Scenario: Reject a missing log file
- **WHEN** the user provides a path that does not exist
- **THEN** the system reports the missing file and exits with a non-zero status

### Requirement: Normalize common log formats
The system SHALL normalize Linux authentication/system log lines and generic application log lines into event records containing timestamp, source file, raw line, category, actor, target, source address, and message fields where available.

#### Scenario: Parse Linux authentication log line
- **WHEN** the input contains an SSH failed-login line from `/var/log/auth.log` or equivalent sample data
- **THEN** the system extracts a normalized failed-login event with the source address and account name when present

#### Scenario: Preserve unknown log line
- **WHEN** the input contains a line that does not match a known parser
- **THEN** the system preserves the raw line as an unknown event instead of discarding it

### Requirement: Handle malformed input safely
The system SHALL continue analysis when individual log lines are malformed or partially missing fields.

#### Scenario: Encounter malformed line
- **WHEN** one line cannot be parsed into a known format
- **THEN** the system records it as an unknown or malformed event and continues parsing later lines
```

## openspec/changes/build-log-intrusion-detector/specs/report-export/spec.md

- Source: openspec/changes/build-log-intrusion-detector/specs/report-export/spec.md
- Lines: 1-26
- SHA256: cf6641850167140f1405bf24590e700f21e90963653e6d1731232598fd306915

```md
## ADDED Requirements

### Requirement: Display terminal summary
The system SHALL display a concise terminal summary after analysis.

#### Scenario: Summary after successful analysis
- **WHEN** analysis completes successfully
- **THEN** the terminal output includes total files, total parsed events, finding count by severity, and top suspicious sources

### Requirement: Export detailed analysis logs
The system SHALL export detailed analysis results to JSON and CSV formats.

#### Scenario: JSON export requested
- **WHEN** the user requests JSON output
- **THEN** the system writes a JSON file containing metadata, parsed-event counts, findings, and evidence records

#### Scenario: CSV export requested
- **WHEN** the user requests CSV output
- **THEN** the system writes a CSV file containing one row per finding with rule, severity, source, target, timestamp, and evidence fields

### Requirement: Produce report-friendly Markdown
The system SHALL generate a Markdown report suitable for screenshots, demo explanation, and inclusion in the course paper.

#### Scenario: Markdown report requested
- **WHEN** the user requests Markdown output
- **THEN** the system writes a report containing overview metrics, rule summaries, key findings, and interpretation notes
```

