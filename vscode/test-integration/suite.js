"use strict";
// Runs inside the VS Code extension host. `.nvmrc` in the fixture asks for Node 99.
const assert = require("node:assert");
const fs = require("node:fs");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const vscode = require("vscode");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitFor(fn, what, ms = 30000) {
  const end = Date.now() + ms;
  for (;;) {
    const v = fn();
    if (v) return v;
    if (Date.now() > end) throw new Error(`timed out waiting for ${what}`);
    await sleep(200);
  }
}

function nvmrcDiagnostics() {
  const folder = vscode.workspace.workspaceFolders[0].uri.fsPath;
  return vscode.languages.getDiagnostics(vscode.Uri.file(path.join(folder, ".nvmrc")));
}

exports.run = async function run() {
  const folder = vscode.workspace.workspaceFolders[0].uri.fsPath;
  const nvmrc = path.join(folder, ".nvmrc");

  // 1. A mismatched .nvmrc produces a diagnostic on that file.
  await vscode.commands.executeCommand("devready.check");
  const first = await waitFor(() => nvmrcDiagnostics().length > 0 && nvmrcDiagnostics(), "diagnostic on .nvmrc");
  assert.strictEqual(first[0].source, "DevReady");
  assert.strictEqual(first[0].range.start.line, 0);
  assert.ok(first[0].severity <= vscode.DiagnosticSeverity.Warning);

  // 1b. The diagnostic offers "Explain this check", and the commands are registered and run.
  await vscode.workspace.openTextDocument(nvmrc); // the built-in command needs an open model
  const actions = await vscode.commands.executeCommand(
    "vscode.executeCodeActionProvider",
    vscode.Uri.file(nvmrc),
    first[0].range,
  );
  const explain = actions.find((a) => a.title === "DevReady: Explain this check");
  assert.ok(explain, "explain code action is offered");
  assert.strictEqual(explain.command.command, "devready.explain");
  assert.strictEqual(explain.command.arguments[0], first[0].code);
  const commands = await vscode.commands.getCommands(true);
  for (const c of ["devready.check", "devready.explain", "devready.fixPlan"]) assert.ok(commands.includes(c), c);
  await vscode.commands.executeCommand("devready.explain", first[0].code);
  await vscode.commands.executeCommand("devready.fixPlan");

  // 2. Fixing the pin and saving re-runs the check and clears the diagnostic.
  const original = fs.readFileSync(nvmrc, "utf8");
  // The Node that devready finds on PATH, so the pin is satisfied.
  const nodeMajor = execFileSync("node", ["--version"]).toString().trim().slice(1).split(".")[0];
  try {
    const doc = await vscode.workspace.openTextDocument(nvmrc);
    const editor = await vscode.window.showTextDocument(doc);
    await editor.edit((e) => e.replace(new vscode.Range(0, 0, 0, 100), nodeMajor));
    await doc.save();
    await waitFor(() => nvmrcDiagnostics().length === 0, "diagnostic cleared after save");
  } finally {
    fs.writeFileSync(nvmrc, original); // leave the fixture as found
  }
};
