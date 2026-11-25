"""Smoke-test a built binary: python packaging/smoke.py <path-to-binary>

Checks the things the 1.x rules in docs/versioning.md promise: `--version`, the JSON report shape
and statuses, and the exit codes (0 no blocking failure, 1 a fail, 2 usage error). Uses only the
standard library so it also runs on a machine whose Python is the system one.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

STATUSES = {"pass", "warn", "fail", "skip", "error"}
FIELDS = {"check_id", "title", "status", "summary", "suggestion", "docs_url"}
ID_RE = re.compile(r"^[a-z_]+(\.[a-z_]+)+$")


def clean_env() -> dict[str, str]:
    """Environment for the binary. With SMOKE_NO_PYTHON=1 the PATH holds only system folders, so the
    run proves the binary needs no Python (git is kept: DevReady checks for it)."""
    env = dict(os.environ)
    if os.environ.get("SMOKE_NO_PYTHON") == "1":
        if sys.platform == "win32":
            root = os.environ.get("SystemRoot", r"C:\Windows")
            env["PATH"] = os.pathsep.join([rf"{root}\System32", root, r"C:\Program Files\Git\cmd"])
        else:
            env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
    return env


def run(binary: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [binary, *args], capture_output=True, text=True, timeout=120, env=clean_env()
    )


def fail(msg: str) -> None:
    print(f"SMOKE FAIL: {msg}")
    sys.exit(1)


def main(binary: str) -> int:
    start = time.perf_counter()
    r = run(binary, "--version")
    cold = time.perf_counter() - start
    if r.returncode != 0 or not re.fullmatch(r"devready \d+\.\d+\.\d+\S*", r.stdout.strip()):
        fail(f"--version gave exit {r.returncode}, stdout {r.stdout!r}")
    print(f"ok  {r.stdout.strip()}  (cold start {cold:.2f}s)")

    with tempfile.TemporaryDirectory() as tmp:
        # A required env var that is never set: a declared requirement is a `fail`, so exit 1. It
        # needs no installed tool, so it also holds on a machine without Python or Node.
        cfg = '{"env": ["DEVREADY_SMOKE_MISSING_VAR"]}'
        Path(tmp, ".devready.json").write_text(cfg, encoding="utf-8")
        r = run(binary, "check", "--format", "json", "--project", tmp)
        if r.returncode != 1:
            fail(f"an unmet requirement should exit 1, got {r.returncode}: {r.stderr[:200]}")
        report = json.loads(r.stdout)
        if report.get("schema_version") != 1:
            fail(f"schema_version is {report.get('schema_version')!r}")
        results = report["results"]
        for res in results:
            if set(res) != FIELDS:
                fail(f"result fields {sorted(res)} differ from the schema")
            if res["status"] not in STATUSES:
                fail(f"unknown status {res['status']!r}")
            if not ID_RE.match(res["check_id"]):
                fail(f"bad check id {res['check_id']!r}")
        if not any(x["status"] == "fail" for x in results):
            fail("expected a fail result for the missing env var")
        print(f"ok  check --format json: {len(results)} results, exit 1 on a fail")

        Path(tmp, ".devready.json").unlink()
        r = run(binary, "check", "--format", "json", "--project", tmp, "--only", "git.version")
        if r.returncode not in (0, 1):
            fail(f"--only run exited {r.returncode}")
        json.loads(r.stdout)
        print("ok  check --only works")

    r = run(binary, "check", "--no-such-flag")
    if r.returncode != 2:
        fail(f"usage error should exit 2, got {r.returncode}")
    print("ok  usage error exits 2")
    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python packaging/smoke.py <path-to-binary>")
    sys.exit(main(sys.argv[1]))
