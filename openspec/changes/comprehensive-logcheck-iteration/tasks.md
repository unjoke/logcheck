## 1. Backend Foundations

- [x] 1.1 Add tests for richer event metadata and batch ingestion diagnostics.
- [x] 1.2 Extend parser/event models to preserve diagnostics, parser confidence where available, and mixed-format context.
- [x] 1.3 Add tests for enhanced behavior-pattern rules, severity reasons, confidence reasons, and invalid rule validation.
- [x] 1.4 Implement deterministic enhanced rule patterns and safe local rule validation.

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
