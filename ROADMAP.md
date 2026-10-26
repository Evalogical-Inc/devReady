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
- [ ] `pom.xml` / `build.gradle` Java targets.
- [x] `Gemfile` ruby version (#13; literal pins only, Gemfile code is never executed).
- [ ] Table-drive the Node/Python pins in `project.py` like `checks/runtimes.py`.

**Project health**
- [ ] Python dependency drift (venv present, `pip check`); held back because conda/global envs make "no venv" noisy.
- [x] Ports from `package.json` scripts, alongside compose files and `.env.example` (#11).
- [ ] Docker: compose validity, image platform mismatch (arm64 vs amd64).
- [ ] WSL version and Docker Desktop backend (`wsl` prints UTF-16, so parsing needs care).

**Output**
- [x] SARIF file locations, so GitHub code scanning can show findings (#10).
- [ ] Exact fix commands in `fix --plan` (suggestions are prose today).
- [ ] Text output readability: column alignment, wrapping, summary line (#12).

**Quality**
- [x] Real-tool runtime tests on CI (`tests/integration/test_runtimes_real.py`). Not covered: pnpm and Bun (not installed on any runner).
- [x] GitHub Action runs on Ubuntu/Windows/macOS in CI (pass, fail and baseline fixtures). Not covered: `sarif` and multi-id `only`/`skip`.
- [x] macOS/Linux compiler lookup runs for real on GitHub's Ubuntu and macOS runners (`tests/integration/`). Not covered: a machine *without* a toolchain, and Windows warning branches on a locked-down machine.

## Decided against

- A separate `doctor` command (`check` + `explain` covers it).
- A `details` result field, `--watch`, or DevReady writing any file (`init` and `--baseline` print or read only). Adding a result field needs `schema_version: 2`.
- Executing project code or installing software.

## Opt-in only (needs a design review first)

- Network reachability checks (registry, DB host): off by default, strict timeouts.
