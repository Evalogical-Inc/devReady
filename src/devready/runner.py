from __future__ import annotations

import platform
from pathlib import Path

from devready.checks.project import check_project
from devready.checks.python_check import check_python
from devready.checks.tools import TOOLS, check_tool
from devready.models import Result


def run_checks(root: Path) -> list[Result]:
    results = [check_python()]
    versions = {}
    for tool in TOOLS:
        result, versions[tool[2]] = check_tool(*tool)
        results.append(result)
    return results + check_project(root, versions["node"], platform.python_version())


def report(results: list[Result]) -> dict:
    return {"schema_version": 1, "results": [r.to_dict() for r in results]}
