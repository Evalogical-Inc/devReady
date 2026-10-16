# Stability and versioning

From 1.0, these are the public interface. Breaking any of them needs a major version.

## JSON report (`--format json`, `docs/schema.json`)

- `schema_version` is `1`. Fields and enum values in the schema are frozen for the 1.x line.
- Allowed in a minor release: new check ids, new result summaries and suggestions (free text, never parse them).
- Needs `schema_version: 2` and a major release: adding, removing or renaming a result field, adding a status, changing a field's type.
- Check ids match `^[a-z_]+(\.[a-z_]+)+$`. Renaming or removing an id is breaking; adding one is not.
- Statuses: `pass`, `warn`, `fail`, `skip`, `error`. `fail` means a declared requirement is unmet; `skip`/`error` mean "not evaluated".

## Exit codes (`check`)

`0` no blocking failure, `1` at least one `fail` (with `--baseline`: a new or worse `fail`), `2` usage error, `3` internal error.

## Config and CLI

- `.devready.json` keys (`skip`, `require`, `env`) are frozen; unknown keys make the file invalid by design.
- Existing flags keep their meaning. New flags are minor releases.

## Not covered

Human-readable text output, JUnit/SARIF layout details beyond their formats, summary wording, and the Python import API (`devready.*` modules are internal).
