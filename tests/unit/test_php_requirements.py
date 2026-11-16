import pytest

from devready.checks.runtimes import check_runtimes
from devready.explain import EXPLANATIONS
from devready.models import Result, Status


@pytest.mark.parametrize(
    "installed,status", [("8.2.0", Status.PASS), ("7.4.0", Status.FAIL), (None, Status.SKIP)]
)
def test_requirement(tmp_path, installed, status):
    (tmp_path / "composer.json").write_text('{"require":{"php":"^8.1"}}')

    def tool(cid, title, exe, docs, args):
        assert exe == "php" and args == ("--version",)
        return Result(cid, title, Status.PASS if installed else Status.WARN, "tool"), installed

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert results["project.php.composer"].status is status
    assert all(cid in EXPLANATIONS for cid in results)
    assert "^8.1" in results["project.php.composer"].summary
    if installed:
        assert installed in results["project.php.composer"].summary


@pytest.mark.parametrize(
    "text",
    [
        None,
        "{",
        "[]",
        "null",
        '{"require": []}',
        '{"require":{"php": 81}}',
        '{"require-dev":{"php":"^8.1"}}',
        '{"require":{"php":"$(DO_NOT_REPORT)"}}',
    ],
)
def test_ignored_content_does_not_probe(tmp_path, text):
    if text is not None:
        (tmp_path / "composer.json").write_text(text)

    def unexpected(*args):
        pytest.fail("No supported requirement should mean no probe")

    assert check_runtimes(tmp_path, unexpected) == []


def test_tool_versions(tmp_path):
    (tmp_path / ".tool-versions").write_text("php 8.2.0\n")

    def tool(cid, title, *args):
        return Result(cid, title, Status.PASS, "tool"), "8.2.0"

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert results["project.php.tool_versions"].status is Status.PASS
    assert all(cid in EXPLANATIONS for cid in results)
