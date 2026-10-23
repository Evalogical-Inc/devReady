import subprocess

import pytest

from devready.checks import tools
from devready.checks.tools import check_tool
from devready.models import Status


def _fake(monkeypatch, stdout="", returncode=0, exc=None):
    monkeypatch.setattr(tools.shutil, "which", lambda exe: f"/bin/{exe}")

    def run(argv, **kw):
        if exc:
            raise exc
        return subprocess.CompletedProcess(argv, returncode, stdout, "")

    monkeypatch.setattr(tools.subprocess, "run", run)


@pytest.mark.parametrize(
    "exe,stdout,want",
    [
        ("git", "git version 2.52.0.windows.1\n", "2.52.0"),  # Git for Windows
        ("git", "git version 2.39.5 (Apple Git-154)\n", "2.39.5"),  # macOS / Homebrew
        ("git", "git version 2.43.0\n", "2.43.0"),  # Debian/Ubuntu
        ("node", "v22.11.0\r\n", "22.11.0"),  # Windows CRLF
        ("npm", "10.9.0\n", "10.9.0"),
    ],
)
def test_parses_platform_outputs(monkeypatch, exe, stdout, want):
    _fake(monkeypatch, stdout)
    result, version = check_tool(f"{exe}.version", exe, exe, "")
    assert version == want and result.status is Status.PASS
    assert result.summary == f"{want} found"


@pytest.mark.parametrize(
    "kw,summary",
    [
        ({"stdout": ""}, "Version output not recognized"),
        ({"stdout": "secret-ish banner text"}, "Version output not recognized"),
        ({"stdout": "git version 2.43.0", "returncode": 1}, "Version command failed"),
        ({"exc": subprocess.TimeoutExpired("git", 15)}, "Could not run version command"),
    ],
)
def test_errors_never_echo_output(monkeypatch, kw, summary):
    _fake(monkeypatch, **kw)
    result, version = check_tool("git.version", "Git", "git", "")
    assert version is None and result.status is Status.ERROR
    assert result.summary.startswith(summary)
    assert "banner" not in result.summary and "2.43" not in result.summary


def test_missing_tool(monkeypatch):
    monkeypatch.setattr(tools.shutil, "which", lambda exe: None)
    result, version = check_tool("git.version", "Git", "git", "")
    assert version is None and result.status is Status.WARN
