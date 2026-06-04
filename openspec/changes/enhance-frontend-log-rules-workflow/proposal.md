## Why

The desktop frontend is close to a practical local log-analysis workflow, but several user-facing gaps remain. Users should be able to pick an existing log file from the Log Sources area and analyze only that file, choose the same log source from the overview screen, import updated detection rules without editing Python code, and download the active rule file from the frontend for review. The overview also needs layout protection so the alert details panel does not cover export controls.

## What Changes

- Let Log Sources support selecting one or more existing source files and running a single-file or selected-file analysis from that section.
- Let the overview analysis input reuse the file choices exposed by Log Sources so users do not have to reselect paths through separate controls.
- Add frontend controls for importing a local detection rule file, with JSON as the required structured format and YAML support when the local runtime has a YAML parser available.
- Let users download or save the currently active rule configuration from the frontend for inspection and editing.
- Update overview layout so alert details and export controls remain separately visible and usable at the initial window size.
- Preserve the local-only safety boundary: no domain access, URL input, remote upload, network scanning, blocking, exploitation, or remote reporting.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-frontend`: Extend log-source and overview workflows for selected existing log files, rule import/export controls, and non-overlapping alert/export layout.
- `intrusion-detection-rules`: Extend configurable rules from TOML-only loading to structured JSON and optional YAML files that users can import from the desktop frontend.

## Impact

- Affected code: `logcheck/desktop.py`, `logcheck/config.py`, detection-rule tests, and focused desktop tests.
- Existing parser, analysis, finding, and report exporter behavior should remain stable.
- Existing TOML config support can remain for CLI/backward compatibility; JSON is the primary frontend rule-file format, with YAML accepted when available.
