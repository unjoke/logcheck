## 1. Layout Contract And Tests

- [x] 1.1 Add or update desktop tests that assert the first screen exposes the workbench regions: local sources, log viewer, rule/context panel, and findings/evidence/history area.
- [x] 1.2 Add desktop tests that assert remote controls are absent, including URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, and external reporting controls.
- [x] 1.3 Add tests for source diagnostics remaining visible while readable files stay analyzable.
- [x] 1.4 Add tests for finding selection driving evidence detail in the workbench output area.

## 2. Workbench Shell

- [x] 2.1 Replace the current primary desktop shell composition with a workbench layout using stable left, center, right, and bottom regions.
- [x] 2.2 Move source selection, selected source state, and source diagnostics into the left source region.
- [x] 2.3 Add the central log viewer surface with stable row styling, empty state, and room for highlighted finding rows.
- [x] 2.4 Move local rule status, rule file state, and local threshold/context controls into the right region.
- [x] 2.5 Move findings, selected evidence detail, analysis history, and local export actions into the bottom output region.

## 3. Interaction Wiring

- [x] 3.1 Wire existing import-folder and import-file actions into the workbench source region.
- [x] 3.2 Wire existing analysis execution into the workbench top or source-adjacent action area.
- [x] 3.3 Refresh source counts, diagnostics, log viewer rows, findings, insights, history, and export availability after analysis completes.
- [x] 3.4 Link finding selection to highlighted log evidence and detail content where parsed event data is available.
- [x] 3.5 Preserve existing JSON, CSV, and Markdown export behavior from the new bottom output region.

## 4. Visual Polish And Responsiveness

- [x] 4.1 Update the stylesheet for a restrained investigation-tool look with readable contrast, consistent borders, and compact controls.
- [x] 4.2 Ensure monospaced log rows, severity indicators, buttons, labels, and scroll areas do not overlap or resize unpredictably.
- [x] 4.3 Define minimum dimensions or collapse behavior so the center log viewer remains usable on smaller windows.
- [x] 4.4 Remove duplicated or obsolete section controls that conflict with the workbench-first flow.

## 5. Verification

- [x] 5.1 Run the desktop-focused tests and fix regressions.
- [ ] 5.2 Run the full test suite.
- [ ] 5.3 Launch the desktop app and visually verify the workbench layout, source flow, analysis flow, finding detail, local exports, and absence of remote controls.
- [ ] 5.4 Update README or course-facing documentation only if the user workflow changes enough to make current instructions misleading.
