from devready import runner
from devready.models import Result, Status


def test_pins_not_checked_against_devready_python_when_none_found(tmp_path, monkeypatch):
    warn = Result("python.version", "Python", Status.WARN, "Not found on PATH")
    monkeypatch.setattr(runner, "check_python", lambda root: (warn, None))
    (tmp_path / ".python-version").write_text("2.7\n")  # would FAIL against DevReady's own Python
    by_id = {r.check_id: r for r in runner.run_checks(tmp_path)}
    assert by_id["project.python.pin"].status is Status.SKIP
