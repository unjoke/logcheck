## 1. Front-End Structure

- [x] 1.1 Choose the production desktop UI toolkit and document the reason.
- [x] 1.2 Create a desktop UI entry point separate from the existing CLI.
- [x] 1.3 Build the top menu, left navigation, main analysis workspace, findings area, and side details panel.
- [x] 1.4 Apply the black-and-white visual style based on `worktmp/logcheck_desktop_mockup.py`.

## 2. Analysis Workflow

- [x] 2.1 Add local log file selection for one or more files.
- [x] 2.2 Invoke the existing Logcheck analysis pipeline from the UI.
- [x] 2.3 Map analysis results into summary metrics, severity counts, suspicious sources, and finding rows.
- [x] 2.4 Display missing or unreadable file errors without crashing the window.

## 3. Findings and Evidence

- [x] 3.1 Render a finding queue with severity, source, target, rule/explanation, and evidence reference.
- [x] 3.2 Provide a detail area for selected finding evidence and source file context.
- [x] 3.3 Keep the UI readable at the target desktop window size.

## 4. Report Export

- [x] 4.1 Add JSON, CSV, and Markdown export controls.
- [x] 4.2 Reuse the existing exporter behavior for selected output formats.
- [x] 4.3 Show export completion status and output location.

## 5. Safety and Verification

- [x] 5.1 Ensure the UI exposes only local file inputs and local report actions.
- [x] 5.2 Verify that no URL, domain scan, remote upload, blocking, or exploit controls are introduced.
- [x] 5.3 Add focused tests for result-to-UI data mapping where practical.
- [x] 5.4 Run existing unit tests and manually launch the desktop window for screenshot verification.
