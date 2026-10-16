from __future__ import annotations

import re
import shutil
import subprocess

from devready.models import Result, Status

# (check_id, title, executable, docs). Fixed argv only: never built from user input.
TOOLS = [
    ("git.version", "Git", "git", "https://git-scm.com/downloads"),
    ("node.version", "Node.js", "node", "https://nodejs.org/en/download"),
    (
        "npm.version",
        "npm",
        "npm",
        "https://docs.npmjs.com/downloading-and-installing-node-js-and-npm",
    ),
]


def check_tool(
    check_id: str, title: str, exe: str, docs: str, args: tuple[str, ...] = ("--version",)
) -> tuple[Result, str | None]:
    """Returns (result, parsed version or None). Raw command output is never reported."""
    path = shutil.which(exe)
    if not path:
        return Result(
            check_id,
            title,
            Status.WARN,
            "Not found on PATH",
            f"Install {title} if your project needs it.",
            docs,
        ), None
    try:
        # 15s: cold Windows .cmd shims (yarn) exceeded 5s on CI
        proc = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=15, errors="replace"
        )
    except (subprocess.TimeoutExpired, OSError):
        return Result(check_id, title, Status.ERROR, "Could not run version command"), None
    out = (proc.stdout or proc.stderr)[:200]  # java -version prints to stderr
    m = re.search(r"\d+(?:\.\d+)+", out) if proc.returncode == 0 else None
    if proc.returncode != 0:  # e.g. dotnet with only a runtime installed (no SDK)
        return Result(
            check_id, title, Status.ERROR, "Version command failed (is it fully installed?)"
        ), None
    if not m:
        return Result(check_id, title, Status.ERROR, "Version output not recognized"), None
    return Result(check_id, title, Status.PASS, f"{m.group()} found"), m.group()
