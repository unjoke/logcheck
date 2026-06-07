## MODIFIED Requirements

### Requirement: Present polished analysis workspace
The desktop frontend SHALL present a visually consistent local investigation workbench with clear hierarchy, stable layout, and readable controls.

#### Scenario: Consistent workspace surfaces
- **WHEN** the desktop frontend is displayed
- **THEN** panes, rows, buttons, labels, and scroll areas use consistent spacing, background hierarchy, and borders
- **AND** text rows do not appear as accidental black strips against unrelated gray regions

#### Scenario: Workbench-first analysis actions
- **WHEN** the primary desktop screen is displayed
- **THEN** it focuses on local source status, log inspection, analysis action, rule context, findings, evidence detail, recent history, and local exports in a single workbench surface
- **AND** it does not duplicate export actions across unrelated sections

### Requirement: Preserve local-only safety during frontend iteration
The iterated desktop frontend SHALL remain limited to local files, local rules, local analysis, and local exports.

#### Scenario: No remote controls after redesign
- **WHEN** the redesigned UI is displayed
- **THEN** it does not include URL inputs, domain inputs, remote uploads, network scans, blocking actions, exploitation actions, or external reporting controls

#### Scenario: Workbench actions remain local
- **WHEN** the user imports sources, runs analysis, reviews rules, opens history, or exports reports
- **THEN** the action operates on local files, local rules, in-process analysis results, or local output files only
