# Security model

DevReady is read-only and local. See [SECURITY.md](../SECURITY.md) to report a vulnerability.

- **Commands:** fixed argument lists, short timeouts, no shell. Never built from project content.
- **Files:** only named files, regular files only, symlinks skipped, 1 MB cap, never executed.
- **Output:** only parsed digits, validated version specs, validated names and fixed phrases. Raw file or command output is never echoed, so a hostile `.nvmrc` or `package.json` cannot inject instructions into an agent reading the JSON. Tests check this.
- **Secrets:** environment and `.env` values are never read into output; only variable names (validated) and presence.
- **Network:** none. The only socket use is connecting to `127.0.0.1` ports the project declares.
- **Writes:** none. `init`, `fix --plan` and `--baseline` print or read; saving files is up to you.
- **Known limit:** project-declared ids and names pass through validated character sets, not an allowlist of meanings.
