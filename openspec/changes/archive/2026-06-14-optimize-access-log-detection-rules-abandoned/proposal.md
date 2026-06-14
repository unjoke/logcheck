## Why

The current access-log SQL injection detection is useful but still too shallow for the middleware example in `samples/access1.log`. That file contains a concentrated CTF-style web attack stream: 2764 parsed access lines, all from `172.17.0.1`, all targeting `/index.php`, all returning HTTP 200, with `python-requests/2.26.0` as the user agent, over the interval `01/Sep/2021:01:37:25 +0000` to `01/Sep/2021:01:46:06 +0000`. URL-decoded requests repeatedly contain `information_schema`, `select table_name`, `substr(`, `database()`, `and if(`, and later `select flag from sqli.flag`, with `substr(...,position,1)` covering 43 character positions.

This shape is stronger than a simple keyword burst. It is a boolean-blind SQL injection enumeration pattern where the repeated request template, decoded SQL markers, source grouping, response-size differences, target path, and representative raw evidence should be preserved as one explainable finding. Without that optimization the tool can either under-explain the attack or produce noisy per-line keyword alerts.

The requested reference project, MaaLogAnalyzer (`MaaXYZ/MaaLogAnalyzer`, cloned and reviewed under `worktmp/MaaLogAnalyzer` at commit `649d420`), does not provide intrusion signatures directly. Its useful lesson is architectural: parse raw lines into structured events, keep raw-line provenance separate, build indexes/statistics over structured events, and project compact evidence for users. Logcheck should adopt that style at a small scale for web access detections while staying local-only and course-friendly.

## What Changes

- Improve access-log parsing so common combined log lines retain method, request path/query, status code, response size, user agent, timestamp, source address, source file, and line number where the existing `Event` model can carry them.
- Refine SQL injection rule matching from a pure indicator burst into a grouped behavior detector for URL-decoded web requests.
- Add detection for boolean-blind SQL injection enumeration traits visible in `access1.log`: repeated source/path, repeated conditional `if(substr(...))` probes, database/table/flag extraction targets, many guessed character positions, and response-size variance.
- Keep generated findings compact and explainable: one behavior finding per source/path attack group with count, severity reason, confidence reason, matched indicators, representative raw evidence, and source context.
- Optimize the example logs and test coverage so `access1.log` acts as a regression fixture for realistic middleware access-log attacks rather than a loose sample.
- Preserve Logcheck's safety boundary: local file analysis only, no domain fetching, no scanning, no exploitation, no active blocking, no external reporting, and no internet-dependent detection.

## Capabilities

### Modified Capabilities

- `intrusion-detection-rules`: Access-log SQL injection detection should identify repeated URL-encoded and decoded web attack behavior with richer grouping, confidence, severity, and evidence.
- `log-ingestion`: Access-log parsing should preserve enough request metadata for behavior rules to group by source, target, status, size, and user agent.
- `course-deliverables`: Example logs and regression tests should demonstrate realistic detection on the supplied middleware access log.

## Impact

- Expected code areas: `logcheck/parsers.py`, `logcheck/models.py`, `logcheck/rules.py`, `logcheck/analysis.py` or serializers only if new metadata needs to surface, and parser/rule/sample tests.
- Expected sample areas: `samples/access1.log` should remain the full realistic fixture; smaller companion examples may be added only if tests or UI demos need faster focused coverage.
- Expected documentation/spec areas: update OpenSpec requirements for access-log parsing and SQL injection behavior findings.
- Non-goals: no remote network capabilities, no large ML dependency, no production SIEM redesign, no full MaaLogAnalyzer port, and no unrelated frontend redesign.
