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
