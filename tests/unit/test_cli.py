import json

from devready.cli import _text, main
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
    assert "[PASS ] PassTitle    Pass summary" in out
    assert "Pass suggestion" not in out
    assert "[FAIL ] FailTitle    Fail summary" in out
    assert "    Fail suggestion" in out
    assert "[WARN ] WarnTitle    Warn summary" in out
    assert "    Warn suggestion" in out
    assert "[SKIP ] SkipTitle    Skip summary" in out


def test_check_text_failing_fixture(capsys, tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"engines": {"node": ">=999"}}))
    assert main(["check", "--project", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "[FAIL ] Node engines" in out
    assert "    Switch versions with your version manager" in out
def test_python_dash_m_entry_point():
    import subprocess
    import sys

    p = subprocess.run(
        [sys.executable, "-m", "devready", "--version"], capture_output=True, text=True
    )
    assert p.returncode == 0 and "devready" in p.stdout
