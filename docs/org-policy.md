# Using DevReady across an organization

DevReady usually reads each project's own pins. A platform team that wants one minimum
toolchain for every repository ("Git >= 2.40, Node >= 20, Docker installed") can put that in an
**org policy** file instead of editing every project's `.devready.json`, whose keys are frozen in
1.x.

## The policy file

```json
{
  "policy_version": 1,
  "require": {"node": ">=20", "python": ">=3.11", "git": ">=2.40", "docker": "*"},
  "skip": ["platform.autocrlf"],
  "env": ["NPM_TOKEN"]
}
```

| Key | Meaning |
|---|---|
| `policy_version` | Must be `1`. |
| `require` | Tool or runtime name → version spec, or `"*"` for "installed, any version". |
| `skip` | Check ids the policy does not want reported, for every project. |
| `env` | Environment variable **names** that must be set. Values are never read. |

`require` accepts the keys DevReady knows: `git`, `node`, `npm`, `python`, `docker`, `go`, `ruby`,
`java`, `rust`, `dotnet`, `pnpm`, `yarn` and `bun`. Specs use the same version matcher as project
pins; anything it cannot parse makes the file invalid rather than guessing.

The file is strict on purpose: an unknown key, a wrong type or an unsupported spec makes the whole
file invalid, so a typo cannot silently weaken the policy.

## Run with a policy

```bash
devready check --policy org.json     # explicit path
DEVREADY_POLICY=org.json devready check   # or through the environment (the value is a path)
```

On Windows PowerShell:

```powershell
$env:DEVREADY_POLICY = "org.json"; devready check
```

A policy adds `policy.<tool>.require` results and, when `env` is used, `policy.env.required`.
Missing or too-old tools are `fail`, so the command exits `1` like any other unmet requirement. The
policy's `skip` list filters the project's other results.

Precedence:

- A repo's `.devready.json` **cannot** skip `policy.*` results.
- Neither can the policy's own `skip` list; remove the requirement instead.
- Explicit `--only`/`--skip` flags are applied last and can filter anything, including
  `policy.*`. Do not pass them in a CI run that must enforce the policy.

With `--recursive`, the policy applies to every package: its `skip` list filters each package, and
because tool versions and environment variables belong to the machine, the `policy.*` results are
reported once, under the root package (`.`).

## In CI

```yaml
- uses: Evalogical-Inc/devReady@v1.3.0   # unreleased; use a tag that contains the policy input
  with:
    policy: .devready/org-policy.json
```

The Action input is passed to the CLI unchanged. To keep the policy next to the other team
configuration, commit it under `.devready/` (or any path) and reference that file.

An unreadable or invalid policy file produces one `policy.file` **ERROR** result and never prints
the file's content or its path. Like DevReady's other `error` results it does not change the exit
code, so a CI job that must not run without a policy should also assert that `policy.file` is
absent from `--format json` output.

## Security

The policy is a local file with the same read rules as other project files: regular files only
(symlinks are not followed), 1 MB cap, content is only parsed as JSON and never echoed. Remote
URLs are not fetched; teams that want a central file can vendor it or download it in their CI job
before running DevReady.

`devready init --policy` prints a starter file you can edit.
