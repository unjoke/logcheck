---
change: fix-sidebar-navigation-actions
design-doc: docs/superpowers/specs/2026-06-04-sidebar-navigation-actions-design.md
base-ref: f753048e9343b7f41aba81318bd2012b9746991d
archived-with: 2026-06-04-fix-sidebar-navigation-actions
---

# Sidebar Navigation Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the desktop sidebar buttons switch meaningful sections or trigger the existing local function named by the button.

**Architecture:** Keep the PyQt6 desktop shell in `logcheck/desktop.py`. Add a `QStackedWidget` workspace, section helpers, central sidebar dispatch, and refreshed suspicious-source content.

**Tech Stack:** Python 3.12, PyQt6, `unittest`.

---

### Task 1: Regression Tests

**Files:**
- Modify: `tests/test_desktop.py`

- [x] **Step 1: Write failing tests**

Add tests for section switching, local action dispatch, and suspicious-source refresh.

- [x] **Step 2: Verify tests fail before implementation**

Run:

```bash
python -m unittest tests.test_desktop.DesktopTests.test_sidebar_navigation_buttons_are_clickable tests.test_desktop.DesktopTests.test_sidebar_action_buttons_dispatch_existing_local_functions tests.test_desktop.DesktopTests.test_sidebar_suspicious_sources_section_reflects_latest_analysis -v
```

Expected before implementation: failures/errors for missing `workspace_stack` and missing `choose_logs()` dispatch.

### Task 2: Sidebar Workspace

**Files:**
- Modify: `logcheck/desktop.py`

- [x] **Step 1: Add workspace stack**

Add `QStackedWidget`, `section_widgets`, `NAV_ITEMS`, and section builder methods.

- [x] **Step 2: Route sidebar clicks**

Connect buttons to `_activate_nav()`, call `_select_nav()` for all entries, and dispatch `choose_logs()` / `export_reports()` for action entries.

- [x] **Step 3: Add click feedback**

Extend the PyQt stylesheet with hover, pressed, and selected button states.

### Task 3: Verification

**Files:**
- Modify: `openspec/changes/fix-sidebar-navigation-actions/tasks.md`

- [x] **Step 1: Run focused tests**

Run the three regression tests and confirm they pass.

- [x] **Step 2: Run desktop tests**

Run:

```bash
python -m unittest tests.test_desktop -v
```

Expected: all desktop tests pass.

- [x] **Step 3: Run full test suite**

Run:

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass.
