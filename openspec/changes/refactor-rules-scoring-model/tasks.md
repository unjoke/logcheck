## 1. Data Models

- [x] 1.1 Add new Finding fields (score, confidence, rule_tier, indicator_ids)
- [x] 1.2 Add internal pipeline types (IndicatorMatch, PatternResult, CorrelationResult, rule types)
- [x] 1.3 Verify backward compatibility with pytest
- [x] 1.4 Commit changes

## 2. Rule Configuration Loader

- [x] 2.1 Write tests for rule config loader (test_rule_config.py)
- [x] 2.2 Implement config.py loader
- [x] 2.3 Run tests and verify they pass
- [x] 2.4 Commit the changes

## 3. Default Rules TOML

- [x] 3.1 Create default_rules.toml with indicator, pattern, correlation, and severity_thresholds
- [x] 3.2 Verify the TOML is valid and loadable by config.py
- [x] 3.3 Commit the changes

## 4. Scoring Engine Core

- [x] 4.1 Create tests/test_scoring_engine.py
- [x] 4.2 Rewrite logcheck/rules.py with three-tier scoring engine (compiler + scanner + detector + correlator)
- [x] 4.3 Run scoring engine tests and verify they pass
- [x] 4.4 Run full test suite and verify non-rules tests still pass
- [x] 4.5 Commit the changes

## 5. Pipeline Integration

- [x] 5.1 Update analysis.py to use new pipeline API
- [x] 5.2 Update cli.py --rules argument and analyze_logs call
- [x] 5.3 Update webapp.py analyze_logs call signature
- [x] 5.4 Smoke test and commit

## 6. Update Downstream Modules

- [x] 6.1 Update insights.py for new scoring-aware insights
- [x] 6.2 Update exporters.py (JSON/CSV/Markdown) for new Finding fields
- [x] 6.3 Update web_serialization.py for new Finding fields
- [x] 6.4 Update frontend (app.js, styles.css, index.html) for score display

## 7. Test Updates

- [x] 7.1 Fix test_analysis.py, test_cli.py, test_webapp.py
- [x] 7.2 Fix test_samples.py
- [x] 7.3 Fix test_exporters.py, test_web_serialization.py, test_insights.py
- [x] 7.4 Fix test_rule_config.py
- [x] 7.5 Fix test_rules.py - complete rewrite for scoring model API
- [x] 7.6 Final verification - run full test suite
- [x] 7.7 Commit changes

## 8. Cleanup and Documentation

- [x] 8.1 Update README.md with scoring model documentation
- [x] 8.2 Update pyproject.toml with default_rules.toml in package data
- [x] 8.3 Create and finalize tasks.md
- [x] 8.4 Final full test run
- [x] 8.5 Smoke test on sample files
- [x] 8.6 Commit final cleanup
