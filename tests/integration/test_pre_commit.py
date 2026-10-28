"""Exercise the packaged hook in disposable Git repositories and Python environments."""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIN = "project.python.requires"


@dataclass
class HookRepo:
    source: Path
    revision: str
    env: dict = field(repr=False)


def command(argv, cwd, env):
    return subprocess.run(
        argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=180, errors="replace"
    )


def git(cwd, env, *args):
    result = command(["git", *args], cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


@pytest.fixture(scope="module")
def hook_repo(tmp_path_factory):
    work = tmp_path_factory.mktemp("pre-commit")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key not in {"PYTHONHOME", "PYTHONPATH", "SKIP"}
    }
    env.update(
        PRE_COMMIT_HOME=str(work / "cache"),
        PIP_CACHE_DIR=str(work / "pip-cache"),
        VIRTUALENV_OVERRIDE_APP_DATA=str(work / "virtualenv"),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )
    source = work / "source"
    source.mkdir()
    for name in (".pre-commit-hooks.yaml", "pyproject.toml", "README.md", "LICENSE"):
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, source / name)
    shutil.copytree(ROOT / "src", source / "src", ignore=shutil.ignore_patterns("__pycache__"))
    git(source, env, "init")
    git(source, env, "add", ".")
    git(source, env, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "Hook snapshot")  # fmt: skip
    return HookRepo(source, git(source, env, "rev-parse", "HEAD"), env)


@pytest.fixture
def project(tmp_path, hook_repo):
    env = hook_repo.env
    git(tmp_path, env, "init")
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.8"\n')
    (tmp_path / "not-a-cli-argument.txt").write_text("fixture\n")
    git(tmp_path, env, "add", ".")
    return tmp_path


def configure(project, hook_repo, args=(), **options):
    config = {"repos": [{"repo": str(hook_repo.source), "rev": hook_repo.revision, "hooks": [
        {"id": "devready", "args": ["--format", "json", *args], **options}
    ]}]}  # fmt: skip
    (project / ".pre-commit-config.yaml").write_text(json.dumps(config))


def run_hook(project, hook_repo, stage="pre-push"):
    return command(
        [
            sys.executable,
            "-m",
            "pre_commit",
            "run",
            "devready",
            "--all-files",
            "--hook-stage",
            stage,
            "--verbose",
        ],  # fmt: skip
        project,
        hook_repo.env,
    )


def report(result, expected):
    output = result.stdout + result.stderr
    assert result.returncode == expected, output
    assert "Skipped" not in output, output
    start = output.find('{\n  "schema_version"')
    assert start >= 0, output  # a successful pre-commit exit alone could mean no hook ran
    data, _ = json.JSONDecoder().raw_decode(output[start:])
    return {r["check_id"]: r["status"] for r in data["results"]}


def test_try_repo_runs_packaged_hook(project, hook_repo):
    result = command(
        [
            sys.executable,
            "-m",
            "pre_commit",
            "try-repo",
            str(hook_repo.source),
            "devready",
            "--all-files",
            "--hook-stage",
            "pre-push",
            "--verbose",
        ],  # fmt: skip
        project,
        hook_repo.env,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "DevReady - Environment Check" in output and "0 failed" in output


def test_passes_without_passing_filenames(project, hook_repo):
    configure(project, hook_repo)
    assert report(run_hook(project, hook_repo), 0)[PIN] == "pass"


@pytest.mark.parametrize(
    ("args", "exit_code", "pin_status"),
    [
        ([], 1, "fail"),
        (["--only", "python"], 0, None),
        (["--skip", PIN], 0, None),
        (["--only", PIN, "--baseline", "baseline.json"], 0, None),
    ],
    ids=["unmet-requirement", "only", "skip", "baseline"],
)
def test_failure_and_args(project, hook_repo, args, exit_code, pin_status):
    (project / "pyproject.toml").write_text('[project]\nrequires-python = ">=99"\n')
    (project / "baseline.json").write_text(
        json.dumps({"schema_version": 1, "results": [{"check_id": PIN, "status": "fail"}]})
    )
    configure(project, hook_repo, args)
    results = report(run_hook(project, hook_repo), exit_code)
    assert results.get(PIN) == pin_status
    if "--only" in args:
        assert results == ({} if "--baseline" in args else {"python.version": "pass"})


def test_missing_baseline_is_usage_error(project, hook_repo):
    configure(project, hook_repo, ["--baseline", "missing.json"])
    result = run_hook(project, hook_repo)
    assert result.returncode == 1
    assert "exit code: 2" in result.stdout
    assert "baseline is not a readable devready JSON report" in result.stdout


def test_always_runs_without_tracked_files(project, hook_repo):
    git(project, hook_repo.env, "rm", "--cached", "-r", ".")
    assert git(project, hook_repo.env, "ls-files") == ""
    configure(project, hook_repo)
    assert report(run_hook(project, hook_repo), 0)[PIN] == "pass"


def test_default_stage_and_override(project, hook_repo):
    configure(project, hook_repo)
    result = run_hook(project, hook_repo, "pre-commit")
    assert result.returncode == 1
    assert "No hook with id" in result.stdout and "pre-commit" in result.stdout
    configure(project, hook_repo, stages=["pre-commit"])
    assert report(run_hook(project, hook_repo, "pre-commit"), 0)[PIN] == "pass"


def test_installed_hook_blocks_push_on_unmet_requirement(project, hook_repo, tmp_path):
    env = hook_repo.env
    configure(project, hook_repo, verbose=True)
    result = command(
        [sys.executable, "-m", "pre_commit", "install", "--hook-type", "pre-push"],
        project,
        env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / ".git" / "hooks" / "pre-push").is_file()
    remote = tmp_path / "remote.git"
    git(project, env, "init", "--bare", str(remote))
    git(project, env, "remote", "add", "origin", str(remote))

    def commit():
        git(project, env, "add", "pyproject.toml", ".pre-commit-config.yaml")
        git(project, env, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-m", "Project requirement")  # fmt: skip

    commit()
    passed = command(["git", "push", "origin", "HEAD:refs/heads/test"], project, env)
    assert report(passed, 0)[PIN] == "pass"
    accepted = git(project, env, "rev-parse", "HEAD")
    (project / "pyproject.toml").write_text('[project]\nrequires-python = ">=99"\n')
    commit()
    failed = command(["git", "push", "origin", "HEAD:refs/heads/test"], project, env)
    assert report(failed, 1)[PIN] == "fail"
    assert git(remote, env, "rev-parse", "refs/heads/test") == accepted
