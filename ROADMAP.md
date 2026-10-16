# Roadmap

Principles (unchanged): read-only, local-first, zero runtime dependencies, Python >= 3.10, never print env values or raw command output.

## Where we are (0.3.0)

- Tools: Git, Node, npm, Python. Docker, Go, Ruby, Java, Rust, .NET, pnpm, Yarn, Bun only when the project declares them (details in the sections below).
- Pins compared: `.nvmrc`, `.node-version`, `.python-version`, `package.json` engines.node, `pyproject.toml` requires-python, `.tool-versions` (node/python only).
- Also: `.env.example` vs `.env` key names, git identity presence, free disk space.
- Interfaces: `check` (text/JSON/JUnit/SARIF, `--only`/`--skip`/`--baseline`, exit 1 on `fail`), `fix --plan`, `init`, `explain`, `mcp`, GitHub Action, Claude Code plugin, `AGENTS.md`.
- CI and PyPI publish workflows exist.

## Decisions (from the docs review)

- Keep `check` + `explain`; no separate `doctor` command.
- JSON schema stays at v1. No `details` field; new fields need a version bump (revisit at 1.0).
- Check ids must match `^[a-z_]+(\.[a-z_]+)+$`: no digits or hyphens.
- Anything echoing project file content only uses validated strings (`SAFE_SPEC`, extracted digits).
- Docs gaps: `docs/architecture.md`, `docs/security.md`, `tests/integration/`, `tests/fixtures/`.

## 0.1 - More runtimes (in progress)

- [x] Go (`go.mod`), Ruby (`.ruby-version`), Java (`.java-version`), Rust (`rust-toolchain[.toml]`), .NET (`global.json`), plus their `.tool-versions` lines. Checked only when the project declares them, so no noise on other projects. (`checks/runtimes.py`)
- [x] `explain` entries and tests for every new id.
- [x] pnpm/yarn/bun via the `packageManager` field in `package.json`.
- [ ] `uv`/`pip` (no pin file to compare against yet).
- [ ] Table-drive the existing Node/Python pins in `project.py` the same way.
- [ ] Add `pom.xml` / `build.gradle` Java targets, `Gemfile` ruby version.
- [ ] Fixture-based integration tests with real tools on CI.

## 0.2 - Project health (in progress)

- [x] Node dependency drift: `node_modules` missing or older than a lockfile (directory mtime).
- [ ] Python drift (venv present, `pip check`); skipped for now since conda/global envs make "no venv" noisy.
- [x] Port conflicts for ports declared in compose files and `*PORT=` in `.env.example` (`package.json` scripts not parsed).
- [x] `.env` hygiene: warn if `.env` is not gitignored or is tracked.
- [ ] Docker: compose file validity, image platform mismatch (arm64 vs amd64).

## 0.3 - Actionable output (in progress)

- [x] `devready fix --plan`: prints each `fail`/`warn` with its suggestion. Never runs anything. (Suggestions are prose today, not exact commands.)
- [x] `--format sarif` and `junit` (SARIF has no file locations yet, so GitHub code scanning may not show alerts).
- [x] `--only` / `--skip` filters by check id or dotted prefix (repeatable).
- [x] Optional `.devready.json` (JSON, so no parser dependency): `skip` ids, `require` node/python, required `env` names.
- [x] `devready init` prints a starter file (does not write it; DevReady stays read-only).

## 0.4 - Team and CI

- [x] GitHub Action (`action.yml`, composite). Untested on a real runner; needs a release with the new flags.
- [x] `--baseline FILE`: compare with a saved `--format json` report (commit it for a team baseline). Shows new/changed results; exit 1 only for a new or worse `fail`. Results that disappeared are not reported.
- [x] Diff mode = `--baseline` against your own saved snapshot. DevReady never writes the snapshot (read-only), and there is no `--watch` loop.

## 0.5 - Platform specifics (WSL left)

- [x] Windows: long paths (registry), PowerShell execution policy (blocks npm.ps1), `core.autocrlf` without `.gitattributes`. Only when relevant (`package.json` / a git repo). Verified against real long-paths and policy values on one Windows machine; the warning paths are unit-tested only.
- [ ] WSL version and Docker Desktop backend.
- [x] macOS Xcode CLT / Linux `cc`+`make`, only when `binding.gyp`, `setup.py`, `Gemfile` or `Cargo.toml` exists. Not run on macOS or Linux yet (CI runs the suite there, with fakes).

## 1.0 - Stabilize

- [x] Schema frozen at v1 with a policy: `docs/versioning.md`, enforced by `tests/unit/test_stability.py` (fields, statuses, id pattern, catalog in sync).
- [x] CI matrix: Ubuntu/Windows/macOS x Python 3.10, 3.11, 3.12, 3.13 (edited, not yet run on GitHub).
- [x] Docs: `docs/checks.md`, `architecture.md`, `security.md`, `versioning.md`, and an "Adding a check" guide in CONTRIBUTING. Plugin/MCP setup already in `docs/agents.md`.
- [ ] Bump to 1.0.0 once the patch release below is out and CI is green on the full matrix.

## Opt-in only (needs explicit design review)

- Network reachability checks (registry, DB host): off by default, strict timeouts.
- Anything that executes project code or installs software: out of scope.
