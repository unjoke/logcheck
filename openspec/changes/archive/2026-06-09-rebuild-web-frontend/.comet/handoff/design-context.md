# Comet Design Handoff

- Change: rebuild-web-frontend
- Phase: design
- Mode: compact
- Context hash: 3f4714114a76d00e9c285965715e26b38900bcd8d82ff7ca680c1964737aab15

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/rebuild-web-frontend/proposal.md

- Source: openspec/changes/rebuild-web-frontend/proposal.md
- Lines: 1-25
- SHA256: 86371b5b003dc1c7589bc71ca05f591dcb431b1977c1bc84605a593690650abe

```md
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
```

## openspec/changes/rebuild-web-frontend/design.md

- Source: openspec/changes/rebuild-web-frontend/design.md
- Lines: 1-82
- SHA256: e00bba601c79eb2f60c3859f5125757b975d7c2eebb3cca39139ff1f5dc547ff

[TRUNCATED]

```md
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
```

Full source: openspec/changes/rebuild-web-frontend/design.md

## openspec/changes/rebuild-web-frontend/tasks.md

- Source: openspec/changes/rebuild-web-frontend/tasks.md
- Lines: 1-29
- SHA256: 8e92f4abc0f7f836f9829021fd1eeba35076e9f14f327c5c66a6d3e01c02294a

```md
## 1. Direction Selection

- [x] 1.1 Select one web application shape: Local Investigation Dashboard, Log Review Workbench, or Guided Analysis Wizard.
- [x] 1.2 Confirm whether the first version supports uploaded local files, bundled sample logs, or both.

## 2. Web App Foundation

- [ ] 2.1 Add a local web frontend entry point and remove or deprecate the GUI entry point.
- [ ] 2.2 Add the frontend/server dependencies needed for a browser-based single-page app.
- [ ] 2.3 Create the web app structure with a first screen that is the working Logcheck interface.

## 3. Local Analysis Integration

- [ ] 3.1 Expose local input handling for uploaded files or approved local samples.
- [ ] 3.2 Connect the web workflow to the existing local analysis pipeline.
- [ ] 3.3 Render summary, findings, evidence, insights, and source context from analysis results.
- [ ] 3.4 Expose local JSON, CSV, and Markdown export states through the web frontend.

## 4. Safety Boundary

- [ ] 4.1 Add checks that URL inputs, domain inputs, remote upload controls, scan buttons, blocking controls, exploitation actions, and external reporting controls are absent.
- [ ] 4.2 Ensure the web frontend does not depend on external browsing, remote fetching, or internet access for analysis.

## 5. Verification

- [ ] 5.1 Replace desktop-focused tests with focused web/API tests.
- [ ] 5.2 Run backend parser, rule, analysis, exporter, CLI, and web frontend tests.
- [ ] 5.3 Verify the implemented web frontend in a browser at desktop and mobile-width viewports.
- [ ] 5.4 Update course deliverable evidence to show web frontend verification instead of desktop verification.
```

## openspec/changes/rebuild-web-frontend/specs/course-deliverables/spec.md

- Source: openspec/changes/rebuild-web-frontend/specs/course-deliverables/spec.md
- Lines: 1-16
- SHA256: 87d7f152094208ccf6ac7dfc2d444eefef0e6876fe6ce839e12c4669748ccf9a

```md
## MODIFIED Requirements

### Requirement: Demonstrate comprehensive local iteration
The project SHALL include evidence that the comprehensive iteration improves frontend polish, backend analysis behavior, reports, and local safety.

#### Scenario: Automated verification evidence
- **WHEN** the project test suite is run
- **THEN** tests cover parser diagnostics, enhanced rules, insight generation, report export, CLI compatibility, and web frontend workflows

#### Scenario: Manual web verification evidence
- **WHEN** the iterated web frontend is reviewed
- **THEN** screenshots or notes show the polished web workspace, multi-source workflow, findings, insights, and export section

#### Scenario: Local-only safety evidence
- **WHEN** the comprehensive iteration is demonstrated
- **THEN** the deliverable evidence shows that no URL, domain, remote upload, network scan, blocking, exploitation, or external reporting controls were added
```

## openspec/changes/rebuild-web-frontend/specs/web-frontend/spec.md

- Source: openspec/changes/rebuild-web-frontend/specs/web-frontend/spec.md
- Lines: 1-56
- SHA256: a8f3bdd0e7d84ff4d88986c5764b9ec9a9fddbb688a7dc8b1e7ab63f7ba72770

```md
## ADDED Requirements

### Requirement: Provide browser-based Logcheck workspace
The system SHALL provide a browser-based Logcheck web application as the primary frontend.

#### Scenario: Open web workspace
- **WHEN** the user opens the Logcheck web frontend
- **THEN** the first screen presents the working analysis interface rather than a landing page or desktop-style GUI shell

#### Scenario: Choose implementation direction
- **WHEN** the web frontend rebuild begins
- **THEN** the implementation direction is selected from Local Investigation Dashboard, Log Review Workbench, or Guided Analysis Wizard

### Requirement: Support local log analysis workflow
The web frontend SHALL let users run Logcheck analysis against local log inputs and review structured local results.

#### Scenario: Analyze local logs
- **WHEN** the user provides local log files or approved local sample logs and starts analysis
- **THEN** the web frontend runs the existing local analysis pipeline and displays summary, findings, evidence, and insights

#### Scenario: Preserve local source context
- **WHEN** findings or insights are displayed
- **THEN** the web frontend shows source context including file, line, raw evidence, actor, target, source address, or parser confidence when available

### Requirement: Export reports from web frontend
The web frontend SHALL expose local report export actions for supported report formats.

#### Scenario: Export latest result
- **WHEN** analysis has completed and the user requests an export
- **THEN** the web frontend writes or downloads a local JSON, CSV, or Markdown report using the existing exporter behavior

#### Scenario: Export before analysis
- **WHEN** the user requests an export before a result exists
- **THEN** the web frontend reports that analysis must run before exporting

### Requirement: Preserve local-only safety boundary
The web frontend MUST remain a local analysis interface and MUST NOT introduce remote target actions.

#### Scenario: Forbidden remote controls absent
- **WHEN** the web frontend is displayed
- **THEN** it does not show URL inputs, domain inputs, remote upload controls, network scan buttons, blocking controls, exploitation actions, or external reporting controls

#### Scenario: CTF redirect environment remains safe
- **WHEN** the project is demonstrated in an environment where domains redirect to `192.168.2.1`
- **THEN** the web frontend workflow does not depend on domain entry, external browsing, or remote fetching

### Requirement: Verify web frontend visually and automatically
The web frontend SHALL be covered by focused automated checks and browser-based visual verification.

#### Scenario: Automated web checks
- **WHEN** the web frontend test suite is run
- **THEN** tests cover local input handling, analysis result rendering, report export states, and absence of forbidden remote controls

#### Scenario: Browser visual verification
- **WHEN** the implemented web frontend is reviewed in a browser
- **THEN** screenshots or notes show that the selected web application shape is readable, non-overlapping, and usable on target desktop and mobile-width viewports
```

