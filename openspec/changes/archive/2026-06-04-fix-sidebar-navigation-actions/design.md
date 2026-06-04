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
