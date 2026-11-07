"""Org policy file (#44): one minimum toolchain for every repo, kept outside `.devready.json`.

{"policy_version": 1, "require": {"node": ">=20", "git": ">=2.40", "docker": "*"},
 "skip": ["platform.autocrlf"], "env": ["NPM_TOKEN"]}

Local files only, same read rules as project.py. A spec must be one the version matcher
understands, or "*" (installed, any version). An unreadable or invalid file gives one ERROR
result that never echoes the file's content or its path.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path

from devready.checks.config import _ENV_NAME, _ID
from devready.checks.extras import DOCKER_DOCS
from devready.checks.project import _compare, _read
from devready.checks.python_check import DOCS as PYTHON_DOCS
from devready.checks.runtimes import RUNTIMES
from devready.checks.tools import TOOLS, check_tool
from devready.models import Result, Status
from devready.versions import parse_version, satisfies

# key -> (title, executable, version args, docs)
_TOOLS = {exe: (title, exe, ("--version",), docs) for _, title, exe, docs in TOOLS}
_TOOLS |= {key: row[:4] for key, row in RUNTIMES.items()}
_TOOLS |= {
    "python": ("Python", "python", ("--version",), PYTHON_DOCS),
    "docker": ("Docker", "docker", ("--version",), DOCKER_DOCS),
}
REQUIRABLE = set(_TOOLS)


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


def check_policy(
    policy: dict,
    versions: Mapping[str, str | None],
    tool: Callable = check_tool,
    environ: Mapping[str, str] = os.environ,
) -> list[Result]:
    """policy.<tool>.require and policy.env.required results. Known versions are reused."""
    out: list[Result] = []
    for key, spec in policy.get("require", {}).items():
        title, exe, args, docs = _TOOLS[key]
        cid, name = f"policy.{key}.require", f"{title} (policy)"
        ver = (
            versions[key] if key in versions else tool(f"{key}.version", title, exe, docs, args)[1]
        )
        if ver is None:
            out.append(
                Result(
                    cid,
                    name,
                    Status.FAIL,
                    "Required by policy; not found",
                    f"Install {title}.",
                    docs,
                )
            )
        elif spec == "*":
            out.append(Result(cid, name, Status.PASS, f"{ver} found (policy: any version)"))
        else:
            out.append(
                _compare(cid, name, "policy", spec, parse_version(ver), Status.FAIL, runtime=key)
            )
    wanted = policy.get("env", [])
    if wanted:
        missing = [n for n in wanted if n not in environ]
        cid, name = "policy.env.required", "Required env (policy)"
        if missing:
            summary = f"{len(missing)} of {len(wanted)} not set: {', '.join(missing[:10])}"
            tip = "Set these variables in your shell or CI (values are never read)."
            out.append(Result(cid, name, Status.FAIL, summary, tip))
        else:
            out.append(Result(cid, name, Status.PASS, f"all {len(wanted)} variables are set"))
    return out
