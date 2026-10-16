# Using DevReady with coding agents

DevReady is a CLI; agents call `devready check --format json` (schema: `schema.json`).

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
args = ["--from", "git+https://github.com/Evalogical-Inc/devReady", "devready", "mcp"]
```

The CLI must be installed first: `pipx install git+https://github.com/Evalogical-Inc/devReady` (PyPI release planned).
