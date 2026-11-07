"""Find the package folders `devready check --recursive` runs project checks in (#43).

Read-only. Patterns come from package.json `workspaces` and pnpm-workspace.yaml `packages:`
(line-based, no YAML dependency); supported shapes are `dir`, `dir/*` and `dir/**`. Without any
pattern, folders up to 3 levels deep are scanned. Either way a folder counts only if it holds a
pin file and every part of its path is a plain name (reports print paths, and agents read them).
Never follows symlinks or junctions, never leaves the root, skips tool folders.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from devready.checks.project import PINS, _read
from devready.checks.runtimes import RUNTIMES

MAX_PACKAGES = 200  # callers check at most this many, root included, and say so when cut
MAX_DEPTH = 3
SKIP = {"node_modules", ".git", ".venv", "venv", "dist", "build"}
PIN_FILES = (
    {name for row in PINS for name in row[2]}
    | {pin[1] for row in RUNTIMES.values() for pin in row[5]}
    | {".tool-versions"}
)
_YAML_ITEM = re.compile(r"""^\s*-\s*(["']?)([^"'#\s]+)\1\s*(?:#.*)?$""")
_UNSUPPORTED = re.compile(r"[*?\[\]{}!:\\]|^/|(^|/)\.\.(/|$)")
_PLAIN_NAME = re.compile(r"[A-Za-z0-9_.@+-]+")  # same as the path pattern in schema-multi.json


def _patterns(root: Path) -> list[str]:
    try:
        ws = json.loads(_read(root / "package.json") or "{}").get("workspaces")
    except (ValueError, AttributeError):
        ws = None
    if isinstance(ws, dict):
        ws = ws.get("packages")
    out = [p for p in ws if isinstance(p, str)] if isinstance(ws, list) else []
    inside = False
    for line in (_read(root / "pnpm-workspace.yaml") or "").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] not in " \t-":
            inside = line.startswith("packages:")
        elif inside and (m := _YAML_ITEM.match(line)):
            out.append(m.group(2))
    return out


def _real(path: Path, expected: Path) -> bool:
    """A folder that really sits at `expected`: no symlink, junction or drive change on the way."""
    try:
        return path.is_dir() and os.path.normcase(path.resolve()) == os.path.normcase(expected)
    except (OSError, RuntimeError):
        return False


def _walk(root: Path, real_root: Path, start: PurePosixPath, depth: int) -> Iterator:
    stack = [start]
    while stack:
        rel = stack.pop()
        yield rel
        if len(rel.parts) - len(start.parts) >= depth:
            continue
        try:
            names = [c.name for c in (root / rel).iterdir()]
        except OSError:
            continue
        stack += [
            rel / n for n in names if n not in SKIP and _real(root / rel / n, real_root / rel / n)
        ]


def _expand(root: Path, real_root: Path, pattern: str) -> list[PurePosixPath]:
    head, star, rest = pattern.strip().removeprefix("./").rstrip("/").partition("/*")
    if not head or rest not in ("", "*") or _UNSUPPORTED.search(head):
        return []
    base = PurePosixPath(head)
    if not _real(root / base, real_root / base):
        return []
    if not star:
        return [base]
    walked = list(_walk(root, real_root, base, MAX_DEPTH if rest else 1))
    return walked if rest else walked[1:]  # `dir/**` includes dir itself, `dir/*` does not


def _has_pin(folder: Path) -> bool:
    return any((folder / n).is_file() and not (folder / n).is_symlink() for n in PIN_FILES)


def discover_packages(root: Path) -> list[str]:
    """Return "." then every package folder relative to root (POSIX, sorted)."""
    real_root = root.resolve()
    patterns = _patterns(root)
    found = (
        {p for pattern in patterns for p in _expand(root, real_root, pattern)}
        if patterns
        else set(_walk(root, real_root, PurePosixPath(), MAX_DEPTH))
    )
    packages = sorted(
        p.as_posix()
        for p in found
        if p.parts and all(_PLAIN_NAME.fullmatch(n) for n in p.parts) and _has_pin(root / p)
    )
    return [".", *packages]
