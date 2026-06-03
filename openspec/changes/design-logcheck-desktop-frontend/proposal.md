## Why

Logcheck already works as a local command-line log intrusion detector, but a course demo and report screenshots need a more intuitive software front end. A desktop black-and-white window, similar in tone to the Codex interface reference, can make the analysis flow easier to present without changing the tool's local-only security posture.

## What Changes

- Add a desktop front-end capability for Logcheck analysis.
- Present a black-and-white application window with a top menu, left navigation, overview metrics, alert queue, log-source panel, rule status, and report export actions.
- Use `worktmp/logcheck_desktop_mockup.py` as the current visual reference for layout direction.
- Connect the future front end to the existing local log analysis pipeline and exported JSON/CSV/Markdown report outputs.
- Keep the interface focused on local files and local analysis; it SHALL NOT introduce network scanning, remote reporting, or domain access.

## Capabilities

### New Capabilities

- `desktop-frontend`: Defines the desktop Logcheck interface, visual structure, analysis workflow, and local-only UI constraints.

### Modified Capabilities

- None.

## Impact

- Affected areas: future desktop UI code, local analysis invocation, output display, and report export workflow.
- Existing CLI behavior and exported file formats remain intact.
- No new network capability is introduced.
- The temporary mockup file in `worktmp/logcheck_desktop_mockup.py` remains a design reference rather than production implementation.
