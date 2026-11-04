import sys

import pytest

from devready.checks.python_check import _project_python, check_python
from devready.models import Status


def test_prefers_project_venv(tmp_path):
    rel = "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    exe = tmp_path / ".venv" / rel
    exe.parent.mkdir(parents=True)
    exe.write_text("")  # not runnable: WARN on Unix (no exec bit), ERROR on Windows; never PASS
    result, version = check_python(tmp_path)
    assert version is None and result.status is not Status.PASS


def test_names_interpreter_from_path(tmp_path):
    result, version = check_python(tmp_path)
    if version:  # a python on PATH; skip the assertion if the host has none
        assert result.status is Status.PASS and "(" in result.summary


def test_dot_venv_wins_over_venv(tmp_path):
    rel = "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    for name in ("venv", ".venv"):
        (tmp_path / name / rel).parent.mkdir(parents=True)
        (tmp_path / name / rel).write_text("")
    assert _project_python(tmp_path) == str(tmp_path / ".venv" / rel)


@pytest.mark.skipif(sys.platform == "win32", reason="needs an executable shell script")
def test_unix_venv_python_is_run_and_named(tmp_path):
    exe = tmp_path / ".venv" / "bin" / "python"
    exe.parent.mkdir(parents=True)
    exe.write_text("#!/bin/sh\necho 'Python 3.99.1'\n")
    exe.chmod(0o755)
    result, version = check_python(tmp_path)
    assert version == "3.99.1" and result.status is Status.PASS
    assert result.summary == "3.99.1 found (.venv/bin/python)"
