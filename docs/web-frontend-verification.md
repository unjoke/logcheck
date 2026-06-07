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

The in-app browser screenshot API timed out during capture, so verification evidence was recorded through DOM region checks and layout metrics instead.

## Browser Layout Metrics

- Desktop `1280x720`: `scrollWidth` was `1280`; no forbidden terms and no `undefined` text were present.
- Mobile `390x844`: `scrollWidth` was `390`; no forbidden terms and no `undefined` text were present.

## Commands

- `python -m pytest tests/test_webapp.py tests/test_web_serialization.py -q`
- `node --check logcheck/web_static/app.js`
- `python -m pytest tests -q`
- `openspec validate rebuild-web-frontend --strict`
- `python -m logcheck.webapp`
