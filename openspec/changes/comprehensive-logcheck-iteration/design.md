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
