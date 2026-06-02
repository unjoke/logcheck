from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import sys

from .config import load_config
from .exporters import export_csv, export_json, export_markdown
from .models import AnalysisResult
from .parsers import parse_files
from .rules import detect_findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze local logs for intrusion indicators.")
    parser.add_argument("logs", nargs="+", help="Local log files to analyze")
    parser.add_argument("--config", type=Path, help="Optional TOML rule configuration")
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
    severities = Counter(finding.severity for finding in result.findings)
    sources = Counter(finding.source_address or "unknown" for finding in result.findings)
    print("Logcheck analysis summary")
    print(f"Events: {len(result.events)}")
    print(f"Findings: {len(result.findings)}")
    print(f"Severity counts: {dict(severities)}")
    print(f"Top suspicious sources: {sources.most_common(5)}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = [Path(log) for log in args.logs]
    try:
        config = load_config(args.config)
        events = parse_files(paths)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read input: {exc}", file=sys.stderr)
        return 2

    result = AnalysisResult(events=events, findings=detect_findings(events, config))
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
