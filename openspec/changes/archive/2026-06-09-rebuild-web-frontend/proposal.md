## Why

The current frontend direction was shaped around a local GUI, but the next iteration needs a browser-based web page that is easier to demo, screenshot, and evolve. The old desktop OpenSpec context has been removed so future work does not keep inheriting GUI assumptions.

## What Changes

- **BREAKING** Replace the desktop GUI frontend direction with a web frontend.
- Introduce a browser-first Logcheck workspace for choosing local log inputs, running local analysis, reviewing findings and insights, and exporting reports.
- Provide a short set of candidate web application shapes before implementation so the final UI direction can be selected deliberately.
- Preserve the safety boundary: no URL/domain target input, remote upload, network scan, blocking, exploitation, external reporting, or internet-dependent analysis behavior.
- Keep the existing parser, rule, insight, exporter, and CLI capabilities as the analysis backend for the web frontend.

## Capabilities

### New Capabilities
- `web-frontend`: Defines the browser-based Logcheck application surface, local-only workflow, candidate app directions, and verification expectations.

### Modified Capabilities
- `course-deliverables`: Course evidence changes from desktop frontend verification to web frontend verification.

## Impact

- Affects frontend implementation structure, project dependencies, application entry points, tests, and manual visual verification.
- Later implementation may remove or deprecate `logcheck/desktop.py`, `tests/test_desktop.py`, the `logcheck-desktop` script entry point, and the PyQt dependency.
- Does not change the analysis model, parser behavior, rule detection contracts, report formats, or CLI behavior unless needed to expose existing data cleanly to the web layer.
