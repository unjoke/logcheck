## Why

The web export workflow is currently reported as unusable, which breaks the coursework/demo path for saving JSON, CSV, and Markdown reports after local analysis. At the same time, the existing detector is still mostly keyword and simple correlation based; recent open-source log detection work shows a practical path toward stronger detection by adding structured template extraction, frequency/sequence anomalies, and clearer rule provenance while preserving Logcheck's local-only safety boundary.

## What Changes

- Fix the web report export flow so JSON, CSV, and Markdown downloads work reliably after the latest local analysis result.
- Add regression coverage for export API and frontend export states, including missing analysis id, stale/unknown analysis id, unsupported formats, and successful downloads.
- Improve detection logic using lightweight lessons from modern open-source log analytics projects:
  - parse or normalize repeated log message templates before matching where feasible;
  - add configurable behavior rules for template frequency, repeated sequences, and rare suspicious combinations;
  - preserve clear evidence, severity reasons, confidence reasons, and source provenance for every new finding.
- Document the research basis and keep the implementation suitable for a small local course project rather than introducing heavyweight model training.
- Preserve the local-only safety boundary: no URL/domain inputs, remote fetching, scanning, blocking, exploitation, external reporting, internet-dependent detection, or automatic changes to host systems.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `report-export`: Web export behavior must reliably return downloadable local reports for the selected analysis run and report actionable errors when export cannot proceed.
- `intrusion-detection-rules`: Detection rules must support explainable local behavior/template signals inspired by current log anomaly detection practice, without requiring remote services or model training.
- `web-frontend`: Export controls must reflect analysis/export state and remain local-only while invoking the fixed export endpoint.

## Impact

- Affects `logcheck/webapp.py`, `logcheck/web_static/app.js`, frontend styling if export state messaging needs adjustment, and tests covering web API/export behavior.
- May affect `logcheck/rules.py`, `logcheck/config.py`, `logcheck/models.py`, `logcheck/parsers.py`, `logcheck/analysis.py`, and related tests if lightweight template/behavior detection requires new fields or configuration.
- Does not add network dependencies, domain inputs, active response features, exploitation logic, blocking controls, or external reporting.
