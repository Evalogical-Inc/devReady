# Changelog

## 0.0.2 - 2026-10-16
- Docker CLI/daemon check (only when a Dockerfile or compose file exists), `.tool-versions`, `.env.example` vs `.env` key names (values never read), git identity presence, free disk space.
- `devready explain <check_id>`.

## 0.0.1 (unreleased)
- `devready check` (text/JSON): Python, Git, Node, npm; compares `.nvmrc`, `.node-version`, `.python-version`, `package.json` engines, `pyproject.toml` requires-python.
- `devready mcp`: stdio MCP server with a read-only `check_environment` tool.
- Claude Code plugin (skill, `/devready:doctor`, MCP config) and `AGENTS.md`.
