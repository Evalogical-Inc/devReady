# Using DevReady with coding agents

DevReady is a CLI; agents call `devready check --format json` (schema: `schema.json`).

## Requirements

- Python 3.10+ for the CLI itself.
- For the **plugin's MCP server** and the `uvx` examples below: [`uv`](https://docs.astral.sh/uv/) installed and on PATH. Without it the MCP server reports "Connection closed". The skill and `/devready:doctor` still work without it if `devready` is installed (`pipx install devready-cli` or `pip install devready-cli`).

## Claude Code

```text
/plugin marketplace add Evalogical-Inc/devReady
/plugin install devready --marketplace Evalogical-Inc/devReady
```

Local test: `claude --plugin-dir .` in this repo. Adds the `devready` skill, `/devready:doctor` and the MCP server (`.mcp.json`).

## OpenAI Codex and other agents

- `AGENTS.md` in this repo already tells agents when to run it.
- The skill is a standard `skills/devready/SKILL.md`; copy the folder into your agent's skills directory (for Codex, check the current location in the Codex docs; it has changed between versions).
- MCP: `devready mcp` runs a stdio server with one read-only tool, `check_environment` (optional `project` path). Example `~/.codex/config.toml` entry (verify keys against current Codex docs):

```toml
[mcp_servers.devready]
command = "uvx"
args = ["--from", "devready-cli", "devready", "mcp"]
```

No `uv`? Install the CLI (`pipx install devready-cli` or `pip install devready-cli`) and use `command = "devready"`, `args = ["mcp"]` instead.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| MCP server "Connection closed" | `uvx` not found. Install `uv`, or install the CLI and point the MCP config at `devready mcp`. |
| `devready: command not found` | Not installed, or its scripts folder is not on PATH. Run `python -m devready check` or reinstall with `pipx`. |
| `python -m devready` fails | The package is not installed for that Python. `pip install devready-cli`. |
