"""Optional `.devready.json`: extra requirements, required env var names, checks to skip.

{"skip": ["project.ports"], "require": {"node": ">=20", "python": ">=3.11"}, "env": ["API_KEY"]}

Read-only, same file rules as project.py. Env vars are tested for presence only; values are
never read. Invalid files give one ERROR result and never echo file content.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path

from devready.checks.project import _compare, _read
from devready.models import Result, Status
from devready.versions import SAFE_SPEC, parse_version

CONFIG_FILE = ".devready.json"
_ID = re.compile(r"^[a-z_]+(\.[a-z_]+)*$")
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_RUNTIMES = {"node": "Node", "python": "Python"}


def _valid(cfg: object) -> bool:
    if not isinstance(cfg, dict) or not set(cfg) <= {"skip", "require", "env"}:
        return False
    skip, req, env = cfg.get("skip", []), cfg.get("require", {}), cfg.get("env", [])
    return (
        isinstance(skip, list)
        and all(isinstance(i, str) and _ID.match(i) for i in skip)
        and isinstance(req, dict)
        and all(
            k in _RUNTIMES and isinstance(v, str) and SAFE_SPEC.match(v) for k, v in req.items()
        )
        and isinstance(env, list)
        and all(isinstance(n, str) and _ENV_NAME.match(n) for n in env)
    )


def load_config(root: Path) -> tuple[dict | None, Result | None]:
    """(config, None) if absent/valid ({} when absent), (None, error result) if invalid."""
    text = _read(root / CONFIG_FILE)
    if text is None:
        return {}, None
    try:
        cfg = json.loads(text)
    except ValueError:
        cfg = None
    if _valid(cfg):
        return cfg, None
    return None, Result(
        "project.config.file",
        "Config",
        Status.ERROR,
        f"{CONFIG_FILE} is invalid; it was ignored",
        'Allowed keys: "skip" (check ids), "require" (node/python specs), "env" (variable names).',
        file=CONFIG_FILE,
    )


def check_config(
    cfg: dict, node: str | None, python: str | None, environ: Mapping[str, str] = os.environ
) -> list[Result]:
    out: list[Result] = []
    versions = {
        "node": parse_version(node) if node else None,
        "python": parse_version(python or ""),
    }
    for key, spec in cfg.get("require", {}).items():
        out.append(
            _compare(
                f"project.{key}.config",
                f"{_RUNTIMES[key]} required",
                CONFIG_FILE,
                spec,
                versions[key],
                Status.FAIL,
                CONFIG_FILE,
                key,
            )
        )
    wanted = cfg.get("env", [])
    if wanted:
        missing = [n for n in wanted if n not in environ]
        cid, title = "project.env.required", "Required env"
        if missing:
            out.append(
                Result(
                    cid,
                    title,
                    Status.FAIL,
                    f"{len(missing)} of {len(wanted)} not set: {', '.join(missing[:10])}",
                    "Set these variables in your shell or CI (values are never read).",
                )
            )
        else:
            out.append(Result(cid, title, Status.PASS, f"all {len(wanted)} variables are set"))
    return out


# Empty on purpose: pre-filling "env" from .env.example would make optional variables fail.
TEMPLATE = json.dumps({"skip": [], "require": {}, "env": []}, indent=2)
