import json
from pathlib import Path

from devready import __version__

ROOT = Path(__file__).parents[2]
SERVER = json.loads((ROOT / "server.json").read_text())


def test_versions_match_package():
    # the registry rejects a server.json whose PyPI version does not exist yet
    assert SERVER["version"] == __version__
    assert [p["version"] for p in SERVER["packages"]] == [__version__]
    # the npm launcher runs the PyPI release with its own version number
    assert json.loads((ROOT / "npm" / "package.json").read_text())["version"] == __version__
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["version"] == __version__


def test_readme_has_registry_ownership_marker():
    # PyPI ownership check: the package README must contain mcp-name: <name>
    assert f"<!-- mcp-name: {SERVER['name']} -->" in (ROOT / "README.md").read_text("utf-8")


def test_uvx_entry_point_exists():
    assert 'devready-cli = "devready.cli:main"' in (ROOT / "pyproject.toml").read_text()
