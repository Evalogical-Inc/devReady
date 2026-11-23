"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { parseSarif, summarize } = require("../out/sarif.js");
const { runCheck, NotInstalledError } = require("../out/runner.js");

const sarif = (results) => JSON.stringify({ version: "2.1.0", runs: [{ results }] });
const res = (level, extra = {}) => ({ ruleId: "x", level, message: { text: "m" }, ...extra });
const at = (uri, line) => ({
  locations: [{ physicalLocation: { artifactLocation: { uri }, region: { startLine: line } } }],
});

test("no results is all green", () => {
  const f = parseSarif(sarif([]));
  assert.deepStrictEqual(f, []);
  assert.strictEqual(summarize(f), "DevReady: ✓");
});

test("warn only", () => {
  const f = parseSarif(sarif([res("warning"), res("warning")]));
  assert.strictEqual(summarize(f), "DevReady: 2 warn");
});

test("fail and warn together", () => {
  const f = parseSarif(sarif([res("error"), res("warning"), res("warning")]));
  assert.strictEqual(summarize(f), "DevReady: 1 fail, 2 warn");
});

test("location is read, missing location is allowed", () => {
  const [a, b] = parseSarif(sarif([res("error", at("a/.nvmrc", 3)), res("warning")]));
  assert.deepStrictEqual([a.uri, a.line], ["a/.nvmrc", 3]);
  assert.deepStrictEqual([b.uri, b.line], [undefined, undefined]);
});

test("bad line numbers are dropped", () => {
  const f = parseSarif(sarif([res("error", at("f", 0)), res("error", at("f", "7"))]));
  assert.deepStrictEqual(f.map((x) => x.line), [undefined, undefined]);
});

test("hostile message text stays plain text", () => {
  const text = "<script>alert(1)</script>";
  const [f] = parseSarif(sarif([{ ruleId: "x", level: "error", message: { text } }]));
  assert.strictEqual(f.message, text);
});

test("malformed or non-SARIF input throws", () => {
  assert.throws(() => parseSarif("not json"));
  assert.throws(() => parseSarif("{}"));
});

test("missing runners give NotInstalledError", async () => {
  await assert.rejects(
    runCheck(".", 5000, [{ cmd: "definitely-not-a-real-command-xyz", prefix: [] }]),
    NotInstalledError,
  );
});

test("non-zero exit still returns stdout", async () => {
  const out = await runCheck(".", 5000, [
    { cmd: process.execPath, prefix: ["-e", "console.log('{\"runs\":[]}');process.exit(1)", "--"] },
  ]);
  assert.match(out, /runs/);
});
