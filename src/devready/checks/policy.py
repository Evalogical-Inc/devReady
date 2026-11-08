"""Org policy file (#44): one minimum toolchain for every repo, kept outside `.devready.json`.

{"policy_version": 1, "require": {"node": ">=20", "git": ">=2.40", "docker": "*"},
 "skip": ["platform.autocrlf"], "env": ["NPM_TOKEN"]}

Local files only, same read rules as project.py. A spec must be one the version matcher
understands, or "*" (installed, any version). An unreadable or invalid file gives one ERROR
result that never echoes the file's content or its path.
"""

from __future__ import annotations

import json
from pathlib import Path

from devready.checks.config import _ENV_NAME, _ID
from devready.checks.project import _read
from devready.checks.runtimes import RUNTIMES
from devready.checks.tools import TOOLS
from devready.models import Result, Status
from devready.versions import satisfies

REQUIRABLE = {tool[2] for tool in TOOLS} | set(RUNTIMES) | {"python", "docker"}


def _spec_ok(spec: object) -> bool:
    return isinstance(spec, str) and (spec == "*" or satisfies((0, 0, 0), spec) is not None)


def _valid(policy: object) -> bool:
    keys = {"policy_version", "require", "skip", "env"}
    if not isinstance(policy, dict) or not set(policy) <= keys:
        return False
    version = policy.get("policy_version")
    req, skip, env = policy.get("require", {}), policy.get("skip", []), policy.get("env", [])
    return (
        type(version) is int  # JSON true would equal 1
        and version == 1
        and isinstance(req, dict)
        and all(k in REQUIRABLE and _spec_ok(v) for k, v in req.items())
        and isinstance(skip, list)
        and all(isinstance(i, str) and _ID.match(i) for i in skip)
        and isinstance(env, list)
        and all(isinstance(n, str) and _ENV_NAME.match(n) for n in env)
    )


def _error(summary: str, suggestion: str) -> Result:
    return Result("policy.file", "Policy", Status.ERROR, summary, suggestion)


def load_policy(path: Path) -> tuple[dict | None, Result | None]:
    """(policy, None) if valid, else (None, one policy.file ERROR result)."""
    try:
        text = _read(path)
    except (OSError, ValueError):
        text = None
    if text is None:
        return None, _error(
            "Policy file is missing, not a regular file, or over 1 MB",
            "Check the --policy path or DEVREADY_POLICY. Symlinks are not followed.",
        )
    try:
        policy = json.loads(text.removeprefix("\ufeff"))
    except ValueError:
        policy = None
    if _valid(policy):
        return policy, None
    return None, _error(
        "Policy file is invalid; it was ignored",
        'Needs "policy_version": 1. Optional: "require" (tool: version spec or "*"), '
        '"skip" (check ids), "env" (variable names).',
    )
