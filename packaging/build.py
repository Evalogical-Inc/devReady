"""Build the standalone binary and archive it: python packaging/build.py <os>-<arch>

Run from the repo root with the package installed (`pip install .`) and the pinned build tool
(`pip install -r packaging/requirements.txt`). Writes dist/devready-<version>-<target>.<zip|tar.gz>.
"""

import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def version() -> str:
    init = ROOT / "src" / "devready" / "__init__.py"
    for line in init.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("could not read __version__")


def main(target: str) -> int:
    windows = target.startswith("windows")
    exe = "devready.exe" if windows else "devready"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "devready",
            "--distpath",
            str(DIST / "bin"),
            "--workpath",
            str(ROOT / "build"),
            "--specpath",
            str(ROOT / "build"),
            "--collect-submodules",
            "devready",
            str(ROOT / "packaging" / "devready_entry.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    binary = DIST / "bin" / exe
    if not binary.is_file():
        raise SystemExit(f"build produced no {exe}")
    name = f"devready-{version()}-{target}"
    files = [binary, ROOT / "LICENSE"]
    if windows:
        archive = DIST / f"{name}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, f"{name}/{f.name}")
    else:
        archive = DIST / f"{name}.tar.gz"
        with tarfile.open(archive, "w:gz") as t:
            for f in files:
                t.add(f, f"{name}/{f.name}")
    print(f"binary  {binary} ({binary.stat().st_size / 1_048_576:.1f} MB)")
    print(f"archive {archive}")
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python packaging/build.py <os>-<arch>   e.g. windows-x64")
    sys.exit(main(sys.argv[1]))
