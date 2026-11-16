import pytest

from devready.checks.runtimes import check_runtimes
from devready.explain import EXPLANATIONS
from devready.models import Result, Status


@pytest.mark.parametrize(
    "installed,status", [("3.2.0", Status.PASS), ("2.19.0", Status.FAIL), (None, Status.SKIP)]
)
def test_requirement(tmp_path, installed, status):
    (tmp_path / "pubspec.yaml").write_text('environment:\n  sdk: ">=3.0.0 <4.0.0"\n')

    def tool(cid, title, exe, docs, args):
        assert exe == "dart" and args == ("--version",)
        return Result(cid, title, Status.PASS if installed else Status.WARN, "tool"), installed

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert results["project.dart.pubspec"].status is status
    assert all(cid in EXPLANATIONS for cid in results)
    assert ">=3.0.0 <4.0.0" in results["project.dart.pubspec"].summary
    if installed:
        assert installed in results["project.dart.pubspec"].summary


@pytest.mark.parametrize(
    "text",
    [
        None,
        "dependencies:\n  flutter:\n    sdk: flutter\n",
        'environment:\n  flutter: ">=3.0.0"\ndependencies:\n  sdk: "^3.0"\n',
        'environment:\n  sdk: "$(DO_NOT_REPORT)"',
        'environment:\n  nested:\n    sdk: "^3.0"',
        "environment:\n  sdk: \"^3.0'",
    ],
)
def test_ignored_content_does_not_probe(tmp_path, text):
    if text is not None:
        (tmp_path / "pubspec.yaml").write_text(text)

    def unexpected(*args):
        pytest.fail("No supported requirement should mean no probe")

    assert check_runtimes(tmp_path, unexpected) == []


def test_tool_versions(tmp_path):
    (tmp_path / ".tool-versions").write_text("dart 3.2.0\n")

    def tool(cid, title, *args):
        return Result(cid, title, Status.PASS, "tool"), "3.2.0"

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert results["project.dart.tool_versions"].status is Status.PASS
    assert all(cid in EXPLANATIONS for cid in results)


@pytest.mark.parametrize(
    "value", [">=3.0.0 <4.0.0", "'>=3.0.0 <4.0.0'", '">=3.0.0 <4.0.0" # comment']
)
def test_quoted_and_unquoted_sdk(value):
    from devready.checks.runtimes import _pubspec_sdk

    assert _pubspec_sdk("environment:\n  # comment\n  sdk: " + value) == ">=3.0.0 <4.0.0"
