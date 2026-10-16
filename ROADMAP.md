# Roadmap

Principles (unchanged): read-only, local-first, zero runtime dependencies, Python >= 3.10, never print env values or raw command output.

## Where we are (0.0.4)

- Tools: Git, Node, npm, Python. Docker CLI/daemon only when a Docker/compose file exists.
- Pins compared: `.nvmrc`, `.node-version`, `.python-version`, `package.json` engines.node, `pyproject.toml` requires-python, `.tool-versions` (node/python only).
- Also: `.env.example` vs `.env` key names, git identity presence, free disk space.
- Interfaces: `check` (text/JSON, exit 1 on `fail`), `explain`, `mcp`, Claude Code plugin, `AGENTS.md`.
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
- [ ] Optional `.devready.toml` to declare requirements and silence checks (needs a 3.10-safe parser, or limit to JSON).
- [ ] `devready init` generates that file from what it detects.

## 0.4 - Team and CI

- [ ] Official GitHub Action wrapping `devready check`.
- [ ] Shared baseline file (committed) to compare against.
- [ ] `--watch`/diff mode: show only what changed since the last run.

## 0.5 - Platform specifics

- [ ] Windows: long paths enabled, execution policy, `core.autocrlf`.
- [ ] WSL version and Docker Desktop backend.
- [ ] macOS: Xcode CLT; Linux: common missing build deps.

## 1.0 - Stabilize

- [ ] Freeze JSON schema (`docs/schema.json`) with a versioning policy.
- [ ] Test matrix on Windows/macOS/Linux x Python 3.10-3.13.
- [ ] Docs pass: check catalog, plugin/MCP setup, contributing guide for adding a check.

## Opt-in only (needs explicit design review)

- Network reachability checks (registry, DB host): off by default, strict timeouts.
- Anything that executes project code or installs software: out of scope.
