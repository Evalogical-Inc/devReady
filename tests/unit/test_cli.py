import json

import pytest

from devready.cli import _text, _use_color, _width, main
from devready.models import Result, Status


def test_check_text(capsys):
    assert main(["check"]) == 0
    out = capsys.readouterr().out
    assert "[PASS ] Python" in out and "No changes were made" in out


def test_check_json(capsys):
    assert main(["check", "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema_version"] == 1
    assert data["results"][0]["check_id"] == "python.version"


def test_bad_usage_exit_code():
    assert main(["nope"]) == 2


def test_version(capsys):
    assert main(["--version"]) == 0
    assert "devready" in capsys.readouterr().out


def test_text_suggestions():
    results = [
        Result("check.pass", "PassTitle", Status.PASS, "Pass summary", "Pass suggestion"),
        Result("check.fail", "FailTitle", Status.FAIL, "Fail summary", "Fail suggestion"),
        Result("check.warn", "WarnTitle", Status.WARN, "Warn summary", "Warn suggestion"),
        Result("check.skip", "SkipTitle", Status.SKIP, "Skip summary", ""),
    ]
    out = _text(results)
    assert "[PASS ] PassTitle Pass summary" in out
    assert "Pass suggestion" not in out
    assert "[FAIL ] FailTitle Fail summary\n                  -> Fail suggestion" in out
    assert "[WARN ] WarnTitle Warn summary\n                  -> Warn suggestion" in out
    assert "[SKIP ] SkipTitle Skip summary" in out
    assert "1 passed, 1 warning, 1 failed, 1 skipped" in out


def test_check_text_failing_fixture(capsys, tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"engines": {"node": ">=999"}}))
    assert main(["check", "--project", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "[FAIL ] Node engines" in out
    assert "-> Switch versions with your version manager" in out


def test_python_dash_m_entry_point():
    import subprocess
    import sys

    p = subprocess.run(
        [sys.executable, "-m", "devready", "--version"], capture_output=True, text=True
    )
    assert p.returncode == 0 and "devready" in p.stdout


def test_quiet_hides_passes():
    results = [
        Result("check.pass", "PassTitle", Status.PASS, "Pass summary"),
        Result("check.warn", "WarnTitle", Status.WARN, "Warn summary", "Warn suggestion"),
    ]
    out = _text(results, quiet=True)
    assert "PassTitle" not in out
    assert "[WARN ] WarnTitle Warn summary" in out and "-> Warn suggestion" in out
    assert "1 passed, 1 warning, 0 failed" in out  # the tally still counts hidden passes
    assert "No changes were made" in out


def test_check_quiet(capsys, tmp_path):
    assert main(["check", "--quiet"]) == 0
    assert "[PASS " not in capsys.readouterr().out
    (tmp_path / "package.json").write_text(json.dumps({"engines": {"node": ">=999"}}))
    assert main(["check", "--quiet", "--project", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "[FAIL ] Node engines" in out and "[PASS " not in out


def test_help_lists_exit_codes(capsys):
    assert main(["check", "--help"]) == 0
    assert "exit codes" in capsys.readouterr().out


RESULTS = [
    Result("python.version", "Python", Status.PASS, "3.11.15 found"),
    Result(
        "docker.daemon",
        "Docker daemon",
        Status.WARN,
        "Docker CLI found but the daemon is not reachable",
        "Start Docker Desktop (or the docker service) and re-run.",
    ),
    Result(
        "project.env.keys",
        "Env keys",
        Status.WARN,
        "14 key(s) in .env.example missing from .env: "
        + ", ".join(f"AWS_KEY_{i}" for i in range(10)),
        "Add the missing keys to .env (values are never read or shown by DevReady).",
    ),
    Result(
        "project.node.engines",
        "Node engines",
        Status.FAIL,
        "23.5.0 does not satisfy package.json engines (>=99)",
    ),
]

WIDE = """DevReady - Environment Check

[PASS ] Python        3.11.15 found
[WARN ] Docker daemon Docker CLI found but the daemon is not reachable
                      -> Start Docker Desktop (or the docker service) and
                         re-run.
[WARN ] Env keys      14 key(s) in .env.example missing from .env: AWS_KEY_0,
                      AWS_KEY_1, AWS_KEY_2, AWS_KEY_3, AWS_KEY_4, AWS_KEY_5,
                      AWS_KEY_6, AWS_KEY_7, AWS_KEY_8, AWS_KEY_9
                      -> Add the missing keys to .env (values are never read or
                         shown by DevReady).
[FAIL ] Node engines  23.5.0 does not satisfy package.json engines (>=99)

1 passed, 2 warnings, 1 failed
No changes were made to your system."""

NARROW = """DevReady - Environment Check

[PASS ] Python
        3.11.15 found
[WARN ] Docker daemon
        Docker CLI found but the daemon is not
        reachable
        -> Start Docker Desktop (or the docker
           service) and re-run.
[WARN ] Env keys
        14 key(s) in .env.example missing from
        .env: AWS_KEY_0, AWS_KEY_1, AWS_KEY_2,
        AWS_KEY_3, AWS_KEY_4, AWS_KEY_5,
        AWS_KEY_6, AWS_KEY_7, AWS_KEY_8, AWS_KEY_9
        -> Add the missing keys to .env (values
           are never read or shown by DevReady).
[FAIL ] Node engines
        23.5.0 does not satisfy package.json
        engines (>=99)

1 passed, 2 warnings, 1 failed
No changes were made to your system."""


def test_text_snapshot_wide():
    assert _text(RESULTS, width=80) == WIDE


def test_text_snapshot_narrow():
    assert _text(RESULTS, width=50) == NARROW


@pytest.mark.parametrize("width", [40, 50, 60, 80, 120])
def test_text_fits_width(width):
    long = Result("x.y", "A much longer check title", Status.WARN, "word " * 60, "fix " * 40)
    assert all(len(line) <= width for line in _text([*RESULTS, long], width=width).splitlines())


def test_text_color():
    out = _text(RESULTS, width=80, color=True)
    assert "\033[33m[WARN ]\033[0m Env keys      14 key(s)" in out
    assert "\033[1;31m[FAIL ]\033[0m Node engines" in out
    assert "\033[" not in _text(RESULTS, width=80)


class _Stream:
    def __init__(self, tty):
        self.tty = tty

    def isatty(self):
        return self.tty


def test_use_color_respects_no_color_and_tty():
    assert not _use_color(_Stream(False), {})
    assert not _use_color(_Stream(True), {"NO_COLOR": "1"})
    assert not _use_color(_Stream(True), {"TERM": "dumb"})


def test_width_falls_back_to_80_when_not_a_tty(monkeypatch):
    monkeypatch.setenv("COLUMNS", "200")
    assert _width(_Stream(False)) == 80
