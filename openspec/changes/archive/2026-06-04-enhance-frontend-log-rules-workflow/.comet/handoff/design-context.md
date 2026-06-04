# Comet Design Handoff

- Change: enhance-frontend-log-rules-workflow
- Phase: design
- Mode: compact
- Context hash: c2495d472a22718a6aeac987df1432612b723b462cab9060dea3ffdaaf3aa701

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/enhance-frontend-log-rules-workflow/proposal.md

- Source: openspec/changes/enhance-frontend-log-rules-workflow/proposal.md
- Lines: 1-29
- SHA256: a9d98f4087b8fadfcf66695c8d3f0dfc7b57603ccc3154b58e7c7b17000aae55

```md
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
```

## openspec/changes/enhance-frontend-log-rules-workflow/design.md

- Source: openspec/changes/enhance-frontend-log-rules-workflow/design.md
- Lines: 1-72
- SHA256: f5557996bf1a3fe99288bead0e86e94c2a58515946275f95ea911dfd31fc70fd

```md
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
```

## openspec/changes/enhance-frontend-log-rules-workflow/tasks.md

- Source: openspec/changes/enhance-frontend-log-rules-workflow/tasks.md
- Lines: 1-36
- SHA256: fcb737a464fd62276840afa398108b4432139f83e3d254cadf56c9c2eed2291d

```md
## 1. Rule File Format Tests

- [ ] 1.1 Add tests for loading custom JSON rule files into `DetectionConfig`.
- [ ] 1.2 Add tests for exporting active rules as readable JSON and reloading them.
- [ ] 1.3 Add tests for malformed JSON/YAML rule files preserving the previous active configuration.
- [ ] 1.4 Add YAML loading tests guarded by local parser availability.

## 2. Rule Configuration Implementation

- [ ] 2.1 Extend config loading to dispatch by `.json`, `.yaml`/`.yml`, and existing `.toml`.
- [ ] 2.2 Validate structured rule data before creating `DetectionConfig`.
- [ ] 2.3 Add a helper to serialize a `DetectionConfig` to the frontend JSON rule-file shape.
- [ ] 2.4 Keep default rules and existing TOML behavior backward compatible.

## 3. Desktop Source and Overview Tests

- [ ] 3.1 Add tests for analyzing exactly one selected file from Log Sources.
- [ ] 3.2 Add tests for overview analysis reusing selected Log Sources files.
- [ ] 3.3 Add tests for preventing source-based analysis when no source files are selected.
- [ ] 3.4 Add tests for rule import success, rule import failure, and rule download actions in the desktop UI.

## 4. Desktop Workflow Implementation

- [ ] 4.1 Add Log Sources actions to analyze selected existing source files directly.
- [ ] 4.2 Wire overview analysis path resolution to selected Log Sources files.
- [ ] 4.3 Track imported rule path or active rule config in `LogcheckDesktop`.
- [ ] 4.4 Refresh Detection Rules display after rule import.
- [ ] 4.5 Add a save/download action for the active rule configuration.
- [ ] 4.6 Show clear UI messages for invalid rule files or unavailable YAML support.

## 5. Overview Layout and Verification

- [ ] 5.1 Adjust overview layout so alert details and export controls occupy distinct non-overlapping layout areas.
- [ ] 5.2 Run focused rule and desktop tests.
- [ ] 5.3 Run the full test suite.
- [ ] 5.4 Manually verify the desktop overview at the initial window size.
```

## openspec/changes/enhance-frontend-log-rules-workflow/specs/desktop-frontend/spec.md

- Source: openspec/changes/enhance-frontend-log-rules-workflow/specs/desktop-frontend/spec.md
- Lines: 1-78
- SHA256: e2e01322d640ed6f07ed2c596fe46486e14cd3c23b950368c325435c730e9944

```md
## ADDED Requirements

### Requirement: Analyze selected existing source files from Log Sources
The desktop frontend SHALL allow users to select existing files shown in the Log Sources section and analyze only the selected files.

#### Scenario: Analyze one selected source file
- **WHEN** the user selects exactly one existing file from the configured log source
- **AND** the user starts analysis from Log Sources or Overview
- **THEN** the desktop frontend runs analysis using only that selected file

#### Scenario: Analyze multiple selected source files
- **WHEN** the user selects multiple existing files from the configured log source
- **AND** the user starts analysis from Log Sources or Overview
- **THEN** the desktop frontend runs analysis using only those selected files

#### Scenario: No selected source files
- **WHEN** a log source contains files but no source files are selected for analysis
- **AND** the user starts source-based analysis
- **THEN** the desktop frontend reports that at least one source file must be selected
- **AND** analysis does not run with an unintended file set

### Requirement: Reuse Log Sources selection from Overview
The desktop frontend SHALL let the overview analysis flow use the file selection maintained by Log Sources.

#### Scenario: Overview analyzes selected source file
- **WHEN** the user has selected a source file in Log Sources
- **AND** the user starts analysis from the overview screen
- **THEN** the selected source file is used as the overview analysis input

#### Scenario: Overview reflects source selection
- **WHEN** the user changes selected source files in Log Sources
- **THEN** the overview screen reflects the selected source count or selected source-file summary

### Requirement: Import local rule files from frontend
The desktop frontend SHALL provide a local file control for importing custom detection rule files.

#### Scenario: Import JSON rule file
- **WHEN** the user imports a readable local JSON rule file with valid rule structure
- **THEN** the desktop frontend uses those rules for subsequent analysis
- **AND** the Detection Rules section displays the imported keyword groups and brute-force parameters

#### Scenario: Import YAML rule file when supported
- **WHEN** the user imports a readable local YAML rule file
- **AND** the local runtime supports YAML parsing
- **THEN** the desktop frontend uses those rules for subsequent analysis

#### Scenario: YAML parser unavailable
- **WHEN** the user imports a YAML rule file
- **AND** the local runtime does not support YAML parsing
- **THEN** the desktop frontend reports that JSON is supported and YAML requires optional parser support
- **AND** the active rules remain unchanged

#### Scenario: Reject malformed rule file
- **WHEN** the user imports a malformed or structurally invalid rule file
- **THEN** the desktop frontend reports the rule-file problem without crashing
- **AND** the active rules remain unchanged

### Requirement: Download active rule file
The desktop frontend SHALL allow users to save the active detection rules to a local file for review or editing.

#### Scenario: Save active rules as JSON
- **WHEN** the user chooses to download or save the active rules
- **THEN** the desktop frontend writes a readable local JSON file containing the active keyword groups and brute-force parameters

#### Scenario: Save reports local output
- **WHEN** the active rules are saved successfully
- **THEN** the desktop frontend displays the local output path or completion status

### Requirement: Keep overview alert details from covering export controls
The desktop frontend SHALL lay out overview alert details and export controls so both remain visible and usable.

#### Scenario: Initial overview layout does not overlap
- **WHEN** the desktop window opens at its configured initial or minimum size
- **THEN** the alert details area does not cover or obscure export controls

#### Scenario: Export controls remain reachable after analysis
- **WHEN** analysis completes and alert details are populated
- **THEN** the export controls remain visible and clickable from the overview screen
```

## openspec/changes/enhance-frontend-log-rules-workflow/specs/intrusion-detection-rules/spec.md

- Source: openspec/changes/enhance-frontend-log-rules-workflow/specs/intrusion-detection-rules/spec.md
- Lines: 1-39
- SHA256: 355e25ed397ae5952cde64ef6f8ed743d4ffd2d367db6d039946761f092d468e

```md
## MODIFIED Requirements

### Requirement: Support configurable rules
The system SHALL load detection rules and thresholds from a local configuration file while providing secure defaults when no configuration is supplied.

#### Scenario: Use default rules
- **WHEN** the user runs analysis without a custom rule file
- **THEN** the system applies the default course-demo rule set

#### Scenario: Use custom threshold
- **WHEN** the user supplies a configuration file with a changed brute-force threshold
- **THEN** the system applies that threshold in the repeated-behavior analysis

#### Scenario: Load JSON rule file
- **WHEN** the user supplies a readable local JSON rule file with `keywords` and optional `brute_force` settings
- **THEN** the system loads keyword groups and brute-force parameters from that file
- **AND** subsequent analysis uses the loaded rule configuration

#### Scenario: Load YAML rule file when parser is available
- **WHEN** the user supplies a readable local YAML rule file with `keywords` and optional `brute_force` settings
- **AND** the local runtime has YAML parser support
- **THEN** the system loads keyword groups and brute-force parameters from that file
- **AND** subsequent analysis uses the loaded rule configuration

#### Scenario: Reject invalid structured rule file
- **WHEN** a supplied JSON or YAML rule file is malformed or does not contain the expected structured values
- **THEN** the system rejects the file with a clear error
- **AND** does not silently fall back to a different custom rule set

### Requirement: Export active rule configuration
The system SHALL serialize the active detection rule configuration to a local structured file that users can inspect and edit.

#### Scenario: Export rules as JSON
- **WHEN** the user requests a rule configuration download from the desktop frontend
- **THEN** the system writes the active keyword groups and brute-force parameters as readable JSON

#### Scenario: Exported rules can be re-imported
- **WHEN** the user imports a rule JSON file previously exported by the system
- **THEN** the loaded detection configuration is equivalent to the exported active configuration
```

