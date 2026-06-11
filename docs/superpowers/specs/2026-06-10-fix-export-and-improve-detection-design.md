---
comet_change: fix-export-and-improve-detection
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-11-fix-export-and-improve-detection
status: final
---

# Fix Export and Improve Detection Technical Design

## Summary

This change fixes the broken web export workflow and improves Logcheck's local detection logic with lightweight, explainable behavior heuristics inspired by modern log anomaly detection work.

The design deliberately adapts ideas from LogAI, LogPAI/Drain, and LogBERT-style sequence detection without adding remote services, model training, external datasets, domain inputs, scanning, blocking, exploitation, or external reporting.

## Current Shape

The web app stores completed analysis results in `app.config["ANALYSIS_RESULTS"]` and exports reports through `/api/exports/<fmt>?analysis_id=...`. Exporter functions already create parent directories and write JSON, CSV, and Markdown files, but the web path needs route-level regression coverage and frontend state hardening.

Detection currently flows through `detect_findings(events, config)`, which combines keyword findings, suspicious command behavior, privilege-escalation indicators, brute-force correlation, and multi-signal correlation. `DetectionConfig` currently contains keyword rules and brute-force thresholds. This is a good base for small deterministic enhancements.

## Approach

### Export Fix

Keep the existing export route contract:

```text
GET /api/exports/<fmt>?analysis_id=<id>
```

The backend will:

- validate supported formats before writing files;
- require `analysis_id`;
- reject unknown or stale ids with a clear JSON error;
- write export files under the configured local worktmp export directory;
- return downloads with stable filenames: `analysis.json`, `analysis.csv`, `analysis.md`;
- convert local exporter or file-serving failures into clear error responses.

The frontend will:

- keep export controls unavailable or explanatory before analysis;
- store only the latest successful `analysis_id`;
- include that id in export requests;
- avoid using stale ids after failed or replaced analysis;
- surface export errors instead of failing silently.

### Detection Enhancement

Add deterministic local behavior rules in three small layers:

1. Template normalization helper

   Normalize variable tokens in event text into template-like forms while preserving raw lines as evidence. Initial normalized token names should cover IP addresses, numbers, quoted strings, obvious paths, hashes, and volatile ports or ids.

2. Template burst detection

   Group events by source address or actor plus normalized template. If a suspicious template repeats at or above a configured threshold within the available event stream, emit a `behavior.template_burst` style finding with representative raw evidence and count.

3. Suspicious sequence detection

   Detect a local sequence where the same source address or actor shows failed authentication followed by privilege-escalation indicators within the configured window. Emit a correlated behavior finding with evidence from both stages.

The new rules should run after existing direct keyword/behavior rules and before final multi-signal correlation, so later correlation can still observe their findings if needed.

## Configuration

Extend `DetectionConfig` conservatively with a behavior section equivalent to:

```text
behavior.template_burst_threshold
behavior.sequence_window_minutes
behavior.enabled
```

The exact field names can follow existing config style during implementation, but they must round-trip through `config_to_dict()` and `load_config()`.

Validation rules:

- thresholds and windows must be positive integers;
- booleans must not be accepted as integers;
- unsupported behavior fields must be rejected instead of ignored;
- malformed behavior configuration must fail the whole config load.

Defaults should keep current behavior stable enough for existing tests, while enabling the new local heuristics for bundled samples and explicit test cases.

## Data Flow

```text
local logs
  -> parsers produce Event(raw_line, message, actor, source_address, timestamp, ...)
  -> detect_findings
       -> keyword and existing behavior rules
       -> template normalization for local events
       -> template burst grouping
       -> auth-to-privilege sequence grouping
       -> multi-signal correlation
  -> AnalysisResult(findings, insights)
  -> web serialization and exporters
  -> browser review and report downloads
```

No network calls or external services are introduced at any point.

## Testing Strategy

### Export Tests

Add or update web API tests to cover:

- successful JSON export after analysis;
- successful CSV export after analysis;
- successful Markdown export after analysis;
- unsupported format;
- missing `analysis_id`;
- unknown or stale `analysis_id`;
- report filename/content-type expectations.

Add frontend or browser verification for:

- export controls before analysis;
- export controls after successful analysis;
- visible error handling when export fails.

### Detection Tests

Add rule tests for:

- repeated local messages with different variable tokens normalizing to the same suspicious template;
- repeated template below threshold not producing a finding;
- failed-authentication to privilege-escalation sequence within the window;
- same sequence outside the window not producing a finding;
- new findings carrying raw evidence, count, severity reason, confidence reason, source file, line number, and actor/source address when available.

Add config tests for:

- valid behavior thresholds loading correctly;
- invalid thresholds and windows rejected;
- unsupported behavior fields rejected;
- `config_to_dict()` output reloading into an equivalent config.

### Verification

Run:

```text
python -m pytest tests -q
node --check logcheck/web_static/app.js
```

Then start the local web dashboard and verify JSON, CSV, and Markdown downloads in a browser. Also verify the UI still contains no URL/domain inputs, remote fetching, scanning, blocking, exploitation, or external reporting controls.

## Risks

- Template normalization can over-group unrelated logs. Mitigation: use conservative suspicious-template matching, preserve raw evidence, and include confidence reasons.
- More behavior rules may increase false positives. Mitigation: configurable thresholds, benign baseline tests, and clear explanations.
- Export temp files may accumulate under worktmp. Mitigation: keep files under the local worktmp export directory and decide cleanup only after confirming Windows download behavior.
- Frontend state can become stale after failures. Mitigation: tests around failed analysis/export state transitions.

## Spec Patch

No additional OpenSpec delta spec patch is required. The existing delta specs already cover export success/error behavior, frontend export state, template behavior signals, suspicious sequences, config validation, explainability, and local-only boundaries.
