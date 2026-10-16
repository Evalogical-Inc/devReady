"""Real-OS checks, no fakes. Strict only on CI runners, whose toolchains are known."""

import os
import sys

import pytest

from devready.checks.platform_checks import _long_paths_enabled, check_platform
from devready.models import Status

ON_CI = os.environ.get("CI") == "true"


@pytest.mark.skipif(sys.platform == "win32", reason="compiler lookup is for macOS/Linux")
def test_build_tools_real_lookup(tmp_path):
    (tmp_path / "setup.py").write_text("")
    (result,) = check_platform(tmp_path)
    assert result.check_id == "platform.build_tools"
    if ON_CI:  # GitHub's macOS and Ubuntu runners ship Xcode CLT / gcc + make
        assert result.status is Status.PASS


@pytest.mark.skipif(sys.platform != "win32", reason="Windows registry and PowerShell")
def test_windows_checks_real(tmp_path):
    assert isinstance(_long_paths_enabled(), bool)  # key exists on every supported Windows
    (tmp_path / "package.json").write_text("{}")
    known = {"platform.long_paths", "platform.exec_policy", "platform.autocrlf"}
    results = check_platform(tmp_path)
    assert {r.check_id for r in results} <= known
    assert all(r.status is Status.WARN for r in results)  # only warnings are ever emitted
