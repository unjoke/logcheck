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
