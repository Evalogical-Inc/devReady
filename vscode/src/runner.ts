import { spawn } from "node:child_process";

export interface Candidate {
  cmd: string;
  prefix: string[];
}

export interface RunResult {
  stdout: string;
  stderr: string;
  code: number | null;
}

// Same idea as npm/bin/devready.js: the installed CLI first, then uvx.
export const CANDIDATES: Candidate[] = [
  { cmd: "devready", prefix: [] },
  { cmd: "uvx", prefix: ["devready-cli"] },
];

export class NotInstalledError extends Error {
  constructor() {
    super("devready and uvx were not found on PATH");
  }
}

// Check ids look like `project.python.requires`. Anything else is never passed to the CLI, so an
// id read from a result cannot turn into an option (leading dash) or an odd argument.
const CHECK_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$/;

export function isCheckId(id: string): boolean {
  return CHECK_ID.test(id);
}

function runOne(c: Candidate, args: string[], timeoutMs: number): Promise<RunResult> {
  return new Promise((resolve, reject) => {
    // Fixed argv list, never a shell. Each value is a single argument.
    const child = spawn(c.cmd, [...c.prefix, ...args], {
      shell: false,
      windowsHide: true,
      timeout: timeoutMs,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));
    child.on("error", reject); // ENOENT when the command is missing
    child.on("close", (code) => resolve({ stdout, stderr, code }));
  });
}

/** Run a devready command. Throws NotInstalledError if no runner exists. */
export async function runDevready(
  args: string[],
  timeoutMs = 60_000,
  candidates: Candidate[] = CANDIDATES,
): Promise<RunResult> {
  for (const c of candidates) {
    try {
      return await runOne(c, args, timeoutMs);
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code === "ENOENT") continue;
      throw e;
    }
  }
  throw new NotInstalledError();
}

/** Run the check and return SARIF text. Exit code 1 means "a requirement failed": still valid. */
export async function runCheck(
  project: string,
  timeoutMs = 60_000,
  candidates: Candidate[] = CANDIDATES,
): Promise<string> {
  const r = await runDevready(["check", "--format", "sarif", "--project", project], timeoutMs, candidates);
  return r.stdout;
}

/** `devready explain <id>`: text for the output channel. Rejects ids that are not check ids. */
export async function runExplain(id: string, candidates: Candidate[] = CANDIDATES): Promise<string> {
  if (!isCheckId(id)) throw new Error(`not a check id: ${JSON.stringify(id.slice(0, 40))}`);
  const r = await runDevready(["explain", id], 30_000, candidates);
  return (r.stdout || r.stderr).trim();
}

/** `devready fix --plan`: suggestions only. DevReady itself never runs them, nor does this. */
export async function runFixPlan(project: string, candidates: Candidate[] = CANDIDATES): Promise<string> {
  const r = await runDevready(["fix", "--plan", "--project", project], 60_000, candidates);
  return (r.stdout || r.stderr).trim();
}
