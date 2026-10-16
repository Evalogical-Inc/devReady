from __future__ import annotations

import platform
from pathlib import Path

from devready.checks.extras import check_disk, check_docker, check_git_identity
from devready.checks.health import check_health
from devready.checks.project import check_project
from devready.checks.python_check import check_python
from devready.checks.runtimes import check_runtimes
from devready.checks.tools import TOOLS, check_tool
from devready.models import Result


def run_checks(root: Path) -> list[Result]:
    results = [check_python()]
    versions = {}
    for tool in TOOLS:
        result, versions[tool[2]] = check_tool(*tool)
        results.append(result)
    results += check_git_identity()
    results += check_project(root, versions["node"], platform.python_version())
    results += check_runtimes(root) + check_health(root)
    return results + check_docker(root) + check_disk(root)


def report(results: list[Result]) -> dict:
    return {"schema_version": 1, "results": [r.to_dict() for r in results]}
