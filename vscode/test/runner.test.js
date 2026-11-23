"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { isCheckId, runExplain, runFixPlan } = require("../out/runner.js");

// A fake `devready`: node printing its own argv tail, so we see exactly what would be passed.
const echo = [{ cmd: process.execPath, prefix: ["-e", "console.log(process.argv.slice(1).join(' '))", "--"] }];

test("check ids: real ids pass", () => {
  for (const id of ["project.python.requires", "git.identity", "disk.space", "a", "x-y_z.1"]) {
    assert.ok(isCheckId(id), id);
  }
});

test("check ids: options, paths, spaces and shell text are refused", () => {
  for (const bad of ["", "-h", "--version", ".hidden", "a b", "a;b", "a/b", "$(x)", "a\nb", "x".repeat(101)]) {
    assert.ok(!isCheckId(bad), JSON.stringify(bad));
  }
});

test("explain passes the id as one argument after `explain`", async () => {
  assert.strictEqual(await runExplain("project.python.requires", echo), "explain project.python.requires");
});

test("explain never runs anything for a bad id", async () => {
  await assert.rejects(runExplain("--version", echo), /not a check id/);
  await assert.rejects(runExplain("a b", echo), /not a check id/);
});

test("fix plan always asks for --plan", async () => {
  assert.strictEqual(await runFixPlan("proj", echo), "fix --plan --project proj");
});
