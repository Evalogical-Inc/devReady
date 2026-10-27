"""Docker (only when the project uses it), git identity presence, and free disk space."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from devready.checks.project import _read
from devready.models import Result, Status

DOCKER_FILES = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
)
DOCKER_DOCS = "https://docs.docker.com/get-started/get-docker/"
MIN_FREE_GB = 1


def _run(argv: list[str]) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=10, errors="replace")
    except (subprocess.TimeoutExpired, OSError):
        return None


def check_docker(root: Path) -> list[Result]:
    """CLI vs daemon are separate results. Skipped silently unless the project uses Docker."""
    if not any((root / f).is_file() and not (root / f).is_symlink() for f in DOCKER_FILES):
        return []
    exe = shutil.which("docker")
    if not exe:
        return [
            Result(
                "docker.cli",
                "Docker",
                Status.WARN,
                "Project uses Docker; CLI not found on PATH",
                "Install Docker if you need to build or run this project's containers.",
                DOCKER_DOCS,
            )
        ]
    daemon, arch = _check_daemon(exe)
    return daemon + _check_compose(root, exe) + _check_platform(root, arch)


def _check_daemon(exe: str) -> tuple[list[Result], str]:
    """Returns the results and the server arch ("" when the daemon is not reachable)."""
    p = _run([exe, "version", "--format", "{{.Server.Version}} {{.Server.Arch}}"])
    if p is None:
        return [
            Result("docker.daemon", "Docker daemon", Status.ERROR, "Could not query Docker")
        ], ""
    m = (
        re.fullmatch(r"(\d+(?:\.\d+)+)(?:\s+([a-z0-9_]+))?", p.stdout.strip())
        if p.returncode == 0
        else None
    )
    if not m:
        return [
            Result(
                "docker.daemon",
                "Docker daemon",
                Status.WARN,
                "Docker CLI found but the daemon is not reachable",
                "Start Docker Desktop (or the docker service) and re-run.",
                DOCKER_DOCS,
            )
        ], ""
    return [
        Result("docker.daemon", "Docker daemon", Status.PASS, f"reachable (server {m.group(1)})")
    ], _ARCH_ALIASES.get(m.group(2) or "", m.group(2) or "")


_INCLUDE = re.compile(r"^include\s*:", re.M)


def _check_compose(root: Path, exe: str) -> list[Result]:
    """Validate compose files with `docker compose config`. Only the exit code is used: Compose
    output can contain interpolated .env values, so it is never shown."""
    files = [f for f in DOCKER_FILES[1:] if _read(root / f) is not None]
    if not files:
        return []
    cid, title = "docker.compose.valid", "Compose file"
    v = _run([exe, "compose", "version"])
    if v is None or v.returncode != 0:
        return [Result(cid, title, Status.SKIP, "Docker Compose plugin not found; not validated")]
    bad = []
    for name in files:
        if _INCLUDE.search(_read(root / name) or ""):
            # include: may name remote files; DevReady makes no network calls.
            return [
                Result(cid, title, Status.SKIP, f"{name} uses include:; not validated", file=name)
            ]
        p = _run([exe, "compose", "--project-directory", str(root), "-f", str(root / name),
                  "config", "--quiet"])  # fmt: skip
        if p is None:
            return [Result(cid, title, Status.ERROR, f"Could not validate {name}", file=name)]
        if p.returncode != 0:
            bad.append(name)
    if bad:
        return [
            Result(
                cid,
                title,
                Status.WARN,
                f"{bad[0]} is not a valid Compose file",
                f"Run `docker compose -f {bad[0]} config` to see the errors.",
                "https://docs.docker.com/reference/compose-file/",
                file=bad[0],
            )
        ]
    return [Result(cid, title, Status.PASS, f"{', '.join(files)} valid", file=files[0])]


# Line-based, no YAML parser: `FROM --platform=linux/amd64 ...` and compose `platform: linux/amd64`.
_FROM_PLATFORM = re.compile(r"^\s*FROM\s+--platform=(\S+)", re.M | re.I)
_COMPOSE_PLATFORM = re.compile(r"^\s*platform\s*:\s*[\"']?([^\"'\s#]+)", re.M)
# Only os/arch[/variant] made of safe characters is compared or echoed; $BUILDPLATFORM etc. are not.
_SAFE_PLATFORM = re.compile(r"[a-z0-9_]+/([a-z0-9_]+)(?:/[a-z0-9_]+)?")
_ARCH_ALIASES = {"x86_64": "amd64", "aarch64": "arm64"}


def _check_platform(root: Path, arch: str) -> list[Result]:
    """Warn when an image is pinned to another CPU architecture than the Docker host (emulated)."""
    if not arch:
        return []
    pins: list[tuple[str, str, str]] = []  # (file, platform, arch)
    for name in DOCKER_FILES:
        rx = _FROM_PLATFORM if name == "Dockerfile" else _COMPOSE_PLATFORM
        for value in rx.findall(_read(root / name) or ""):
            if m := _SAFE_PLATFORM.fullmatch(value.lower()):
                pins.append((name, m.group(), _ARCH_ALIASES.get(m.group(1), m.group(1))))
    if not pins:
        return []
    cid, title = "docker.platform", "Image platform"
    for name, platform, want in pins:
        if want != arch:
            return [
                Result(
                    cid,
                    title,
                    Status.WARN,
                    f"{name} pins {platform}; Docker host is {arch} (runs under emulation)",
                    "Use a multi-arch image or drop the platform pin; emulated containers are "
                    "slower and some crash.",
                    "https://docs.docker.com/build/building/multi-platform/",
                    file=name,
                )
            ]
    return [Result(cid, title, Status.PASS, f"pinned platforms match the host ({arch})",
                   file=pins[0][0])]  # fmt: skip


def check_git_identity() -> list[Result]:
    """Presence only: the configured name/email are never captured into output."""
    exe = shutil.which("git")
    if not exe:
        return []
    missing = []
    for key in ("user.name", "user.email"):
        p = _run([exe, "config", "--get", key])
        if p is None or p.returncode != 0 or not p.stdout.strip():
            missing.append(key)
    if not missing:
        return [Result("git.identity", "Git identity", Status.PASS, "user.name and user.email set")]
    return [
        Result(
            "git.identity",
            "Git identity",
            Status.WARN,
            f"not set: {', '.join(missing)}",
            'Run: git config --global user.name "Your Name" (and user.email).',
        )
    ]


def check_disk(root: Path) -> list[Result]:
    try:
        free_gb = shutil.disk_usage(root).free / 1024**3
    except OSError:
        return [Result("disk.space", "Disk space", Status.ERROR, "Could not read disk usage")]
    if free_gb < MIN_FREE_GB:
        return [
            Result(
                "disk.space",
                "Disk space",
                Status.WARN,
                f"only {free_gb:.1f} GB free",
                "Free some space before installing dependencies.",
            )
        ]
    return [Result("disk.space", "Disk space", Status.PASS, f"{free_gb:.0f} GB free")]
