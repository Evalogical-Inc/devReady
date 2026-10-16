import json
import xml.etree.ElementTree as ET

from devready.cli import _selected, main
from devready.formats import fix_plan, junit, sarif
from devready.models import Result, Status

RESULTS = [
    Result("a.ok", "A", Status.PASS, "fine"),
    Result("b.warn", "B", Status.WARN, "meh <&>", "Do the thing", "https://x.test"),
    Result("c.fail", "C", Status.FAIL, "broken", "Switch versions"),
    Result("d.skip", "D", Status.SKIP, "n/a"),
    Result("e.err", "E", Status.ERROR, "oops"),
]


def test_junit_counts_and_escaping():
    suite = ET.fromstring(junit(RESULTS))  # parses, so special characters were escaped
    assert suite.attrib["tests"] == "5"
    assert (suite.attrib["failures"], suite.attrib["errors"], suite.attrib["skipped"]) == (
        "1",
        "1",
        "1",
    )
    assert suite.find("testcase[@name='c.fail']/failure") is not None
    assert suite.find("testcase[@name='b.warn']/failure") is None


def test_sarif_levels():
    run = json.loads(sarif(RESULTS))["runs"][0]
    levels = {r["ruleId"]: r["level"] for r in run["results"]}
    assert levels == {"b.warn": "warning", "c.fail": "error", "e.err": "error"}


def test_fix_plan_lists_only_actionable():
    plan = fix_plan(RESULTS)
    assert "Do the thing" in plan and "Switch versions" in plan and "https://x.test" in plan
    assert "fine" not in plan and "oops" not in plan
    assert "Nothing to fix." in fix_plan(RESULTS[:1])


def test_selection_by_id_or_prefix():
    assert _selected("project.node.pin", ["project"], [])
    assert not _selected("projects.x", ["project"], [])  # prefix needs a dot boundary
    assert not _selected("git.version", [], ["git"])
    assert _selected("git.version", [], [])


def test_cli_only_and_formats(capsys):
    assert main(["check", "--only", "python", "--format", "json"]) == 0
    ids = [r["check_id"] for r in json.loads(capsys.readouterr().out)["results"]]
    assert ids == ["python.version"]
    assert main(["check", "--only", "python", "--format", "junit"]) == 0
    ET.fromstring(capsys.readouterr().out)
    assert main(["check", "--only", "python", "--format", "sarif"]) == 0
    assert json.loads(capsys.readouterr().out)["version"] == "2.1.0"


def test_fix_requires_plan(capsys):
    assert main(["fix"]) == 2
    assert main(["fix", "--plan", "--only", "python"]) == 0
    assert "Nothing to fix." in capsys.readouterr().out
