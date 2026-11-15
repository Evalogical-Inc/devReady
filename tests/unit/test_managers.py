import pytest

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
    assert command("python", "3.12", ON_PATH) is None


def test_mismatch_suggests_command(tmp_path, monkeypatch):
    monkeypatch.setattr("devready.managers.shutil.which", ON_PATH)
    (tmp_path / ".nvmrc").write_text("20\n")
    r = project.check_project(tmp_path, "18.0.0", None)[0]
    assert r.status is Status.WARN
    assert r.suggestion == "Run `fnm use --install-if-missing 20`, or update the requirement."


@pytest.mark.parametrize(
    "runtime, manager, version, expected",
    [
        ("node", "nvm", "20", "nvm install 20 && nvm use 20"),
        ("python", "pyenv", "3.12", "pyenv install -s 3.12 && pyenv local 3.12"),
        ("node", "mise", "20", "mise use node@20"),
        ("python", "mise", "3.12", "mise use python@3.12"),
        ("node", "asdf", "20.11.0", "asdf install nodejs 20.11.0 && asdf set nodejs 20.11.0"),
        ("python", "asdf", "3.12.1", "asdf install python 3.12.1 && asdf set python 3.12.1"),
        ("node", "asdf", "20", "asdf install nodejs latest:20 && asdf set nodejs latest:20"),
        (
            "python",
            "asdf",
            "v3.12",
            "asdf install python latest:3.12 && asdf set python latest:3.12",
        ),
    ],
)
def test_supported_manager_present_and_absent(runtime, manager, version, expected):
    assert command(runtime, version, lambda exe: exe == manager) == expected
    assert command(runtime, version, lambda exe: None) is None


@pytest.mark.parametrize("runtime", ["node", "python"])
@pytest.mark.parametrize("spec", [">=20 <21", "3.12.*", "20; echo bad", "20\nwhoami", "$(id)"])
def test_non_plain_versions_never_look_up_managers(runtime, spec):
    def forbidden_lookup(exe):
        pytest.fail("Unsupported versions must not trigger manager lookup")

    assert command(runtime, spec, forbidden_lookup) is None


@pytest.mark.parametrize(
    "runtime, available, expected",
    [
        ("node", {"fnm", "nvm", "mise", "asdf"}, "fnm use --install-if-missing 20"),
        ("node", {"nvm", "mise", "asdf"}, "nvm install 20 && nvm use 20"),
        ("python", {"pyenv", "mise", "asdf"}, "pyenv install -s 20 && pyenv local 20"),
        ("node", {"mise", "asdf"}, "mise use node@20"),
        ("python", {"mise", "asdf"}, "mise use python@20"),
    ],
)
def test_first_available_manager_wins(runtime, available, expected):
    assert command(runtime, "20", available.__contains__) == expected


@pytest.mark.parametrize(
    "filename, version, manager, expected",
    [
        (".nvmrc", "20", "nvm", "nvm install 20 && nvm use 20"),
        (".python-version", "3.12", "pyenv", "pyenv install -s 3.12 && pyenv local 3.12"),
    ],
)
def test_project_pin_uses_manager_suggestion(
    tmp_path, monkeypatch, filename, version, manager, expected
):
    monkeypatch.setattr("devready.managers.shutil.which", lambda exe: exe == manager)
    (tmp_path / filename).write_text(version)
    result = project.check_project(tmp_path, "18.0.0", "3.10.0")[0]
    assert result.status is Status.WARN
    assert result.suggestion == f"Run `{expected}`, or update the requirement."
