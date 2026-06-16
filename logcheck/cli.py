from __future__ import annotations

from pathlib import Path
import argparse
import sys

from .analysis import analyze_logs, summarize_result
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze local logs for intrusion indicators.")
    parser.add_argument("logs", nargs="+", help="Local log files to analyze")
    parser.add_argument("--rules", type=Path, default=None, help="Path to a TOML/JSON/YAML rules file")
    parser.add_argument("--out-dir", type=Path, default=Path("outputs"), help="Directory for exported reports")
    parser.add_argument(
        "--format",
        action="append",
        choices=["json", "csv", "markdown"],
        default=[],
        help="Export format; can be repeated",
    )
    return parser


def _print_summary(result: AnalysisResult) -> None:
    summary = summarize_result(result)
    print("Logcheck analysis summary")
    print(f"Events: {summary.total_events}")
    print(f"Findings: {summary.total_findings}")
    print(f"Severity counts: {summary.findings_by_severity}")
    print(f"Top suspicious sources: {summary.top_suspicious_sources}")
    if result.insights is not None:
        print(f"Insight: {result.insights.headline}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = [Path(log) for log in args.logs]
    try:
        result = analyze_logs(paths, rules_path=args.rules)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2

    _print_summary(result)

    formats = args.format or ["json", "markdown"]
    if "json" in formats:
        export_json(result, args.out_dir / "analysis.json")
    if "csv" in formats:
        export_csv(result, args.out_dir / "analysis.csv")
    if "markdown" in formats:
        export_markdown(result, args.out_dir / "analysis.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
