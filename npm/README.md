# devready-cli (npm launcher)

```bash
npx devready-cli check
```

DevReady checks, read-only, whether your machine meets a project's declared requirements (`.nvmrc`, `engines`, `packageManager`, `.python-version`, `go.mod`, ...) and tells you what to fix.

This npm package runs the [`devready-cli`](https://pypi.org/project/devready-cli/) Python package of the same version through [`uv`](https://docs.astral.sh/uv/) (`uvx`) or `pipx`, so one of those must be installed. Every argument is passed through, along with the exit code.

Docs, flags and the GitHub Action: https://github.com/Evalogical-Inc/devReady
