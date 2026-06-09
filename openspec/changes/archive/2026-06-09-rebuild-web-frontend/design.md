## Context

Logcheck is currently a Python package with a CLI and a PyQt desktop entry point. The useful backend shape is already local and testable: local paths are parsed into events, detection rules produce findings, insights add investigation context, and exporters write JSON/CSV/Markdown. The frontend reset should keep that backend boundary but replace the GUI surface with a browser-based web application.

The CTF deployment note matters: all domains in the private environment redirect to `192.168.2.1`, so the web frontend must not invite users to enter domains, remote URLs, external upload targets, blocking actions, or network scan targets. The web app is a local operator surface for local files and local reports only.

## Goals / Non-Goals

**Goals:**
- Replace the GUI direction with a web frontend suitable for course demo, screenshots, and repeated local analysis.
- Let the user choose from a small set of web application shapes before implementation.
- Preserve local-only analysis: local log inputs, local rule review/import when supported, local result rendering, and local exports.
- Keep parser/rule/analysis/exporter modules as the backend contract.
- Remove or deprecate GUI-specific dependencies and tests during implementation.

**Non-Goals:**
- No remote target scanning, domain lookup, URL fetching, blocking, exploitation, external reporting, or internet upload.
- No browser authentication or multi-user server design for this iteration.
- No rewrite of the detection engine unless the web layer exposes a missing backend contract.
- No continuation of PyQt layout, navigation, or desktop-only UX assumptions.

## Decisions

### Selected Web Application

Use **Local Investigation Dashboard** for the first implementation.

First screen: source picker, analysis summary, finding queue, evidence detail, insight cards, and export actions. This is the best fit when the project needs a polished security-analysis web page that demonstrates the whole workflow without feeling like a toy demo.

Alternatives considered:
- **Log Review Workbench**
   - First screen: dense log viewer in the center, rule/source controls on the side, findings and evidence in a bottom panel.
   - Best fit when the demo should feel like an analyst IDE for inspecting raw logs line by line.
   - Trade-off: stronger investigation feel, but harder to make visually clean on small screens.
- **Guided Analysis Wizard**
   - First screen: step flow for selecting local logs, running analysis, reviewing highlights, and exporting reports.
   - Best fit when the course demo prioritizes clarity for first-time viewers.
   - Trade-off: easier to understand, but less like a professional security workspace.

### Web Architecture

Use a small local web server plus a browser UI. The server owns file selection/import endpoints, calls the existing `analyze_logs()` pipeline, and returns structured result data. The UI renders state and never performs network analysis itself.

Alternative considered: a static HTML file that shells out manually. This is too limited for file selection, report export, and reliable automated browser verification.

### Local Inputs

Support both uploaded local log files and bundled project sample logs in the first version. Uploaded files support realistic user demonstrations, while sample logs make course screenshots and repeatable verification quick.

Alternative considered: only uploaded files. Rejected because demo setup would be slower and less repeatable. Alternative considered: only sample logs. Rejected because the web app would feel less useful as a real local analysis tool.

### Frontend Scope

Build one focused single-page app rather than a landing page. The first viewport should be the actual working Logcheck interface with local input controls, analysis status, finding review, and export controls visible or one click away.

Alternative considered: a marketing-style product page. This does not serve the course/demo workflow and would hide the useful tool behind explanatory copy.

### Safety Boundary

The UI must explicitly avoid remote-control affordances: no URL/domain fields, remote upload buttons, scan buttons, exploit/block actions, or external reporting controls. Any sample data or demo state must be local to the project.

Alternative considered: adding a URL field for convenience. Rejected because the private CTF routing behavior makes domain-based workflows misleading and risky.

## Risks / Trade-offs

- [Risk] Web UI could accidentally imply remote attack capability -> Mitigation: local-only specs, tests that assert forbidden controls are absent, and manual browser verification.
- [Risk] Replacing GUI tests may leave backend regressions hidden -> Mitigation: keep parser/rule/analysis/exporter/CLI tests and add web-focused tests around rendered workflow and API behavior.
- [Risk] File dialogs differ between browser and desktop GUI expectations -> Mitigation: use browser file upload controls or local sample path selection instead of OS-native GUI dialogs.
- [Risk] Visual scope may sprawl -> Mitigation: keep the first version to the selected Local Investigation Dashboard shape and one single-page workflow.

## Migration Plan

1. Support both uploaded local files and bundled sample logs in the first version.
2. Add the local web server and browser UI structure.
3. Connect the UI to existing local analysis and export behavior.
4. Replace desktop-focused tests with web/API tests and browser visual verification.
5. Remove or deprecate PyQt dependency and desktop script entry point if no longer needed.
6. Rollback by restoring the previous GUI entry point and removing the web entry point if the web direction is abandoned.

## Open Questions

- None for the design phase.
