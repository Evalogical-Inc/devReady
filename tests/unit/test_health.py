import json
import os
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


def test_ports_from_package_scripts(tmp_path):
    package_file = tmp_path / "package.json"
    package_file.write_text("{")
    assert check_ports(tmp_path) == []  # project.py reports invalid JSON

    package_file.write_text(
        json.dumps(
            {
                "scripts": {
                    "dev": "vite --port 5173",
                    "start": "next start -p 3000",
                    "equal": "server --port=4173",
                    "env": "PORT=4000 node server.js",
                    "junk": "echo nothing useful",
                    "too_large": "server --port 65536",
                    "too_many_digits": "server -p 999999",
                },
                "description": "server --port 9999",
            }
        )
    )
    seen = []
    result = check_ports(tmp_path, lambda port: seen.append(port) or False)

    assert seen == [3000, 4000, 4173, 5173]
    assert result[0].status is Status.PASS
    assert result[0].summary == "4 declared port(s) are free"


def test_ids_have_explanations():
    for cid in ("project.env.ignored", "project.node.modules", "project.ports.free"):
        assert cid in EXPLANATIONS
