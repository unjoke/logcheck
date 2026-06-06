# Comet Design Handoff

- Change: comprehensive-logcheck-iteration
- Phase: design
- Mode: compact
- Context hash: 913f8000d10fc276390b962cf30abe019b2b5e5aba44d69c31132d35a0b04c2d

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/comprehensive-logcheck-iteration/proposal.md

- Source: openspec/changes/comprehensive-logcheck-iteration/proposal.md
- Lines: 1-33
- SHA256: 11d4c5fb4c6f829820b072765a69f77d95349c1ccce8f5d20d61a2db2ad94486

```md
## Why

Logcheck already works as a local log analysis desktop tool, but the current experience still feels like a course demo: the desktop UI is functional but visually uneven, backend analysis is rule-limited, and reports do not yet tell a strong investigation story. A comprehensive iteration should turn it into a more polished local security-analysis application while preserving the safety boundary.

## What Changes

- Refine the desktop frontend into a cleaner operational workspace with stronger visual hierarchy, consistent panels, clearer source selection, better empty states, and less duplicated navigation/control surface.
- Improve backend log ingestion resilience for larger local batches, clearer file diagnostics, normalized event metadata, and safer handling of mixed log formats.
- Expand detection rules beyond basic keywords and repeated failed login into configurable behavior patterns with explainable severity and confidence.
- Add a local analysis-insights capability that turns findings into an investigation summary, suspicious entity profile, timeline highlights, and local remediation suggestions.
- Improve report export so JSON/CSV/Markdown include richer metadata, selected-source context, insight summaries, and clearer output status.
- Preserve the local-only safety boundary: no URL input, domain access, remote upload, network scanning, blocking, exploitation, or external reporting.

## Capabilities

### New Capabilities

- `analysis-insights`: Produce local, explainable investigation insights from parsed events and findings, including timeline highlights, suspicious entity profiles, and remediation suggestions.

### Modified Capabilities

- `desktop-frontend`: Improve layout, visual consistency, local source workflow, analysis review ergonomics, and integration of insight summaries.
- `log-ingestion`: Improve local batch ingestion diagnostics, normalization, and mixed-format resilience.
- `intrusion-detection-rules`: Add richer configurable behavior patterns, confidence/severity explanations, and safer rule validation.
- `report-export`: Include insight and source-context metadata in exported reports while keeping existing formats.
- `course-deliverables`: Update verification expectations so the polished UI, enhanced backend behavior, exports, and local-only safety evidence are demonstrable.

## Impact

- Affects `logcheck/desktop.py`, analysis orchestration, parser normalization, rule detection, export payloads, CLI/desktop result presentation, and tests across desktop, parsing, rules, exporters, and CLI.
- May add a small internal module for insight generation, but should not add network dependencies.
- Existing CLI commands and export file formats remain backward compatible where possible; new fields may be added to JSON/Markdown output.
- Requires visual/manual desktop verification in addition to automated unit tests.
```

## openspec/changes/comprehensive-logcheck-iteration/design.md

- Source: openspec/changes/comprehensive-logcheck-iteration/design.md
- Lines: 1-49
- SHA256: 25a17fef5839e9e7b540144f76e90bf4de374737d12c175cc2f74e94b22d642e

```md
## Context

Logcheck is a local Python desktop/CLI application for analyzing local log files. The current architecture is intentionally small: parsers normalize files into events, rules produce findings, analysis summarizes results, exporters write reports, and the PyQt desktop frontend presents the workflow.

Recent frontend changes improved log source selection and removed some unwanted UI clutter, but the product still needs a coherent iteration across visual design, backend analysis quality, report usefulness, and a locally safe innovation layer. The main constraint is security: this private CTF deployment must remain local-only and must not reintroduce domain, URL, remote upload, scanning, blocking, or exploitation behavior.

## Goals / Non-Goals

**Goals:**

- Make the desktop frontend feel like a polished analysis workspace rather than a demo screen.
- Improve ingestion diagnostics and mixed-format resilience for local batch workflows.
- Expand detection from simple keyword/repetition matching into explainable behavior patterns.
- Add local insight generation that summarizes incidents, entity risk, timeline highlights, and next-step suggestions.
- Improve exports so reports carry source context, findings, insights, and clear metadata.
- Keep CLI behavior stable while enriching available output.

**Non-Goals:**

- No remote targets, network scanning, URL/domain analysis, uploads, blocking, exploitation, or external reporting.
- No cloud AI or external model dependency.
- No persistent database requirement.
- No full SIEM replacement.

## Decisions

- Keep the existing local pipeline shape: `parse -> detect -> summarize/export -> render`. This preserves testability and avoids turning the desktop frontend into a second detection engine.
- Add `analysis-insights` as a pure local post-processing layer over `AnalysisResult`. It should consume events and findings, then produce structured insights that can be rendered in desktop, CLI, and Markdown/JSON exports.
- Keep parser improvements format-aware but conservative. The parser should preserve unknown lines and add better metadata instead of discarding ambiguous input.
- Model rule enhancements as deterministic behavior patterns with confidence/severity reasons. This fits the course/security context and avoids opaque AI claims.
- Redesign the desktop layout around stable work areas: source management, analysis action, findings queue, evidence detail, insights, rules, and export. Visual polish should come from consistent spacing, surfaces, labels, and state handling rather than decorative effects.
- Extend exports by adding fields/sections, not by removing existing JSON/CSV/Markdown compatibility.

## Risks / Trade-offs

- [Risk] The change is broad enough to become unfocused -> Mitigation: implement in slices: UI shell, ingestion diagnostics, rules, insights, exports, verification.
- [Risk] Insight summaries may sound more certain than the evidence supports -> Mitigation: include confidence and evidence references for every insight.
- [Risk] UI polish could regress existing workflows -> Mitigation: keep current navigation concepts, add tests for core actions, and run manual desktop verification.
- [Risk] Export additions could break downstream consumers -> Mitigation: add fields and sections without removing existing keys or columns.
- [Risk] Larger local batches may expose performance issues -> Mitigation: keep parsing streaming-friendly where practical and test representative multi-file batches.

## Migration Plan

No persistent data migration is required. The implementation can introduce new models and optional export fields while preserving existing APIs. If the iteration needs rollback, disable insight rendering/export sections and keep the existing analysis result flow.

## Open Questions

- Should the insight panel appear in Overview, Suspicious Sources, or as a dedicated navigation item? Initial recommendation: show a concise insight summary in Overview and detailed profiles under Suspicious Sources.
- Should CSV export include insight rows, or should CSV remain findings-only while JSON/Markdown carry insights? Initial recommendation: keep CSV findings-focused and add insights to JSON/Markdown.
```

## openspec/changes/comprehensive-logcheck-iteration/tasks.md

- Source: openspec/changes/comprehensive-logcheck-iteration/tasks.md
- Lines: 1-35
- SHA256: b09d354a7be628b3c98a7e3b167e743bd22c4db1d482fe8ac3226fbafe61d506

```md
## 1. Backend Foundations

- [ ] 1.1 Add tests for richer event metadata and batch ingestion diagnostics.
- [ ] 1.2 Extend parser/event models to preserve diagnostics, parser confidence where available, and mixed-format context.
- [ ] 1.3 Add tests for enhanced behavior-pattern rules, severity reasons, confidence reasons, and invalid rule validation.
- [ ] 1.4 Implement deterministic enhanced rule patterns and safe local rule validation.

## 2. Local Analysis Insights

- [ ] 2.1 Add tests for insight summaries, suspicious entity profiles, timeline highlights, missing timestamp handling, and non-destructive suggestions.
- [ ] 2.2 Add an `analysis-insights` module or equivalent local post-processing layer.
- [ ] 2.3 Integrate insight generation with analysis results without changing the local-only safety boundary.
- [ ] 2.4 Add CLI or analysis-level access to insight summaries where appropriate.

## 3. Desktop Frontend Iteration

- [ ] 3.1 Add desktop tests for polished layout expectations, removed duplicated export controls, consistent source workflow, and insight rendering.
- [ ] 3.2 Refine the desktop stylesheet and layout hierarchy so panels, rows, labels, scroll areas, and buttons look intentional and consistent.
- [ ] 3.3 Improve Log Sources ergonomics for multiple folders/files, diagnostics, selection state, and analysis actions.
- [ ] 3.4 Add insight summary and entity profile rendering to the desktop review workflow.
- [ ] 3.5 Re-check local-only UI controls after the redesign.

## 4. Report Export Iteration

- [ ] 4.1 Add exporter tests for source context metadata, JSON insight payloads, Markdown insight sections, and compatibility of existing fields.
- [ ] 4.2 Extend JSON export with source context, insight summary, entity profiles, timeline highlights, and suggestions.
- [ ] 4.3 Extend Markdown export with readable insight and investigation sections.
- [ ] 4.4 Keep CSV finding-level output compatible while documenting any added columns.

## 5. Verification and Deliverables

- [ ] 5.1 Run parser, rules, analysis, exporter, CLI, and desktop test suites.
- [ ] 5.2 Perform manual desktop visual verification at initial and minimum window sizes.
- [ ] 5.3 Capture local-only safety evidence showing no remote target, upload, scanning, blocking, exploitation, or external reporting controls.
- [ ] 5.4 Update course deliverable notes or screenshots if required by the final packaging workflow.
```

## openspec/changes/comprehensive-logcheck-iteration/specs/analysis-insights/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/analysis-insights/spec.md
- Lines: 1-43
- SHA256: 3519cfb67a777db1e4fb10df118044510b4c2b5c3ec888ff0d8d3d2357c8bd20

```md
## ADDED Requirements

### Requirement: Generate local investigation insights
The system SHALL generate local investigation insights from parsed events and detected findings without using network access or external services.

#### Scenario: Insight summary after analysis
- **WHEN** analysis completes with one or more findings
- **THEN** the system produces an insight summary describing the most important suspicious behavior, affected entities, and evidence references
- **AND** the summary is derived only from local parsed events and findings

#### Scenario: No findings insight
- **WHEN** analysis completes with parsed events but no findings
- **THEN** the system produces a low-risk insight summary that states no configured rule patterns were detected

### Requirement: Profile suspicious entities
The system SHALL identify suspicious local entities such as source addresses, actors, targets, and files from analysis results.

#### Scenario: Entity profile includes evidence
- **WHEN** a source address, actor, target, or file appears in multiple findings
- **THEN** the system creates an entity profile with finding count, severity distribution, related rules, and evidence references

#### Scenario: Unknown entity handling
- **WHEN** a finding lacks source address or actor information
- **THEN** the system preserves the finding in an unknown-entity group instead of discarding it

### Requirement: Highlight incident timeline
The system SHALL produce a concise timeline of notable local log activity.

#### Scenario: Timeline highlights suspicious sequence
- **WHEN** multiple findings have timestamps
- **THEN** the system orders notable activity by time and includes rule, entity, severity, and source-file context

#### Scenario: Missing timestamps
- **WHEN** findings do not contain timestamps
- **THEN** the system still provides ordered evidence based on file and line references where available

### Requirement: Suggest local remediation steps
The system SHALL provide local remediation suggestions that are safe, review-oriented, and non-destructive.

#### Scenario: Suggestions remain non-destructive
- **WHEN** insights include remediation suggestions
- **THEN** the suggestions describe manual review, account audit, password policy, rule tuning, or log collection steps
- **AND** they do not perform blocking, scanning, exploitation, remote access, or system modification
```

## openspec/changes/comprehensive-logcheck-iteration/specs/course-deliverables/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/course-deliverables/spec.md
- Lines: 1-16
- SHA256: 285b0b864c6aa0648fa0a5522223077a5ec2504548296439fab133fe7cf7e5fe

```md
## ADDED Requirements

### Requirement: Demonstrate comprehensive local iteration
The project SHALL include evidence that the comprehensive iteration improves frontend polish, backend analysis behavior, reports, and local safety.

#### Scenario: Automated verification evidence
- **WHEN** the project test suite is run
- **THEN** tests cover parser diagnostics, enhanced rules, insight generation, report export, CLI compatibility, and desktop workflows

#### Scenario: Manual desktop verification evidence
- **WHEN** the iterated desktop frontend is reviewed
- **THEN** screenshots or notes show the polished workspace, multi-source workflow, findings, insights, and export section

#### Scenario: Local-only safety evidence
- **WHEN** the comprehensive iteration is demonstrated
- **THEN** the deliverable evidence shows that no URL, domain, remote upload, network scan, blocking, exploitation, or external reporting controls were added
```

## openspec/changes/comprehensive-logcheck-iteration/specs/desktop-frontend/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/desktop-frontend/spec.md
- Lines: 1-43
- SHA256: 34143c3d4b4cb49e9f3714acbcee8dbd89f325821a957c0e9082f0feca1f34ec

```md
## ADDED Requirements

### Requirement: Present polished analysis workspace
The desktop frontend SHALL present a visually consistent local analysis workspace with clear hierarchy, stable layout, and readable controls.

#### Scenario: Consistent workspace surfaces
- **WHEN** the desktop frontend is displayed
- **THEN** panels, rows, buttons, labels, and scroll areas use consistent spacing, background hierarchy, and borders
- **AND** text rows do not appear as accidental black strips against unrelated gray regions

#### Scenario: Clean overview actions
- **WHEN** the Overview screen is displayed
- **THEN** it focuses on source status, analysis action, metrics, findings, details, and insight summary
- **AND** it does not duplicate export actions that belong to the Export Reports section

### Requirement: Integrate analysis insights
The desktop frontend SHALL display local analysis insights alongside findings in a way that supports investigation.

#### Scenario: Show insight summary
- **WHEN** analysis completes
- **THEN** the Overview screen displays a concise local insight summary with risk level, top suspicious entities, and evidence count

#### Scenario: Show detailed entity profiles
- **WHEN** the user opens the suspicious sources or finding detail workflow
- **THEN** the desktop frontend shows entity profiles and related evidence generated by the local insight layer

### Requirement: Improve source workflow ergonomics
The desktop frontend SHALL support efficient local source selection and review for multiple folders and files.

#### Scenario: Multiple folders and files
- **WHEN** the user selects multiple local folders or multiple local files
- **THEN** the desktop frontend lists all eligible local files and lets the user choose which files participate in analysis

#### Scenario: Source diagnostics visible
- **WHEN** some selected files are unreadable, empty, or unsupported
- **THEN** the desktop frontend reports diagnostics without hiding readable files that can still be analyzed

### Requirement: Preserve local-only safety during frontend iteration
The iterated desktop frontend SHALL remain limited to local files, local rules, local analysis, and local exports.

#### Scenario: No remote controls after redesign
- **WHEN** the redesigned UI is displayed
- **THEN** it does not include URL inputs, domain inputs, remote uploads, network scans, blocking actions, exploitation actions, or external reporting controls
```

## openspec/changes/comprehensive-logcheck-iteration/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/intrusion-detection-rules/spec.md
- Lines: 1-31
- SHA256: 4a141af47ef8865eb9dfc3608d739345e94cc1b85ef0c7f1eb6fc4e9bf4fe228

```md
## ADDED Requirements

### Requirement: Detect configurable behavior patterns
The intrusion detection rules capability SHALL detect configurable behavior patterns beyond individual keyword matches.

#### Scenario: Suspicious command pattern
- **WHEN** parsed events contain suspicious command execution indicators
- **THEN** the system emits a behavior-pattern finding with rule identifier, severity, confidence, matched evidence, and explanation

#### Scenario: Multi-signal suspicious actor
- **WHEN** one actor or source address triggers multiple lower-severity indicators in a local analysis run
- **THEN** the system can emit a correlated behavior finding with evidence references

### Requirement: Explain severity and confidence
The intrusion detection rules capability SHALL explain why each finding received its severity and confidence.

#### Scenario: Severity explanation
- **WHEN** the system emits a finding
- **THEN** the finding includes or can derive a human-readable severity reason based on rule type, count, evidence, and configured thresholds

#### Scenario: Confidence explanation
- **WHEN** the system emits a finding from a behavior pattern
- **THEN** the finding includes or can derive a confidence reason that distinguishes exact keyword matches, repeated behavior, and correlated signals

### Requirement: Validate enhanced rule configuration safely
The intrusion detection rules capability SHALL validate enhanced local rule configuration before applying it.

#### Scenario: Reject unsafe or malformed enhanced rules
- **WHEN** a local rule file contains malformed behavior patterns, invalid thresholds, or unsupported rule fields
- **THEN** the system rejects the file with a clear error
- **AND** it does not silently apply partial unsafe configuration
```

## openspec/changes/comprehensive-logcheck-iteration/specs/log-ingestion/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/log-ingestion/spec.md
- Lines: 1-24
- SHA256: a6d6b735d873fb9d48933cb8d2610c4e950c708ff9b8a9091569a0d2c82bcc50

```md
## ADDED Requirements

### Requirement: Report local batch ingestion diagnostics
The log ingestion capability SHALL report diagnostics for local batch inputs while continuing to parse readable files.

#### Scenario: Mixed readable and unreadable files
- **WHEN** a batch includes readable files and files that are missing or unreadable
- **THEN** the system reports diagnostics for the problem files
- **AND** the readable files remain available for analysis when the caller supports partial results

#### Scenario: Empty local file
- **WHEN** a selected local file contains no parseable lines
- **THEN** the system records a diagnostic indicating that the file contributed no events

### Requirement: Normalize richer event metadata
The log ingestion capability SHALL preserve source context needed for frontend review, insight generation, and reports.

#### Scenario: Preserve source context
- **WHEN** a local log line is parsed
- **THEN** the event includes source file, line number, raw line, category, timestamp when available, actor, target, source address, and parser confidence when available

#### Scenario: Mixed format batch
- **WHEN** local batch input contains Linux authentication logs, system logs, and generic application logs
- **THEN** the system normalizes known patterns and preserves unknown lines as unknown events
```

## openspec/changes/comprehensive-logcheck-iteration/specs/report-export/spec.md

- Source: openspec/changes/comprehensive-logcheck-iteration/specs/report-export/spec.md
- Lines: 1-27
- SHA256: 13e2a1723eddecd1b4c677c86ce6c27b11e20b4b2262f398ca9988c74a4f67cb

```md
## ADDED Requirements

### Requirement: Export local insight summaries
The report export capability SHALL include local investigation insights in supported report formats.

#### Scenario: JSON includes insights
- **WHEN** JSON export is requested after analysis with insights
- **THEN** the JSON output includes insight summary, entity profiles, timeline highlights, remediation suggestions, and evidence references

#### Scenario: Markdown includes readable insight section
- **WHEN** Markdown export is requested after analysis with insights
- **THEN** the Markdown output includes a readable investigation insight section suitable for demo review and coursework screenshots

### Requirement: Export selected source context
The report export capability SHALL include source-selection context for the exported analysis run.

#### Scenario: Export source context
- **WHEN** a report is exported from a selected analysis run
- **THEN** the report metadata includes analyzed file names or paths, event count, finding count, active rule source, and export timestamp

### Requirement: Preserve existing export compatibility
The report export capability SHALL preserve existing JSON, CSV, and Markdown report availability.

#### Scenario: Existing formats remain available
- **WHEN** the user exports reports after the comprehensive iteration
- **THEN** JSON, CSV, and Markdown outputs are still written locally
- **AND** existing finding-level fields remain available
```

