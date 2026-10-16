from __future__ import annotations

import platform
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


def run_checks(root: Path) -> list[Result]:
    cfg, cfg_error = load_config(root)
    results = [check_python()]
    versions = {}
    for tool in TOOLS:
        result, versions[tool[2]] = check_tool(*tool)
        results.append(result)
    results += check_git_identity()
    results += check_project(root, versions["node"], platform.python_version())
    results += check_runtimes(root) + check_health(root)
    results += check_docker(root) + check_platform(root) + check_disk(root)
    results += (
        [cfg_error] if cfg_error else check_config(cfg, versions["node"], platform.python_version())
    )
    skip = (cfg or {}).get("skip", [])
    return [r for r in results if not matches(r.check_id, skip)]


def report(results: list[Result]) -> dict:
    return {"schema_version": 1, "results": [r.to_dict() for r in results]}
