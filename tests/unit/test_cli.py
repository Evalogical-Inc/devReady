import json

from devready.cli import main


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
