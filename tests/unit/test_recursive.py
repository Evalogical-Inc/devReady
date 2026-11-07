"""devready check --recursive (#43): machine-wide checks once, project checks per package."""

import json
from pathlib import Path

import jsonschema
import pytest

from devready import runner
from devready.cli import main
from devready.models import Result, Status

DOCS = Path(__file__).parents[2] / "docs"
SINGLE = json.loads((DOCS / "schema.json").read_text())
MULTI = json.loads((DOCS / "schema-multi.json").read_text())


def write(root, rel, text=""):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "package.json", json.dumps({"workspaces": ["packages/*"]}))
    write(tmp_path, "packages/web/package.json", "{}")
    # A required env var nobody sets: a FAIL on every machine, only in packages/web.
    write(tmp_path, "packages/web/.devready.json", '{"env": ["DEVREADY_TEST_NEVER_SET"]}')
    write(tmp_path, "packages/api/pyproject.toml")
    write(tmp_path, "packages/api/.env.example", "API_KEY=\n")  # no .env: a WARN on every machine
    return tmp_path


@pytest.fixture
def fake_checks(monkeypatch):
    """Machine-wide: one Git result. Per package: one result, FAIL only for the `web` folder."""

    def project(root, versions, machine=()):
        status = Status.FAIL if root.name == "web" else Status.PASS
        return [*machine, Result("project.x", f"Pin {root.name}", status, "summary")]

    git = Result("git.version", "Git", Status.PASS, "2.45.0 found")
    monkeypatch.setattr(runner, "machine_checks", lambda root: ([git], {}))
    monkeypatch.setattr(runner, "project_checks", project)


def run(capsys, *args):
    code = main(["check", "--recursive", *args])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_json_has_one_project_per_package_and_matches_schema_multi(repo, capsys):
    code, out, _ = run(capsys, "--format", "json", "--project", str(repo))
    data = json.loads(out)
    jsonschema.validate(data, MULTI)
    ids = {p["path"]: {r["check_id"]: r["status"] for r in p["results"]} for p in data["projects"]}
    assert list(ids) == [".", "packages/api", "packages/web"]
    assert "git.version" in ids["."] and "git.version" not in ids["packages/web"]  # once
    assert ids["packages/api"]["project.env.keys"] == "warn"  # project checks run per package
    assert "project.env.keys" not in ids["."]
    assert ids["packages/web"]["project.env.required"] == "fail"  # the package's own config
    assert "project.env.required" not in ids["."]
    assert code == 1


def test_multi_schema_reuses_the_frozen_result_shape():
    assert MULTI["properties"]["schema_version"] == {"const": 1}
    project = MULTI["properties"]["projects"]["items"]
    assert project["properties"]["results"] == SINGLE["properties"]["results"]


def test_without_the_flag_json_keeps_the_single_project_shape(repo, capsys):
    main(["check", "--format", "json", "--project", str(repo)])
    jsonschema.validate(json.loads(capsys.readouterr().out), SINGLE)


def test_text_has_a_section_per_package(repo, fake_checks, capsys):
    code, out, _ = run(capsys, "--project", str(repo))
    root, api, web = (
        out.index("-- . (root) --"),
        out.index("-- packages/api --"),
        out.index("-- packages/web --"),
    )
    assert root < out.index("[PASS ] Git") < api < web < out.index("[FAIL ] Pin web")
    assert "3 passed, 0 warnings, 1 failed across 3 packages" in out  # Git + 3 pins
    assert code == 1


def test_quiet_hides_packages_with_nothing_to_report(repo, fake_checks, capsys):
    _, out, _ = run(capsys, "--quiet", "--project", str(repo))
    assert "-- packages/web --" in out and "[FAIL ] Pin web" in out
    assert "-- packages/api --" not in out and "-- . (root) --" not in out


def test_only_and_skip_apply_to_every_package(repo, fake_checks, capsys):
    code, out, _ = run(capsys, "--format", "json", "--skip", "project", "--project", str(repo))
    projects = json.loads(out)["projects"]
    ids = {p["path"]: [r["check_id"] for r in p["results"]] for p in projects}
    assert ids == {".": ["git.version"], "packages/api": [], "packages/web": []}
    assert code == 0


def test_packages_past_the_limit_are_reported_not_silently_dropped(tmp_path, fake_checks, capsys):
    write(tmp_path, "package.json", json.dumps({"workspaces": ["packages/*"]}))
    for i in range(205):
        write(tmp_path, f"packages/p{i:03}/package.json", "{}")
    _, out, err = run(capsys, "--format", "json", "--project", str(tmp_path))
    assert len(json.loads(out)["projects"]) == 200
    assert "206 packages" in err and "first 200" in err


@pytest.mark.parametrize(
    "extra", [["--format", "junit"], ["--format", "sarif"], ["--baseline", "b.json"]]
)
def test_formats_not_supported_yet_are_a_usage_error(tmp_path, extra, capsys):
    code, out, err = run(capsys, "--project", str(tmp_path), *extra)
    assert code == 2 and out == "" and "--recursive" in err


def test_machine_results_that_repeat_across_packages_are_shown_once(repo, monkeypatch, capsys):
    def project(root, versions, machine=()):
        python = "3.12.1 found (.venv/bin/python)" if root.name == "api" else "3.12.1 found"
        return [
            Result("python.version", "Python", Status.PASS, python),
            Result("docker.daemon", "Docker daemon", Status.WARN, "not reachable"),
            Result("project.x", "Pin", Status.PASS, "same summary in every package"),
        ]

    monkeypatch.setattr(runner, "machine_checks", lambda root: ([], {}))
    monkeypatch.setattr(runner, "project_checks", project)
    _, out, _ = run(capsys, "--format", "json", "--project", str(repo))
    projects = json.loads(out)["projects"]
    assert {p["path"]: [r["check_id"] for r in p["results"]] for p in projects} == {
        ".": ["python.version", "docker.daemon", "project.x"],
        "packages/api": ["python.version", "project.x"],  # its own .venv: a different result
        "packages/web": ["project.x"],  # project results always stay
    }
