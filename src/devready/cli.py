from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from devready import __version__
from devready.models import Result, Status
from devready.runner import report, run_checks

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_INTERNAL = 0, 1, 2, 3


def _text(results: list[Result]) -> str:
    lines = ["DevReady - Environment Check", ""]
    lines += [f"[{r.status.value.upper():<5}] {r.title:<12} {r.summary}" for r in results]
    lines += ["", "No changes were made to your system."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devready", description=__doc__)
    parser.add_argument("--version", action="version", version=f"devready {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run read-only environment checks")
    check.add_argument("--format", choices=["text", "json"], default="text")
    sub.add_parser("mcp", help="run as an MCP server over stdio")
    check.add_argument("--project", default=".", help="directory whose version pins to compare")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:  # argparse exits 2 on bad usage, 0 on --help/--version
        return int(e.code or 0)

    if args.command == "mcp":
        from devready.mcp_server import serve

        return serve()

    root = Path(args.project)
    if not root.is_dir():
        print(f"devready: not a directory: {args.project}", file=sys.stderr)
        return EXIT_USAGE
    try:
        results = run_checks(root)
    except Exception as e:  # noqa: BLE001 - last-resort guard; never leak raw output
        print(f"devready: internal error ({type(e).__name__})", file=sys.stderr)
        return EXIT_INTERNAL

    if args.format == "json":
        print(json.dumps(report(results), indent=2))
    else:
        print(_text(results))
    return EXIT_FAILED if any(r.status is Status.FAIL for r in results) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
