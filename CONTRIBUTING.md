# Contributing

DevReady is a read-only environment checker. It must never install, modify or delete anything,
print environment variable values, or echo raw file/command output. PRs that break these rules
will be declined.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

## Pull requests

1. Open an issue first for anything larger than a small fix.
2. One focused branch per change, with tests (unit tests must not depend on installed tools).
3. Run the commands above; CI runs them on Ubuntu, Windows and macOS.
4. Describe the problem, the fix, test evidence and known limitations.

## Adding a check

Return a `Result` (`src/devready/models.py`). Run external commands with a fixed argument list and
a timeout, and report only parsed values. Then:

1. Pick a stable id matching `^[a-z_]+(\.[a-z_]+)+$` (no digits or hyphens). Ids are public API.
2. Add an entry in `src/devready/explain.py` and a row in `docs/checks.md` (a test enforces both).
3. Register it in `src/devready/runner.py`; make it silent when the project does not use the thing.
4. Test with injected fakes, plus a hostile-content case if it reads project files.
5. Mention it in `CHANGELOG.md`. See [docs/versioning.md](docs/versioning.md) for what may change.

## Adding a version manager

Add a row to `MANAGERS` in `src/devready/managers.py` (runtime key, executable looked up on PATH,
command template with `{v}`) and a case in `tests/unit/test_managers.py` with a fake `which`.
The manager is never executed.

## Conduct and security

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately per [SECURITY.md](SECURITY.md).
