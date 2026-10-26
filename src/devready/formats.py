"""Extra output formats for CI: JUnit XML, SARIF 2.1.0, and the read-only fix plan."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from devready import __version__
from devready.models import Result, Status

_LEVEL = {Status.FAIL: "error", Status.ERROR: "error", Status.WARN: "warning"}


def junit(results: list[Result]) -> str:
    count = lambda *s: str(sum(r.status in s for r in results))  # noqa: E731
    suite = ET.Element(
        "testsuite",
        name="devready",
        tests=str(len(results)),
        failures=count(Status.FAIL),
        errors=count(Status.ERROR),
        skipped=count(Status.SKIP),
    )
    for r in results:
        case = ET.SubElement(suite, "testcase", classname="devready", name=r.check_id)
        if r.status is Status.FAIL:
            ET.SubElement(case, "failure", message=r.summary)
        elif r.status is Status.ERROR:
            ET.SubElement(case, "error", message=r.summary)
        elif r.status is Status.SKIP:
            ET.SubElement(case, "skipped", message=r.summary)
        elif r.status is Status.WARN:  # warnings do not fail the suite; keep them visible
            ET.SubElement(case, "system-out").text = f"WARN: {r.summary}"
    return ET.tostring(suite, encoding="unicode", xml_declaration=False)


def _location(r: Result, base: str) -> dict:
    # GitHub code scanning needs a start line; checks know the file, not the line
    uri = f"{base}/{r.file}" if base else r.file
    return {
        "physicalLocation": {
            "artifactLocation": {"uri": uri},
            "region": {"startLine": 1},
        }
    }


def sarif(results: list[Result], base: str = "") -> str:
    """`base` is the project directory relative to the repository root, as a POSIX path."""
    bad = [r for r in results if r.status in _LEVEL]
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "devready",
                        "version": __version__,
                        "rules": [
                            {"id": i, "shortDescription": {"text": i}}
                            for i in sorted({r.check_id for r in bad})
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": r.check_id,
                        "level": _LEVEL[r.status],
                        "message": {"text": f"{r.summary}. {r.suggestion}".strip()},
                        **({"locations": [_location(r, base)]} if r.file else {}),
                    }
                    for r in bad
                ],
            }
        ],
    }
    return json.dumps(doc, indent=2)


def fix_plan(results: list[Result]) -> str:
    """Suggested next steps only. DevReady never runs any of them."""
    todo = [r for r in results if r.status in (Status.FAIL, Status.WARN) and r.suggestion]
    lines = ["DevReady - Fix Plan (suggestions only)", ""]
    if not todo:
        lines.append("Nothing to fix.")
    for i, r in enumerate(todo, 1):
        lines.append(f"{i}. [{r.status.value.upper()}] {r.title}: {r.summary}")
        lines.append(f"   -> {r.suggestion}")
        if r.docs_url:
            lines.append(f"   {r.docs_url}")
    lines += ["", "DevReady did not run any of these. Nothing was changed."]
    return "\n".join(lines)
