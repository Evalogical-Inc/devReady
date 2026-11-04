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

## Add it to your project's AGENTS.md

One line is enough for most agents. Paste this into your project's `AGENTS.md` (or `CLAUDE.md`):

```markdown
Before installing dependencies or running builds/tests, run `devready check --format json` and read the result. A `fail` means a declared requirement is unmet: tell the user instead of working around it.
```

The check is read-only and also reports which Python it used, so an agent starting a fresh shell sees the same interpreter it will get.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| MCP server "Connection closed" | `uvx` not found. Install `uv`, or install the CLI and point the MCP config at `devready mcp`. |
| `devready: command not found` | Not installed, or its scripts folder is not on PATH. Run `python -m devready check` or reinstall with `pipx`. |
| `python -m devready` fails | The package is not installed for that Python. `pip install devready-cli`. |


What's next:
1. Release 1.3.0. Unreleased now holds the 4 Docker checks, exact fix commands, SARIF file locations, the Action's output input and the text output changes. Follow the new checklist, then tag v1.3.0. That's what actually gets the new checks to plugin users.
2. Post the contributor issues by running the script with --post:
! python "C:\Users\nithi\AppData\Local\Temp\claude\D--code-PL2025-devready\86fa0eb3-afa4-46a1-8007-c5c5217c9328\scratchpad\file_issues.py" --post
   One of those issues is the Docker checks tracking issue, which should be closed now that they've shipped.
3. Next feature: monorepo --recursive or the VS Code extension. The extension is the most visible, and the most likely to attract users and sponsors.

The 4 Docker checks still haven't been run against a real Docker install. Run devready check once on a machine with Docker before tagging.