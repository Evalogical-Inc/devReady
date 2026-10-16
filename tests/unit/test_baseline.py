import json

from devready.baseline import diff, load_baseline
from devready.cli import main
from devready.models import Result, Status
from devready.runner import report


def res(cid, status):
    return Result(cid, cid, status, "s")


def save(path, results):
    path.write_text(json.dumps(report(results)))
    return path


def test_load_rejects_bad_files(tmp_path):
    assert load_baseline(tmp_path / "missing.json") is None
    for bad in ("{nope", "[]", '{"schema_version": 2, "results": []}', '{"schema_version": 1}'):
        (tmp_path / "b.json").write_text(bad)
        assert load_baseline(tmp_path / "b.json") is None
    (tmp_path / "b.json").write_text(
        json.dumps({"schema_version": 1, "results": [{"check_id": "Bad Id", "status": "pass"}]})
    )
    assert load_baseline(tmp_path / "b.json") == {}  # invalid ids are dropped, not echoed


def test_diff_changed_new_and_worse():
    base = {"a.x": Status.PASS, "b.x": Status.FAIL, "c.x": Status.WARN}
    now = [
        res("a.x", Status.PASS),  # unchanged
        res("b.x", Status.FAIL),  # unchanged failure: not a regression
        res("c.x", Status.FAIL),  # worse
        res("d.x", Status.WARN),  # new, not a fail
    ]
    changed, worse = diff(now, base)
    assert [r.check_id for r in changed] == ["c.x", "d.x"] and worse
    assert diff(now[:2], base) == ([], False)
    assert diff([res("e.x", Status.FAIL)], base)[1]  # new FAIL counts


def test_cli_baseline_exit_codes(tmp_path, capsys):
    base = save(tmp_path / "base.json", [res("python.version", Status.PASS)])
    assert main(["check", "--only", "python", "--baseline", str(base), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["results"] == []  # nothing changed
    broken = save(tmp_path / "old.json", [res("python.version", Status.FAIL)])
    assert main(["check", "--only", "python", "--baseline", str(broken)]) == 0
    assert main(["check", "--baseline", str(tmp_path / "missing.json")]) == 2
