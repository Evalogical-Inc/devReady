# Execution plan: VS Code extension (#45)

**Branch:** `feat/vscode-extension` · **Tracking:** #45 · **Design source:** section 7 of
[features-5-8.md](features-5-8.md). This file adds the work breakdown, acceptance checks and risks.
It does not change the design.

## 1. Goal

Give developers daily visibility of DevReady inside VS Code:

- a status-bar item (`DevReady: ✓`, `DevReady: 2 warn`, `DevReady: 1 fail`),
- diagnostics on the pin file in the Problems panel,
- a re-run when a watched pin file is saved.

## 2. Constraints (from the issue and plan)

- Lives in `vscode/`, TypeScript, **no runtime dependencies** beyond the VS Code API.
- Never runs fix commands. No telemetry. Disabled in untrusted workspaces.
- No change to the Python CLI, its output, exit codes or check ids. The extension only reads
  `devready check --format sarif`.
- Falls back to `uvx devready-cli` when `devready` is not on PATH (same idea as `npm/`).
- Publishing needs `VSCE_PAT` / `OVSX_PAT` secrets, which only maintainers can add.

## 3. Facts about the SARIF the extension consumes

Verified against `devready check --format sarif` (1.3.0):

- Only non-pass results are emitted. An empty `results` array means all green (`✓`).
- `level` is `error` (fail or error status) or `warning` (warn status).
- `locations[0].physicalLocation.artifactLocation.uri` is relative to the **repository root**
  (not the `--project` folder) and `region.startLine` is 1-based. Tool-only results have no
  location.
- The process exits `1` when a hard requirement fails, **but stdout is still valid SARIF**, so a
  non-zero exit must not be treated as a crash.
- Message text contains only parsed versions and fixed wording. It is still treated as untrusted
  text (shown as plain text, never as markdown or HTML).

## 4. Work breakdown (one PR per step)

| Step | Scope | Verified here | Depends on |
|---|---|---|---|
| 1 | Scaffold: `vscode/package.json`, activation on pin files, status bar, run + parse SARIF, unit tests | yes | none |
| 2 | Diagnostics on the pin file, debounced on-save watcher, `@vscode/test-electron` tests, CI job (Ubuntu only) | partly (CI is GitHub only) | step 1 |
| 3 | Commands `DevReady: Check`, `Explain…`, `Show fix plan`; "Explain this check" code action | yes | step 2 |
| 4 | Publish job in `publish.yml` for VS Marketplace and Open VSX | no | maintainer secrets |
| 5 | README badge and GIF | partly | published extension |

### Step 5 detail (this branch)

Done now (true before publishing): a "Use it in VS Code" section in `README.md` (what it does,
install from a checkout with `npm run package` and `code --install-extension`) and a CHANGELOG
line. The roadmap checkbox for #45 stays **unticked** until the extension is on a marketplace.

**Deliberately not done yet** (would be false or impossible before step 4 setup):
- Marketplace badge: it would show "extension not found" until the first publish.
- The GIF: it needs a screen recording of the real extension.

After the first successful publish, paste into the README badge row:

```md
[![VS Code](https://img.shields.io/visual-studio-marketplace/v/evalogical.devready-vscode?label=VS%20Code)](https://marketplace.visualstudio.com/items?itemName=evalogical.devready-vscode)
[![Open VSX](https://img.shields.io/open-vsx/v/evalogical/devready-vscode?label=Open%20VSX)](https://open-vsx.org/extension/evalogical/devready-vscode)
```

(`publisher.name` comes from `vscode/package.json`; adjust if the publisher id changes.) Then
replace the install-from-source block with the marketplace install, tick the #45 roadmap boxes
in `README.md` and `ROADMAP.md`, and add `docs/devready-vscode-demo.gif` next to the CLI demo.

**GIF shot list (about 15 s, under 1 MB, 800 px wide):**
1. Open a folder whose `.nvmrc` says `99`: status bar shows `DevReady: 1 warn`, amber (a Node pin mismatch is a warning; use a failing requirement, such as `requires-python = ">=99"`, to show a red `1 fail`).
2. Problems panel lists the diagnostic on `.nvmrc`; click it to jump to line 1.
3. Quick fix: "DevReady: Explain this check" opens the output channel.
4. Edit `.nvmrc` to the installed Node major and save: the diagnostic disappears, status bar
   goes to `DevReady: ✓`.
Record with ScreenToGif (Windows) or similar; no secrets or personal paths in frame.

### Step 4 detail

- Packaging: `npm run package` builds `vscode/devready.vsix` (9 files, about 9 KB: manifest,
  README, LICENSE, compiled `out/`). `.vscodeignore` keeps tests, fixtures and sources out.
  `@vscode/vsce` and `ovsx` are dev dependencies, so the lockfile pins them.
- `publish.yml`: new `vscode` job after `publish`, on full-version tags only (no `-rc` tags).
  It runs `npm ci`, `npm test`, `npm run package`, uploads the `.vsix` as a run artifact, then
  publishes to the VS Marketplace (`VSCE_PAT`) and Open VSX (`OVSX_PAT`) with `--skip-duplicate`,
  so a re-run does not fail on an existing version.
- A missing secret skips that registry with a warning; it does not fail the release or touch the
  PyPI, npm, Homebrew or MCP jobs.
- `ci.yml`: the `vscode` job also runs `npm run package`, so a broken package fails the PR.
- Versioning: the extension is versioned by `vscode/package.json` (currently `0.1.0`), not by the
  CLI tag. Bump it when the extension changes; an unchanged version is skipped.

**Maintainer setup still required (cannot be done from a branch):**
1. Create the publisher `evalogical` on the VS Marketplace and on Open VSX (and, for Open VSX,
   sign the publisher agreement). Change `publisher` in `vscode/package.json` if another id is used.
2. Add repository secrets `VSCE_PAT` (Azure DevOps PAT, scope Marketplace: Manage) and `OVSX_PAT`.
3. Decide whether to drop `"private": true`; it does not affect `vsce`/`ovsx`.

**Not verified here:** the publish steps themselves (no secrets, nothing is uploaded), and the
workflow on GitHub. Verified locally: both workflow files parse, the `.vsix` builds, `npm ci`
matches the lockfile, and both CLIs accept the flags used.

### Step 3 detail

- Commands: `DevReady: Explain…` (pick from the last run's check ids, or type one),
  `DevReady: Show fix plan` (`devready fix --plan`). Output goes to a read-only `DevReady` output
  channel. Nothing is ever executed from a plan; the channel title says so.
- Code action: "DevReady: Explain this check" (quick fix) on every DevReady diagnostic.
- Safety: a check id is passed to the CLI only if it matches `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$`
  (no leading dash, no spaces or shell characters), as a single argv element.
- Tests: `test/runner.test.js` (id validation, exact argv for explain and fix plan, bad ids never
  spawn); integration suite also checks the code action and that all three commands are registered
  and run. Note: the built-in code-action command needs the document open, so the test opens it.

### Step 2 detail

- `src/paths.ts` (pure): watched pin-file list, `resolveFinding` (workspace folder, then parents,
  refusing absolute and `..` paths), `debounce`.
- `src/extension.ts`: a `DiagnosticCollection`; one diagnostic per located finding on its line
  (plain text, source `DevReady`, code = check id); tool-only results stay in the status bar.
  `onDidSaveTextDocument` on a watched file triggers a 500 ms debounced re-run; a save during a
  run queues exactly one more run.
- Tests: `test/paths.test.js` (unit) and `test-integration/` (`@vscode/test-electron`): a fixture
  `.nvmrc` of `99` must raise a diagnostic on line 1, and saving the fixed pin must clear it.
- CI: new `vscode` job in `ci.yml`, Ubuntu only: `npm test`, then `xvfb-run npm run test:integration`.

**Known local quirk:** `@vscode/test-electron` breaks on a repo path containing spaces. CI paths have
none. Locally set `DEVREADY_EXT_ROOT` to a space-free junction to the `vscode/` folder.

### Step 1 detail

1. `vscode/package.json`: manifest, activation events for pin files, `capabilities.untrustedWorkspaces`
   set to `false`, scripts `compile` / `test`.
2. `vscode/src/sarif.ts`: pure parser. SARIF text to findings and a status-bar summary. No `vscode`
   import, so it is unit-testable with `node --test`.
3. `vscode/src/runner.ts`: choose the command (`devready`, else `uvx devready-cli`), spawn with a
   fixed argv list (never a shell), timeout, return stdout.
4. `vscode/src/extension.ts`: status bar item, click to re-run, run on activation.
5. `vscode/test/sarif.test.js`: parser and summary tests, including a hostile-text case and the
   non-zero-exit case.
6. Add `.vscode`-style ignores (`out/`, `node_modules/`) to the repo `.gitignore`.

**Done when (step 1):**
- `npm run compile` and `npm test` pass in `vscode/`.
- Parser handles: no results, warn only, fail + warn, missing locations, malformed JSON.
- Command spawn uses an argv array and never `shell: true`.

## 5. Overall acceptance (matches the issue)

- A project with a mismatched `.nvmrc` shows a diagnostic on that file and `DevReady: 1 warn`.
- Saving a pin file re-runs the check.
- The extension is published to both marketplaces from `publish.yml`.

## 6. Risks and open questions

| Risk | Handling |
|---|---|
| Neither `devready` nor `uvx` installed | Status bar shows `DevReady: not installed` with a hint; no crash |
| SARIF paths are repo-root relative, workspace may be a subfolder | Resolve against the workspace, then walk up parents until the file exists (step 2) |
| `devready` on Windows resolves to the Microsoft Store `python` placeholder | Known bug F1 in the review report (separate fix, not part of this branch) |
| Marketplace publisher names and secrets | Maintainer task; step 4 stays blocked until then |
| Windows and macOS extension-host tests | Out of scope: plan says Ubuntu only |

## 7. Working rules for this branch

- Work is local and **uncommitted** until the owner reviews it.
- The unrelated Windows Python-alias fix lives in the main checkout and is not on this branch.
