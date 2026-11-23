import * as fs from "node:fs";
import * as vscode from "vscode";
import { debounce, isWatched, resolveFinding } from "./paths";
import { NotInstalledError, isCheckId, runCheck, runExplain, runFixPlan } from "./runner";
import { Finding, parseSarif, summarize } from "./sarif";

const DEBOUNCE_MS = 500;

/** Length of a 1-based line, so the squiggle covers the line. Pin files are small; cap the read. */
function lineLength(file: string, line: number): number {
  try {
    if (fs.statSync(file).size > 1_000_000) return 1;
    return fs.readFileSync(file, "utf8").split(/\r?\n/)[line - 1]?.length || 1;
  } catch {
    return 1;
  }
}

function toDiagnostic(f: Finding, file: string): vscode.Diagnostic {
  const line = (f.line ?? 1) - 1;
  const d = new vscode.Diagnostic(
    new vscode.Range(line, 0, line, lineLength(file, line + 1)),
    f.message, // plain text only
    f.level === "error" ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning,
  );
  d.source = "DevReady";
  d.code = f.ruleId;
  return d;
}

/** "Explain this check" on any DevReady diagnostic. It only explains; it never fixes anything. */
class ExplainActions implements vscode.CodeActionProvider {
  static readonly kinds = [vscode.CodeActionKind.QuickFix];

  provideCodeActions(_doc: vscode.TextDocument, _range: vscode.Range, ctx: vscode.CodeActionContext) {
    return ctx.diagnostics
      .filter((d) => d.source === "DevReady" && typeof d.code === "string" && isCheckId(d.code))
      .map((d) => {
        const a = new vscode.CodeAction("DevReady: Explain this check", vscode.CodeActionKind.QuickFix);
        a.diagnostics = [d];
        a.command = { command: "devready.explain", title: "Explain", arguments: [d.code] };
        return a;
      });
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
  item.command = "devready.check";
  const diagnostics = vscode.languages.createDiagnosticCollection("devready");
  const output = vscode.window.createOutputChannel("DevReady"); // read-only for the user
  context.subscriptions.push(item, diagnostics, output);
  let lastIds: string[] = [];

  async function show(title: string, work: () => Promise<string>): Promise<void> {
    output.clear();
    output.appendLine(title);
    output.appendLine("");
    try {
      output.appendLine((await work()) || "(no output)");
    } catch (e) {
      output.appendLine(
        e instanceof NotInstalledError
          ? "DevReady is not installed. Try `pipx install devready-cli` or `uv tool install devready-cli`."
          : `DevReady failed: ${(e as Error).message}`,
      );
    }
    output.show(true);
  }

  async function explain(arg?: unknown): Promise<void> {
    let id = typeof arg === "string" ? arg : undefined;
    if (!id) {
      id = lastIds.length
        ? await vscode.window.showQuickPick(lastIds, { placeHolder: "Check to explain" })
        : await vscode.window.showInputBox({ prompt: "Check id, e.g. project.python.requires" });
    }
    id = id?.trim();
    if (!id) return;
    const checkId = id;
    await show(`DevReady: ${checkId}`, () => runExplain(checkId));
  }

  async function fixPlan(): Promise<void> {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) return;
    await show("DevReady: fix plan (suggestions only, nothing is run)", () =>
      runFixPlan(folder.uri.fsPath),
    );
  }

  function publish(folder: string, findings: Finding[]): void {
    const byFile = new Map<string, vscode.Diagnostic[]>();
    for (const f of findings) {
      if (!f.uri) continue; // tool-only result: shown in the status bar only
      const file = resolveFinding(folder, f.uri, fs.existsSync);
      if (!file) continue;
      byFile.set(file, [...(byFile.get(file) ?? []), toDiagnostic(f, file)]);
    }
    diagnostics.clear();
    for (const [file, list] of byFile) diagnostics.set(vscode.Uri.file(file), list);
  }

  let running = false;
  let rerun = false;
  async function check(): Promise<void> {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) return;
    if (running) {
      rerun = true; // a save arrived mid-run: run once more when this one ends
      return;
    }
    running = true;
    item.text = "DevReady: $(sync~spin)";
    item.show();
    try {
      const findings = parseSarif(await runCheck(folder.uri.fsPath));
      publish(folder.uri.fsPath, findings);
      lastIds = [...new Set(findings.map((f) => f.ruleId).filter(isCheckId))];
      item.text = summarize(findings);
      item.backgroundColor = findings.some((f) => f.level === "error")
        ? new vscode.ThemeColor("statusBarItem.errorBackground")
        : findings.length
          ? new vscode.ThemeColor("statusBarItem.warningBackground")
          : undefined;
      item.tooltip = "Click to re-run DevReady";
    } catch (e) {
      diagnostics.clear();
      item.backgroundColor = undefined;
      if (e instanceof NotInstalledError) {
        item.text = "DevReady: not installed";
        item.tooltip = "Install with `pipx install devready-cli` or `uv tool install devready-cli`";
      } else {
        item.text = "DevReady: error";
        item.tooltip = "DevReady could not read the check result";
      }
    } finally {
      running = false;
      if (rerun) {
        rerun = false;
        void check();
      }
    }
  }

  const onSave = debounce(() => void check(), DEBOUNCE_MS);
  context.subscriptions.push(
    { dispose: () => onSave.cancel() },
    vscode.workspace.onDidSaveTextDocument((doc) => {
      if (isWatched(doc.fileName)) onSave.call();
    }),
    // The command returns the promise so callers (and tests) can await the run.
    vscode.commands.registerCommand("devready.check", check),
    vscode.commands.registerCommand("devready.explain", explain),
    vscode.commands.registerCommand("devready.fixPlan", fixPlan),
    vscode.languages.registerCodeActionsProvider({ scheme: "file" }, new ExplainActions(), {
      providedCodeActionKinds: ExplainActions.kinds,
    }),
  );
  void check();
}

export function deactivate(): void {}
