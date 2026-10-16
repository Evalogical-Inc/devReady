"""Compare version requirements declared by a project with what is installed.

Read-only: reads only .nvmrc, .node-version, .python-version, package.json and pyproject.toml
(no symlinks, 1 MB cap, never executed). Only a validated requirement string is echoed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from devready.models import Result, Status
from devready.versions import SAFE_SPEC, Version, parse_version, satisfies

MAX_BYTES = 1_000_000


def _read(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _compare(
    check_id: str, title: str, source: str, spec: str, installed: Version | None, miss: Status
) -> Result:
    shown = spec if SAFE_SPEC.match(spec) else "(unrecognized)"
    if installed is None:
        return Result(check_id, title, Status.SKIP, f"{source} wants {shown}; tool not found")
    ok = satisfies(installed, spec)
    have = ".".join(map(str, installed))
    if ok is None:
        return Result(
            check_id,
            title,
            Status.SKIP,
            f"{source} requirement could not be evaluated (installed {have})",
        )
    if ok:
        return Result(check_id, title, Status.PASS, f"{have} satisfies {source} ({shown})")
    return Result(
        check_id,
        title,
        miss,
        f"{have} does not satisfy {source} ({shown})",
        "Switch versions with your version manager (nvm, pyenv, mise, ...) "
        "or update the requirement.",
    )


def check_project(root: Path, node: str | None, python: str | None) -> list[Result]:
    node_v = parse_version(node) if node else None
    py_v = parse_version(python) if python else None
    out: list[Result] = []

    for name in (".nvmrc", ".node-version"):
        if (text := _read(root / name)) is not None:
            out.append(
                _compare("project.node.pin", "Node pin", name, text.strip(), node_v, Status.WARN)
            )
            break

    if (text := _read(root / "package.json")) is not None:
        try:
            engines = json.loads(text).get("engines", {})
            spec = engines.get("node") if isinstance(engines, dict) else None
        except (ValueError, AttributeError):
            out.append(
                Result(
                    "project.node.engines",
                    "Node engines",
                    Status.ERROR,
                    "package.json could not be parsed",
                )
            )
            spec = None
        if isinstance(spec, str):
            out.append(
                _compare(
                    "project.node.engines",
                    "Node engines",
                    "package.json engines",
                    spec,
                    node_v,
                    Status.FAIL,
                )
            )

    if (text := _read(root / ".python-version")) is not None:
        out.append(
            _compare(
                "project.python.pin",
                "Python pin",
                ".python-version",
                text.strip().splitlines()[0] if text.strip() else "",
                py_v,
                Status.WARN,
            )
        )

    if (text := _read(root / "pyproject.toml")) is not None:
        # ponytail: regex instead of tomllib (3.11+) to keep 3.10 support; first match wins.
        m = re.search(r"^\s*requires-python\s*=\s*[\"']([^\"']*)[\"']", text, re.M)
        if m:
            out.append(
                _compare(
                    "project.python.requires",
                    "Python requires",
                    "pyproject requires-python",
                    m.group(1),
                    py_v,
                    Status.FAIL,
                )
            )
    return out
