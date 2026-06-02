## 1. Project Setup

- [x] 1.1 Create Python package structure for CLI, parser, rules, exporter, config, and tests.
- [x] 1.2 Add project metadata, dependency list, and a runnable command entry point.
- [x] 1.3 Add sample log files covering normal behavior, failed login, unauthorized access, brute force, sudo failure, and malformed lines.

## 2. Log Ingestion

- [x] 2.1 Implement local file loading with clear errors for missing or unreadable files.
- [x] 2.2 Implement parsers for Linux auth/syslog-style lines and generic application log lines.
- [x] 2.3 Normalize parsed lines into event objects and preserve unknown or malformed lines.
- [x] 2.4 Add parser unit tests for known formats, unknown lines, and malformed input.

## 3. Detection Rules

- [x] 3.1 Implement default keyword rules for failed login, invalid user, unauthorized access, permission denied, sudo failure, and suspicious commands.
- [x] 3.2 Implement repeated failed-login or brute-force detection using configurable thresholds and time windows.
- [x] 3.3 Implement severity classification and evidence-rich finding objects.
- [x] 3.4 Add rule-engine tests for keyword matches, threshold matches, defaults, and custom config.

## 4. Report Export and CLI

- [x] 4.1 Implement terminal summary output with event counts, finding counts by severity, and top suspicious sources.
- [x] 4.2 Implement JSON export with metadata, counts, findings, and evidence.
- [x] 4.3 Implement CSV export with one row per finding.
- [x] 4.4 Implement Markdown report export for course paper screenshots and demo narration.
- [x] 4.5 Implement CLI options for input files, config path, output directory, output formats, and verbosity.

## 5. Verification and Course Materials

- [x] 5.1 Add end-to-end CLI tests using sample logs.
- [x] 5.2 Add documentation for setup, demo commands, test commands, export examples, and packaging.
- [x] 5.3 Add course-report notes that map the implementation to the provided template sections.
- [x] 5.4 Run the full verification command and record sample outputs for the final report/demo.
