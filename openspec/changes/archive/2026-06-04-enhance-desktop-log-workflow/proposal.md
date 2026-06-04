## Why

The desktop UI needs to support a more realistic local analysis workflow: users often keep logs in folders, want to analyze only selected files, need visible rule details, and may export an earlier analysis result rather than only the latest one. The current course-demo entry is no longer useful and should be removed from the production navigation.

## What Changes

- Add folder-based log sources; by default, a chosen folder contributes all regular files directly under that folder.
- Allow analysis from either selected files in the configured log source or standalone files chosen from the computer.
- Remove the unused Course Demo navigation section from the desktop UI.
- Render detection rule details in the desktop frontend instead of only showing high-level rule labels.
- Keep multiple local analysis runs in a timestamped in-memory history for the session.
- Let report export choose which timestamped analysis run to export.
- Preserve the local-only safety boundary: no URL inputs, remote uploads, domain access, scanning, blocking, exploitation, or network reporting.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-frontend`: Extend the desktop workflow for folder log sources, selectable source files, standalone local file analysis, timestamped report export history, detection rule presentation, and removal of the course demo navigation entry.

## Impact

- Affected code: `logcheck/desktop.py`, focused desktop tests, and possibly small helper functions for UI data mapping.
- Existing CLI analysis, parser, rule engine, and exporter formats remain unchanged.
- The frontend remains a local desktop app with local file dialogs only.
