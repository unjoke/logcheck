## Context

`LogcheckDesktop` already tracks folder-backed source files, selected source paths, standalone paths, analysis history, and export state. Analysis still flows through `analyze_logs(paths, config_path=None)`, which loads a `DetectionConfig` from `logcheck.config`. Current configuration loading is TOML-only, while the UI displays rule details from the default local configuration. The requested workflow is frontend-centered but needs a small rule-loading extension so users can import and inspect structured rule files.

## Goals / Non-Goals

**Goals:**

- Allow a user to select an existing log file from Log Sources and analyze only that file.
- Let overview analysis use the same selected source files from Log Sources.
- Add desktop controls for importing a local JSON rule file and, when supported, a YAML rule file.
- Let the user save or download the active rule configuration from the desktop frontend.
- Keep alert details from overlapping or hiding export controls in the overview.
- Preserve local-only operation.

**Non-Goals:**

- Add remote log sources, URLs, upload endpoints, network monitoring, blocking, exploitation, or domain access.
- Replace the detection engine with a general rule DSL.
- Persist imported rule selections across app restarts.
- Change report exporter formats or parser behavior.
- Require a new runtime dependency if YAML support is not already available.

## Decisions

### Use JSON as the Required Frontend Rule Format

The frontend will accept `.json` rule files as the baseline custom-rule format because Python can parse JSON without extra dependencies and it is easy for users to download, edit, and re-import. YAML files (`.yaml` and `.yml`) may be accepted if a local YAML parser such as PyYAML is installed. If YAML support is unavailable, the UI should report that JSON is supported and YAML needs the optional parser.

The file shape should map directly to `DetectionConfig`:

```json
{
  "keywords": {
    "failed_login": ["failed password", "authentication failure"],
    "suspicious_command": ["curl http", "bash -i"]
  },
  "brute_force": {
    "threshold": 5,
    "window_minutes": 10
  }
}
```

TOML loading can remain for existing CLI compatibility, but the desktop import control should advertise JSON first and YAML second.

### Keep Rule Import as Local UI State

`LogcheckDesktop` should store the imported rule path and active `DetectionConfig`. Running analysis from the desktop passes the selected rule path or config through the existing analysis boundary with minimal changes. The Detection Rules section refreshes from the active config so users can verify which keyword groups and brute-force parameters will be used.

Alternative considered: copy imported rules into a project rules directory. Rejected for this change because temporary persistence expands the storage and cleanup contract. Local session state is enough for user-driven analysis.

### Export the Active Rule Configuration

The frontend should provide a save/download action that writes the current active rule configuration to a user-selected local `.json` path. The exported file should be human-readable and structurally equivalent to the accepted import format. This supports the workflow of reviewing built-in rules, editing them, and importing the edited file later.

### Reuse Source Selection Across Sections

The Log Sources section remains the source of truth for discovered source files and checked/selected paths. The overview should show or consume those same selected paths when starting analysis. If exactly one source file is selected, the analysis should run on that file only. If multiple are selected, the analysis should run on the selected set. If none are selected, the UI should provide a clear empty-state or prompt rather than silently analyzing all files.

Standalone file selection can remain available, but source-file selection should be the preferred path for logs already visible in Log Sources.

### Separate Overview Alert Details and Export Controls

The overview layout should reserve distinct areas for alert details and export controls. At the current minimum window size, the alert details region must not cover, float over, or visually hide the export actions. A simple, testable approach is to place alert details and export controls in separate layout rows or columns with fixed ownership in the Qt layout, avoiding absolute positioning.

## Risks / Trade-offs

- YAML support may not be installed. The design treats YAML as optional and keeps JSON as the reliable path.
- User-supplied rules may be malformed. Import should validate expected object types and show a desktop error without crashing.
- Custom rule names may not exist in `SEVERITY_BY_RULE`. Existing behavior can default unknown keyword rule severity to low unless the config model is later expanded to carry severity.
- Changing overview layout can regress compactness. Tests should verify export controls remain present and reachable, and manual UI verification should check the initial window size.
