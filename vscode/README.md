# DevReady for VS Code

Is this machine ready to work on this project? DevReady reads the versions your project asks for
(`.nvmrc`, `.python-version`, `package.json` engines, `pyproject.toml`, `go.mod`, ...) and compares
them with what is installed. This extension shows the result in the editor.

- **Status bar:** `DevReady: ✓`, `DevReady: 2 warn` or `DevReady: 1 fail`. Click it to re-run.
- **Problems panel:** a diagnostic on the pin file that is not satisfied.
- **On save:** saving a pin file re-runs the check.
- **Commands:** `DevReady: Check`, `DevReady: Explain…`, `DevReady: Show fix plan`.
- **Quick fix:** "DevReady: Explain this check" on a DevReady diagnostic.

## Requirements

The extension runs the [DevReady CLI](https://github.com/Evalogical-Inc/devReady). Install it with
`pipx install devready-cli` or `uv tool install devready-cli`. If `devready` is not on your PATH,
the extension tries `uvx devready-cli`.

## Privacy and safety

- Read-only. It never runs the commands in a fix plan; it only shows them.
- No telemetry and no network calls from the extension.
- Disabled in untrusted workspaces, because it runs a local command.

[Source and issues](https://github.com/Evalogical-Inc/devReady)
