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
a timeout, and report only parsed values. Add the check to the README only once it works.

## Conduct and security

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately per [SECURITY.md](SECURITY.md).
