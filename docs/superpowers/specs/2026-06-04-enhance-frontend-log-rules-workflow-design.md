---
comet_change: enhance-frontend-log-rules-workflow
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-04-enhance-frontend-log-rules-workflow
status: final
---

# Enhance Frontend Log Rules Workflow Design

## Goal

Improve the local desktop workflow so users can analyze selected existing log-source files, reuse that selection from the overview, import structured local rule files, download active rules, and keep overview alert details from covering export controls.

## Architecture

The change stays inside the current PyQt6 desktop application and local rule configuration layer. `LogcheckDesktop` remains responsible for UI state, local file dialogs, source-file selection, active rule selection, and dispatching analysis. `logcheck.config` becomes responsible for parsing and validating structured rule files and serializing `DetectionConfig` back to JSON.

No network behavior is introduced. All inputs are local files or folders, and all outputs are local files.

## Data Flow

### Source file analysis

1. The user selects a folder in Log Sources.
2. The UI discovers direct regular files and renders one checkbox per source file.
3. Checkbox changes update `selected_source_paths`.
4. Starting analysis from Log Sources or Overview resolves paths in this priority:
   - selected source files
   - standalone files chosen through the existing file picker
5. If source-based analysis is requested with no selected source files, the UI reports the selection problem and does not analyze unintended files.
6. `analyze_logs(paths, config_path)` runs the existing parser and detection pipeline.

### Rule import and display

1. The user chooses a local `.json`, `.yaml`, or `.yml` rule file from the Detection Rules section.
2. `load_config(path)` dispatches by suffix:
   - `.json` uses Python `json`
   - `.yaml` and `.yml` use an optional YAML parser if available
   - `.toml` keeps existing `tomllib` compatibility
3. Parsed data is validated before creating `DetectionConfig`.
4. On success, the desktop stores the active rule path/config and refreshes the rule display.
5. On failure, the previous active config remains unchanged and the UI shows a clear local error message.

### Rule download

1. The user chooses a local output path for the active rules.
2. The desktop writes a readable JSON object with `keywords` and `brute_force`.
3. The resulting JSON can be imported again and produce an equivalent `DetectionConfig`.

## File Responsibilities

- `logcheck/config.py`: parse TOML/JSON/optional YAML rule files, validate structured config data, and serialize `DetectionConfig` to JSON-compatible data.
- `logcheck/desktop.py`: add rule import/save actions, active rule state, selected source analysis actions, overview source-summary updates, and non-overlapping overview layout.
- `tests/test_rules.py`: cover JSON/YAML config parsing, validation failures, and rule serialization.
- `tests/test_desktop.py`: cover desktop source selection, overview reuse, rule import/save behavior, and error handling.

## Rule Format

JSON is the required frontend rule format:

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

`keywords` must be an object whose keys are rule names and whose values are string arrays. `brute_force` is optional; missing threshold/window values fall back to defaults. Unknown keyword rule names are accepted and use existing severity fallback behavior.

## UI Design

The Detection Rules section should include compact controls for:

- importing a local rule file
- saving/downloading the active rules
- showing active source: default rules or selected rule filename
- listing keyword groups and brute-force parameters from the active config

The Log Sources section should include an analyze action for checked source files. The overview should show a concise source-selection summary and use the same selected paths when analysis starts.

The overview layout should avoid floating or absolute-positioned alert details. Alert details and export controls should occupy separate Qt layout containers so export remains reachable at the configured minimum size and after analysis results populate the page.

## Error Handling

- Missing or unreadable rule file: show a desktop error and keep the previous active rules.
- Invalid JSON/YAML: show a parse error and keep the previous active rules.
- Structurally invalid rule data: show a validation error and keep the previous active rules.
- YAML parser unavailable: show that JSON is supported and YAML needs optional parser support.
- No selected source files: show a source-selection message and do not analyze an accidental fallback set.

## Testing Strategy

Use TDD for each behavior:

1. Add config tests for JSON loading and rule serialization, watch them fail, then implement config helpers.
2. Add guarded YAML tests. If YAML support exists, verify loading; otherwise verify the unavailable-parser error path.
3. Add invalid rule-file tests that confirm failures do not replace active desktop config.
4. Add desktop tests for single selected source analysis, overview source reuse, and no-selection prevention.
5. Add desktop tests for import/save actions by patching file dialogs and message display helpers.
6. Run focused tests, then the full test suite.

Manual verification should open the desktop frontend and check that overview alert details do not cover export controls at the initial window size.

## Risks

- YAML availability varies by environment, so JSON must stay the dependable path.
- `logcheck/desktop.py` is already a broad UI file; changes should use small helpers to keep path resolution, rule import, and rule rendering understandable.
- Custom user rule names currently inherit severity fallback behavior. Expanding custom severities would be a separate capability.
