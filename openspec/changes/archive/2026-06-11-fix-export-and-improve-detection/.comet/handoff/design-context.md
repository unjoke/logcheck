# Comet Design Handoff

- Change: fix-export-and-improve-detection
- Phase: design
- Mode: compact
- Context hash: 2c90d70ae586511ca58172a23d9e3bb7ee7c15ef07ea4d180b46ead2c74b49d5

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/fix-export-and-improve-detection/proposal.md

- Source: openspec/changes/fix-export-and-improve-detection/proposal.md
- Lines: 1-32
- SHA256: bc5f2f30c5935a668eecc85858e70b0bd7c16fbd9ecb529256654f783fa8bafc

```md
## Why

The web export workflow is currently reported as unusable, which breaks the coursework/demo path for saving JSON, CSV, and Markdown reports after local analysis. At the same time, the existing detector is still mostly keyword and simple correlation based; recent open-source log detection work shows a practical path toward stronger detection by adding structured template extraction, frequency/sequence anomalies, and clearer rule provenance while preserving Logcheck's local-only safety boundary.

## What Changes

- Fix the web report export flow so JSON, CSV, and Markdown downloads work reliably after the latest local analysis result.
- Add regression coverage for export API and frontend export states, including missing analysis id, stale/unknown analysis id, unsupported formats, and successful downloads.
- Improve detection logic using lightweight lessons from modern open-source log analytics projects:
  - parse or normalize repeated log message templates before matching where feasible;
  - add configurable behavior rules for template frequency, repeated sequences, and rare suspicious combinations;
  - preserve clear evidence, severity reasons, confidence reasons, and source provenance for every new finding.
- Document the research basis and keep the implementation suitable for a small local course project rather than introducing heavyweight model training.
- Preserve the local-only safety boundary: no URL/domain inputs, remote fetching, scanning, blocking, exploitation, external reporting, internet-dependent detection, or automatic changes to host systems.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `report-export`: Web export behavior must reliably return downloadable local reports for the selected analysis run and report actionable errors when export cannot proceed.
- `intrusion-detection-rules`: Detection rules must support explainable local behavior/template signals inspired by current log anomaly detection practice, without requiring remote services or model training.
- `web-frontend`: Export controls must reflect analysis/export state and remain local-only while invoking the fixed export endpoint.

## Impact

- Affects `logcheck/webapp.py`, `logcheck/web_static/app.js`, frontend styling if export state messaging needs adjustment, and tests covering web API/export behavior.
- May affect `logcheck/rules.py`, `logcheck/config.py`, `logcheck/models.py`, `logcheck/parsers.py`, `logcheck/analysis.py`, and related tests if lightweight template/behavior detection requires new fields or configuration.
- Does not add network dependencies, domain inputs, active response features, exploitation logic, blocking controls, or external reporting.
```

## openspec/changes/fix-export-and-improve-detection/design.md

- Source: openspec/changes/fix-export-and-improve-detection/design.md
- Lines: 1-78
- SHA256: 882d71b80bb3aa2a3a05fa2766b059ef9daa92639cacd1a45a459475d68de31f

```md
## Context

Logcheck is a local log intrusion detection tool for coursework and CTF-style demonstration. Existing specs already require local analysis, browser exports, report metadata, insight summaries, and safe rule validation. The code currently stores web analysis results in memory and exposes `/api/exports/<fmt>` for `json`, `csv`, and `markdown`; exporters themselves create parent directories, but the web flow needs regression coverage around analysis id handling, response download behavior, and frontend state.

The current detection model is intentionally simple: parsers normalize local lines into `Event`, keyword rules match common indicators, and correlation rules such as brute force group repeated failures. External research suggests useful next steps, but most advanced systems are larger than this project. Salesforce LogAI describes a full log analytics stack with a common data model, preprocessing, parsing, clustering, time-series/statistical/ML/deep-learning anomaly detection, and GUI review. LogPAI's logparser emphasizes automated template extraction as a foundation for structured analytics, with Drain extracting event templates and structured logs. LogBERT-style work uses parsed sequences and language-model style training, but that is too heavy for this local tool.

The design therefore adapts the ideas, not the infrastructure: improve local deterministic rules using template-like normalization, per-source/template counts, sequence/frequency heuristics, and clear evidence explanations.

## Goals / Non-Goals

**Goals:**

- Make web exports reliably downloadable for JSON, CSV, and Markdown after a successful analysis run.
- Return clear local API errors for unsupported format, missing analysis id, unknown/stale analysis id, and exporter failures.
- Keep frontend export buttons disabled or explanatory before analysis and use the latest returned `analysis_id` when exporting.
- Add lightweight, explainable behavior detection inspired by template/frequency/sequence anomaly systems.
- Extend rule configuration safely so new behavior thresholds can be tuned and validated.
- Preserve local source context, severity reason, confidence reason, and evidence for every finding.

**Non-Goals:**

- No remote log collection, domain/URL target analysis, internet lookup, scan, block, exploit, or external report submission.
- No mandatory ML/deep-learning dependency, GPU requirement, online dataset download, or model training workflow.
- No production SIEM replacement, multi-user case management, or persistent database.
- No removal of existing keyword, brute-force, CLI, JSON, CSV, or Markdown behavior.

## Decisions

### Decision: Treat export as a selected analysis artifact

The web API should export only a result identified by `analysis_id`, and the frontend should hold the latest successful id. Export responses should be downloads with stable filenames and correct content types. Tests should exercise the API directly because broken export is easiest to pin down at the route boundary.

Alternative considered: export from global "latest result" without an id. That is simpler in the UI, but it makes stale results harder to reason about and weakens the current route contract.

### Decision: Fix export by hardening the route and frontend state together

Backend work should ensure export directories and temporary paths are safe, exporter exceptions become JSON errors, and successful files are served without requiring remote access. Frontend work should ensure buttons are disabled before analysis, include the latest `analysis_id`, handle non-OK responses, and avoid stale id reuse after failed or empty analysis.

Alternative considered: only patch frontend buttons. That may hide the current symptom but would leave backend edge cases and no durable regression coverage.

### Decision: Use lightweight template normalization before advanced models

Borrow the first step from LogAI/logparser/Drain-style systems: normalize variable tokens such as IP addresses, users, quoted paths, numbers, and hashes into template-like forms. Use those templates for counts and correlations, while retaining the original raw evidence for review.

Alternative considered: import a full log parsing library. That brings more dependencies and configuration than the course project needs, and some research toolkits explicitly warn that they are benchmark/research-oriented rather than production-ready.

### Decision: Add explainable behavior heuristics rather than train models

Add deterministic rules for repeated template bursts, suspicious template sequences, and multi-signal source/actor behavior. These rules should be configurable and tested with local samples. Severity and confidence must be derived from observable count/window/evidence facts, not opaque scores.

Alternative considered: implement LogBERT/DeepLog-style sequence modeling. That would better match modern research, but it requires training data, model artifacts, and runtime complexity that conflict with Logcheck's local lightweight scope.

### Decision: Keep research citations in docs and tests grounded in behavior

The implementation should not depend on external sources at runtime. Research informs the design only; tests verify local behavior such as "template burst produces a finding" and "export endpoint returns Markdown attachment."

Alternative considered: include external benchmark datasets or downloads. That would violate the local-only demonstration boundary and make test runs fragile.

## Risks / Trade-offs

- Template normalization may over-group unrelated messages -> keep raw evidence, conservative thresholds, and clear confidence reasons.
- Added rules may increase false positives -> expose thresholds in validated config and test benign baselines.
- Exported temporary files may accumulate -> keep them under `worktmp/web_uploads/exports` and consider cleanup after response only if it does not break downloads on Windows.
- Frontend may retain stale analysis state after errors -> explicitly clear or preserve state according to analysis success and test the expected behavior.
- Research-inspired wording may overpromise "AI" capability -> describe this as deterministic local heuristics inspired by log anomaly detection literature.

## Migration Plan

1. Add failing regression tests for the current export failure and frontend export state.
2. Fix the web export route and frontend export invocation.
3. Add tests for template normalization and behavior-rule findings.
4. Implement the smallest config/model/rule changes needed for explainable template and sequence detection.
5. Run Python tests, JavaScript syntax checks, and browser verification for export buttons/download responses.

## Open Questions

- Should exported web files be deleted immediately after `send_file` completes, or retained under `worktmp` for manual inspection during coursework demos?
- Should template normalization be internal-only for rules, or should template ids/templates be included in JSON and Markdown exports as evidence context?
```

## openspec/changes/fix-export-and-improve-detection/tasks.md

- Source: openspec/changes/fix-export-and-improve-detection/tasks.md
- Lines: 1-33
- SHA256: 80821f8b14d8da3b079e633c17ba0c9e1190d6ff163b36713969ed3bb3fac941

```md
## 1. Export Regression Coverage

- [ ] 1.1 Add API regression tests for successful JSON, CSV, and Markdown export downloads after a web analysis run.
- [ ] 1.2 Add API tests for unsupported export format, missing analysis id, and unknown or stale analysis id.
- [ ] 1.3 Add frontend test coverage or browser verification for export buttons before analysis, after analysis, and after export errors.

## 2. Export Fix

- [ ] 2.1 Audit the current frontend export button handler and backend `/api/exports/<fmt>` route to identify the failing path.
- [ ] 2.2 Fix backend export handling so report files are created under the local worktmp export directory and served with stable filenames/content types.
- [ ] 2.3 Fix frontend export invocation so the latest successful `analysis_id` is included and stale state is cleared or handled correctly.
- [ ] 2.4 Add clear local error handling for export failures without introducing remote/network behavior.

## 3. Detection Research Adaptation

- [ ] 3.1 Document the specific LogAI, LogPAI/logparser/Drain, and LogBERT-inspired ideas being adapted as lightweight local heuristics.
- [ ] 3.2 Add tests for normalized-template burst detection using repeated local log messages with variable tokens.
- [ ] 3.3 Add tests for suspicious local behavior sequence detection, including a non-matching outside-window case.
- [ ] 3.4 Add tests for behavior-rule configuration validation, including invalid thresholds and unsupported fields.

## 4. Detection Implementation

- [ ] 4.1 Add a small local template-normalization helper for rule logic while preserving original raw evidence.
- [ ] 4.2 Extend `DetectionConfig` and config loading with validated behavior/template thresholds and windows.
- [ ] 4.3 Implement deterministic template-burst and sequence-correlation findings with severity and confidence reasons.
- [ ] 4.4 Ensure new findings serialize and export with source context, evidence, severity reason, confidence reason, and counts.

## 5. Verification

- [ ] 5.1 Run the Python test suite covering parsers, rules, exporters, CLI, and web API.
- [ ] 5.2 Run JavaScript syntax/static checks for the web frontend.
- [ ] 5.3 Run the local web dashboard and verify export downloads work from the browser for JSON, CSV, and Markdown.
- [ ] 5.4 Verify the UI still has no URL/domain inputs, remote fetching, scanning, blocking, exploitation, or external reporting controls.
```

## openspec/changes/fix-export-and-improve-detection/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/fix-export-and-improve-detection/specs/intrusion-detection-rules/spec.md
- Lines: 1-47
- SHA256: 297ac9f9c4b20e65d42135f156b55a9953e70bd924efbb2739d6a1ed60f96f8a

```md
## ADDED Requirements

### Requirement: Detect local template behavior signals
The intrusion detection rules capability SHALL support explainable local behavior signals derived from normalized log message templates.

#### Scenario: Repeated template burst
- **WHEN** local parsed events from the same source address or actor repeat a suspicious normalized template at or above a configured threshold
- **THEN** the system emits a behavior finding with rule id, severity, confidence reason, severity reason, count, source context, and representative raw evidence

#### Scenario: Benign repeated template below threshold
- **WHEN** local parsed events repeat a normalized template below the configured threshold or match a benign baseline
- **THEN** the system does not emit a template-burst finding for that behavior

### Requirement: Detect suspicious local behavior sequences
The intrusion detection rules capability SHALL support deterministic sequence rules for suspicious local event progressions.

#### Scenario: Authentication to privilege escalation sequence
- **WHEN** local events from the same source address or actor show failed authentication followed by privilege-escalation indicators within a configured window
- **THEN** the system emits a correlated behavior finding that includes evidence from both stages

#### Scenario: Sequence outside window
- **WHEN** matching local events occur outside the configured correlation window
- **THEN** the system does not emit the sequence finding

### Requirement: Validate behavior rule configuration
The intrusion detection rules capability SHALL validate behavior/template rule configuration before applying it.

#### Scenario: Valid behavior thresholds are loaded
- **WHEN** a local rule configuration provides supported behavior thresholds and windows
- **THEN** the system applies those values to behavior/template detection

#### Scenario: Invalid behavior rules are rejected
- **WHEN** a local rule configuration contains malformed behavior rule fields, invalid thresholds, invalid windows, or unsupported rule types
- **THEN** the system rejects the configuration with a clear error
- **AND** it does not silently apply partial behavior-rule configuration

### Requirement: Preserve explainability for research-inspired rules
The intrusion detection rules capability SHALL keep research-inspired behavior detections explainable and reviewable.

#### Scenario: Behavior finding includes provenance
- **WHEN** a template or sequence behavior finding is emitted
- **THEN** the finding includes local source file, line number when available, actor or source address when available, raw evidence lines, severity reason, and confidence reason

#### Scenario: Detection remains local-only
- **WHEN** behavior/template detection runs
- **THEN** it uses only local parsed events and local configuration
- **AND** it does not fetch external data, query domains, scan networks, train remote models, or submit reports externally
```

## openspec/changes/fix-export-and-improve-detection/specs/report-export/spec.md

- Source: openspec/changes/fix-export-and-improve-detection/specs/report-export/spec.md
- Lines: 1-34
- SHA256: 9e7277ad5b1e900c0672e487e2ad6aceeb212f070b0d61558086ef599b79606e

```md
## ADDED Requirements

### Requirement: Export selected web analysis result
The report export capability SHALL return a downloadable local report for a completed web analysis result identified by analysis id.

#### Scenario: Web export succeeds after analysis
- **WHEN** a web analysis has completed and the caller requests JSON, CSV, or Markdown export with that analysis id
- **THEN** the system returns a downloadable report file for that result
- **AND** the report content preserves existing finding fields, insights when available, and source context metadata

#### Scenario: Web export uses supported filenames
- **WHEN** a supported web export format is requested
- **THEN** the downloaded filename is `analysis.json`, `analysis.csv`, or `analysis.md` according to the requested format
- **AND** the response content type matches the exported format closely enough for browsers to download it

### Requirement: Report web export errors clearly
The report export capability SHALL return clear local errors when a web export cannot be produced.

#### Scenario: Missing analysis id
- **WHEN** a web export request omits the analysis id
- **THEN** the system returns an error explaining that analysis must run and an analysis id is required before exporting

#### Scenario: Unknown analysis id
- **WHEN** a web export request references an analysis id that is not available in the current local session
- **THEN** the system returns an error explaining that analysis must run before exporting

#### Scenario: Unsupported export format
- **WHEN** a web export request uses an unsupported format
- **THEN** the system rejects the request without creating a report

#### Scenario: Exporter failure
- **WHEN** the local exporter cannot write or serve the report file
- **THEN** the system returns a clear local error
- **AND** it does not report a successful download
```

## openspec/changes/fix-export-and-improve-detection/specs/web-frontend/spec.md

- Source: openspec/changes/fix-export-and-improve-detection/specs/web-frontend/spec.md
- Lines: 1-29
- SHA256: ce7c3d8e1bc23c17ca75247d25f5da2361b34db58f833ebb8135b43ce57727b7

```md
## ADDED Requirements

### Requirement: Manage export controls from analysis state
The web frontend SHALL manage report export controls according to the latest local analysis state.

#### Scenario: Export disabled before analysis
- **WHEN** no local analysis result is available
- **THEN** JSON, CSV, and Markdown export controls are unavailable or report that analysis must run before exporting

#### Scenario: Export uses latest analysis id
- **WHEN** a local analysis completes successfully and the user requests an export
- **THEN** the frontend calls the export endpoint with the latest returned analysis id
- **AND** it does not use a stale analysis id from an earlier failed or replaced analysis

#### Scenario: Export failure is visible
- **WHEN** the export endpoint returns an error
- **THEN** the frontend displays or exposes a clear local error state instead of silently failing

### Requirement: Preserve local-only export UX
The web frontend SHALL keep export behavior local and passive.

#### Scenario: Export controls do not introduce remote targets
- **WHEN** the export controls are displayed
- **THEN** they do not introduce URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, or external reporting controls

#### Scenario: Browser download remains local report output
- **WHEN** the user downloads a report from the web frontend
- **THEN** the downloaded content is generated from local analysis results already held by the application
- **AND** the workflow does not require external browsing or internet access
```

