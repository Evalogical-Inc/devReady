"""run_checks = machine-wide checks (run once) + project checks (once per package, #43)."""

import pytest

from devready import runner
from devready.models import Result, Status

VERSIONS = {"git": "2.45.0", "node": "20.1.0"}
# Order users see (README sample): Python, then the other tools, then project pins.
ALL_IDS = [
    "python.version",
    "git.version", "node.version", "git.identity", "disk.free",  # machine-wide
    "project.x", "go.version", "health.x", "docker.daemon", "platform.x", "config.x",
]  # fmt: skip


def fake(cid):
    return Result(cid, cid, Status.PASS, "ok")


@pytest.fixture
def seen(monkeypatch):
    """Replace every check with a marker result; record the versions handed to version checks."""
    calls = {}

    def project(root, node, py):
        calls["project"] = (root, node, py)
        return [fake("project.x")]

    def config(cfg, node, py):
        calls["config"] = (node, py)
        return [fake("config.x")]

    monkeypatch.setattr(runner, "TOOLS", [("git.version", "Git", "git", "u"),
                                          ("node.version", "Node", "node", "u")])  # fmt: skip
    monkeypatch.setattr(runner, "check_tool", lambda *t: (fake(t[0]), VERSIONS[t[2]]))
    monkeypatch.setattr(runner, "check_python", lambda root: (fake("python.version"), "3.12.1"))
    monkeypatch.setattr(runner, "check_git_identity", lambda: [fake("git.identity")])
    monkeypatch.setattr(runner, "check_project", project)
    monkeypatch.setattr(runner, "check_runtimes", lambda root: [fake("go.version")])
    monkeypatch.setattr(runner, "check_health", lambda root: [fake("health.x")])
    monkeypatch.setattr(runner, "check_docker", lambda root: [fake("docker.daemon")])
    monkeypatch.setattr(runner, "check_platform", lambda root: [fake("platform.x")])
    monkeypatch.setattr(runner, "check_disk", lambda root: [fake("disk.free")])
    monkeypatch.setattr(runner, "check_config", config)
    return calls


def test_run_checks_runs_every_check_once_in_the_documented_order(tmp_path, seen):
    assert [r.check_id for r in runner.run_checks(tmp_path)] == ALL_IDS
    assert seen["project"] == (tmp_path, "20.1.0", "3.12.1")
    assert seen["config"] == ("20.1.0", "3.12.1")


def test_root_config_skip_also_hides_machine_wide_results(tmp_path, seen):
    (tmp_path / ".devready.json").write_text('{"skip": ["disk", "git.identity", "docker"]}')
    ids = {r.check_id for r in runner.run_checks(tmp_path)}
    assert ids == set(ALL_IDS) - {"disk.free", "git.identity", "docker.daemon"}


def test_machine_checks_are_the_ones_that_never_read_project_files(tmp_path, seen):
    results, versions = runner.machine_checks(tmp_path)
    assert [r.check_id for r in results] == ["git.version", "node.version", "git.identity",
                                             "disk.free"]  # fmt: skip
    assert versions == VERSIONS


def test_project_checks_use_given_versions_and_their_own_folder_config(tmp_path, seen):
    pkg = tmp_path / "packages" / "web"
    pkg.mkdir(parents=True)
    (pkg / ".devready.json").write_text('{"skip": ["docker"]}')
    results = runner.project_checks(pkg, {"node": "18.0.0"})
    assert {r.check_id for r in results} == {
        "python.version", "project.x", "go.version", "health.x", "platform.x", "config.x",
    }  # fmt: skip
    assert seen["project"] == (pkg, "18.0.0", "3.12.1")
    assert seen["config"] == ("18.0.0", "3.12.1")
