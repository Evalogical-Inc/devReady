from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from devready import __version__
from devready.baseline import diff, load_baseline
from devready.formats import fix_plan, junit, sarif
from devready.models import Result, Status
from devready.runner import matches, report, run_checks

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_INTERNAL = 0, 1, 2, 3


def _text(results: list[Result]) -> str:
    lines = ["DevReady - Environment Check", ""]
    for r in results:
        lines.append(f"[{r.status.value.upper():<5}] {r.title:<12} {r.summary}")
        if r.status is not Status.PASS and r.suggestion:
            lines.append(f"    {r.suggestion}")
    lines += ["", "No changes were made to your system."]
    return "\n".join(lines)


def _selected(check_id: str, only: list[str], skip: list[str]) -> bool:
    return (not only or matches(check_id, only)) and not matches(check_id, skip)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devready", description=__doc__)
    parser.add_argument("--version", action="version", version=f"devready {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run read-only environment checks")
    check.add_argument("--format", choices=["text", "json", "junit", "sarif"], default="text")
    check.add_argument(
        "--baseline", metavar="FILE", help="saved --format json report; show only what changed"
    )
    fix = sub.add_parser("fix", help="print suggested fixes (never runs them)")
    fix.add_argument("--plan", action="store_true", help="required: list steps without running")
    explain = sub.add_parser("explain", help="explain what a check id means")
    explain.add_argument("check_id")
    sub.add_parser("init", help="print a starter .devready.json (does not write it)")
    sub.add_parser("mcp", help="run as an MCP server over stdio")
    for p in (check, fix):
        p.add_argument("--project", default=".", help="directory whose version pins to compare")
        p.add_argument("--only", action="append", default=[], metavar="ID", help="check id/prefix")
        p.add_argument("--skip", action="append", default=[], metavar="ID", help="check id/prefix")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:  # argparse exits 2 on bad usage, 0 on --help/--version
        return int(e.code or 0)

    if args.command == "mcp":
        from devready.mcp_server import serve

        return serve()

    if args.command == "init":
        from devready.checks.config import TEMPLATE

        print(TEMPLATE)
        return EXIT_OK

    if args.command == "explain":
        from devready.explain import EXPLANATIONS

        text = EXPLANATIONS.get(args.check_id)
        if text is None:
            print(f"devready: unknown check id; known: {', '.join(EXPLANATIONS)}", file=sys.stderr)
            return EXIT_USAGE
        print(text)
        return EXIT_OK

    if args.command == "fix" and not args.plan:
        print(
            "devready: fix only supports --plan (DevReady never changes your system)",
            file=sys.stderr,
        )
        return EXIT_USAGE

    root = Path(args.project)
    if not root.is_dir():
        print(f"devready: not a directory: {args.project}", file=sys.stderr)
        return EXIT_USAGE
    try:
        results = run_checks(root)
    except Exception as e:  # noqa: BLE001 - last-resort guard; never leak raw output
        print(f"devready: internal error ({type(e).__name__})", file=sys.stderr)
        return EXIT_INTERNAL

    results = [r for r in results if _selected(r.check_id, args.only, args.skip)]

    if args.command == "fix":
        print(fix_plan(results))
        return EXIT_OK

    regressed = None
    if args.baseline:
        base = load_baseline(Path(args.baseline))
        if base is None:
            print("devready: baseline is not a readable devready JSON report", file=sys.stderr)
            return EXIT_USAGE
        total = len(results)
        results, regressed = diff(results, base)
        print(f"Compared with baseline: {len(results)} of {total} changed.", file=sys.stderr)
    if args.format == "json":
        print(json.dumps(report(results), indent=2))
    elif args.format in ("junit", "sarif"):
        print(junit(results) if args.format == "junit" else sarif(results))
    else:
        print(_text(results))
    if regressed is not None:  # with a baseline only a new or worse FAIL breaks the build
        return EXIT_FAILED if regressed else EXIT_OK
    return EXIT_FAILED if any(r.status is Status.FAIL for r in results) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
