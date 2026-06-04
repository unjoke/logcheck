---
comet_change: fix-sidebar-navigation-actions
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-04-fix-sidebar-navigation-actions
status: final
---

# Sidebar Navigation Actions Design

## Context

The canonical requirement is in `openspec/changes/fix-sidebar-navigation-actions/specs/desktop-frontend/spec.md`. `LogcheckDesktop` already has PyQt6 sidebar buttons, local log selection, local analysis, and local report export. The bug is that sidebar entries were mostly visual selection controls: they did not change the visible workspace or invoke the named local action.

## Technical Approach

Use a `QStackedWidget` as the main workspace container. The existing dashboard becomes the overview section. Additional lightweight sections cover log sources, rule status, suspicious sources, export information, and course demo content.

Route sidebar clicks through a single `_activate_nav()` method. It first selects the target section, then dispatches action entries:

- `nav_sources` calls `choose_logs()`.
- `nav_export` calls `export_reports()`.
- Other entries switch the stack only.

Keep analysis and exporter logic unchanged. The suspicious-source section reads from `summarize_result()` output when `_render_result()` refreshes the UI.

## Risks and Mitigations

- File dialogs are awkward in automated tests. Tests patch `choose_logs()` and `export_reports()` to verify dispatch without opening dialogs.
- Extra section widgets could clutter `desktop.py`. Helper methods stay small and reuse `_simple_section()`.
- UI safety boundaries must remain intact. New sections contain only local file, rule, suspicious-source, export, and demo information; no URL or remote target controls are added.

## Test Strategy

- Add regression tests that fail before implementation:
  - sidebar section clicks switch `workspace_stack.currentWidget()`
  - log-source and export sidebar entries dispatch existing local functions
  - suspicious-source section reflects latest analysis summary
- Run focused desktop tests, then the full unittest suite.
