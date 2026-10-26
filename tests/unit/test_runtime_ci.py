"""Required CI runtimes must fail visibly without depending on installed tools."""

import runpy
from pathlib import Path

import pytest

from devready.models import Result, Status


@pytest.mark.parametrize("missing", [True, False], ids=["missing", "broken"])
@pytest.mark.parametrize(
    ("ci", "key", "outcome"),
    [
        (True, "pnpm", AssertionError),
        (True, "bun", AssertionError),
        (True, "java", pytest.skip.Exception),
        (False, "pnpm", pytest.skip.Exception),
        (False, "bun", pytest.skip.Exception),
    ],
)
def test_required_runtime_failure(ci, key, outcome, missing, monkeypatch, tmp_path, capsys):
    module = runpy.run_path(
        str(Path(__file__).parents[1] / "integration" / "test_runtimes_real.py")
    )
    check = module["test_real_version_output_is_parsed"]
    monkeypatch.setitem(check.__globals__, "ON_CI", ci)
    monkeypatch.setattr(module["shutil"], "which", lambda exe: None if missing else exe)
    monkeypatch.setitem(
        check.__globals__,
        "check_runtimes",
        lambda root: [
            Result(f"{key}.version", key, Status.ERROR, "Version command failed"),
            Result(f"project.{key}.tool_versions", key, Status.SKIP, "Not evaluated"),
        ],
    )
    try:
        with pytest.raises(outcome, match=key):
            check(key, tmp_path, capsys)
    except pytest.skip.Exception:
        pytest.fail(f"{key} unexpectedly skipped instead of failing")
