import json
import subprocess
import sys

from devready.mcp_server import handle


def test_handshake_list_call(tmp_path):
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "check_environment", "arguments": {"project": str(tmp_path)}},
        },
        {"jsonrpc": "2.0", "id": 4, "method": "nope"},
    ]
    p = subprocess.run(
        [sys.executable, "-m", "devready.cli", "mcp"],
        capture_output=True,
        text=True,
        timeout=60,
        input="\n".join(map(json.dumps, msgs)) + "\n",
    )
    out = [json.loads(line) for line in p.stdout.splitlines()]
    assert [o["id"] for o in out] == [1, 2, 3, 4]  # notification gets no reply
    assert out[1]["result"]["tools"][0]["name"] == "check_environment"
    report = json.loads(out[2]["result"]["content"][0]["text"])
    assert report["schema_version"] == 1
    assert out[3]["error"]["code"] == -32601


def test_bad_inputs():
    assert (
        handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "x"}})[
            "error"
        ]["code"]
        == -32603
    )
    r = handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "check_environment", "arguments": {"project": "/no/such"}},
        }
    )
    assert r["result"]["isError"] is True


def _call(arguments):
    msg = {"name": "check_environment", "arguments": arguments}
    return handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": msg})["result"]


def test_recursive_argument_is_declared_and_reports_each_package(tmp_path):
    from devready.mcp_server import TOOL

    assert TOOL["inputSchema"]["properties"]["recursive"]["type"] == "boolean"
    (tmp_path / "package.json").write_text(json.dumps({"workspaces": ["apps/*"]}))
    (tmp_path / "apps" / "web").mkdir(parents=True)
    (tmp_path / "apps" / "web" / ".nvmrc").write_text("20\n")
    result = _call({"project": str(tmp_path), "recursive": True})
    report = json.loads(result["content"][0]["text"])
    assert [p["path"] for p in report["projects"]] == [".", "apps/web"]
    assert len(result["content"]) == 1  # no note: nothing was left out


def test_recursive_says_when_packages_were_left_out(tmp_path, monkeypatch):
    from devready import runner
    from devready.models import Result, Status

    def project(root, versions, machine=()):
        return [Result("project.x", "Pin", Status.PASS, "ok")]

    monkeypatch.setattr(runner, "machine_checks", lambda root: ([], {}))
    monkeypatch.setattr(runner, "project_checks", project)
    (tmp_path / "package.json").write_text(json.dumps({"workspaces": ["p/*"]}))
    for i in range(201):
        (tmp_path / "p" / f"x{i:03}").mkdir(parents=True)
        (tmp_path / "p" / f"x{i:03}" / "package.json").write_text("{}")
    content = _call({"project": str(tmp_path), "recursive": True})["content"]
    assert len(json.loads(content[0]["text"])["projects"]) == 200
    assert "202 packages" in content[1]["text"] and "first 200" in content[1]["text"]
