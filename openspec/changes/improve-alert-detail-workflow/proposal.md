## Why

The current web dashboard shows local findings, charts, and insights, but the review workflow is too compressed: visual report text can overflow, insight content competes with evidence, and clicking a finding does not guarantee enough raw log context for an audit. This change makes the alert review experience clearer and more defensible for coursework demonstration and local incident investigation.

## What Changes

- Separate alert review from general insights so findings can be scanned, selected, and inspected without being buried in the right panel.
- Require selected alerts to show detailed log evidence, such as the single matched log line or other local evidence available for that alert.
- Improve visual report presentation so chart labels and bars remain readable without overlap or accidental horizontal overflow.
- Keep insights as a summary aid, not a replacement for the selected alert's evidence.
- Preserve the local-only safety boundary: no URL/domain inputs, remote fetching, scanning, blocking, exploitation, external reporting, or internet-dependent behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend`: Adds requirements for alert-focused review, selected-alert log detail, clearer visual report layout, and separation between evidence detail and investigation insights.

## Impact

- Affects `logcheck/web_static/app.js`, web CSS/templates, and web/desktop-oriented tests that assert finding selection and detail rendering behavior.
- May require extending frontend result rendering to use existing `Finding.evidence`, `source_file`, `line_number`, actor, target, source address, matched keyword, severity reason, confidence reason, and other local evidence data.
- Does not change parser, detector, exporter, CLI, or any remote/network behavior unless a small local data-shaping change is needed to expose already-computed evidence.
