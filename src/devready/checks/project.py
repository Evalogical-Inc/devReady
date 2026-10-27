"""Compare version requirements declared by a project with what is installed.

Read-only: reads only .nvmrc, .node-version, .python-version, package.json and pyproject.toml
(no symlinks, 1 MB cap, never executed). Only a validated requirement string is echoed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from devready.managers import command
from devready.models import Result, Status
from devready.versions import Version, parse_version, satisfies

MAX_BYTES = 1_000_000


def _read(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _compare(
    check_id: str,
    title: str,
    source: str,
    spec: str,
    installed: Version | None,
    miss: Status,
    file: str = "",
    runtime: str = "",
) -> Result:
    # Echo only specs the matcher fully parses: plain words can pass SAFE_SPEC but are not versions.
    shown = spec if satisfies((0, 0, 0), spec) is not None else "(unrecognized)"
    if installed is None:
        return Result(
            check_id, title, Status.SKIP, f"{source} wants {shown}; tool not found", file=file
        )
    ok = satisfies(installed, spec)
    have = ".".join(map(str, installed))
    if ok is None:
        return Result(
            check_id,
            title,
            Status.SKIP,
            f"{source} requirement could not be evaluated (installed {have})",
            file=file,
        )
    if ok:
        return Result(
            check_id, title, Status.PASS, f"{have} satisfies {source} ({shown})", file=file
        )
    cmd = command(runtime, spec)
    return Result(
        check_id,
        title,
        miss,
        f"{have} does not satisfy {source} ({shown})",
        f"Run `{cmd}`, or update the requirement."
        if cmd
        else "Switch versions with your version manager (nvm, pyenv, mise, ...) "
        "or update the requirement.",
        file=file,
    )


def _engines(text: str) -> str | None:
    engines = json.loads(text).get("engines", {})
    spec = engines.get("node") if isinstance(engines, dict) else None
    return spec if isinstance(spec, str) else None


def _first_line(text: str) -> str:
    return text.strip().splitlines()[0] if text.strip() else ""


def _requires_python(text: str) -> str | None:
    # ponytail: regex instead of tomllib (3.11+) to keep 3.10 support; first match wins.
    m = re.search(r"^\s*requires-python\s*=\s*[\"']([^\"']*)[\"']", text, re.M)
    return m.group(1) if m else None


# (id, title, files (first readable wins), source label ("" = file name), extractor, runtime, miss)
# An extractor returns the spec, None to stay silent, or raises ValueError/AttributeError (ERROR).
PINS: list[tuple] = [
    ("project.node.pin", "Node pin", (".nvmrc", ".node-version"), "", str.strip, "node",
     Status.WARN),
    ("project.node.engines", "Node engines", ("package.json",), "package.json engines", _engines,
     "node", Status.FAIL),
    ("project.python.pin", "Python pin", (".python-version",), "", _first_line, "python",
     Status.WARN),
    ("project.python.requires", "Python requires", ("pyproject.toml",),
     "pyproject requires-python", _requires_python, "python", Status.FAIL),
]  # fmt: skip


def check_project(root: Path, node: str | None, python: str | None) -> list[Result]:
    installed = {
        "node": parse_version(node) if node else None,
        "python": parse_version(python) if python else None,
    }
    out: list[Result] = []

    for cid, title, files, label, extract, runtime, miss in PINS:
        for name in files:
            if (text := _read(root / name)) is None:
                continue
            try:
                spec = extract(text)
            except (ValueError, AttributeError):
                out.append(
                    Result(cid, title, Status.ERROR, f"{name} could not be parsed", file=name)
                )
                break
            if spec is not None:
                out.append(
                    _compare(
                        cid, title, label or name, spec, installed[runtime], miss, name, runtime
                    )
                )
            break

    if (text := _read(root / ".tool-versions")) is not None:
        want = {"nodejs": "node", "node": "node", "python": "python"}
        for line in text.splitlines():
            parts = line.split("#")[0].split()
            if len(parts) >= 2 and parts[0] in want:
                is_node = want[parts[0]] == "node"
                out.append(
                    _compare(
                        f"project.{want[parts[0]]}.tool_versions",
                        "Node tool-versions" if is_node else "Python tool-versions",
                        ".tool-versions",
                        parts[1],
                        installed[want[parts[0]]],
                        Status.WARN,
                        ".tool-versions",
                        want[parts[0]],
                    )
                )

    return out + _check_env(root)


_ENV_KEY = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.M)
_SAFE_NAME = re.compile(r"^[A-Z0-9_]{1,40}$")


def _check_env(root: Path) -> list[Result]:
    """Compare variable NAMES in .env.example with .env. Values are never kept or shown."""
    example = _read(root / ".env.example")
    if example is None:
        return []
    cid, title = "project.env.keys", "Env keys"
    wanted = set(_ENV_KEY.findall(example))
    env_text = _read(root / ".env")
    if env_text is None:
        return [
            Result(
                cid,
                title,
                Status.WARN,
                f".env not found ({len(wanted)} keys in .env.example)",
                "Copy .env.example to .env and fill in the values.",
            )
        ]
    missing = sorted(wanted - set(_ENV_KEY.findall(env_text)))
    if not missing:
        return [Result(cid, title, Status.PASS, f"all {len(wanted)} .env.example keys present")]
    shown = [m for m in missing if _SAFE_NAME.match(m)][:10]
    extra = f": {', '.join(shown)}" if shown else ""
    return [
        Result(
            cid,
            title,
            Status.WARN,
            f"{len(missing)} key(s) in .env.example missing from .env{extra}",
            "Add the missing keys to .env (values are never read or shown by DevReady).",
        )
    ]
