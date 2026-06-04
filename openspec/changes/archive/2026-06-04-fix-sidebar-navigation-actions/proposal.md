## Why

The desktop UI currently renders the left sidebar entries as buttons, but most of them only change visual selection text and do not switch the user to a meaningful workspace or invoke the named function. This makes the red-boxed navigation in the screenshot feel decorative instead of operational.

## What Changes

- Make each sidebar navigation button change the visible main workspace section that matches its label.
- Connect action-oriented sidebar entries to the existing local-only behaviors: log selection and report export.
- Add clear hover/pressed/selected button feedback so sidebar controls feel clickable.
- Preserve the local-only safety boundary; no URL, domain, remote upload, blocking, or exploit controls are added.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-frontend`: Sidebar navigation shall switch visible desktop sections or trigger the matching existing local function, with tactile visual feedback.

## Impact

- Affected code: `logcheck/desktop.py` and focused desktop UI tests.
- Affected specs: `desktop-frontend`.
- Existing CLI behavior, analysis logic, and exporter output formats remain unchanged.
- No new dependency or network behavior is introduced.
