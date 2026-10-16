# Changelog

## Unreleased
- `check --baseline FILE` (and `baseline:` Action input): show only results that changed since a saved JSON report.
- Optional `.devready.json` (`skip`, `require`, `env`) and `devready init` (prints a starter).

## 0.1.0 - 2026-10-16
- GitHub Action (`action.yml`) wrapping `devready check`.
- `--format junit|sarif`, `--only`/`--skip` filters, and `devready fix --plan` (suggestions only).
- Project health: `.env` not git-ignored, `node_modules` missing/older than lockfile, declared ports already in use.
- pnpm, Yarn and Bun checks when `package.json` `packageManager` names them.
- Go, Ruby, Java, Rust and .NET checks, run only when the project pins them (`go.mod`, `.ruby-version`, `.java-version`, `rust-toolchain[.toml]`, `global.json`, `.tool-versions`).

## 0.0.4 - 2026-10-16
- `python -m devready` entry point.
- Skill, `/devready:doctor` and `AGENTS.md` now fall back to `python -m devready`, `uvx`, then `pipx run`, and tell the user how to install instead of failing.
- Docs: requirements (`uv` for the plugin MCP server), no-`uv` MCP config and a troubleshooting table.

## 0.0.3 - 2026-10-16
- Add project website (https://devready-ten.vercel.app/) to package metadata.

## 0.0.2 - 2026-10-16
- Docker CLI/daemon check (only when a Dockerfile or compose file exists), `.tool-versions`, `.env.example` vs `.env` key names (values never read), git identity presence, free disk space.
- `devready explain <check_id>`.

## 0.0.1 (unreleased)
- `devready check` (text/JSON): Python, Git, Node, npm; compares `.nvmrc`, `.node-version`, `.python-version`, `package.json` engines, `pyproject.toml` requires-python.
- `devready mcp`: stdio MCP server with a read-only `check_environment` tool.
- Claude Code plugin (skill, `/devready:doctor`, MCP config) and `AGENTS.md`.
