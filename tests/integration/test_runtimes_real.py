"""Real tools, no fakes: checks each installed runtime's actual `--version` output parses.

Tools that are not installed are skipped. On CI each runtime is announced as a GitHub
annotation (::notice) so the run shows which ones were actually exercised.
"""

import os
import re
import shutil

import pytest

from devready.checks.runtimes import RUNTIMES, check_runtimes
from devready.models import Status

ON_CI = os.environ.get("CI") == "true"


def announce(capsys, text):
    if ON_CI:
        with capsys.disabled():
            print()  # the runner only parses a command that starts its own line
            print(f"::notice title=devready runtime::{text}")


@pytest.mark.parametrize("key", sorted(RUNTIMES))
def test_real_version_output_is_parsed(key, tmp_path, capsys):
    title, exe, _, _, tv_name, _ = RUNTIMES[key]
    if not shutil.which(exe):
        announce(capsys, f"{key}: not installed")
        pytest.skip(f"{exe} not installed")
    (tmp_path / ".tool-versions").write_text(f"{tv_name} >=0\n")  # any real version satisfies
    version, pin = check_runtimes(tmp_path)
    if version.status is Status.ERROR and "failed" in version.summary:
        announce(capsys, f"{key}: installed but its version command fails")
        pytest.skip(f"{exe} is installed without a working version command")
    assert version.check_id == f"{key}.version" and version.status is Status.PASS
    assert re.fullmatch(r"\d+(\.\d+)+ found", version.summary), version.summary
    assert pin.check_id == f"project.{key}.tool_versions" and pin.status is Status.PASS
    announce(capsys, f"{key}: {version.summary}")


def test_real_go_mod_minimum(tmp_path):
    if not shutil.which("go"):
        pytest.skip("go not installed")
    (tmp_path / "go.mod").write_text("module x\n\ngo 1.0\n")
    assert {r.check_id: r.status for r in check_runtimes(tmp_path)}["project.go.mod"] is Status.PASS
