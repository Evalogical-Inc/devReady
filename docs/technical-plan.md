## DevReady --- Developer Environment Doctor

## Technical Design and Implementation Plan

**Document status:** Proposal / implementation guide\
**Project type:** Open-source command-line developer tool\
**Initial language:** Python\
**Proposed package name:** `devready` (verify package-name availability
before publishing)\
**License:** MIT (confirm this choice fits your goals before release)

------------------------------------------------------------------------

## 1. Project summary

DevReady is a command-line tool that checks a developer's local
environment for common setup problems and explains practical next steps.

It aims to answer questions such as:

-   Is Python or Node.js installed and available on `PATH`?
-   Is the installed version compatible with the project requirements?
-   Are Git and other common development tools available?
-   Are expected environment variables present, without printing their
    values?
-   Is Docker installed, and is its daemon reachable?
-   What should the developer check next when a test fails?

DevReady should be diagnostic and transparent. It must not silently
install packages, modify configuration, delete files, or change the
user's system.

### Problem statement

Environment setup instructions are often spread across README files,
package manifests, CI configuration, and troubleshooting discussions.
When a setup fails, beginners may not know which command to run or how
to interpret the result.

DevReady consolidates selected checks into one readable report and gives
users safe, actionable troubleshooting guidance.

### Goals

1.  Detect common missing tools and version mismatches.
2.  Explain findings in beginner-friendly language.
3.  Produce both human-readable and machine-readable output.
4.  Run locally without uploading environment details.
5.  Be extensible so contributors can add checks.
6.  Work consistently across Windows, macOS, and Linux where the check
    is supported.

### Non-goals for the first release

-   Automatically repair the operating system or install dependencies.
-   Guarantee that every project will build successfully.
-   Replace official package managers, language version managers, or
    security scanners.
-   Collect telemetry or upload diagnostic reports.
-   Claim full compatibility with every tool and platform.

------------------------------------------------------------------------

## 2. Intended users

-   Students setting up their first development environment.
-   Developers switching between projects.
-   Maintainers writing setup documentation.
-   Educators and bootcamp instructors supporting learners.
-   CI maintainers who want a simple environment preflight report.

------------------------------------------------------------------------

## 3. MVP scope

Keep the first release small enough to test and maintain.

### Required checks

  -----------------------------------------------------------------------
  Check                   Initial behavior        Safety notes
  ----------------------- ----------------------- -----------------------
  Python                  Detect executable and   Do not assume one
                          report version          version suits every
                                                  project

  Git                     Detect executable and   Do not read credentials
                          report version          or repository secrets

  Node.js                 Detect executable and   Use `node --version`;
                          report version          do not run project
                                                  scripts

  npm                     Detect executable and   Do not install or
                          report version          update packages

  Docker CLI              Detect executable and   Daemon connectivity can
                          report version          be an optional separate
                                                  check

  PATH                    Check whether selected  Never print the entire
                          executables can be      PATH by default
                          resolved                

  Environment variables   Check explicitly        Report present/missing
                          configured variable     only; never print
                          names                   values

  Project files           Recognize selected      Do not execute project
                          files such as           configuration
                          `pyproject.toml`,       
                          `package.json`, or      
                          `.nvmrc`                
  -----------------------------------------------------------------------

### MVP commands

``` text
devready check
devready check --format json
devready check --project .
devready doctor
devready --version
devready --help
```

Suggested behavior:

-   `check`: run safe environment checks and print a summary.
-   `check --format json`: output a stable JSON report for automation.
-   `check --project PATH`: inspect supported project metadata in the
    selected directory.
-   `doctor`: show findings with explanations and suggested next steps.
    In the MVP, it should not make changes.
-   `--version` and `--help`: standard CLI behavior.

Do not implement every command immediately. Start with `devready check`
and add options once the core behavior is reliable.

### Example terminal output

``` text
DevReady — Environment Check

[PASS] Python       3.12.2 found
[PASS] Git          2.45.1 found
[WARN] Node.js      Not found
[SKIP] Docker       Check not enabled

Summary: 2 passed, 1 warning, 1 skipped

Suggested next step:
Install Node.js if the project you are working on requires it.
See the official Node.js installation documentation.

No changes were made to your system.
```

This is illustrative output, not a claim about an actual run. Use
official documentation links in the implemented help text.

------------------------------------------------------------------------

## 4. Product principles

1.  **Local-first:** no network access is required for basic checks.
2.  **Read-only by default:** checks must not modify files or system
    configuration.
3.  **Explain the result:** every warning should explain why it matters
    and what a user can do.
4.  **Be honest about uncertainty:** distinguish a missing tool from a
    tool that could not be checked.
5.  **Protect secrets:** never print environment variable values,
    tokens, passwords, or full environment dumps.
6.  **Cross-platform:** use Python's standard library where possible and
    test on Windows, macOS, and Linux.
7.  **Accessible output:** readable text first; color is optional and
    must not be the only way to communicate status.
8.  **No false guarantees:** a passing environment check does not
    guarantee that an application will build or run.

------------------------------------------------------------------------

## 5. Proposed technology stack

### Core

-   Python 3.10+ as an initial compatibility target (validate this
    choice against dependencies and supported platforms).
-   `argparse` for the first CLI version, or Typer if a richer command
    interface is justified.
-   `subprocess` for calling narrowly defined version commands.
-   `shutil.which` for executable discovery.
-   `json` for machine-readable output.
-   `pathlib` for filesystem paths.
-   `pytest` for tests.
-   Ruff for linting and formatting.
-   GitHub Actions for continuous integration.
-   `pyproject.toml` for packaging and tool configuration.

Prefer the Python standard library for the first release to keep
installation lightweight. Add dependencies only when they provide clear
value.

### Packaging and distribution

Start with installation from a cloned repository and an editable
install. Once tests and package metadata are ready, publish a package to
a Python package index only after verifying the project name, ownership,
and release workflow.

Potential later distribution methods:

-   Python package index
-   Standalone executable
-   Homebrew or other package-manager formula, if community demand
    justifies it

Do not promise support for a distribution channel until it has been
tested and documented.

------------------------------------------------------------------------

## 6. Architecture

Use a small, modular architecture:

``` text
User command
    |
    v
CLI / argument parser
    |
    v
Check orchestrator
    |
    +--> Python check
    +--> Git check
    +--> Node.js check
    +--> npm check
    +--> Docker check
    +--> Project metadata checks
    |
    v
Normalized result objects
    |
    +--> Human-readable formatter
    +--> JSON formatter
    |
    v
Exit code
```

### Suggested repository structure

``` text
devready/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   ├── workflows/
│   │   └── ci.yml
│   ├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── roadmap.md
│   └── screenshots/
├── src/
│   └── devready/
│       ├── __init__.py
│       ├── cli.py
│       ├── orchestrator.py
│       ├── models.py
│       ├── formatters/
│       │   ├── __init__.py
│       │   ├── text.py
│       │   └── json.py
│       └── checks/
│           ├── __init__.py
│           ├── base.py
│           ├── python_check.py
│           ├── git_check.py
│           ├── node_check.py
│           ├── npm_check.py
│           └── docker_check.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

This is a target structure. Create files as needed rather than
generating empty modules for features that are not implemented yet.

### Normalized result model

Each check should return a predictable result with fields such as:

-   `check_id`: stable identifier, such as `python.version`.
-   `title`: short human-readable name.
-   `status`: one of `pass`, `warn`, `fail`, `skip`, or `error`.
-   `summary`: concise finding.
-   `details`: optional non-sensitive diagnostic information.
-   `suggestion`: safe next step.
-   `docs_url`: optional official documentation link.

Keep the model independent from terminal formatting. Both text and JSON
output should use the same result objects.

Define and document the difference between `fail`, `warn`, and `error`.
For example, a missing optional tool may be a warning, while a failed
internal check may be an error.

------------------------------------------------------------------------

## 7. Implementation details and safety requirements

### Running external commands safely

-   Use argument lists with `subprocess.run`, not shell command strings.
-   Set a short timeout for each external command.
-   Capture output and limit how much is retained.
-   Handle missing executables, non-zero exit codes, invalid text
    output, and timeouts.
-   Never execute commands constructed from user-provided strings.
-   Do not invoke package installation, shell profiles, project scripts,
    or build commands as part of diagnostics.
-   Avoid exposing raw command output when it may contain sensitive
    information.

For example, checking a version should invoke a fixed executable and
fixed argument list such as `git --version`. Do not use `shell=True` for
routine checks.

### Environment variable checks

-   Check only variable names explicitly configured by a check or user.
-   Return `present` or `missing`; do not return the variable's value.
-   Never dump all environment variables.
-   Avoid printing secrets in exception messages or debug logs.

### Filesystem checks

-   Read only the specific project files required for supported checks.
-   Set file-size limits and handle invalid encodings.
-   Do not follow symlinks or scan the entire home directory by default.
-   Never modify a user's project files during a check.
-   Clearly state which directory was inspected.

### Network behavior

The MVP should not require network access. If online vulnerability or
update checks are added later, make them explicit, document the
destination and data sent, and provide offline behavior.

### Exit codes

Document stable exit codes before the first release. A possible scheme:

-   `0`: checks completed with no blocking failures.
-   `1`: one or more checks reported a blocking failure.
-   `2`: invalid CLI usage or configuration.
-   `3`: DevReady encountered an internal error.

If this scheme is adopted, keep it consistent across releases and JSON
output.

------------------------------------------------------------------------

## 8. Testing strategy

### Unit tests

Test each check independently, including:

-   executable found and missing;
-   supported, unsupported, and unexpected version output;
-   timeout and non-zero exit status;
-   malformed project metadata;
-   absent and present environment variables;
-   output formatting and JSON schema;
-   exit-code mapping.

Mock subprocess calls where appropriate. Unit tests should not depend on
which tools happen to be installed on the developer's machine.

### Integration tests

-   Run the CLI as a subprocess.
-   Verify `--help`, `--version`, text output, JSON output, and exit
    codes.
-   Test a temporary project directory with known fixture files.
-   Confirm that diagnostics do not change fixture files.

### Cross-platform tests

Use a GitHub Actions matrix for supported operating systems:

-   Ubuntu
-   Windows
-   macOS

Start with the operating systems you can realistically maintain. Add
platform-specific checks only when behavior is defined and tested on
that platform.

### Quality gates

Every pull request should run:

1.  Unit and integration tests.
2.  Lint and formatting checks.
3.  Type checks, if adopted.
4.  Packaging/build validation.
5.  Secret scanning or other repository security checks where available.

Never put real credentials in test fixtures or CI secrets unless
strictly necessary.

------------------------------------------------------------------------

## 9. Implementation roadmap

The roadmap below is a suggested sequence. Adjust it after the first
working prototype.

### Phase 0 --- Validate the problem (1--2 days)

-   [ ] Search GitHub and package indexes for similar environment
    diagnostic tools.
-   [ ] Read issue trackers and user discussions to identify recurring
    setup failures.
-   [ ] Write down the target user and the first three problems DevReady
    will solve.
-   [ ] Check whether the name `DevReady` and intended package name are
    already in use.
-   [ ] Create a short project proposal and ask a few developers for
    feedback.

**Deliverable:** a scoped problem statement and initial MVP
specification.

### Phase 1 --- Repository foundation (1--2 days)

-   [ ] Create a public GitHub repository.
-   [ ] Add the README, license, `.gitignore`, and `pyproject.toml`.
-   [ ] Establish the `src/` layout and test structure.
-   [ ] Add formatting, linting, and a basic CI workflow.
-   [ ] Add issue templates and a pull request template.
-   [ ] Publish the roadmap and contribution instructions.

**Deliverable:** a clean repository that contributors can install, test,
and understand.

### Phase 2 --- Core CLI (2--4 days)

-   [ ] Implement `devready --help` and `devready --version`.
-   [ ] Implement a single `devready check` command.
-   [ ] Create the normalized result model.
-   [ ] Implement the text formatter.
-   [ ] Add stable exit-code behavior.
-   [ ] Add tests for the CLI and result model.

**Deliverable:** a working CLI with a small number of reliable checks.

### Phase 3 --- Initial diagnostics (3--5 days)

-   [ ] Add Python and Git checks.
-   [ ] Add Node.js and npm checks.
-   [ ] Add Docker CLI detection, clearly distinguishing CLI
    availability from daemon availability.
-   [ ] Add safe project metadata detection.
-   [ ] Add actionable suggestions and official documentation links.
-   [ ] Test missing tools, timeouts, and unexpected command output.

**Deliverable:** the first useful end-to-end environment report.

### Phase 4 --- JSON and project mode (2--4 days)

-   [ ] Add `--format json`.
-   [ ] Add `--project PATH`.
-   [ ] Define and document the JSON schema.
-   [ ] Add fixture-based integration tests.
-   [ ] Confirm JSON output does not include secret values or
    unnecessary machine details.

**Deliverable:** output that both people and automation can consume.

### Phase 5 --- Reliability and release readiness (2--4 days)

-   [ ] Run tests on supported operating systems.
-   [ ] Verify installation in a clean virtual environment.
-   [ ] Review dependency and license choices.
-   [ ] Review error messages, accessibility, and security behavior.
-   [ ] Record known limitations.
-   [ ] Capture a terminal screenshot or short demo.
-   [ ] Prepare release notes and a version tag.

**Deliverable:** a tested MVP ready for public feedback.

### Phase 6 --- Community feedback (ongoing)

-   [ ] Ask early users to try the documented installation steps.
-   [ ] Label small, well-defined issues as `good first issue`.
-   [ ] Prioritize recurring user problems over speculative features.
-   [ ] Review pull requests and release fixes.
-   [ ] Update the roadmap based on evidence.
-   [ ] Publish a changelog for each release.

**Deliverable:** a maintainable project with a contribution process.

### Rough time estimate

A focused MVP may take around 2--4 weeks of part-time work, depending on
experience and platform coverage. Cross-platform edge cases, packaging,
and community support can take longer.

------------------------------------------------------------------------

## 10. GitHub repository setup

### Repository description

> A local-first CLI that diagnoses common developer environment setup
> issues and provides safe, actionable troubleshooting guidance.

### Suggested topics

`developer-tools`, `cli`, `python`, `diagnostics`,
`developer-experience`, `open-source`

Use only topics that accurately describe the implemented project.

### Branch and pull request workflow

1.  Keep `main` releasable.
2.  Create a focused branch for each issue.
3.  Write or update tests with the change.
4.  Run the documented checks locally.
5.  Open a pull request with the problem, solution, test evidence, and
    limitations.
6.  Require CI to pass before merging.
7.  Use releases and a changelog to communicate changes.

Avoid adding complicated branching rules until the project has multiple
regular contributors.

------------------------------------------------------------------------

## 11. Inviting collaborators

Do not invite people only to increase contributor counts. Give them a
clear reason and a small task they can complete.

### Prepare before inviting people

-   [ ] Ensure a fresh clone can be installed by following the README.
-   [ ] Make sure CI works.
-   [ ] Add `CONTRIBUTING.md`.
-   [ ] Add a code of conduct and a security reporting process.
-   [ ] Create 3--5 real, scoped issues.
-   [ ] Mark only genuinely beginner-friendly issues as
    `good first issue`.
-   [ ] State the expected behavior and acceptance criteria for each
    issue.
-   [ ] Explain how contributors can run tests.

### Example first issues

1.  Add tests for missing Git executable behavior.
2.  Improve the Windows version parsing test cases.
3.  Add a JSON output example to the README.
4.  Improve the message shown when Node.js is missing.
5.  Add a tested project metadata check for one supported file.

These are candidate issues; verify that they are still needed before
opening them.

### Example collaboration invitation

> Hi! I'm building DevReady, an open-source CLI that helps developers
> diagnose common local environment setup issues. I'm preparing the
> initial MVP and would appreciate feedback on the design and usability.
>
> The project is focused on safe, read-only checks, clear
> troubleshooting guidance, and cross-platform reliability. If this area
> interests you, you can review the roadmap or pick up a small issue in
> the repository.
>
> Contributions, bug reports, documentation improvements, and
> suggestions are welcome. Please open an issue before starting a larger
> change so we can agree on the approach.

Personalize this message when contacting a maintainer or developer. Do
not mass-message strangers or imply that they have already agreed to
collaborate.

### Contributor onboarding

`CONTRIBUTING.md` should explain:

-   what the project does and does not do;
-   prerequisites and local setup;
-   how to run tests, linting, and formatting;
-   how to create a branch and submit a pull request;
-   the expected test coverage for a change;
-   code style and commit conventions, if any;
-   how maintainers make decisions and review contributions;
-   how to report security issues privately.

------------------------------------------------------------------------

## 12. README.md requirements

The README is the project's front door. It should help a new user
understand the problem, decide whether the tool is relevant, install it,
run it, and contribute.

Recommended order:

1.  Project name and one-line explanation.
2.  Project status: prototype, alpha, beta, or stable.
3.  Badges only when they reflect real CI, release, or license status.
4.  Problem statement and intended audience.
5.  Features that are already implemented.
6.  Supported platforms and prerequisites.
7.  Installation instructions.
8.  Quick-start command.
9.  Example output and explanation.
10. Command reference and JSON output example.
11. Safety, privacy, and data-handling guarantees.
12. Limitations and unsupported cases.
13. Development setup and test commands.
14. How to report bugs and request features.
15. Contribution guidelines and code of conduct.
16. License and acknowledgments.

Do not advertise planned features as if they already work. Mark future
functionality as planned.

### README installation example

Replace these examples with commands that have been tested against the
actual packaging configuration.

``` bash
git clone https://github.com/YOUR_USERNAME/devready.git
cd devready
python -m venv .venv
```

Activate the virtual environment:

``` bash
# macOS / Linux
source .venv/bin/activate
```

``` powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install in editable mode:

``` bash
python -m pip install -e ".[dev]"
devready check
```

This assumes the `dev` optional dependency group and CLI entry point
have been configured in `pyproject.toml`. Implement and verify them
before publishing these commands as final instructions.

### Screenshot or demo

Capture a real terminal run after the CLI is functional. A useful demo
should show:

-   the command being run;
-   at least one passing check;
-   at least one warning;
-   a clear suggested next step;
-   a statement that the check made no system changes.

Save images in `docs/screenshots/` and reference them with relative
paths. Do not use mock output as proof of implemented behavior.

------------------------------------------------------------------------

## 13. Suggested project metadata

Configure `pyproject.toml` with:

-   build system;
-   package name, version, description, and supported Python versions;
-   license and project URLs;
-   runtime dependencies;
-   optional development dependencies;
-   CLI entry point, such as `devready = "devready.cli:main"`;
-   pytest configuration;
-   Ruff configuration.

Keep metadata consistent with the actual license file, supported
versions, and release state.

------------------------------------------------------------------------

## 14. Open-source license and project governance

-   Choose a recognized license after considering how you want others to
    reuse the code.
-   MIT is a simple permissive option, but it is not the right choice
    for every project or organization.
-   Include the full license text and copyright notice as appropriate.
-   Do not copy code or documentation from other projects without
    checking its license and attribution requirements.
-   Add a code of conduct to define expected community behavior.
-   Add a security policy explaining where to report vulnerabilities.
-   Document how maintainers will handle bug reports, feature requests,
    and contributions.

A license does not guarantee adoption or prevent every possible misuse.
Seek qualified legal advice if the project has unusual licensing or
commercial requirements.

------------------------------------------------------------------------

## 15. Security and privacy checklist

Before every release, confirm:

-   [ ] No environment variable values are printed.
-   [ ] No credentials, tokens, or personal machine details are included
    in examples.
-   [ ] External commands use fixed argument lists and timeouts.
-   [ ] No user-provided string is executed as shell code.
-   [ ] File inspection is limited to documented paths and file types.
-   [ ] Diagnostics do not modify system configuration or project files.
-   [ ] Network behavior is absent or explicitly documented.
-   [ ] Exceptions do not leak sensitive command output.
-   [ ] Dependencies are reviewed and pinned or constrained where
    appropriate.
-   [ ] CI does not expose secrets to untrusted pull-request code.

------------------------------------------------------------------------

## 16. Success metrics

Measure whether DevReady helps people, not just whether the repository
receives stars.

Potential indicators:

-   Users successfully install and run the CLI by following the README.
-   Issues reveal recurring problems that the tool can address.
-   Contributors outside the original author submit useful changes.
-   Supported-platform tests remain reliable.
-   Releases reduce known defects without adding regressions.
-   Users report that a diagnostic message helped them resolve a setup
    issue.
-   Documentation questions and repeated setup failures decrease over
    time.

Do not add telemetry by default just to measure adoption. Use voluntary
feedback, public issue discussions, and opt-in surveys first.

------------------------------------------------------------------------

## 17. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Similar tools already exist         Research alternatives and focus on
                                      a clear gap

  False warnings frustrate users      Explain confidence and allow
                                      optional checks to be skipped

  Platform differences cause bugs     Use a CI matrix and
                                      platform-specific tests

  Tool accidentally exposes secrets   Never print variable values; add
                                      regression tests

  Project scope becomes too large     Keep a strict MVP and defer
                                      auto-fixing

  Contributors cannot get started     Maintain reproducible setup steps
                                      and small issues

  Project becomes unmaintained        Publish realistic support
                                      expectations and keep releases
                                      small
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 18. Definition of Done for the first public release

The MVP is ready for a public release when:

-   [ ] A new user can install it using the README.
-   [ ] `devready check` works on the explicitly supported platforms.
-   [ ] At least Python and Git checks have automated tests.
-   [ ] Missing tools and command timeouts are handled gracefully.
-   [ ] Text output is readable and JSON output is valid, if JSON is
    included in the release.
-   [ ] Exit codes are documented and tested.
-   [ ] Checks are read-only and do not reveal secret values.
-   [ ] CI passes on the supported operating systems.
-   [ ] License, contribution guide, code of conduct, and security
    policy are present.
-   [ ] Known limitations are documented.
-   [ ] A real example or demo is included.
-   [ ] A release note explains what is included and what is not.

------------------------------------------------------------------------

## 19. First seven actions

If you are starting today, do these in order:

1.  Research existing projects and document the specific gap DevReady
    will address.
2.  Create the GitHub repository and add this plan as
    `docs/technical-plan.md`.
3.  Write a short README that clearly labels the project as an early
    prototype.
4.  Set up `pyproject.toml`, the `src/devready/` package, and pytest.
5.  Implement one reliable check: Python executable detection and
    version reporting.
6.  Add tests for success, missing executable, and unexpected output.
7.  Publish the initial code and ask for focused feedback before adding
    more checks.

**Guiding principle:** A small, safe, well-tested tool that solves one
recurring problem is a better first release than a large collection of
unreliable diagnostics.
