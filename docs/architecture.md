# Architecture

```
cli.py  ->  runner.run_checks(root)  ->  checks/*  ->  list[Result]
                  |                                        |
          .devready.json skip                 filters (--only/--skip), --baseline diff
                                                           |
                                    text | json | junit | sarif | fix plan   (formats.py)
```

- `models.py`: `Result` and `Status`. Every check returns `Result`s; nothing else crosses a boundary.
- `runner.py`: runs the checks in order, applies the config `skip` list. `mcp_server.py` calls it too.
- `checks/`: `tools` (Git/Node/npm), `python_check`, `project` (pin files), `runtimes` (Go, Ruby, Java, Rust, .NET, pnpm, Yarn, Bun), `health` (.env ignored, node_modules, ports), `extras` (Docker, git identity, disk), `platform_checks`, `config` (`.devready.json`).
- `versions.py`: tiny range matcher; anything it cannot parse is `skip`, never a guess.
- `explain.py`: one text per check id; `docs/checks.md` mirrors it (enforced by a test).
- `baseline.py`: compares a run with a saved JSON report. DevReady never writes it.

Rules every check follows: fixed argv with a timeout, regular files only (no symlinks, 1 MB cap), report only parsed or validated values.
