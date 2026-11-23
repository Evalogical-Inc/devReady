"use strict";
// Launches a real VS Code, loads this extension and runs suite.js inside it.
// Needs `devready` on PATH (pip install -e . from the repo root) and Node for the fixture.
const path = require("node:path");
const { runTests } = require("@vscode/test-electron");

async function main() {
  // DEVREADY_EXT_ROOT lets a path with spaces be passed via a space-free junction (Windows).
  const root = process.env.DEVREADY_EXT_ROOT || path.resolve(__dirname, "..");
  await runTests({
    extensionDevelopmentPath: root,
    extensionTestsPath: path.join(root, "test-integration", "suite.js"),
    launchArgs: [
      path.join(root, "test-fixtures", "mismatch"),
      "--disable-extensions",
      "--disable-workspace-trust", // the extension is off in untrusted workspaces
    ],
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
