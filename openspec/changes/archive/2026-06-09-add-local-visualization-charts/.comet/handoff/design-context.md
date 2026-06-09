# Comet Design Handoff

- Change: add-local-visualization-charts
- Phase: design
- Mode: compact
- Context hash: 006c3e1ad5fd26c865af524e926c1f26575a97e56515d9fb49793c1f45df0576

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/add-local-visualization-charts/proposal.md

- Source: openspec/changes/add-local-visualization-charts/proposal.md
- Lines: 1-35
- SHA256: e34f2e9a9ac79a89ba7f368b271988c566f3944cf49e7251582d0e63766f284c

```md
# Add Local Visualization Charts

## Why

Course topic 11 explicitly asks for visual reports such as attack source IP statistics and time distribution, and for a rule library that identifies common attack behavior such as brute force and privilege escalation. Logcheck already has local analysis, findings, insights, and export flows, but the course demonstration would be stronger if it renders chart-style summaries, highlights privilege-escalation evidence clearly, and ships a richer incident-style sample log.

## What

- Add local-only chart summaries to the web frontend for:
  - Source IP / entity frequency.
  - Finding time or evidence-order distribution.
  - Severity distribution.
- Strengthen privilege-escalation detection presentation by making sudo, `su`, sensitive-file access, and admin-path access findings easy to identify in findings, insights, charts, and reports.
- Add a richer local sample log that demonstrates normal activity, brute force, invalid users, unauthorized access, privilege escalation attempts, suspicious command execution, and multiple source entities.
- Reuse the existing local analysis API payload and derive chart data in the browser unless a small serialization helper is needed for clarity.
- Keep the implementation dependency-light and offline-safe: no CDN, remote chart libraries, domain inputs, URL fetching, network scans, blocking controls, exploitation actions, or external reporting.
- Add focused automated tests and verification notes so the charts can be cited in the course report and recording.

## Scope

In scope:
- Browser dashboard chart section.
- Privilege-escalation rule/display enhancements that remain passive and local-only.
- A richer bundled local sample log for repeatable coursework screenshots and recording.
- Local chart data derivation from existing findings, summary, and insights.
- Empty-state behavior before analysis and for analyses with no findings.
- Automated checks for chart rendering hooks and local-only safety.
- Documentation or verification notes for course evidence.

Out of scope:
- Real-time monitoring.
- Machine learning detection implementation.
- ELK integration.
- Remote target collection or remote reporting.
- Active response such as account lockout, IP blocking, or firewall updates.
```

## openspec/changes/add-local-visualization-charts/design.md

- Source: openspec/changes/add-local-visualization-charts/design.md
- Lines: 1-66
- SHA256: 36aafd99f88065714b362926d4e7c6d0b224cc57fa6579020d4abf8607014810

```md
# Design

## Overview

The web frontend will gain a compact visualization band inside the existing local investigation workspace. The charts will be rendered from the latest analysis result already returned by `/api/analyze`, keeping all computation and rendering local to the browser and Flask app. The same iteration will also make privilege-escalation evidence more explicit and add a richer incident sample so the course demo exercises the charts and rule library with realistic scenarios.

## Architecture

Use a small, local chart renderer in `logcheck/web_static/app.js` with ordinary DOM/CSS or Canvas primitives. This avoids external chart dependencies and preserves the project safety boundary.

Data flow:

```text
Local log files / samples
  -> Flask /api/analyze
  -> existing AnalysisResult serialization
  -> browser state
  -> chart data aggregation + attack-family labels
  -> source, time, severity charts + privilege-escalation callouts
```

## Chart Behavior

Source chart:
- Prefer `source_address` when present.
- Fall back to `actor`, then `source_file`, then `unknown`.
- Show the top entries with counts and labels.

Time chart:
- Use finding `timestamp` when available.
- Fall back to insight timeline labels or finding source order when timestamps are missing.
- Display a deterministic evidence-order distribution for sample logs that do not include parseable dates.

Severity chart:
- Use `summary.findings_by_severity`.
- Preserve the severity ladder `critical`, `high`, `medium`, `low`.
- Show zero/empty state clearly when no findings exist.

Privilege-escalation display:
- Treat sudo authentication failure, `su` authentication failure, sensitive file access, and admin/root path access as privilege-escalation indicators.
- Surface these findings with a clear rule identifier and explanation, not just a generic keyword match.
- Let charts and insights reveal the privilege-escalation family through labels or finding text without adding active response controls.

Richer sample log:
- Add a bundled local incident sample, for example `samples/incident.log`.
- Include benign baseline activity plus brute force, invalid user, unauthorized access, permission denied, sudo/su failure, sensitive path access, and suspicious command download lines.
- Keep sample addresses in documentation ranges such as `192.0.2.0/24`, `198.51.100.0/24`, or `203.0.113.0/24`.

## UI Placement

Add a "Visual report" region near the analysis summary and investigation insights. It should be visible after analysis and have a quiet empty state before analysis. The layout should stack cleanly on mobile width and avoid nested cards.

Recommended layout: place the visual report in the main column after the analysis summary and before the finding queue. Desktop shows three compact charts side by side; mobile stacks them vertically.

## Safety

Charts are read-only local summaries. They do not add URL/domain inputs, remote fetches, scanning, blocking, exploitation, or external reporting. Any browser fetch targets remain local API paths.

## Testing

- Unit-style frontend checks for chart helper names, labels, local-only fetch targets, and empty-state text.
- Web app tests that the dashboard includes the visual report region and excludes forbidden remote-control terms.
- Rule/parser tests for privilege-escalation indicators and rich sample coverage.
- Sample-analysis tests or fixture checks that `samples/incident.log` produces source, time/evidence-order, severity, brute-force, privilege-escalation, and suspicious-command evidence.
- Existing API/export tests must continue to pass.
- Manual browser verification should record desktop and mobile layout metrics and note the chart section.
```

## openspec/changes/add-local-visualization-charts/tasks.md

- Source: openspec/changes/add-local-visualization-charts/tasks.md
- Lines: 1-11
- SHA256: eacc308fb096da2380b027184cd18628856837a03c5378549e836b3cde380dff

```md
# Tasks

- [ ] Add chart data derivation helpers for source/entity, time/evidence order, and severity distributions.
- [ ] Add the visual report region to the web dashboard markup.
- [ ] Render local charts after analysis and reset them for empty/pre-analysis states.
- [ ] Style the charts responsively for desktop and mobile widths.
- [ ] Add or refine passive privilege-escalation indicators for sudo, su, sensitive-file, and admin/root path access evidence.
- [ ] Add a richer bundled local incident sample log covering benign activity, brute force, invalid user, unauthorized access, privilege escalation attempts, and suspicious command execution.
- [ ] Extend automated tests for chart hooks, local-only safety, and dashboard region presence.
- [ ] Extend rule/sample tests for privilege-escalation findings and rich sample analysis coverage.
- [ ] Update course/frontend verification notes with chart evidence and commands.
```

## openspec/changes/add-local-visualization-charts/specs/web-frontend/spec.md

- Source: openspec/changes/add-local-visualization-charts/specs/web-frontend/spec.md
- Lines: 1-43
- SHA256: 0c9484592315e22279784aff8e276674ff6c10134386710dbf7129f18ccdc5e2

```md
## ADDED Requirements

### Requirement: Show local visual report charts
The web frontend SHALL show local visualization charts derived from the latest Logcheck analysis result.

#### Scenario: Display charts after local analysis
- **WHEN** the user runs analysis against local sample logs or uploaded local log files
- **THEN** the web frontend displays source/entity frequency, time or evidence-order distribution, and severity distribution charts
- **AND** the charts are derived from local analysis results already available to the frontend

#### Scenario: Chart empty states
- **WHEN** no analysis has run or the latest analysis has no findings
- **THEN** the visual report area shows a clear empty state instead of broken or stale charts

#### Scenario: Charts preserve local-only safety
- **WHEN** the visual report area is displayed
- **THEN** it does not introduce URL inputs, domain inputs, remote fetching, network scanning, blocking, exploitation, or external reporting controls

#### Scenario: Charts remain responsive
- **WHEN** the dashboard is viewed on desktop and mobile-width viewports
- **THEN** the chart area remains readable without horizontal overflow or overlapping text

### Requirement: Highlight privilege-escalation evidence in local review
The web frontend SHALL make passive privilege-escalation evidence easy to identify in local analysis results.

#### Scenario: Privilege-escalation indicators appear in findings
- **WHEN** local logs contain sudo failure, su failure, sensitive-file access, or admin/root path access indicators
- **THEN** the analysis result includes findings whose rule identifiers or explanations clearly identify privilege-escalation behavior
- **AND** the evidence remains tied to local source file and line context

#### Scenario: Privilege-escalation remains passive
- **WHEN** privilege-escalation evidence is displayed
- **THEN** the dashboard provides review-oriented evidence and suggestions only
- **AND** it does not perform account changes, blocking, exploitation, remote access, or system modification

### Requirement: Provide richer local incident sample
The project SHALL include a bundled local incident sample suitable for coursework demonstration.

#### Scenario: Incident sample exercises major report sections
- **WHEN** the user analyzes the bundled incident sample
- **THEN** the result includes enough local findings to populate source/entity, time or evidence-order, and severity charts
- **AND** the sample includes brute-force, invalid-user, unauthorized-access, privilege-escalation, suspicious-command, and benign baseline lines

```

