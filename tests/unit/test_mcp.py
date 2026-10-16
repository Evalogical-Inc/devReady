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
