#!/usr/bin/env node
// Runs the devready-cli Python package (same version as this npm package) via uvx or pipx.
"use strict";

const { spawnSync } = require("node:child_process");
const { version } = require("../package.json");

// Each runner downloads and caches the pinned PyPI release on first use.
function candidates(v) {
  return [
    ["uvx", [`devready-cli@${v}`]],
    ["pipx", ["run", "--spec", `devready-cli==${v}`, "devready"]],
  ];
}

function run(args, spawn = spawnSync) {
  for (const [cmd, prefix] of candidates(version)) {
    const r = spawn(cmd, [...prefix, ...args], { stdio: "inherit" });
    if (r.error && r.error.code === "ENOENT") continue; // runner not installed; try the next
    if (r.error) throw r.error;
    return r.status ?? 1;
  }
  process.stderr.write(
    "devready: needs uv (https://docs.astral.sh/uv/) or pipx to run the devready-cli Python package.\n" +
      "Install one of them, or run: pipx install devready-cli\n",
  );
  return 2; // usage error, same as the Python CLI
}

module.exports = { candidates, run };

if (require.main === module) process.exit(run(process.argv.slice(2)));
