# Comet Design Handoff

- Change: fix-sidebar-navigation-actions
- Phase: design
- Mode: compact
- Context hash: 5d23bc099c7aa836360ed999daad90a7b607848e18ffe6e3b85f3b08ace98b1d

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/fix-sidebar-navigation-actions/proposal.md

- Source: openspec/changes/fix-sidebar-navigation-actions/proposal.md
- Lines: 1-27
- SHA256: 6db500cca0c06240dac0401c69f115005dde00e62710d69347f0fc95b9015e87

```md
## Why

The desktop UI currently renders the left sidebar entries as buttons, but most of them only change visual selection text and do not switch the user to a meaningful workspace or invoke the named function. This makes the red-boxed navigation in the screenshot feel decorative instead of operational.

## What Changes

- Make each sidebar navigation button change the visible main workspace section that matches its label.
- Connect action-oriented sidebar entries to the existing local-only behaviors: log selection and report export.
- Add clear hover/pressed/selected button feedback so sidebar controls feel clickable.
- Preserve the local-only safety boundary; no URL, domain, remote upload, blocking, or exploit controls are added.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-frontend`: Sidebar navigation shall switch visible desktop sections or trigger the matching existing local function, with tactile visual feedback.

## Impact

- Affected code: `logcheck/desktop.py` and focused desktop UI tests.
- Affected specs: `desktop-frontend`.
- Existing CLI behavior, analysis logic, and exporter output formats remain unchanged.
- No new dependency or network behavior is introduced.
```

## openspec/changes/fix-sidebar-navigation-actions/design.md

- Source: openspec/changes/fix-sidebar-navigation-actions/design.md
- Lines: 1-52
- SHA256: 1057d9a69f9e02956e50005d881ea377a97ac125808ab967ec9aecc379dac709

```md
## Context

`LogcheckDesktop` already builds a PyQt6 shell with a left sidebar, overview metrics, findings, details, file selection, analysis, and export actions. The sidebar stores `nav_buttons` and `_select_nav()` currently updates `current_section`, selected styling, and status text, but the central content remains the same for every sidebar label. The result is a button-like surface without meaningful navigation.

## Goals / Non-Goals

**Goals:**

- Keep the existing PyQt6 implementation and visual direction.
- Introduce a lightweight workspace switching model inside `logcheck/desktop.py`.
- Give every sidebar entry a visible result:
  - Overview shows the current analysis dashboard.
  - Log Sources opens the local file selection flow.
  - Detection Rules shows rule-status content.
  - Suspicious Sources shows suspicious-source summary content.
  - Export Report invokes the existing export flow.
  - Course Demo shows demo-oriented local sample guidance.
- Improve hover, pressed, and selected states for sidebar buttons.

**Non-Goals:**

- Redesign the whole desktop UI.
- Add routing, external services, web views, remote targets, or networking.
- Change parser, detection, summary, or exporter behavior.

## Decisions

### Use a QStackedWidget for Workspace Sections

The main area will keep the existing header, action buttons, metric cards, and content layout as the overview section, then place it inside a `QStackedWidget` with additional compact sections for rules, suspicious sources, and course demo. This is the smallest PyQt-native way to make navigation produce real window changes without introducing routing abstractions.

Alternative considered: rebuild the main layout on every click. Rejected because it is more error-prone and would require more widget lifetime management.

### Keep Action Buttons as Local Function Entrypoints

`nav_sources` should call `choose_logs()` and then keep the user on a useful log-source view. `nav_export` should call `export_reports()` so the sidebar button does exactly what it says. Both functions already enforce local-only file dialogs and result availability checks.

Alternative considered: make every sidebar item purely switch views. Rejected because the user specifically called out buttons not triggering named functions, and export/log-source entries already map to existing functions.

### Store Navigation Metadata

Add a small `NAV_ITEMS` data structure that maps each sidebar key to display text and behavior. This prevents six independent lambdas from drifting and makes tests straightforward.

### Use Stylesheet States for Click Feedback

Update the stylesheet with `QPushButton:hover`, `QPushButton:pressed`, `QPushButton#sidebar`, and `QPushButton#primary` rules. Object names will continue to control selected state, while pseudo-states provide tactile feedback.

## Risks / Trade-offs

- More widgets in `desktop.py` -> Keep helper methods small and focused.
- File dialog side effects in tests -> Test action dispatch by patching `choose_logs`/`export_reports`, and test visual switching separately.
- Suspicious-source view may be empty before analysis -> Show a clear local-only empty state and populate it from the latest result after analysis.
```

## openspec/changes/fix-sidebar-navigation-actions/tasks.md

- Source: openspec/changes/fix-sidebar-navigation-actions/tasks.md
- Lines: 1-21
- SHA256: 8f9e49c725ae2d4589ad5a75a295ac8accbe98cf242c833c1db2c82cff197340

```md
## 1. Specification and Design

- [x] 1.1 Create OpenSpec proposal, design, and delta spec for meaningful sidebar navigation actions.
- [x] 1.2 Initialize and advance Comet state through the open/design gates as far as the workflow permits.

## 2. Regression Tests

- [x] 2.1 Add failing desktop tests proving sidebar navigation switches visible content and dispatches local functions.
- [x] 2.2 Run the focused desktop tests and confirm the new regression tests fail before implementation.

## 3. Sidebar Implementation

- [x] 3.1 Add PyQt workspace switching for overview, rules, suspicious sources, and course demo sections.
- [x] 3.2 Connect sidebar log-source and export entries to the existing local file selection and export workflows.
- [x] 3.3 Add hover, pressed, and selected styling for sidebar click feedback.
- [x] 3.4 Refresh sidebar-derived section content after analysis.

## 4. Verification and Delivery

- [ ] 4.1 Run focused desktop tests and the full unit test suite.
- [ ] 4.2 Record verification evidence, archive the OpenSpec change, commit the work, push to `unjoke/logcheck.git`, and create a pull request.
```

## openspec/changes/fix-sidebar-navigation-actions/specs/desktop-frontend/spec.md

- Source: openspec/changes/fix-sidebar-navigation-actions/specs/desktop-frontend/spec.md
- Lines: 1-39
- SHA256: a69f9972fbe903644d0962b75c240234681e1b525eb19b815c091d48eb78a26e

```md
## ADDED Requirements

### Requirement: Sidebar navigation actions are meaningful
The desktop front end SHALL ensure every left sidebar button either switches the visible workspace section to matching content or triggers the existing local function named by the button.

#### Scenario: Switch to overview section
- **WHEN** the user clicks the Overview sidebar button
- **THEN** the main workspace displays the analysis overview section

#### Scenario: Open local log source selection
- **WHEN** the user clicks the Log Sources sidebar button
- **THEN** the desktop UI invokes the local log file selection workflow

#### Scenario: Switch to rule section
- **WHEN** the user clicks the Detection Rules sidebar button
- **THEN** the main workspace displays detection rule status content

#### Scenario: Switch to suspicious source section
- **WHEN** the user clicks the Suspicious Sources sidebar button
- **THEN** the main workspace displays suspicious source content derived from the latest local analysis when available

#### Scenario: Trigger report export
- **WHEN** the user clicks the Export Report sidebar button
- **THEN** the desktop UI invokes the existing local report export workflow

#### Scenario: Switch to course demo section
- **WHEN** the user clicks the Course Demo sidebar button
- **THEN** the main workspace displays local course demonstration content

### Requirement: Sidebar buttons provide click feedback
The desktop front end SHALL provide visible hover, pressed, and selected states for left sidebar buttons.

#### Scenario: Highlight selected sidebar section
- **WHEN** a sidebar section is selected
- **THEN** that button is visually distinguished from unselected sidebar buttons

#### Scenario: Show tactile button state
- **WHEN** the user hovers over or presses a sidebar button
- **THEN** the button appearance changes to communicate that it is clickable
```

