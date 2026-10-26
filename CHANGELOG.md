# Changelog

## 1.2.0 - 2026-10-26
- The ports check now reads valid port declarations from string-valued `package.json` scripts, alongside Compose and `.env.example` files.
- Read literal Ruby versions from Gemfile when .ruby-version has no readable version (#7). Mismatches warn; Gemfile code is never executed.

## 1.1.2 - 2026-10-23
- npm launcher `devready-cli` (`npx devready-cli check`): runs the PyPI release of the same version through `uvx` or `pipx`. First published by hand as 1.1.1; from 1.1.2 it is published from `publish.yml` with npm provenance.
- The npm package page shows the full project README.

## 1.1.1 - 2026-10-23
- `devready-cli` command alias, so `uvx devready-cli check` and `uvx devready-cli mcp` work without `--from`.
- `server.json` for the MCP Registry (`io.github.Evalogical-Inc/devready`).
- CI and the GitHub Action use `actions/checkout@v7` and `actions/setup-python@v7` (Node 24).

## 1.1.0 - 2026-10-23
- `check --quiet` shows only non-pass results in text output (#3). `devready --help` and `devready check --help` now list the exit codes.
- Tests: version parsing for Windows, macOS and Debian `git`/`node`/`npm` output, plus empty output, non-zero exit and timeout (#4).
- A tool whose version command exits with an error (for example `dotnet` with only a runtime installed) now reports "Version command failed" instead of "Version output not recognized".
- Version commands now get 15 seconds instead of 5, so slow Windows shims (such as `yarn.cmd`) no longer report "Could not run version command".

## 1.0.0 - 2026-10-16
- First stable release. No behaviour changes since 0.3.0.
- From here the JSON schema (v1), check ids, exit codes and `.devready.json` keys follow the stability rules in `docs/versioning.md`; breaking any of them needs 2.0.

## 0.3.0 - 2026-10-16
- Text output now shows the suggestion under each non-passing result (community PR #6, fixes #2).
- Fix: a pin file with short hostile text (e.g. `.nvmrc`, `rust-toolchain.toml`, `global.json`, `.tool-versions`) was echoed in the summary when the matching tool was not installed. Only specs the matcher fully parses are now shown. Affects 0.2.0 and earlier.
- Docs: check catalog, architecture, security model, versioning policy; CI matrix adds Python 3.11/3.12.
- Platform checks, shown only when relevant: Windows long paths, PowerShell execution policy, `core.autocrlf`; macOS Xcode CLT and Linux compiler/make for native builds.

## 0.2.0 - 2026-10-16
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
