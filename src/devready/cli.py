from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
from collections import Counter
from pathlib import Path

from devready import __version__
from devready.baseline import diff, load_baseline
from devready.formats import fix_plan, junit, sarif
from devready.models import Result, Status
from devready.runner import matches, report, run_checks

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_INTERNAL = 0, 1, 2, 3


EXIT_CODES = """exit codes (check):
  0  no blocking failures
  1  a project requirement is not met
  2  invalid usage
  3  internal error"""


_COLORS = {
    Status.PASS: "32",
    Status.WARN: "33",
    Status.FAIL: "1;31",
    Status.SKIP: "2",
    Status.ERROR: "35",
}
_TAG = 8  # len("[WARN ] ")


def _use_color(stream=None, env=None) -> bool:
    stream, env = stream or sys.stdout, os.environ if env is None else env
    if env.get("NO_COLOR") or env.get("TERM") == "dumb" or not stream.isatty():
        return False
    if sys.platform != "win32":
        return True
    try:  # Windows 10+ consoles need ANSI escapes switched on
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle, mode = kernel32.GetStdHandle(-11), ctypes.c_uint32()
        return bool(
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            and kernel32.SetConsoleMode(handle, mode.value | 4)
        )
    except (AttributeError, OSError):
        return False


def _width(stream=None) -> int:
    stream = stream or sys.stdout
    return max(shutil.get_terminal_size().columns, 40) if stream.isatty() else 80


def _sarif_base(project: str) -> str:
    # SARIF uris resolve against the repository root, which is the working directory in CI
    try:
        rel = Path(project).resolve().relative_to(Path.cwd().resolve())
    except ValueError:  # project outside the working directory: keep project-relative uris
        return ""
    return "" if rel == Path(".") else rel.as_posix()


def _tally(results: list[Result]) -> str:
    n = Counter(r.status for r in results)
    parts = [
        f"{n[Status.PASS]} passed",
        f"{n[Status.WARN]} warning{'s' * (n[Status.WARN] != 1)}",
        f"{n[Status.FAIL]} failed",
    ]
    if n[Status.SKIP]:
        parts.append(f"{n[Status.SKIP]} skipped")
    if n[Status.ERROR]:
        parts.append(f"{n[Status.ERROR]} error{'s' * (n[Status.ERROR] != 1)}")
    return ", ".join(parts)


def _text(results: list[Result], quiet: bool = False, width: int = 80, color: bool = False) -> str:
    shown = [r for r in results if not (quiet and r.status is Status.PASS)]
    col = max((len(r.title) for r in shown), default=0)
    indent = _TAG + col + 1
    narrow = width - indent < 30  # too little room beside the title: summary goes on its own lines

    def wrap(text: str, first: int, rest: int) -> list[str]:
        return textwrap.wrap(
            text,
            width,
            initial_indent=" " * first,
            subsequent_indent=" " * rest,
            break_on_hyphens=False,
        )

    lines = ["DevReady - Environment Check", ""]
    for r in shown:
        tag = f"[{r.status.value.upper():<5}]"
        if color:
            tag = f"\033[{_COLORS[r.status]}m{tag}\033[0m"
        if narrow:
            body = _TAG
            lines += [f"{tag} {r.title}", *wrap(r.summary, body, body)]
        else:
            body = indent
            summary = wrap(r.summary, body, body) or [""]
            lines += [f"{tag} {r.title:<{col}} {summary[0].lstrip()}".rstrip(), *summary[1:]]
        if r.status is not Status.PASS and r.suggestion:
            lines += wrap(f"-> {r.suggestion}", body, body + 3)
    lines += ["", _tally(results), "No changes were made to your system."]
    return "\n".join(lines)


def _selected(check_id: str, only: list[str], skip: list[str]) -> bool:
    return (not only or matches(check_id, only)) and not matches(check_id, skip)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="devready",
        description=__doc__,
        epilog=EXIT_CODES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"devready {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser(
        "check",
        help="run read-only environment checks",
        epilog=EXIT_CODES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check.add_argument("--format", choices=["text", "json", "junit", "sarif"], default="text")
    check.add_argument(
        "--baseline", metavar="FILE", help="saved --format json report; show only what changed"
    )
    check.add_argument(
        "--quiet", action="store_true", help="text format: show only non-pass results"
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
        print(
            junit(results) if args.format == "junit" else sarif(results, _sarif_base(args.project))
        )
    else:
        print(_text(results, args.quiet, _width(), _use_color()))
    if regressed is not None:  # with a baseline only a new or worse FAIL breaks the build
        return EXIT_FAILED if regressed else EXIT_OK
    return EXIT_FAILED if any(r.status is Status.FAIL for r in results) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
