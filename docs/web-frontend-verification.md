# Web Frontend Verification

Change: rebuild-web-frontend

## Manual Browser Checks

- Local server: started the Flask web frontend on `http://127.0.0.1:8766` because port `8765` was already occupied by an existing local process.
- Desktop viewport: verified at `1280x720`; the dashboard rendered nonblank with Source intake, Analysis summary, Finding queue, Evidence detail, Investigation insights, and Exports visible.
- Mobile-width viewport: verified at `390x844`; the same dashboard regions stacked cleanly without horizontal overflow.
- Local-only controls: no URL, domain, remote upload, network scan, blocking, exploitation, or external reporting controls were visible.
- Source intake: bundled sample log selection was available, and analysis completed with the `auth.log` sample.
- Analysis review: summary metrics, finding queue, evidence source context, insight text, and export controls were visible after analysis.
- Regression check: the insight timeline did not render `undefined`; it used actual timeline fields such as severity, rule id, entity, and source.
- Visual report: verified source/entity, time/evidence-order, and severity charts after analyzing the bundled `incident.log` sample.
- Privilege-escalation evidence: verified findings for sudo/su failure and sensitive/admin path access remain passive and retain local source context.
- Incident sample: verified `samples/incident.log` covers benign baseline, brute-force, invalid-user, unauthorized-access, privilege-escalation, suspicious-command, and multiple source entities.

The in-app browser screenshot API timed out during capture, so verification evidence was recorded through DOM region checks and layout metrics instead.

## Browser Layout Metrics

- Desktop `1280x720`: `scrollWidth` was `1280`; no forbidden terms and no `undefined` text were present.
- Mobile `390x844`: `scrollWidth` was `390`; no forbidden terms and no `undefined` text were present.

## Commands

- `python -m pytest tests/test_webapp.py tests/test_web_serialization.py -q`
- `python -m pytest tests/test_rules.py tests/test_samples.py tests/test_webapp.py tests/test_web_serialization.py -q`
- `node --check logcheck/web_static/app.js`
- `python -m pytest tests -q`
- `openspec validate rebuild-web-frontend --strict`
- `openspec validate add-local-visualization-charts --strict`
- `python -m logcheck.webapp`

## 2026-06-09 Alert Detail Workflow Verification

- Local server: started Logcheck on `http://127.0.0.1:8766` because `8765` was already occupied by another local process.
- Desktop verification: analyzed bundled `incident.log`; the dashboard completed with `27` findings and `12` chart rows.
- Desktop selected-alert verification: the default `keyword.failed_login` alert showed `Selected alert`, source metadata, and the single alert log line `Jun  2 10:01:05 ubuntu sshd[123]: Failed password for invalid user admin from 192.0.2.10 port 51234 ssh2`.
- Desktop click verification: clicking the next finding changed the selected alert to `keyword.invalid_user` and kept the same alert-specific source log detail visible for that finding.
- Desktop layout verification: chart label/track overlap count was `0`; chart grid did not overflow; page-level horizontal overflow was false.
- Insight separation verification: insights rendered as 6 concise summary items including risk and affected entities, not as a duplicated per-alert timeline list.
- Mobile-width verification: at `390x844`, charts stacked vertically, selected alert detail still contained log detail, the detail panel did not overflow, and page-level horizontal overflow was false.
- Commands also run during build verification: `python -m pytest tests/test_webapp.py tests/test_web_serialization.py -q` -> `32 passed`; `python -m pytest -q` -> `82 passed`; `node --check logcheck/web_static/app.js` -> no syntax errors.
