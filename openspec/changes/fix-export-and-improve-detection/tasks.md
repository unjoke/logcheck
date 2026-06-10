## 1. Export Regression Coverage

- [x] 1.1 Add API regression tests for successful JSON, CSV, and Markdown export downloads after a web analysis run.
- [x] 1.2 Add API tests for unsupported export format, missing analysis id, and unknown or stale analysis id.
- [x] 1.3 Add frontend test coverage or browser verification for export buttons before analysis, after analysis, and after export errors.

## 2. Export Fix

- [x] 2.1 Audit the current frontend export button handler and backend `/api/exports/<fmt>` route to identify the failing path.
- [x] 2.2 Fix backend export handling so report files are created under the local worktmp export directory and served with stable filenames/content types.
- [x] 2.3 Fix frontend export invocation so the latest successful `analysis_id` is included and stale state is cleared or handled correctly.
- [x] 2.4 Add clear local error handling for export failures without introducing remote/network behavior.

## 3. Detection Research Adaptation

- [ ] 3.1 Document the specific LogAI, LogPAI/logparser/Drain, and LogBERT-inspired ideas being adapted as lightweight local heuristics.
- [x] 3.2 Add tests for normalized-template burst detection using repeated local log messages with variable tokens.
- [x] 3.3 Add tests for suspicious local behavior sequence detection, including a non-matching outside-window case.
- [x] 3.4 Add tests for behavior-rule configuration validation, including invalid thresholds and unsupported fields.

## 4. Detection Implementation

- [x] 4.1 Add a small local template-normalization helper for rule logic while preserving original raw evidence.
- [x] 4.2 Extend `DetectionConfig` and config loading with validated behavior/template thresholds and windows.
- [x] 4.3 Implement deterministic template-burst and sequence-correlation findings with severity and confidence reasons.
- [x] 4.4 Ensure new findings serialize and export with source context, evidence, severity reason, confidence reason, and counts.

## 5. Verification

- [ ] 5.1 Run the Python test suite covering parsers, rules, exporters, CLI, and web API.
- [ ] 5.2 Run JavaScript syntax/static checks for the web frontend.
- [ ] 5.3 Run the local web dashboard and verify export downloads work from the browser for JSON, CSV, and Markdown.
- [ ] 5.4 Verify the UI still has no URL/domain inputs, remote fetching, scanning, blocking, exploitation, or external reporting controls.
