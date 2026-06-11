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
