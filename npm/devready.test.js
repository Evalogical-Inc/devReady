"use strict";

const assert = require("node:assert");
const test = require("node:test");
const { candidates, run } = require("./bin/devready.js");
const { version } = require("./package.json");

const missing = () => ({ error: Object.assign(new Error("not found"), { code: "ENOENT" }) });

test("pins the PyPI release to this package's version", () => {
  assert.deepStrictEqual(candidates("1.2.3"), [
    ["uvx", ["devready-cli@1.2.3"]],
    ["pipx", ["run", "--spec", "devready-cli==1.2.3", "devready"]],
  ]);
});

test("uses uvx and passes args and the exit code through", () => {
  const calls = [];
  const code = run(["check", "--quiet"], (cmd, args) => (calls.push([cmd, args]), { status: 1 }));
  assert.strictEqual(code, 1);
  assert.deepStrictEqual(calls, [["uvx", [`devready-cli@${version}`, "check", "--quiet"]]]);
});

test("falls back to pipx when uvx is missing", () => {
  const seen = [];
  const code = run(["check"], (cmd) => (seen.push(cmd), cmd === "uvx" ? missing() : { status: 0 }));
  assert.strictEqual(code, 0);
  assert.deepStrictEqual(seen, ["uvx", "pipx"]);
});

test("exits 2 with install help when neither runner exists", (t) => {
  t.mock.method(process.stderr, "write", () => true);
  assert.strictEqual(run(["check"], missing), 2);
  assert.match(process.stderr.write.mock.calls[0].arguments[0], /uv .* or pipx/);
});
