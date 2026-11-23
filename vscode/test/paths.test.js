"use strict";
const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");
const { isWatched, resolveFinding, debounce } = require("../out/paths.js");

test("watched files are matched by basename", () => {
  assert.ok(isWatched("/a/b/.nvmrc"));
  assert.ok(isWatched("C:\\proj\\package.json"));
  assert.ok(!isWatched("/a/b/readme.md"));
  assert.ok(!isWatched("/a/b/package.json.bak"));
});

test("resolves inside the workspace folder first", () => {
  const ws = path.join(path.sep, "repo", "app");
  const want = path.join(ws, ".nvmrc");
  assert.strictEqual(resolveFinding(ws, ".nvmrc", (p) => p === want), want);
});

test("walks up when the repository root is above the workspace", () => {
  const ws = path.join(path.sep, "repo", "packages", "app");
  const want = path.join(path.sep, "repo", "packages", "app", ".nvmrc");
  const up = path.join(path.sep, "repo", "packages", "app", ".nvmrc");
  assert.strictEqual(resolveFinding(ws, "packages/app/.nvmrc", (p) => p === up || p === want), up);
  const root = path.join(path.sep, "repo", "packages", "app", "pyproject.toml");
  assert.strictEqual(resolveFinding(ws, "packages/app/pyproject.toml", (p) => p === root), root);
});

test("returns undefined when nothing exists", () => {
  assert.strictEqual(resolveFinding(path.join(path.sep, "a", "b"), "x.txt", () => false), undefined);
});

test("refuses absolute, drive and parent-escaping uris", () => {
  const yes = () => true;
  const ws = path.join(path.sep, "repo");
  for (const bad of ["/etc/passwd", "C:\\Windows\\win.ini", "../secret", "a/../../b", ""]) {
    assert.strictEqual(resolveFinding(ws, bad, yes), undefined, bad);
  }
});

test("debounce runs once after the last call and can be cancelled", async () => {
  let n = 0;
  const d = debounce(() => n++, 20);
  d.call();
  d.call();
  d.call();
  await new Promise((r) => setTimeout(r, 60));
  assert.strictEqual(n, 1);
  d.call();
  d.cancel();
  await new Promise((r) => setTimeout(r, 60));
  assert.strictEqual(n, 1);
});
