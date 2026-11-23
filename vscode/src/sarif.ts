// Pure SARIF handling: no `vscode` import, so it can be tested with `node --test`.

export type Level = "error" | "warning";

export interface Finding {
  ruleId: string;
  level: Level;
  message: string;
  uri?: string; // relative to the repository root
  line?: number; // 1-based
}

/** Parse `devready check --format sarif` output. Throws on anything that is not SARIF. */
export function parseSarif(text: string): Finding[] {
  const doc = JSON.parse(text);
  const runs = doc && Array.isArray(doc.runs) ? doc.runs : null;
  if (!runs) throw new Error("not a SARIF document");
  const findings: Finding[] = [];
  for (const run of runs) {
    for (const r of Array.isArray(run?.results) ? run.results : []) {
      const loc = r?.locations?.[0]?.physicalLocation;
      const line = loc?.region?.startLine;
      findings.push({
        ruleId: String(r?.ruleId ?? "devready"),
        level: r?.level === "error" ? "error" : "warning",
        message: String(r?.message?.text ?? ""),
        uri: typeof loc?.artifactLocation?.uri === "string" ? loc.artifactLocation.uri : undefined,
        line: Number.isInteger(line) && line > 0 ? line : undefined,
      });
    }
  }
  return findings;
}

/** Status-bar text: `DevReady: ✓`, `DevReady: 2 warn`, `DevReady: 1 fail, 2 warn`. */
export function summarize(findings: Finding[]): string {
  const fail = findings.filter((f) => f.level === "error").length;
  const warn = findings.length - fail;
  const parts: string[] = [];
  if (fail) parts.push(`${fail} fail`);
  if (warn) parts.push(`${warn} warn`);
  return `DevReady: ${parts.length ? parts.join(", ") : "✓"}`;
}
