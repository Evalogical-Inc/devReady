# Check catalog

Every check id DevReady can emit. Ids are a public API (see [versioning.md](versioning.md)).
`devready explain <id>` prints the same text. A test fails if an id is missing from this file.

| Check id | What it means |
|---|---|
| `bun.version` | Bun runtime and package manager; checked only when package.json packageManager names bun. |
| `disk.space` | Warns below 1 GB free where the project lives; installs and builds can fail when the disk is full. |
| `docker.cli` | Shown only when the project has a Dockerfile or compose file and the docker command is missing. |
| `docker.compose.valid` | Validates compose files with `docker compose config` (local parse, no daemon needed). Output is never shown; files using include: are skipped. |
| `docker.daemon` | The Docker CLI can exist while the daemon is stopped. Start Docker Desktop or the service. |
| `dotnet.version` | The .NET SDK; checked only when the project has a global.json or a dotnet pin. |
| `git.identity` | Commits need user.name and user.email. DevReady checks they exist, never what they are. |
| `git.version` | Git is needed to clone, branch and commit. Install: https://git-scm.com/downloads |
| `go.version` | Go toolchain; checked only when the project has a go.mod or a golang line in .tool-versions. |
| `java.version` | Java runtime; checked only when the project pins it (.java-version or .tool-versions). |
| `node.version` | Node.js runs JavaScript tooling. Many projects pin a version; see project.node.* checks. |
| `npm.version` | npm installs JavaScript dependencies and ships with Node.js. |
| `platform.autocrlf` | Windows only, in a git repo without .gitattributes. Unset core.autocrlf can flip line endings between Windows and Linux/macOS contributors. |
| `platform.build_tools` | macOS/Linux, when the project has binding.gyp, setup.py, Gemfile or Cargo.toml. Native dependencies need a compiler (Xcode CLT on macOS, cc/gcc/clang and make on Linux). |
| `platform.exec_policy` | Windows only, when package.json exists. A Restricted or AllSigned PowerShell policy blocks npm.ps1 ('running scripts is disabled'). Use cmd or relax the policy for your user. |
| `platform.long_paths` | Windows only, when package.json exists. Without LongPathsEnabled, deeply nested node_modules paths can exceed 260 characters and installs fail. |
| `pnpm.version` | pnpm package manager; checked only when package.json packageManager names pnpm. |
| `project.bun.pin` | package.json packageManager pins the Bun version. |
| `project.bun.tool_versions` | .tool-versions (asdf/mise) pins Bun for this project. |
| `project.config.file` | .devready.json is optional. With unknown keys or invalid values it is ignored entirely. Run `devready init` for a starter. |
| `project.dotnet.global` | global.json sdk.version pins the .NET SDK for this project. |
| `project.dotnet.tool_versions` | .tool-versions (asdf/mise) pins .NET for this project. |
| `project.env.ignored` | Warns when .env exists but git would commit it (not ignored, or already tracked). Values are never shown. |
| `project.env.keys` | Compares variable NAMES in .env.example with .env. Values are never read or shown. |
| `project.env.required` | Variable NAMES listed under env in .devready.json must be set in the environment. Values are never read. |
| `project.go.mod` | The go directive in go.mod is the minimum Go version. A lower toolchain fails the check. |
| `project.go.tool_versions` | .tool-versions (asdf/mise) pins Go for this project. |
| `project.java.pin` | .java-version pins Java for this project (jenv, mise). |
| `project.java.tool_versions` | .tool-versions (asdf/mise) pins Java for this project. |
| `project.node.config` | require.node in .devready.json is a hard requirement (fails when unmet). |
| `project.node.engines` | package.json engines.node is a hard requirement. A mismatch fails the check and npm may refuse to install. |
| `project.node.modules` | Checked when package.json lists dependencies: node_modules must exist and not be older than a lockfile. |
| `project.node.pin` | A .nvmrc/.node-version file says which Node the team uses. A mismatch is a warning; switch with nvm, fnm or mise. |
| `project.node.tool_versions` | .tool-versions (asdf/mise) pins Node for this project. |
| `project.pnpm.pin` | package.json packageManager pins the pnpm version (corepack enable can install it). |
| `project.pnpm.tool_versions` | .tool-versions (asdf/mise) pins pnpm for this project. |
| `project.ports.free` | Ports declared in compose files (host side), `*PORT=` lines in `.env.example`, or `--port`/`-p`/`PORT=` in `package.json` scripts, tested by connecting to localhost. A busy port may be this project already running. |
| `project.python.config` | require.python in .devready.json is a hard requirement (fails when unmet). |
| `project.python.pin` | .python-version (pyenv/uv) pins Python for this project. |
| `project.python.requires` | pyproject.toml requires-python is a hard requirement; pip refuses incompatible versions. |
| `project.python.tool_versions` | .tool-versions (asdf/mise) pins Python for this project. |
| `project.ruby.gemfile` | A literal ruby declaration in Gemfile pins Ruby when .ruby-version has no readable version. Reads quoted major.minor or major.minor.patch versions, with optional trailing comments; never evaluates Ruby. A mismatch is a warning. |
| `project.ruby.pin` | .ruby-version pins Ruby for this project (rbenv, rvm, mise). |
| `project.ruby.tool_versions` | .tool-versions (asdf/mise) pins Ruby for this project. |
| `project.rust.tool_versions` | .tool-versions (asdf/mise) pins Rust for this project. |
| `project.rust.toolchain` | rust-toolchain(.toml) pins the Rust channel. Named channels such as stable are reported as not evaluated. |
| `project.yarn.pin` | package.json packageManager pins the Yarn version (corepack enable can install it). |
| `project.yarn.tool_versions` | .tool-versions (asdf/mise) pins Yarn for this project. |
| `python.version` | The Python interpreter running DevReady; not necessarily your project's virtualenv. |
| `ruby.version` | Ruby interpreter; checked only when the project pins it (.ruby-version, Gemfile or .tool-versions). |
| `rust.version` | Rust compiler (rustc); checked only when the project has a rust-toolchain file or pin. |
| `yarn.version` | Yarn package manager; checked only when package.json packageManager names yarn. |
