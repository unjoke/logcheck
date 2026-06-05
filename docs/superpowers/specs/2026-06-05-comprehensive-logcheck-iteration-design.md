---
comet_change: comprehensive-logcheck-iteration
role: technical-design
canonical_spec: openspec
---

# Comprehensive Logcheck Iteration Design

## Summary

This iteration turns Logcheck from a functional local course-demo tool into a more polished local security-analysis workspace. The core design keeps the existing deterministic pipeline:

```text
local log files
  -> parse and normalize
  -> detect findings
  -> summarize result
  -> generate local insights
  -> render in desktop, CLI, and exports
```

The new `analysis-insights` layer is intentionally local-only. It does not use cloud AI, threat-intelligence lookup, URL/domain access, remote upload, scanning, blocking, exploitation, or external reporting.

## Architecture

### Existing Pipeline

The current system already has a clean shape:

- `logcheck.parsers` reads local log files and normalizes lines into `Event` objects.
- `logcheck.rules` applies keyword and repeated-behavior detection to parsed events.
- `logcheck.analysis` orchestrates parsing and rule detection, then summarizes results.
- `logcheck.exporters` writes JSON, CSV, and Markdown reports.
- `logcheck.desktop` presents the PyQt local desktop workflow.
- `logcheck.cli` exposes the local command-line workflow.

The comprehensive iteration should preserve those boundaries and add only focused extensions.

### New Insights Layer

Add a local post-processing layer, likely `logcheck.insights`, that accepts an `AnalysisResult` and returns a structured insight object. The layer should be deterministic and evidence-based.

Suggested model shape:

- `InsightSummary`: risk level, headline, top suspicious behavior, evidence count.
- `EntityProfile`: entity kind, value, finding count, severity distribution, related rules, evidence references.
- `TimelineHighlight`: timestamp or file-line fallback, severity, rule, entity, source file.
- `RemediationSuggestion`: short local review suggestion, rationale, related evidence.

The insight layer should not mutate findings or events. It should derive its output from existing analysis results so desktop, CLI, and exporters can consume the same structure.

## Backend Design

### Parser and Event Metadata

Parser improvements should remain conservative. Known Linux authentication/system patterns and generic application logs should be normalized where possible; unknown lines should continue to be preserved.

Additions should focus on:

- clearer diagnostics for empty, missing, unreadable, or unsupported files;
- source context for each event: file, line number, raw line, category, timestamp, actor, target, source address;
- optional parser confidence when a parser can distinguish exact, partial, and unknown matches.

If partial batch analysis is introduced, it should be explicit. CLI can keep hard failure for missing files if backward compatibility requires it, while desktop can show diagnostics and continue with readable files.

### Rule Enhancements

Rule expansion should stay deterministic and configurable. The goal is not broad AI-style judgment; it is explainable behavior detection.

Add behavior patterns such as:

- suspicious command execution indicators;
- repeated lower-severity signals from the same actor or source address;
- multi-signal correlation across failed login, invalid user, permission denied, sudo failure, and suspicious commands.

Each enhanced finding should include or be able to derive:

- severity reason;
- confidence reason;
- related evidence references;
- rule configuration source.

Rule configuration validation should reject malformed enhanced rules before applying them. Partial unsafe configuration should not silently proceed.

## Frontend Design

### Visual Direction

The desktop UI should remain a restrained local operations tool, not a landing page or decorative dashboard. Polish should come from consistent layout and clear state ownership:

- one stable shell with top menu and left navigation;
- consistent panel, row, scroll-area, button, and label backgrounds;
- no accidental black strips behind text rows;
- predictable spacing and fixed work areas;
- export controls only in the Export Reports section;
- Overview focused on inputs, analysis, metrics, finding review, and insight summary.

### Workflow Layout

Recommended section responsibilities:

- Overview: source summary, run action, metrics, finding queue, finding detail, concise insight summary.
- Log Sources: multiple folders/files, candidate files, selection state, diagnostics, analyze selected logs.
- Detection Rules: active rules, imported/exported local rule configuration, enhanced behavior-pattern explanations.
- Suspicious Sources: entity profiles, severity distribution, related findings, timeline highlights.
- Export Reports: selectable analysis history and local JSON/CSV/Markdown export.

The UI must continue to show local mode clearly and must not add URL/domain/remote controls.

## Export Design

JSON and Markdown should gain richer context while preserving existing findings fields.

JSON additions:

- source context for the exported analysis run;
- active rule source;
- insight summary;
- entity profiles;
- timeline highlights;
- remediation suggestions.

Markdown additions:

- investigation summary section;
- top suspicious entities;
- notable timeline;
- non-destructive local suggestions;
- existing findings section retained.

CSV should remain findings-focused for compatibility. If columns are added, existing columns should remain.

## Data Flow

```text
Desktop/CLI selected local paths
  -> parse_files(paths)
  -> AnalysisResult(events, findings)
  -> generate_insights(result)
  -> AnalysisRun(paths, result, insights)
  -> UI render / CLI summary / export
```

If `AnalysisResult` is extended to carry insights, it should do so with a default value so existing tests and call sites remain stable. An alternative is to keep insights separate on `AnalysisRun`; however, exporters and CLI will be simpler if they can receive one enriched result object. The implementation should choose the smaller compatible change after tests pin the desired API.

## Testing Strategy

Use TDD for implementation slices:

- parser diagnostics and richer event metadata;
- enhanced behavior-pattern findings and rule validation;
- insight generation for findings, no findings, missing timestamps, unknown entities, and suggestions;
- exporter compatibility plus new JSON/Markdown insight sections;
- desktop rendering of insight summary, entity profiles, source diagnostics, and polished UI constraints;
- local-only safety checks for frontend controls.

Full verification should include:

- `python -m unittest discover`;
- targeted desktop tests;
- manual desktop visual check at initial and minimum window sizes;
- local-only safety review showing no remote target, upload, scan, block, exploitation, or external reporting controls.

## Risks and Mitigations

- Broad scope could sprawl. Mitigate by implementing in ordered slices: backend metadata, rules, insights, frontend, export, verification.
- Insight text could overclaim. Mitigate by tying every insight to severity, confidence, and evidence references.
- Export changes could break compatibility. Mitigate by adding fields and sections rather than removing existing fields.
- UI polish could regress workflows. Mitigate with desktop tests for core actions and manual screenshots.
- Batch diagnostics may conflict with CLI hard-fail behavior. Mitigate by keeping CLI compatibility unless a spec explicitly changes it.

## Acceptance

This design is accepted when the implementation demonstrates:

- a cleaner desktop workspace;
- better local source diagnostics and mixed-format resilience;
- enhanced explainable rules;
- local insight summaries and entity profiles;
- enriched JSON/Markdown reports;
- full test coverage and manual desktop verification;
- unchanged local-only safety boundary.
