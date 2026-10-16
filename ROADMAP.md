# Roadmap

Principles: read-only, local-first, zero runtime dependencies, Python >= 3.10, never print env values or raw command output. Stability rules for 1.x: [docs/versioning.md](docs/versioning.md).

## Shipped (1.0.0)

- **Tools and pins:** Git, Node, npm, Python always; Docker, Go, Ruby, Java, Rust, .NET, pnpm, Yarn and Bun only when the project declares them (`.nvmrc`, `.python-version`, `engines`, `requires-python`, `go.mod`, `global.json`, `packageManager`, `.tool-versions`, ...). Full list: [docs/checks.md](docs/checks.md).
- **Project health:** `.env` not git-ignored, `node_modules` vs lockfile, declared ports in use, `.env.example` vs `.env` key names, git identity, disk space.
- **Platform:** Windows long paths, PowerShell execution policy, `core.autocrlf`; macOS Xcode CLT / Linux compiler + `make` for native builds.
- **Interfaces:** `check` (text, JSON, JUnit, SARIF; `--only`, `--skip`, `--baseline`), `fix --plan`, `init`, `explain`, `mcp`, GitHub Action, Claude Code plugin, `.devready.json`.

## After 1.0 (backlog, all additive, so 1.x minors)

**Runtimes and pins**
- [ ] `uv` / `pip` (needs a pin file to compare against).
- [ ] `pom.xml` / `build.gradle` Java targets, `Gemfile` ruby version.
- [ ] Table-drive the Node/Python pins in `project.py` like `checks/runtimes.py`.

**Project health**
- [ ] Python dependency drift (venv present, `pip check`); held back because conda/global envs make "no venv" noisy.
- [ ] Ports from `package.json` scripts (only compose files and `.env.example` today).
- [ ] Docker: compose validity, image platform mismatch (arm64 vs amd64).
- [ ] WSL version and Docker Desktop backend (`wsl` prints UTF-16, so parsing needs care).

**Output**
- [ ] SARIF file locations, so GitHub code scanning can show findings.
- [ ] Exact fix commands in `fix --plan` (suggestions are prose today).

**Quality**
- [ ] Fixture-based integration tests with real tools on CI (`tests/integration/`, `tests/fixtures/`).
- [ ] Run the GitHub Action on a real runner. It has never been exercised outside local argument tests.
- [ ] Run the macOS/Linux platform checks on real machines. CI covers them with fakes only.

## Decided against

- A separate `doctor` command (`check` + `explain` covers it).
- A `details` result field, `--watch`, or DevReady writing any file (`init` and `--baseline` print or read only). Adding a result field needs `schema_version: 2`.
- Executing project code or installing software.

## Opt-in only (needs a design review first)

- Network reachability checks (registry, DB host): off by default, strict timeouts.
