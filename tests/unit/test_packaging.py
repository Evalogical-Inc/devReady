"""The binary build scripts in packaging/ stay in step with the package (no PyInstaller needed)."""

import importlib.util
import sys
from pathlib import Path

from devready import __version__

PACKAGING = Path(__file__).resolve().parents[2] / "packaging"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"_pkg_{name}", PACKAGING / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_reads_the_package_version():
    assert _load("build").version() == __version__


def test_entry_point_calls_the_real_cli():
    text = (PACKAGING / "devready_entry.py").read_text(encoding="utf-8")
    assert "from devready.cli import main" in text
    assert "sys.exit(main())" in text


def test_smoke_no_python_env_replaces_path(monkeypatch):
    smoke = _load("smoke")
    monkeypatch.setenv("PATH", "/some/python/bin")
    monkeypatch.delenv("SMOKE_NO_PYTHON", raising=False)
    assert smoke.clean_env()["PATH"] == "/some/python/bin"
    monkeypatch.setenv("SMOKE_NO_PYTHON", "1")
    assert "python" not in smoke.clean_env()["PATH"].lower()
    assert sys.platform  # the branch taken depends on the platform; both drop the inherited PATH


def test_build_requirements_are_pinned_and_not_package_dependencies():
    for line in (PACKAGING / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            assert "==" in line, line
    pyproject = (PACKAGING.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert "pyinstaller" not in pyproject.lower()
