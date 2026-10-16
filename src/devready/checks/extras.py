"""Docker (only when the project uses it), git identity presence, and free disk space."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

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
    p = _run([exe, "version", "--format", "{{.Server.Version}}"])
    if p is None:
        return [Result("docker.daemon", "Docker daemon", Status.ERROR, "Could not query Docker")]
    m = re.fullmatch(r"\d+(?:\.\d+)+", p.stdout.strip()) if p.returncode == 0 else None
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
        ]
    return [
        Result("docker.daemon", "Docker daemon", Status.PASS, f"reachable (server {m.group()})")
    ]


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
