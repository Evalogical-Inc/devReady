"""Go, Ruby, Java, Rust, .NET, pnpm, Yarn, Bun: checked only when the project pins them.

Same read-only rules as project.py. Only digits/validated specs ever reach the report.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from devready.checks.project import _compare, _read
from devready.checks.tools import check_tool
from devready.models import Result, Status
from devready.versions import parse_version


def _first_version(text: str) -> str | None:
    m = re.search(r"\d+(?:\.\d+){0,2}", text.strip().split("\n", 1)[0])
    return m.group() if m else None


def _go_mod(text: str) -> str | None:
    m = re.search(r"^go\s+(\d+(?:\.\d+){1,2})", text, re.M)
    return f">={m.group(1)}" if m else None


def _gemfile(text: str) -> str | None:
    # Recognize a literal declaration only; never evaluate Ruby or return other file content.
    m = re.search(
        r"""^[ \t]*ruby[ \t]+(["'])([0-9]+(?:\.[0-9]+){1,2})\1[ \t]*(?:\#[^\r\n]*)?\r?$""",
        text,
        re.M,
    )
    return m.group(2) if m else None


def _rust(text: str) -> str | None:
    m = re.search(r"^\s*channel\s*=\s*[\"']([^\"']*)[\"']", text, re.M)
    return m.group(1) if m else text.strip().split("\n", 1)[0] or None


def _global_json(text: str) -> str | None:
    try:
        spec = json.loads(text).get("sdk", {}).get("version")
    except (ValueError, AttributeError):
        return None
    return spec if isinstance(spec, str) else None


def _pkg_manager(name: str) -> Callable[[str], str | None]:
    def extract(text: str) -> str | None:
        try:
            value = json.loads(text).get("packageManager")
        except (ValueError, AttributeError):
            return None
        m = (
            re.fullmatch(rf"{name}@(\d+(?:\.\d+){{0,2}})(?:\+.*)?", value)
            if isinstance(value, str)
            else None
        )
        return m.group(1) if m else None

    return extract


# key -> (title, exe, version args, docs, .tool-versions name, [(id, file, extractor, miss)])
RUNTIMES: dict[str, tuple] = {
    "go": ("Go", "go", ("version",), "https://go.dev/doc/install", "golang",
           [("project.go.mod", "go.mod", _go_mod, Status.FAIL)]),
    "ruby": ("Ruby", "ruby", ("--version",), "https://www.ruby-lang.org/en/downloads/", "ruby",
             [("project.ruby.pin", ".ruby-version", _first_version, Status.WARN),
              ("project.ruby.gemfile", "Gemfile", _gemfile, Status.WARN)]),
    "java": ("Java", "java", ("-version",), "https://adoptium.net/", "java",
             [("project.java.pin", ".java-version", _first_version, Status.WARN)]),
    "rust": ("Rust", "rustc", ("--version",), "https://rustup.rs/", "rust",
             [("project.rust.toolchain", "rust-toolchain.toml", _rust, Status.WARN),
              ("project.rust.toolchain", "rust-toolchain", _rust, Status.WARN)]),
    "dotnet": ("dotnet", "dotnet", ("--version",), "https://dotnet.microsoft.com/download",
               "dotnet", [("project.dotnet.global", "global.json", _global_json, Status.WARN)]),
    # packageManager in package.json pins one manager, e.g. "pnpm@9.1.0"
    "pnpm": ("pnpm", "pnpm", ("--version",), "https://pnpm.io/installation", "pnpm",
             [("project.pnpm.pin", "package.json", _pkg_manager("pnpm"), Status.WARN)]),
    "yarn": ("Yarn", "yarn", ("--version",), "https://yarnpkg.com/getting-started/install", "yarn",
             [("project.yarn.pin", "package.json", _pkg_manager("yarn"), Status.WARN)]),
    "bun": ("Bun", "bun", ("--version",), "https://bun.sh/docs/installation", "bun",
            [("project.bun.pin", "package.json", _pkg_manager("bun"), Status.WARN)]),
}  # fmt: skip


def check_runtimes(
    root: Path, tool: Callable = check_tool, runtimes: dict[str, tuple] = RUNTIMES
) -> list[Result]:
    tv = _read(root / ".tool-versions") or ""
    tv_pins = {p[0]: p[1] for line in tv.splitlines() if len(p := line.split("#")[0].split()) >= 2}
    out: list[Result] = []
    for key, (title, exe, args, docs, tv_name, pins) in runtimes.items():
        found: list[tuple[str, str, str, Status]] = []
        for cid, fname, extract, miss in pins:
            text = _read(root / fname)
            if text is not None and (spec := extract(text)):
                found.append((cid, fname, spec, miss))
                break
        if tv_name in tv_pins:
            found.append((f"project.{key}.tool_versions", ".tool-versions", tv_pins[tv_name],
                          Status.WARN))  # fmt: skip
        if not found:
            continue
        res, ver = tool(f"{key}.version", title, exe, docs, args)
        out.append(res)
        v = parse_version(ver) if ver else None
        out += [_compare(c, f"{title} pin", src, spec, v, miss) for c, src, spec, miss in found]
    return out
