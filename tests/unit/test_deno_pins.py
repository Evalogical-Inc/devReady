import pytest

from devready.checks.runtimes import check_runtimes
from devready.explain import EXPLANATIONS
from devready.models import Result, Status


@pytest.mark.parametrize(
    "source,cid", [(".dvmrc", "project.deno.pin"), (".tool-versions", "project.deno.tool_versions")]
)
@pytest.mark.parametrize(
    "installed,status", [("1.44.0", Status.PASS), ("1.0.0", Status.WARN), (None, Status.SKIP)]
)
def test_declared_version(tmp_path, source, cid, installed, status):
    (tmp_path / source).write_text("deno 1.44.0\n" if source == ".tool-versions" else "1.44.0\n")
    calls = []

    def tool(check_id, title, exe, docs, args):
        calls.append((exe, args))
        return Result(check_id, title, Status.PASS if installed else Status.WARN, "tool"), installed

    results = {r.check_id: r for r in check_runtimes(tmp_path, tool)}
    assert calls == [("deno", ("--version",))]
    assert set(results) == {"deno.version", cid}
    assert results[cid].status is status
    assert "1.44.0" in results[cid].summary
    if installed:
        assert installed in results[cid].summary
    assert all(k in EXPLANATIONS for k in results)


@pytest.mark.parametrize("content", [None, "latest", "min-required", "# no numeric version"])
def test_no_version_does_not_probe(tmp_path, content):
    if content is not None:
        (tmp_path / ".dvmrc").write_text(content)

    def unexpected(*args):
        pytest.fail("No version pin should mean no runtime probe")

    assert check_runtimes(tmp_path, unexpected) == []


def test_pin_content_not_echoed(tmp_path):
    (tmp_path / ".dvmrc").write_text("1.44.0 DO_NOT_REPORT\n")

    def tool(cid, title, *args):
        return Result(cid, title, Status.WARN, "missing"), None

    results = check_runtimes(tmp_path, tool)
    assert "DO_NOT_REPORT" not in str(results)
    assert results[-1].status is Status.SKIP
