# Using DevReady with coding agents

DevReady is a CLI; agents call `devready check --format json` (schema: `schema.json`).

## Claude Code

```text
/plugin marketplace add <owner>/devready
/plugin install devready --marketplace <owner>/devready
```

Local test: `claude --plugin-dir .` in this repo. Adds the `devready` skill, `/devready:doctor` and the MCP server (`.mcp.json`).

## OpenAI Codex and other agents

- `AGENTS.md` in this repo already tells agents when to run it.
- The skill is a standard `skills/devready/SKILL.md`; copy the folder into your agent's skills directory (for Codex, check the current location in the Codex docs; it has changed between versions).
- MCP: `devready mcp` runs a stdio server with one read-only tool, `check_environment` (optional `project` path). Example `~/.codex/config.toml` entry (verify keys against current Codex docs):

```toml
[mcp_servers.devready]
command = "uvx"
args = ["devready", "mcp"]
```

The CLI itself must be installed (`pipx install devready` / `uvx devready`) once it is published to PyPI; until then use `pip install -e .` from a clone.
