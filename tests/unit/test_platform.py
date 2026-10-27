from types import SimpleNamespace

from devready.checks.platform_checks import check_platform
from devready.explain import EXPLANATIONS
from devready.models import Status


def proc(out="", rc=0):
    return SimpleNamespace(stdout=out, returncode=rc)


def ids(results):
    return {r.check_id: r for r in results}


def win(tmp_path, policy="Restricted", long_paths=False, autocrlf="", have=("powershell", "git")):
    def run(argv):
        return proc(policy if "Get-ExecutionPolicy" in argv else autocrlf)

    return check_platform(
        tmp_path,
        "win32",
        run,
        lambda n: n if n in have else None,
        lambda: long_paths,
    )


def test_windows_only_when_relevant(tmp_path):
    assert win(tmp_path) == []  # no package.json, no .git
    (tmp_path / "package.json").write_text("{}")
    r = ids(win(tmp_path))
    assert r["platform.long_paths"].status is Status.WARN
    assert (
        r["platform.exec_policy"].status is Status.WARN
        and "Restricted" in r["platform.exec_policy"].summary
    )
    assert win(tmp_path, "RemoteSigned", True) == []
    assert win(tmp_path, "Weird; rm -rf", True) == []  # unrecognized output is never echoed
    assert (
        win(tmp_path, "Restricted", None, have=("git",)) == []
    )  # unknown registry / no powershell


def test_windows_autocrlf(tmp_path):
    (tmp_path / ".git").mkdir()
    assert ids(win(tmp_path))["platform.autocrlf"].status is Status.WARN
    assert win(tmp_path, autocrlf="true") == []
    (tmp_path / ".gitattributes").write_text("* text=auto\n")
    assert win(tmp_path) == []


def test_build_tools(tmp_path):
    assert check_platform(tmp_path, "linux", which=lambda n: None) == []  # nothing native
    (tmp_path / "setup.py").write_text("")
    none = check_platform(tmp_path, "linux", which=lambda n: None)
    assert none[0].status is Status.WARN
    have = check_platform(tmp_path, "linux", which=lambda n: n)
    assert have[0].status is Status.PASS
    ok = check_platform(tmp_path, "darwin", lambda a: proc(rc=0), lambda n: n)
    bad = check_platform(tmp_path, "darwin", lambda a: proc(rc=2), lambda n: n)
    assert (ok[0].status, bad[0].status) == (Status.PASS, Status.WARN)


def test_ids_have_explanations(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / ".git").mkdir()
    (tmp_path / "setup.py").write_text("")
    found = win(tmp_path) + check_platform(tmp_path, "linux", which=lambda n: None)
    assert len(found) == 4
    for r in found:
        assert r.check_id in EXPLANATIONS, r.check_id


def _utf16(text):
    # What `wsl -l -v` bytes look like after Python decodes them as UTF-8/cp1252.
    return text.encode("utf-16-le").decode("latin-1")


def test_wsl_version_only_with_docker(tmp_path):
    table = (
        "  NAME      STATE    VERSION\r\n"
        "* Ubuntu    Running  {v}\r\n"
        "  docker-desktop  Stopped  2\r\n"
    )

    def run_wsl(v, rc=0):
        def run(argv):
            return proc(_utf16(table.format(v=v)), rc) if argv[1:] == ["-l", "-v"] else proc()

        return check_platform(tmp_path, "win32", run, lambda n: n, lambda: True)

    assert run_wsl("1") == []  # no Docker files
    (tmp_path / "Dockerfile").write_text("FROM x\n")
    r = ids(run_wsl("1"))["platform.wsl.version"]
    assert r.status is Status.WARN and "Ubuntu" not in repr(r)
    assert ids(run_wsl("2"))["platform.wsl.version"].status is Status.PASS
    assert "platform.wsl.version" not in ids(run_wsl("2", rc=1))  # WSL not installed
    assert "platform.wsl.version" not in ids(run_wsl("x; rm -rf"))  # unrecognized
