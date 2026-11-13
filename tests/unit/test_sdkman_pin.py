import pytest

from devready.checks.runtimes import _sdkman, check_runtimes
from devready.models import Result, Status


@pytest.mark.parametrize(
    "text,expected",
    [
        ("java=21.0.2-tem", "21.0.2"),
        ("# java=17-tem\ngradle=8.7\njava=21.0.2-graal\n", "21.0.2"),
        ("  java = 21.0.2-tem # note\r\n", "21.0.2"),
        ("gradle=8.7", None),
        ("# java=21", None),
        ("java=$SECRET", None),
        ("java=21.0.2;run_secret", None),
        ("java=21.0.2.3", None),
        ("notjava=21", None),
    ],
)
def test_extract_java_only(text, expected):
    assert _sdkman("java")(text) == expected


@pytest.mark.parametrize(
    "installed,status", [("21.0.2", Status.PASS), ("17.0.1", Status.WARN), (None, Status.SKIP)]
)
def test_sdkman_version_result(tmp_path, installed, status):
    (tmp_path / ".sdkmanrc").write_text("java=21.0.2-tem\n# DO_NOT_REPORT\n")

    def tool(cid, title, exe, docs, args):
        assert exe == "java" and args == ("-version",)
        return Result(cid, title, Status.PASS if installed else Status.WARN, "tool"), installed

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert results["project.java.sdkman"].status is status
    assert "21.0.2" in results["project.java.sdkman"].summary
    assert "DO_NOT_REPORT" not in str(results)
    (tmp_path / ".java-version").write_text("17\n")
    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert "project.java.pin" in results
    assert "project.java.sdkman" not in results


def test_no_java_does_not_probe(tmp_path):
    (tmp_path / ".sdkmanrc").write_text("gradle=8.7\n")

    def unexpected(*args):
        pytest.fail("No Java pin should mean no probe")

    assert check_runtimes(tmp_path, unexpected) == []
