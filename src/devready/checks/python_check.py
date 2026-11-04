from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from devready.checks.tools import check_tool
from devready.models import Result

DOCS = "https://www.python.org/downloads/"


def _project_python(root: Path) -> str | None:
    """The interpreter a developer gets in this project: its venv first, else first on PATH."""
    for venv in (".venv", "venv"):
        for rel in ("Scripts/python.exe", "bin/python"):
            if (root / venv / rel).is_file():
                return str(root / venv / rel)
    return shutil.which("python") or shutil.which("python3")


def check_python(root: Path) -> tuple[Result, str | None]:
    """Returns (result, version) for the project's Python, not the one running DevReady."""
    exe = _project_python(root)
    result, version = check_tool("python.version", "Python", exe or "python", DOCS)
    if exe and version:  # name the interpreter so the result is verifiable
        shown = Path(exe).relative_to(root) if Path(exe).is_relative_to(root) else exe
        result = replace(result, summary=f"{version} found ({shown})")
    return result, version
