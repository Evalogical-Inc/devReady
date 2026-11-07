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


def report(results: list[Result]) -> dict:
    return {"schema_version": 1, "results": [r.to_dict() for r in results]}
