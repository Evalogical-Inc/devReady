"""Exact version-switch commands for suggestions, from the version managers found on PATH.

Managers are only looked up with shutil.which; DevReady never runs them. A command is offered
only for a plain version (20, v20.11.0, 3.12.1) and echoes just its digits; ranges get None.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable

_PLAIN = re.compile(r"v?(\d+(?:\.\d+){0,2})")

# runtime key (as in project.py PINS / runtimes.py RUNTIMES) -> [(exe on PATH, template)].
# First manager found wins. Add one row per manager; {v} is the pinned version.
MANAGERS: dict[str, list[tuple[str, str]]] = {
    "node": [("fnm", "fnm use --install-if-missing {v}")],
}


def command(
    runtime: str, spec: str, which: Callable[[str], str | None] | None = None
) -> str | None:
    m = _PLAIN.fullmatch(spec.strip())
    if not m:
        return None
    for exe, template in MANAGERS.get(runtime, []):
        if (which or shutil.which)(exe):
            return template.format(v=m.group(1))
    return None
