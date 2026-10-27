# Plan: team-facing features (5-8)

Status: proposed. Each feature has a tracking issue; each numbered step below is one PR.
All of it keeps the [principles](../../ROADMAP.md): read-only, local-first, zero runtime
dependencies, Python >= 3.10, never print env values or raw file/command output, no network.
Stability rules: [versioning.md](../versioning.md). Everything here is a 1.x minor unless noted.

Suggested order: 8 (Docker, smallest) and 7 (VS Code, most visible) can start in parallel;
5 (monorepo) before 6 (policy), because a policy is most useful across many packages.

---

## 5. Monorepo support: `devready check --recursive`

**Why:** teams with pnpm/npm workspaces or several Python packages run DevReady once per folder
today, or not at all.

**Design**
- Discovery (read-only, same file rules as `project.py`: no symlinks, 1 MB cap):
  - `package.json` `workspaces` (array or `{packages: [...]}`) and `pnpm-workspace.yaml`
    `packages:` (line-based parse, no YAML dependency).
  - Fallback: any directory up to depth 3 containing a pin file from `PINS`/`RUNTIMES`,
    skipping `node_modules`, `.git`, `.venv`, `venv`, `dist`, `build`.
  - Glob support limited to `dir/*` and `dir/**` via `pathlib.Path.glob`; cap at 200 packages.
- Machine-wide checks (git, docker, disk, platform, tools) run **once**; project checks
  (`check_project`, `check_runtimes`, `check_health`, `check_config`) run per package.
- **Schema:** the v1 schema forbids extra top-level keys, so `--recursive` JSON uses a separate
  documented shape, `docs/schema-multi.json`:
  `{"schema_version": 1, "projects": [{"path": "packages/web", "results": [...]}]}` where
  `path` is `"."` for machine-wide results. Existing output is unchanged without the flag.
- Text: one section per package, only packages with non-pass results when `--quiet`.
- SARIF: already carries `file`; prefix it with the package path. JUnit: one `testsuite` per package.
- Exit code: `1` if any package has a `fail`. `--baseline` keyed by `(path, check_id)`.

**PRs**
1. `discover_packages(root)` + unit tests (workspaces, pnpm yaml, fallback scan, caps, symlink loop).
2. `run_checks` split into machine-wide and per-project parts (no behavior change, tests prove it).
3. `--recursive` flag: text + `schema-multi.json` + schema test.
4. SARIF/JUnit/baseline support; GitHub Action `recursive` input; MCP tool argument.
5. Docs: README section, `docs/checks.md`, CHANGELOG.

**Risks:** large repos (cap + skip list), duplicate results between root and packages (root is
just another package with path `"."`).

---

## 6. Org policy file: `devready check --policy FILE`

**Why:** platform teams want one minimum toolchain for every repo ("Git >= 2.40, Node >= 20,
Docker required") without editing each repo's `.devready.json`. This is the feature companies
pay for in support time, so it is the main sponsor hook.

**Design**
- `.devready.json` keys are frozen, so the policy is a **separate file** passed by flag or
  `DEVREADY_POLICY` env var (the path only; the value is never printed).
- Shape (validated like `config.py`, unknown keys make the file invalid, one ERROR result):
  ```json
  {"policy_version": 1,
   "require": {"node": ">=20", "python": ">=3.11", "git": ">=2.40", "docker": "*"},
   "skip": ["platform.autocrlf"],
   "env": ["NPM_TOKEN"]}
  ```
  `require` accepts any key from `TOOLS` and `RUNTIMES`; `"*"` means "must be installed".
- New ids: `policy.<tool>.require` (e.g. `policy.git.require`), `policy.file`. A policy `fail`
  is a `fail` (exit 1).
- Precedence: repo `.devready.json` `skip` cannot skip `policy.*` ids (the policy wins).
- **Local files only.** Remote URLs stay out (network checks are "opt-in, design review first"
  in the ROADMAP); teams vendor the file or fetch it in CI themselves.

**PRs**
1. `checks/policy.py`: loader/validator + hostile-content tests (no echo of file content).
2. Requirement evaluation reusing `check_tool` versions and `_compare`; `policy.*` ids,
   `explain.py` entries, `docs/checks.md` rows.
3. `--policy` flag + `DEVREADY_POLICY`; works with `--recursive` (applies to every package).
4. GitHub Action `policy` input; `devready init --policy` prints a starter file.
5. Docs: "Using DevReady across an organization" guide.

---

## 7. VS Code extension

**Why:** daily visibility. A status-bar item that turns red when `.nvmrc` changes is the best
discovery channel DevReady can have, and extensions bring TypeScript contributors.

**Design**
- Lives in `vscode/` in this repo (like `npm/`), TypeScript, no runtime deps beyond the
  VS Code API.
- Runs `devready check --format sarif --project <workspaceFolder>` (SARIF already has file
  locations from #10), falling back to `uvx devready-cli` like the npm launcher.
- Maps results to `Diagnostics` on the pin file (Problems panel); status bar shows
  `DevReady: ✓` / `2 warn` / `1 fail`; click runs the check.
- Re-runs on save of watched pin files (`.nvmrc`, `.node-version`, `.python-version`,
  `package.json`, `pyproject.toml`, `.tool-versions`, `.devready.json`, ...), debounced.
- Commands: `DevReady: Check`, `DevReady: Explain…` (runs `devready explain <id>`, shows in
  a read-only output channel), `DevReady: Show fix plan`.
- Code action on a diagnostic: "Explain this check". It never runs fix commands.
- No telemetry. Workspace trust: disabled in untrusted workspaces.

**PRs**
1. Scaffold (`vscode/package.json`, activation on pin files, status bar, run + parse SARIF).
2. Diagnostics + on-save watcher + tests (`@vscode/test-electron` in CI, Ubuntu only).
3. Explain / fix-plan commands.
4. Publish job in `publish.yml` to VS Marketplace and Open VSX (needs `VSCE_PAT`, `OVSX_PAT`
   secrets; maintainer setup).
5. README badge + GIF.

---

## 8. Docker checks

**Why:** "works in Docker on my Intel laptop, breaks on M-series" and "Docker Desktop not using
WSL 2" are common team pain.

**Design** (extends `checks/extras.py`; silent unless a Docker/Compose file exists, like today)
- `docker.compose.valid`: run `docker compose -f <file> config --quiet` (fixed argv, timeout);
  report only pass/fail and the file name, never Compose's output. Skip when the daemon check
  did not pass.
- `docker.platform`: host arch from `docker version --format {{.Server.Arch}}`; read
  `platform:` entries in compose files and `FROM --platform=` in `Dockerfile` (line-based).
  WARN when a pinned platform differs from the host ("runs under emulation, slower").
  No registry/manifest lookups (no network).
- `platform.wsl.version` (Windows only): `wsl --status` output is UTF-16LE; decode with
  `utf-16-le`, parse only the default version digit. WARN if WSL 1 and Docker is declared.
- `docker.backend` (Windows only): `docker info --format {{.OperatingSystem}}`; WARN when
  Docker Desktop is not on the WSL 2 backend and the project uses bind mounts.

**PRs** (each is good-first-issue sized once the first lands)
1. `docker.compose.valid` + fakes-based tests.
2. `docker.platform` + hostile-content test for the Dockerfile/compose parse.
3. `platform.wsl.version` with a UTF-16 fixture.
4. `docker.backend`.

Each PR adds `explain.py` + `docs/checks.md` entries (a test enforces both) and a CHANGELOG line.
