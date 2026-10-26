"""Compare version requirements declared by a project with what is installed.

Read-only: reads only .nvmrc, .node-version, .python-version, package.json and pyproject.toml
(no symlinks, 1 MB cap, never executed). Only a validated requirement string is echoed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

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
    return Result(
        check_id,
        title,
        miss,
        f"{have} does not satisfy {source} ({shown})",
        "Switch versions with your version manager (nvm, pyenv, mise, ...) "
        "or update the requirement.",
        file=file,
    )


def check_project(root: Path, node: str | None, python: str | None) -> list[Result]:
    node_v = parse_version(node) if node else None
    py_v = parse_version(python) if python else None
    out: list[Result] = []

    for name in (".nvmrc", ".node-version"):
        if (text := _read(root / name)) is not None:
            out.append(
                _compare(
                    "project.node.pin", "Node pin", name, text.strip(), node_v, Status.WARN, name
                )
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
                    file="package.json",
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
                    "package.json",
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
                ".python-version",
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
                    "pyproject.toml",
                )
            )

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
                        node_v if is_node else py_v,
                        Status.WARN,
                        ".tool-versions",
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
