<div align="center">

# 🩺 DevReady

### "Works on my machine" - finally answered before it wastes your afternoon.

**A zero-dependency, read-only CLI that checks whether your machine actually meets a project's declared requirements, and tells you exactly what to fix.**
Built for humans, CI, and AI coding agents (Claude Code, Codex, any MCP client).

[![CI](https://github.com/Evalogical-Inc/devReady/actions/workflows/ci.yml/badge.svg)](https://github.com/Evalogical-Inc/devReady/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devready-cli)](https://pypi.org/project/devready-cli/)
[![DevReady](https://img.shields.io/badge/DevReady-%E2%9C%93%20ready-2ea44f)](https://github.com/Evalogical-Inc/devReady)
[![Website](https://img.shields.io/badge/website-devready--ten.vercel.app-ff6a35)](https://devready-ten.vercel.app/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies: 0](https://img.shields.io/badge/dependencies-0-brightgreen)
![Status: stable](https://img.shields.io/badge/status-stable-green)

<br/>

<img src="https://raw.githubusercontent.com/Evalogical-Inc/devReady/main/docs/devready-demo.gif" alt="Demo of running devready check in a terminal" width="800"/>

<sub>One command, every requirement checked, exact fixes shown.</sub>

</div>

---

## What is DevReady?

DevReady is a command-line tool that tells you whether your computer is set up to work on a project. Run `devready check` inside a project folder and it:

1. **Reads** the versions the project says it needs (`.nvmrc`, `.python-version`, `package.json` engines, `pyproject.toml` requires-python).
2. **Compares** them with what is actually installed on your machine (Python, Node.js, npm, Git, and so on).
3. **Reports** PASS, WARN or FAIL for each item, with what to fix. The exit code is `1` if a requirement is unmet, so it also works in CI.

It only looks. It never installs, changes or deletes anything, makes no network calls and sends no telemetry. Fixing the problem (for example switching Node versions) is up to you.

## The problem

You clone a repo. `npm install` explodes. The README says "Node 20", your machine has 16, and the error message says nothing useful. Multiply by every new hire, student, CI runner and **AI agent** that burns tokens guessing why a build failed.

## The fix

```console
$ devready check

DevReady - Environment Check

[PASS ] Python       3.15.0 found
[PASS ] Git          2.52.0 found
[PASS ] Node.js      23.5.0 found
[PASS ] npm          11.14.1 found
[FAIL ] Node engines 23.5.0 does not satisfy package.json engines (>=99)
[WARN ] Python pin   3.15.0 does not satisfy .python-version (3.99)

4 passed, 1 warning, 1 failed
No changes were made to your system.
```

> Output above is from a real run (pins deliberately set to impossible values to show failures). Exit code `1` when a requirement is unmet, so it drops straight into CI.

## Why DevReady

| | |
|---|---|
| 🎯 **Project-aware** | Reads what *your project* declares (`.nvmrc`, `.node-version`, `.python-version`, `package.json` engines, `pyproject.toml` requires-python) and compares it to what is installed. Not just "is Node installed?" |
| 🔒 **Read-only by design** | Never installs, edits or deletes. Never prints env values. No network. No telemetry. |
| 🤖 **Agent-ready** | Stable, versioned [JSON schema](docs/schema.json), a Claude Code plugin, an MCP server and `AGENTS.md`. Agents check first instead of guessing. |
| 🛡️ **Prompt-injection safe** | Output contains only parsed versions and fixed text, never raw file or command output, so a hostile `package.json` can't smuggle instructions to your agent (tested). |
| 📦 **Zero dependencies** | Pure Python standard library. Installs in a second, runs anywhere Python 3.10+ does. |
| ⚙️ **CI-friendly** | Documented exit codes, JSON output, tested on Linux, macOS and Windows in CI. |

## Who it's for

- 🧑‍🎓 **Students & bootcamp learners**: plain-language results instead of cryptic stack traces.
- 🧑‍💻 **Developers switching projects**: one command tells you what's off before you lose an hour.
- 👩‍🏫 **Maintainers & educators**: put `devready check` in your README's setup steps and cut "it doesn't work" issues.
- 🏗️ **CI & platform teams**: fail fast with a clear preflight step.
- 🤖 **AI-agent users**: give Claude Code / Codex a ground-truth environment check.

## Install

Install from [PyPI](https://pypi.org/project/devready-cli/):

```bash
pipx install devready-cli
# or run without installing:
uvx devready-cli check
```

From npm (runs the same PyPI release through `uvx` or `pipx`, so one of them must be installed):

```bash
npx devready-cli check
```

From a clone (for development):

```bash
git clone https://github.com/Evalogical-Inc/devReady && cd devReady
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Usage

```bash
devready check                    # human-readable report for the current directory
devready check --quiet            # only non-pass results (text format)
devready check --project ../app   # inspect another project's pins
devready check --format json      # machine-readable (see docs/schema.json)
devready explain docker.daemon    # what a check means and how to fix it
devready check --format junit     # or sarif, for CI
devready check --only project --skip project.ports   # filter by id or prefix
devready fix --plan               # suggested steps only; never runs them
devready check --format json > baseline.json   # save a snapshot (commit it for a team baseline)
devready check --baseline baseline.json          # show only what changed; fail only on new/worse failures
devready init > .devready.json    # optional config: skip ids, require node/python, required env names
devready mcp                      # run as an MCP server over stdio
devready --version
```

| Exit code | Meaning |
|---|---|
| `0` | No blocking failures |
| `1` | A project requirement is not met |
| `2` | Invalid usage (e.g. bad `--project` path) |
| `3` | Internal error |

| Status | Meaning |
|---|---|
| `pass` | Requirement met |
| `warn` | Tool missing, or a soft pin (`.nvmrc`, `.python-version`) differs |
| `fail` | A hard requirement (`engines`, `requires-python`) is not met |
| `skip` | Not evaluated (tool absent, or requirement syntax not understood) |
| `error` | DevReady couldn't run the check |

### JSON output

```json
{
  "schema_version": 1,
  "results": [
    {
      "check_id": "project.node.engines",
      "title": "Node engines",
      "status": "fail",
      "summary": "23.5.0 does not satisfy package.json engines (>=99)",
      "suggestion": "Switch versions with your version manager (nvm, pyenv, mise, ...) or update the requirement.",
      "docs_url": ""
    }
  ]
}
```

## Use it in CI (GitHub Actions)

```yaml
- uses: Evalogical-Inc/devReady@main   # pin a release tag once published
  with:
    skip: project.ports                  # optional; also: only, format, project, version
```

To show findings in GitHub code scanning, save a SARIF report and upload it. Pin findings point at the file that declares the pin (`package.json`, `.nvmrc`, `go.mod`, ...); tool-only findings have no file.

```yaml
- uses: Evalogical-Inc/devReady@main
  with:
    format: sarif
    output: devready.sarif
  continue-on-error: true               # still upload when a requirement is unmet
- uses: github/codeql-action/upload-sarif@v4
  with:
    sarif_file: devready.sarif
```

The job fails when a declared requirement is unmet (`fail`). It installs `devready-cli` from PyPI, so flags added after your installed release (`--only`, `--skip`, junit/sarif) need a release that includes them; set `version:` to pin one.

## Use it with pre-commit

With [pre-commit](https://pre-commit.com/) 3.2.0+ and Python 3.10+, add this to your
`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Evalogical-Inc/devReady
    rev: main  # unreleased; replace with a containing release tag or full commit SHA
    hooks:
      - id: devready
        args: [--skip, disk.space]  # optional
```

The hook is unreleased; `v1.2.0` does not contain it. For a reproducible configuration,
pin a full commit SHA or a later release tag that contains `.pre-commit-hooks.yaml`.

Install the hook for pushes, then try it manually:

```bash
pre-commit install --hook-type pre-push
pre-commit run devready --all-files --hook-stage pre-push
```

It runs `devready check` from your repository root before a push, even when no files
match, and does not pass filenames to the CLI. Unmet requirements block the push.
Use `args` for existing options such as `--only`, `--skip` and `--baseline`; relative
paths are resolved from your repository root.

pre-commit installs DevReady in an isolated Python environment. That interpreter is
the Python version DevReady checks; set the hook's `language_version` if your project
needs a specific installed Python. To run before commits instead, set
`stages: [pre-commit]` on the hook and install with `--hook-type pre-commit`.

## Add the badge

Tell contributors your project declares its requirements and can be checked with one command. Paste this into your README:

```markdown
[![DevReady](https://img.shields.io/badge/DevReady-%E2%9C%93%20ready-2ea44f)](https://github.com/Evalogical-Inc/devReady)
```

[![DevReady](https://img.shields.io/badge/DevReady-%E2%9C%93%20ready-2ea44f)](https://github.com/Evalogical-Inc/devReady)

## Use it with AI coding agents

DevReady ships the same engine three ways, so your agent can verify the environment *before* it installs, builds or tests.

**Claude Code** - plugin with a skill, a `/devready:doctor` command and an MCP server (the MCP server needs [`uv`](https://docs.astral.sh/uv/); the rest works without it once `devready-cli` is installed):

```text
/plugin marketplace add Evalogical-Inc/devReady
/plugin install devready --marketplace Evalogical-Inc/devReady
```

**Any MCP client** (Codex, Cursor, ...) - one read-only tool, `check_environment`. Also listed in the [MCP Registry](https://registry.modelcontextprotocol.io/) as `io.github.Evalogical-Inc/devready`:

<!-- mcp-name: io.github.Evalogical-Inc/devready -->

```toml
# ~/.codex/config.toml (verify keys against your Codex version)
[mcp_servers.devready]
command = "uvx"
args = ["--from", "devready-cli", "devready", "mcp"]
```

**Anything else** - drop [`AGENTS.md`](AGENTS.md) in your repo, or copy [`skills/devready`](skills/devready/SKILL.md). Details in [docs/agents.md](docs/agents.md).

## Safety & privacy

- Fixed command lists with timeouts; no shell, no user-built commands.
- Project files are read only if regular files ≤ 1 MB (symlinks skipped) and are never executed.
- Environment variable values are never read into output. Nothing leaves your machine.
- A passing report does **not** guarantee your project builds.

See [docs/security.md](docs/security.md) for the model, [docs/versioning.md](docs/versioning.md) for what stays stable, [docs/checks.md](docs/checks.md) for every check, and [SECURITY.md](SECURITY.md) to report a vulnerability.

## Limitations

- Checks today: Python, Git (+ identity set), Node.js, npm, project pins (`.nvmrc`, `.node-version`, `.python-version`, `.tool-versions`, `package.json` engines, `pyproject.toml` requires-python), `.env.example` vs `.env` key names, Docker CLI + daemon, compose file validity and image platform (arm64 vs amd64) mismatch (only when the project has a Dockerfile/compose file), free disk space, Windows long paths, PowerShell policy, line endings, WSL version and Docker Desktop engine, macOS/Linux build tools, and (only when the project declares them) Go, Ruby, Java, Rust, .NET, pnpm, Yarn and Bun pins, `.env` not git-ignored, `node_modules` vs lockfile, and declared ports already in use.
- The version-range matcher covers common npm/PEP 440 syntax; pre-releases and exotic ranges report `skip` rather than guess.
- The Python version compared is the interpreter running DevReady, not necessarily your project's virtualenv.

## Roadmap

- [x] Docker CLI + daemon reachability, `.tool-versions`, `.env` key-name diff, disk space, git identity, `devready explain`
- [x] Port-in-use checks, more ecosystems (Go, Rust, Java, Ruby, .NET, pnpm/yarn/bun), JUnit/SARIF output, `fix --plan`, GitHub Action
- [x] `.devready.json` config, `--baseline` snapshots
- [x] Platform-specific checks (Windows, macOS/Linux build tools, WSL)
- [x] Docker compose validity, image platform, Docker Desktop engine
- [x] Exact version-switch commands in suggestions (first: `fnm`)
- [ ] Monorepo `--recursive`, org `--policy` file, VS Code extension (see [ROADMAP.md](ROADMAP.md))
- [ ] Standalone binaries

Have a setup problem DevReady should catch? [Open an issue](https://github.com/Evalogical-Inc/devReady/issues/new/choose). Early feedback shapes the roadmap.

## Contributing

PRs welcome, especially new read-only checks and platform fixes. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [technical plan](docs/technical-plan.md); background research is in [docs/research.md](docs/research.md). Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

```bash
ruff check . && ruff format --check . && pytest
```

## About Evalogical

DevReady is built and maintained by [Evalogical](https://evalogical.com/), a software company offering AI-enabled product engineering, custom software and IT services. Need help with a product or an engineering team? [Talk to us](https://evalogical.com/contactus).

## License

[MIT](LICENSE) © Evalogical Inc

<div align="center">

If DevReady saved you an afternoon, a ⭐ helps others find it.

</div>
