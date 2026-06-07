## Why

The current desktop frontend has grown through incremental screens and now feels more like a collection of panels than a focused investigation tool. Logcheck needs a full frontend reset into a compact local workbench that helps users inspect logs, run rules, review evidence, and export reports without navigating through scattered views.

## What Changes

- Replace the current overview-first desktop layout with an investigation workbench layout:
  - left pane for local log sources and source diagnostics
  - center pane for a readable log viewer with highlighted rule hits
  - right pane for local rule controls and analysis context
  - bottom pane for findings, evidence detail, analysis history, and local exports
- Keep the first screen as the usable analysis workspace rather than a landing, hero, or explanatory page.
- Preserve the local-only safety boundary: local files, local rules, local analysis, and local exports only.
- Remove or de-emphasize duplicated navigation that forces users to jump between pages for one investigation flow.
- Keep the existing parsing, analysis, insight generation, and export behavior as backend logic; this change focuses on frontend composition and interaction ergonomics.

## Capabilities

### New Capabilities

- `investigation-workbench-ui`: Defines the redesigned workbench-style desktop interface, including pane layout, log viewer, finding/evidence workflow, and local-only UI constraints.

### Modified Capabilities

- `desktop-frontend`: Tightens the desktop frontend requirement from a polished multi-section analysis workspace to a cohesive investigation workbench that makes log inspection, rule review, finding detail, and export actions available in one stable surface.

## Impact

- Affected code: primarily `logcheck/desktop.py` and its desktop UI tests in `tests/test_desktop.py`.
- Affected behavior: desktop layout, visual hierarchy, navigation model, source review workflow, finding detail workflow, rule control placement, and export placement.
- Unchanged systems: log parsing, detection rules, insight generation, CLI behavior, export file formats, and local-only security posture.
- Dependencies: no new network services or external reporting dependencies are expected.
