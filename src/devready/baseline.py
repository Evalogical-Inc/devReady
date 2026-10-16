"""Compare a run with a saved report (`devready check --format json > baseline.json`).

DevReady only reads the baseline; saving or committing it is up to you. That covers both a
shared team baseline (committed file) and diffing against an earlier local run.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from devready.checks.project import _read
from devready.models import Result, Status

_ID = re.compile(r"^[a-z_]+(\.[a-z_]+)+$")
_RANK = {Status.PASS: 0, Status.SKIP: 0, Status.WARN: 1, Status.ERROR: 2, Status.FAIL: 3}


def load_baseline(path: Path) -> dict[str, Status] | None:
    """check_id -> status, or None if the file is missing, too big, or not a v1 report."""
    text = _read(path)
    try:
        data = json.loads(text) if text else None
        if data["schema_version"] != 1:
            return None
        return {
            r["check_id"]: Status(r["status"])
            for r in data["results"]
            if isinstance(r["check_id"], str) and _ID.match(r["check_id"])
        }
    except (ValueError, KeyError, TypeError):
        return None


def diff(results: list[Result], base: dict[str, Status]) -> tuple[list[Result], bool]:
    """(results that are new or changed status, whether any FAIL got worse)."""
    changed = [r for r in results if base.get(r.check_id) is not r.status]
    worse = any(
        r.status is Status.FAIL and _RANK[r.status] > _RANK.get(base.get(r.check_id), 0)
        for r in changed
    )
    return changed, worse
