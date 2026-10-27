"""OS-specific pain points, each checked only when the project makes it relevant.

Windows: long paths, PowerShell execution policy (blocks npm.ps1), git line endings, WSL version.
macOS/Linux: a compiler toolchain when the project looks like it builds native code.
Read-only; fixed argv only.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from devready.checks.extras import DOCKER_FILES, _run
from devready.models import Result, Status

NATIVE_HINTS = ("binding.gyp", "setup.py", "Gemfile", "Cargo.toml")
BLOCKING_POLICIES = {"Restricted", "AllSigned"}
KNOWN_POLICIES = BLOCKING_POLICIES | {"RemoteSigned", "Unrestricted", "Bypass", "Undefined"}


def _long_paths_enabled() -> bool | None:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem"
        ) as key:
            return bool(winreg.QueryValueEx(key, "LongPathsEnabled")[0])
    except (ImportError, OSError):
        return None


def _windows(root: Path, run: Callable, which: Callable, long_paths: Callable) -> list[Result]:
    out: list[Result] = []
    if (root / "package.json").is_file():
        if long_paths() is False:
            out.append(
                Result(
                    "platform.long_paths",
                    "Long paths",
                    Status.WARN,
                    "Windows long path support is off; deep node_modules trees can fail",
                    "Enable LongPathsEnabled (administrator) and git's core.longpaths.",
                )
            )
        ps = which("powershell")
        p = (
            run([ps, "-NoProfile", "-NonInteractive", "-Command", "Get-ExecutionPolicy"])
            if ps
            else None
        )
        policy = p.stdout.strip() if p is not None and p.returncode == 0 else ""
        if policy in BLOCKING_POLICIES:
            out.append(
                Result(
                    "platform.exec_policy",
                    "PowerShell policy",
                    Status.WARN,
                    f"PowerShell policy is {policy}; npm/pnpm .ps1 scripts will be blocked",
                    "Use cmd, or allow local scripts for your user: "
                    "Set-ExecutionPolicy -Scope CurrentUser RemoteSigned",
                )
            )
    git = which("git")
    if git and (root / ".git").exists() and not (root / ".gitattributes").is_file():
        p = run([git, "-C", str(root), "config", "--get", "core.autocrlf"])
        if p is not None and not p.stdout.strip():
            out.append(
                Result(
                    "platform.autocrlf",
                    "Line endings",
                    Status.WARN,
                    "core.autocrlf is unset and the repo has no .gitattributes",
                    "Add a .gitattributes with line-ending rules, or set core.autocrlf.",
                )
            )
    if any((root / f).is_file() and not (root / f).is_symlink() for f in DOCKER_FILES):
        out += _wsl_version(run, which)
    return out


def _wsl_version(run: Callable, which: Callable) -> list[Result]:
    """Version of the default WSL distribution, from `wsl -l -v` (the row marked `*`).

    wsl prints UTF-16LE; its ASCII text survives any decoding with NULs in between, so NULs are
    dropped. Headers are localized, so only the row marker and the last column are used. The
    distribution name is never shown."""
    wsl = which("wsl")
    p = run([wsl, "-l", "-v"]) if wsl else None
    if p is None or p.returncode != 0:
        return []
    rows = [ln.split() for ln in p.stdout.replace("\x00", "").splitlines()]
    version = next((r[-1] for r in rows if len(r) >= 3 and r[0] == "*"), "")
    cid, title = "platform.wsl.version", "WSL version"
    if version == "1":
        return [
            Result(
                cid,
                title,
                Status.WARN,
                "default WSL distribution uses WSL 1; Docker needs WSL 2",
                "Convert it with `wsl --set-version <distro> 2` (list names with `wsl -l -v`) "
                "and run `wsl --set-default-version 2`.",
                "https://learn.microsoft.com/windows/wsl/install#upgrade-version-from-wsl-1-to-wsl-2",
            )
        ]
    if version == "2":
        return [Result(cid, title, Status.PASS, "default WSL distribution uses WSL 2")]
    return []


def _build_tools(root: Path, plat: str, run: Callable, which: Callable) -> list[Result]:
    if not any((root / n).is_file() for n in NATIVE_HINTS):
        return []
    cid, title = "platform.build_tools", "Build tools"
    if plat == "darwin":
        xs = which("xcode-select")
        p = run([xs, "-p"]) if xs else None
        ok = p is not None and p.returncode == 0
        fix = "Install the Xcode Command Line Tools: xcode-select --install"
    else:
        ok = any(which(c) for c in ("cc", "gcc", "clang")) and bool(which("make"))
        fix = "Install a C compiler and make (for example your distro's build-essential)."
    if ok:
        return [Result(cid, title, Status.PASS, "compiler toolchain found")]
    return [Result(cid, title, Status.WARN, "no compiler toolchain found for native builds", fix)]


def check_platform(
    root: Path,
    plat: str = sys.platform,
    run: Callable = _run,
    which: Callable = shutil.which,
    long_paths: Callable = _long_paths_enabled,
) -> list[Result]:
    if plat == "win32":
        return _windows(root, run, which, long_paths)
    return _build_tools(root, plat, run, which)
