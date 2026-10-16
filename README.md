<div align="center">

# 🩺 DevReady

### "Works on my machine" - finally answered before it wastes your afternoon.

**A zero-dependency, read-only CLI that checks whether your machine actually meets a project's declared requirements, and tells you exactly what to fix.**
Built for humans, CI, and AI coding agents (Claude Code, Codex, any MCP client).

[![CI](https://github.com/Evalogical-Inc/devReady/actions/workflows/ci.yml/badge.svg)](https://github.com/Evalogical-Inc/devReady/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devready-cli)](https://pypi.org/project/devready-cli/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies: 0](https://img.shields.io/badge/dependencies-0-brightgreen)
![Status: alpha](https://img.shields.io/badge/status-alpha-orange)

</div>

---

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
uvx --from devready-cli devready check
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
devready check --project ../app   # inspect another project's pins
devready check --format json      # machine-readable (see docs/schema.json)
devready explain docker.daemon    # what a check means and how to fix it
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

## Use it with AI coding agents

DevReady ships the same engine three ways, so your agent can verify the environment *before* it installs, builds or tests.

**Claude Code** - plugin with a skill, a `/devready:doctor` command and an MCP server:

```text
/plugin marketplace add Evalogical-Inc/devReady
/plugin install devready --marketplace Evalogical-Inc/devReady
```

**Any MCP client** (Codex, Cursor, ...) - one read-only tool, `check_environment`:

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

See [SECURITY.md](SECURITY.md) to report a vulnerability.

## Limitations (alpha)

- Checks today: Python, Git (+ identity set), Node.js, npm, project pins (`.nvmrc`, `.node-version`, `.python-version`, `.tool-versions`, `package.json` engines, `pyproject.toml` requires-python), `.env.example` vs `.env` key names, Docker CLI + daemon (only when the project has a Dockerfile/compose file), and free disk space.
- The version-range matcher covers common npm/PEP 440 syntax; pre-releases and exotic ranges report `skip` rather than guess.
- The Python version compared is the interpreter running DevReady, not necessarily your project's virtualenv.

## Roadmap

- [x] Docker CLI + daemon reachability, `.tool-versions`, `.env` key-name diff, disk space, git identity, `devready explain`
- [ ] Port-in-use checks (ports read from compose files)
- [ ] More ecosystems (Go, Rust, Java, Ruby pins)
- [ ] Standalone binaries

Have a setup problem DevReady should catch? [Open an issue](https://github.com/Evalogical-Inc/devReady/issues/new/choose). Early feedback shapes the roadmap.

## Contributing

PRs welcome, especially new read-only checks and platform fixes. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [technical plan](docs/technical-plan.md); background research is in [docs/research.md](docs/research.md). Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

```bash
ruff check . && pytest
```

## License

[MIT](LICENSE) © Evalogical Inc

<div align="center">

If DevReady saved you an afternoon, a ⭐ helps others find it.

</div>
