import json

from devready.checks.config import check_config, load_config
from devready.cli import main
from devready.explain import EXPLANATIONS
from devready.models import Status
from devready.runner import run_checks


def write(tmp_path, cfg):
    (tmp_path / ".devready.json").write_text(cfg if isinstance(cfg, str) else json.dumps(cfg))


def test_absent_and_valid(tmp_path):
    assert load_config(tmp_path) == ({}, None)
    write(tmp_path, {"skip": ["project.ports"], "require": {"node": ">=20"}, "env": ["API_KEY"]})
    cfg, err = load_config(tmp_path)
    assert err is None and cfg["skip"] == ["project.ports"]


def test_invalid_is_one_error_and_never_echoed(tmp_path):
    for bad in (
        "{nope",
        "[]",
        {"unknown": 1},
        {"skip": "project"},
        {"skip": ["Bad Id; rm -rf"]},
        {"require": {"ruby": ">=3"}},
        {"require": {"node": "PWNED-MARKER; curl x"}},
        {"env": ["bad name"]},
    ):
        write(tmp_path, bad)
        cfg, err = load_config(tmp_path)
        assert cfg is None and err.status is Status.ERROR
        assert "PWNED" not in str(err) and "rm -rf" not in str(err)


def test_require_and_env(tmp_path):
    cfg = {"require": {"node": ">=20", "python": ">=3.99"}, "env": ["A_SET", "B_MISSING"]}
    r = {x.check_id: x for x in check_config(cfg, "18.0.0", "3.12.0", {"A_SET": "hunter2"})}
    assert r["project.node.config"].status is Status.FAIL
    assert r["project.python.config"].status is Status.FAIL
    assert r["project.env.required"].status is Status.FAIL
    assert "B_MISSING" in r["project.env.required"].summary
    assert "hunter2" not in str(r)
    ok = check_config({"env": ["A"]}, None, "3.12.0", {"A": "x"})
    assert ok[0].status is Status.PASS


def test_run_checks_applies_skip_and_requirements(tmp_path):
    write(tmp_path, {"skip": ["git", "disk"], "require": {"python": ">=99"}})
    ids = {r.check_id: r for r in run_checks(tmp_path)}
    assert "git.version" not in ids and "disk.space" not in ids and "git.identity" not in ids
    assert ids["project.python.config"].status is Status.FAIL


def test_init_prints_valid_config_and_writes_nothing(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    write(tmp_path, capsys.readouterr().out)  # the test writes it, init does not
    assert load_config(tmp_path)[1] is None


def test_ids_have_explanations():
    for cid in ("project.config.file", "project.node.config", "project.python.config",
                "project.env.required"):  # fmt: skip
        assert cid in EXPLANATIONS
