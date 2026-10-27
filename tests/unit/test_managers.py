from devready.checks import project
from devready.managers import command
from devready.models import Status

ON_PATH = {"fnm"}.__contains__


def test_command_only_for_plain_versions():
    assert command("node", "20", ON_PATH) == "fnm use --install-if-missing 20"
    assert command("node", " v20.11.0\n", ON_PATH) == "fnm use --install-if-missing 20.11.0"
    for spec in (">=18", "lts/iron", "20; rm -rf /", "node"):
        assert command("node", spec, ON_PATH) is None
    assert command("node", "20", lambda exe: None) is None
    assert command("python", "3.12", ON_PATH) is None  # no python manager rows yet


def test_mismatch_suggests_command(tmp_path, monkeypatch):
    monkeypatch.setattr("devready.managers.shutil.which", ON_PATH)
    (tmp_path / ".nvmrc").write_text("20\n")
    r = project.check_project(tmp_path, "18.0.0", None)[0]
    assert r.status is Status.WARN
    assert r.suggestion == "Run `fnm use --install-if-missing 20`, or update the requirement."
