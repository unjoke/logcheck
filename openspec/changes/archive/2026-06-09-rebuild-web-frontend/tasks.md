## 1. Direction Selection

- [x] 1.1 Select one web application shape: Local Investigation Dashboard, Log Review Workbench, or Guided Analysis Wizard.
- [x] 1.2 Confirm whether the first version supports uploaded local files, bundled sample logs, or both.

## 2. Web App Foundation

- [x] 2.1 Add a local web frontend entry point and remove or deprecate the GUI entry point.
- [x] 2.2 Add the frontend/server dependencies needed for a browser-based single-page app.
- [x] 2.3 Create the web app structure with a first screen that is the working Logcheck interface.

## 3. Local Analysis Integration

- [x] 3.1 Expose local input handling for uploaded files or approved local samples.
- [x] 3.2 Connect the web workflow to the existing local analysis pipeline.
- [x] 3.3 Render summary, findings, evidence, insights, and source context from analysis results.
- [x] 3.4 Expose local JSON, CSV, and Markdown export states through the web frontend.

## 4. Safety Boundary

- [x] 4.1 Add checks that URL inputs, domain inputs, remote upload controls, scan buttons, blocking controls, exploitation actions, and external reporting controls are absent.
- [x] 4.2 Ensure the web frontend does not depend on external browsing, remote fetching, or internet access for analysis.

## 5. Verification

- [x] 5.1 Replace desktop-focused tests with focused web/API tests.
- [x] 5.2 Run backend parser, rule, analysis, exporter, CLI, and web frontend tests.
- [x] 5.3 Verify the implemented web frontend in a browser at desktop and mobile-width viewports.
- [x] 5.4 Update course deliverable evidence to show web frontend verification instead of desktop verification.
