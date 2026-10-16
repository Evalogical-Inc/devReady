# DevReady

A local-first, read-only CLI that checks a project's environment requirements against what is installed, and explains what to do next.

**Status: early prototype.** Only a Python version check exists today. Everything else below is planned.

## Install (from source)

```bash
git clone <repo-url> && cd devready
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
devready check
devready check --format json
```

Exit codes: `0` ok, `1` a check failed, `2` bad usage, `3` internal error.

## Use with coding agents

Claude Code (after publishing the repo):

```text
/plugin marketplace add <owner>/devready
/plugin install devready --marketplace <owner>/devready
```

Codex and others: see [docs/agents.md](docs/agents.md). MCP: `devready mcp` (stdio).

## Planned

- Compare project pins (`.nvmrc`, `package.json` engines, `requires-python`, `.tool-versions`) with installed tools
- Git, Node, npm, Docker checks; env-var presence (names only, never values)
- See [docs/technical-plan.md](docs/technical-plan.md) and [docs/research.md](docs/research.md)

## Safety

Read-only. No network, no telemetry, no env values printed.

## License

MIT
