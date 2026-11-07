from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from devready.checks.config import check_config, load_config
from devready.checks.extras import check_disk, check_docker, check_git_identity
from devready.checks.health import check_health
from devready.checks.platform_checks import check_platform
from devready.checks.project import check_project
from devready.checks.python_check import check_python
from devready.checks.runtimes import check_runtimes
from devready.checks.tools import TOOLS, check_tool
from devready.models import Result
from devready.workspace import MAX_PACKAGES, discover_packages


def matches(check_id: str, ids: list[str]) -> bool:
    return any(check_id == i or check_id.startswith(i + ".") for i in ids)


def machine_checks(root: Path) -> tuple[list[Result], dict[str, str | None]]:
    """Checks that never read project files (tools on PATH, git identity, disk): run once.

    Returns the results and the tool versions found, for project_checks.
    """
    results, versions = [], {}
    for tool in TOOLS:
        result, versions[tool[2]] = check_tool(*tool)
        results.append(result)
    return results + check_git_identity() + check_disk(root), versions


def project_checks(
    root: Path, versions: dict[str, str | None], machine: Sequence[Result] = ()
) -> list[Result]:
    """Checks that read files in `root`: Python/.venv, pins, health, Docker files, platform, config.

    `machine` results (if any) are placed right after Python, the order users know. Everything
    returned is filtered by the `skip` list in root's `.devready.json`.
    """
    cfg, cfg_error = load_config(root)
    py_result, py_version = check_python(root)
    node = versions.get("node")
    results = [py_result, *machine, *check_project(root, node, py_version)]
    results += check_runtimes(root) + check_health(root)
    results += check_docker(root) + check_platform(root)
    results += [cfg_error] if cfg_error else check_config(cfg, node, py_version)
    skip = (cfg or {}).get("skip", [])
    return [r for r in results if not matches(r.check_id, skip)]


def run_checks(root: Path) -> list[Result]:
    machine, versions = machine_checks(root)
    return project_checks(root, versions, machine)


# Results about the machine that project files only trigger: with --recursive, an identical one
# (same id, status, summary) is shown once. A package's own .venv gives a different summary.
MACHINE_IDS = {
    "python.version", "docker.cli", "docker.daemon", "docker.backend",
    "platform.long_paths", "platform.exec_policy", "platform.wsl.version", "platform.build_tools",
}  # fmt: skip


def run_recursive(root: Path) -> tuple[list[tuple[str, list[Result]]], int]:
    """Machine-wide checks once (reported under "."), then project checks once per package.

    Checks at most MAX_PACKAGES packages; also returns how many were found, so callers can say so.
    """
    # ponytail: `docker` still runs once per package with Docker files; cache it if that is slow.
    packages = discover_packages(root)
    machine, versions = machine_checks(root)
    seen: set[tuple] = set()
    out = []
    for p in packages[:MAX_PACKAGES]:
        kept = []
        for r in project_checks(root / p, versions, machine if p == "." else ()):
            key = (r.check_id, r.status, r.summary)
            if r.check_id in MACHINE_IDS and key in seen:
                continue
            seen.add(key)
            kept.append(r)
        out.append((p, kept))
    return out, len(packages)


def report(results: list[Result]) -> dict:
    return {"schema_version": 1, "results": [r.to_dict() for r in results]}


def report_projects(projects: list[tuple[str, list[Result]]]) -> dict:
    """The --recursive JSON report (docs/schema-multi.json)."""
    return {
        "schema_version": 1,
        "projects": [{"path": p, "results": [r.to_dict() for r in rs]} for p, rs in projects],
    }
