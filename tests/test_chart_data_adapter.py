from pathlib import Path


APP_JS = Path("logcheck/web_static/app.js")


def test_chart_dataset_adapter_functions_are_defined():
    source = APP_JS.read_text(encoding="utf-8")

    expected_functions = [
        "function buildChartDatasets(",
        "function buildSourceIpRows(",
        "function buildTimeBucketRows(",
        "function buildRuleRows(",
        "function buildSourceFileRows(",
        "function renderChartFallbackTable(",
    ]

    for function_name in expected_functions:
        assert function_name in source
