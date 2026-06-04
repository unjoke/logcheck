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
