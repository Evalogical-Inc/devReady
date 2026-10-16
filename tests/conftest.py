"""On GitHub Actions, surface test failures as annotations (readable without a log login)."""

import os

ON_CI = os.environ.get("CI") == "true"


def pytest_runtest_logreport(report):
    if ON_CI and report.failed:
        last = report.longreprtext.strip().splitlines()[-6:]
        text = "%0A".join(line.replace("%", "%25").replace("\r", "")[:200] for line in last)
        # Leading newline: the runner only parses a command that starts its line.
        print(f"\n::error title=pytest failure::{report.nodeid}%0A{text}")
