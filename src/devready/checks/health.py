"""Project health: .env ignored by git, node_modules vs lockfile, ports the project declares.

Read-only. Only numbers and fixed phrases reach the report, never file content.
"""

from __future__ import annotations

import json
import re
import shutil
import socket
from collections.abc import Callable
from pathlib import Path

from devready.checks.extras import DOCKER_FILES, _run
from devready.checks.project import _read
from devready.models import Result, Status

LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock")
_COMPOSE_PORT = re.compile(r"^\s*-\s*[\"']?(?:[\d.]+:)?(\d{2,5}):\d+", re.M)
_ENV_PORT = re.compile(r"^\s*(?:export\s+)?[A-Z_]*PORT\s*=\s*[\"']?(\d{2,5})\b", re.M)
MAX_PORTS = 20


def _listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def check_env_ignored(root: Path, run: Callable = _run) -> list[Result]:
    """A .env that git would commit is a leak risk. Silent outside a git repo."""
    git = shutil.which("git")
    if not (root / ".env").is_file() or not git:
        return []
    p = run([git, "-C", str(root), "check-ignore", "-q", ".env"])
    if p is None or p.returncode not in (0, 1):
        return []
    if p.returncode == 0:
        return [Result("project.env.ignored", "Env ignored", Status.PASS, ".env is git-ignored")]
    return [
        Result(
            "project.env.ignored",
            "Env ignored",
            Status.WARN,
            ".env is not ignored by git (or is already tracked)",
            "Add .env to .gitignore; if it is tracked, untrack it and rotate its secrets.",
        )
    ]


def check_node_modules(root: Path) -> list[Result]:
    text = _read(root / "package.json")
    try:
        data = json.loads(text) if text else None
    except ValueError:
        return []  # project.py already reports the parse error
    if not isinstance(data, dict) or not any(
        isinstance(data.get(k), dict) and data[k] for k in ("dependencies", "devDependencies")
    ):
        return []
    cid, title = "project.node.modules", "node_modules"
    nm = root / "node_modules"
    if not nm.is_dir():
        return [
            Result(
                cid,
                title,
                Status.WARN,
                "node_modules not found",
                "Install dependencies with your package manager (npm, pnpm, yarn or bun).",
            )
        ]
    # ponytail: directory mtime, not a content comparison; upgrade if it proves noisy.
    locks = [root / f for f in LOCKFILES if (root / f).is_file()]
    if any(lock.stat().st_mtime > nm.stat().st_mtime for lock in locks):
        return [
            Result(
                cid,
                title,
                Status.WARN,
                "a lockfile is newer than node_modules",
                "Re-run your package manager's install to sync dependencies.",
            )
        ]
    return [Result(cid, title, Status.PASS, "node_modules is present and not older than lockfiles")]


def check_ports(root: Path, in_use: Callable[[int], bool] = _listening) -> list[Result]:
    ports: set[int] = set()
    for name in DOCKER_FILES[1:]:  # compose files only
        if (text := _read(root / name)) is not None:
            ports.update(int(p) for p in _COMPOSE_PORT.findall(text))
    if (text := _read(root / ".env.example")) is not None:
        ports.update(int(p) for p in _ENV_PORT.findall(text))
    ports = {p for p in ports if 0 < p < 65536}
    if not ports:
        return []
    cid, title = "project.ports.free", "Ports"
    shown = sorted(ports)[:MAX_PORTS]
    busy = [p for p in shown if in_use(p)]
    if busy:
        return [
            Result(
                cid,
                title,
                Status.WARN,
                f"already in use on localhost: {', '.join(map(str, busy))}",
                "Stop the other process or change the port; it may be this project running.",
            )
        ]
    return [Result(cid, title, Status.PASS, f"{len(shown)} declared port(s) are free")]


def check_health(root: Path) -> list[Result]:
    return check_env_ignored(root) + check_node_modules(root) + check_ports(root)
