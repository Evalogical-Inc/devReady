"""Tiny version/range matcher for npm-style (engines) and PEP 440-style (requires-python) specs.

ponytail: handles >=,>,<=,<,==,!=,^,~,~= and bare/partial versions, joined by space/comma (AND)
or `||` (OR). Ignores pre-releases, 0.x caret rules and `~1.2` vs `~=1.2` differences.
Anything it cannot fully parse returns None ("could not evaluate"); upgrade to `packaging`
only if real projects hit this.
"""

from __future__ import annotations

import re

Version = tuple[int, ...]

# Spec text is echoed in reports, so only this charset is ever accepted (injection-safe).
SAFE_SPEC = re.compile(r"^[0-9A-Za-z.\s<>=!^~|,*-]{1,60}$")
_TERM = re.compile(r"(>=|<=|==|!=|~=|>|<|\^|~|=)?\s*v?(\d+(?:\.(?:\d+|x|\*))*)")


def parse_version(text: str) -> Version | None:
    m = re.match(r"v?(\d+(?:\.\d+){0,2})", text.strip())
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def _parts(raw: str) -> Version:
    out = []
    for p in raw.split("."):
        if not p.isdigit():
            break
        out.append(int(p))
    return tuple(out)


def _pad(v: Version) -> Version:
    return (v + (0, 0, 0))[:3]


def _term_ok(ver: Version, op: str, want: Version) -> bool:
    n = len(want)
    if op in ("", "=", "=="):
        return ver[:n] == want
    if op == "!=":
        return ver[:n] != want
    if op == "^":
        return _pad(ver) >= _pad(want) and ver[:1] == want[:1]
    if op in ("~", "~="):
        k = max(n - 1, 1)
        return _pad(ver) >= _pad(want) and ver[:k] == want[:k]
    a, b = _pad(ver), _pad(want)
    return {">=": a >= b, ">": a > b, "<=": a <= b, "<": a < b}[op]


def satisfies(version: Version, spec: str) -> bool | None:
    """True/False if `spec` is understood, None if not."""
    if not SAFE_SPEC.match(spec):
        return None
    ver = version
    results = []
    for alt in spec.split("||"):
        terms = list(_TERM.finditer(alt))
        if not terms or re.sub(r"[\s,]", "", _TERM.sub("", alt)):
            return None
        results.append(all(_term_ok(ver, m.group(1) or "", _parts(m.group(2))) for m in terms))
    return any(results)
