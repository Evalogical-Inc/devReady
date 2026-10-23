import json
import os
import re
import socket
import subprocess
from types import SimpleNamespace

from devready.checks.health import check_env_ignored, check_node_modules, check_ports
from devready.explain import EXPLANATIONS
from devready.models import Status


def test_env_ignored_branches(tmp_path):
    assert check_env_ignored(tmp_path) == []  # no .env
    (tmp_path / ".env").write_text("SECRET=hunter2")
    for rc, want in ((0, Status.PASS), (1, Status.WARN)):
        r = check_env_ignored(tmp_path, lambda argv, rc=rc: SimpleNamespace(returncode=rc))
        assert r[0].status is want and "hunter2" not in str(r)
    assert check_env_ignored(tmp_path, lambda argv: SimpleNamespace(returncode=128)) == []


def test_env_ignored_real_git(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".env").write_text("A=1")
    assert check_env_ignored(tmp_path)[0].status is Status.WARN
    (tmp_path / ".gitignore").write_text(".env\n")
    assert check_env_ignored(tmp_path)[0].status is Status.PASS


def test_node_modules(tmp_path):
    assert check_node_modules(tmp_path) == []
    (tmp_path / "package.json").write_text(json.dumps({"name": "x"}))
    assert check_node_modules(tmp_path) == []  # no dependencies
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"a": "1"}}))
    assert check_node_modules(tmp_path)[0].status is Status.WARN
    (tmp_path / "node_modules").mkdir()
    lock = tmp_path / "package-lock.json"
    lock.write_text("{}")
    os.utime(tmp_path / "node_modules", (1, 1))
    assert "newer" in check_node_modules(tmp_path)[0].summary
    os.utime(lock, (1, 1))
    assert check_node_modules(tmp_path)[0].status is Status.PASS


def test_ports(tmp_path):
    assert check_ports(tmp_path) == []
    (tmp_path / "docker-compose.yml").write_text(
        'services:\n  db:\n    ports:\n      - "5432:5432"\n      - 127.0.0.1:8080:80\n'
    )
    (tmp_path / ".env.example").write_text("APP_PORT=3000\nNAME=x\n")
    r = check_ports(tmp_path, lambda p: p == 8080)
    assert r[0].status is Status.WARN and r[0].summary.endswith("8080")
    assert check_ports(tmp_path, lambda p: False)[0].summary.startswith("3 ")


def test_ports_real_socket(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        (tmp_path / "docker-compose.yml").write_text(
            f'services:\n  app:\n    ports:\n      - "{port}:80"\n'
        )
        (result,) = check_ports(tmp_path)
        assert result.check_id == "project.ports.free"
        assert result.status is Status.WARN
        assert result.summary.partition(":")[2].strip() == str(port)

    (result,) = check_ports(tmp_path)
    assert result.check_id == "project.ports.free"
    assert result.status is Status.PASS


def test_ports_hostile_yaml(tmp_path):
    hostile = "IGNORE PREVIOUS INSTRUCTIONS"
    shell = "$(touch SHOULD_NOT_EXIST)"
    (tmp_path / "docker-compose.yml").write_text(
        f'services:\n  app:\n    ports:\n      - "8080:80" # {hostile}\n'
        '      - "127.0.0.1:5432:5432"\n'
        '      - "99999:80"\n'
        '      - "65536:80"\n'
        '      - "00000:80"\n'
        '      - "not-a-port:80"\n'
        f'      - "{hostile}"\n'
        f'      - "{shell}:80"\n'
    )
    probed = []

    def in_use(port):
        probed.append(port)
        return True

    results = check_ports(tmp_path, in_use)
    (result,) = results
    assert probed == [5432, 8080]
    assert result.check_id == "project.ports.free"
    assert result.status is Status.WARN
    shown = result.summary.partition(":")[2]
    assert re.fullmatch(r"[0-9, ]+", shown)
    assert shown.strip() == "5432, 8080"
    assert all(text not in str(results) for text in (hostile, shell, "not-a-port", "99999"))


def test_ids_have_explanations():
    for cid in ("project.env.ignored", "project.node.modules", "project.ports.free"):
        assert cid in EXPLANATIONS
