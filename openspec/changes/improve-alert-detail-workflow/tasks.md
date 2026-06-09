## 1. Tests

- [x] 1.1 Add or update frontend tests for selecting a finding and rendering its detailed evidence, metadata, and selected state.
- [x] 1.2 Add a regression test that a new analysis with no findings clears stale selected-alert detail.
- [ ] 1.3 Add a test or browser verification note for long evidence/log paths staying inside the detail panel without page-level horizontal overflow.
- [ ] 1.4 Add a test or browser verification note for visual report labels not overlapping adjacent chart groups.

## 2. Data Flow

- [ ] 2.1 Audit the current analysis result payload for fields needed by the selected-alert detail view.
- [ ] 2.2 If existing evidence is insufficient, add a minimal local-only detail representation for the matched log line or other alert-specific evidence without changing detection semantics.
- [ ] 2.3 Ensure serialized finding data omits empty optional detail fields from the rendered UI while preserving existing export behavior.

## 3. Frontend Rendering

- [ ] 3.1 Refactor finding list rendering into an explicit alert review list with clear selected state and source metadata.
- [x] 3.2 Refactor selected-alert detail rendering into structured sections for summary, evidence, reasons, and optional supporting detail.
- [x] 3.3 Refactor investigation insights so they stay concise and separate from selected-alert evidence.
- [ ] 3.4 Adjust visual report chart layout constraints to prevent label/bar overlap and page-level horizontal scrolling.
- [x] 3.5 Verify empty states for no analysis, no findings, and findings without optional metadata.

## 4. Verification

- [ ] 4.1 Run the automated test suite covering models, rules, insights, exports, and web rendering.
- [ ] 4.2 Run the web dashboard locally and capture desktop verification that selected alerts show detailed log evidence.
- [ ] 4.3 Capture mobile-width verification that charts and alert detail remain readable without incoherent overlap.
