import sys

from devready.checks.python_check import check_python
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
