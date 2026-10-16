# Phase 0 research (2026-10-16)

## Name availability
- PyPI: `devready`, `devready-cli`, `devready-doctor` all returned 404 (unclaimed) at time of check. Re-check before first publish.
- GitHub: several unrelated repos named DevReady (interview prep, MVC demo, one "one-click developer environment orchestrator" with 1 star). No dominant project; low collision risk, but not unique.

## Prior art (found via web search; verify before citing publicly)
| Tool | What it does | Overlap |
|---|---|---|
| `npm doctor` | Checks npm install, registry, cache | Not project-aware |
| `flutter doctor`, `brew doctor`, `mise doctor` | Ecosystem-specific health checks | Single ecosystem |
| `npx envinfo` | Prints environment info | Detection only |
| onboard-mcp | MCP server: Node version vs `.nvmrc`/engines, Docker, git config, `.env` keys, ports | **Close**, Node-centric, MCP-only |
| Local Dev Doctor MCP | Derives probes from project manifests, user-approved | **Close**, MCP-only |
| mcpkit `check-env`/`doctor` | Node + package manager readiness | Node only |
| "envcheck" Claude skill | Prompt-only workflow comparing `.nvmrc`/`.python-version`/`.tool-versions`/engines | Same idea, not a CLI |

## Conclusion
The space is crowded with MCP-only, Node-leaning tools. A remaining gap: **a standalone, polyglot (Python + Node first), stdlib-only CLI with a stable versioned JSON schema**, usable from CI and from any agent (skill and MCP as thin wrappers). Differentiators to commit to: multi-ecosystem pins (`requires-python` + engines + `.tool-versions`), zero dependencies, prompt-injection-safe output. If that is not compelling enough, consider contributing to onboard-mcp instead.

## Agent packaging notes (from third-party sources, not official docs: verify)
- Claude Code: `.claude-plugin/plugin.json` at plugin root; `skills/<name>/SKILL.md`, `commands/`, `agents/`, `hooks/` at root; marketplace = repo with `.claude-plugin/marketplace.json`; test with `claude --plugin-dir .`; install via `/plugin marketplace add owner/repo`.
- Codex: `~/.codex/config.toml` or project `.codex/config.toml` with `[mcp_servers.<name>]` (command + args); skills in `.codex/skills`-style dirs; `AGENTS.md` for instructions. Config keys changed across recent versions: check openai/codex before documenting.
