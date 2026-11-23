// Pure helpers (no `vscode` import) so they can be tested with `node --test`.
import * as path from "node:path";

/** Files whose save should re-run the check (basenames, case-sensitive like the CLI). */
export const WATCHED = new Set([
  ".nvmrc",
  ".node-version",
  ".python-version",
  ".ruby-version",
  ".java-version",
  ".terraform-version",
  ".tool-versions",
  ".devready.json",
  "package.json",
  "pyproject.toml",
  "go.mod",
  "Cargo.toml",
  "rust-toolchain.toml",
  "global.json",
  "composer.json",
  "pubspec.yaml",
  "pom.xml",
  "build.gradle",
  "build.gradle.kts",
]);

export function isWatched(fileName: string): boolean {
  return WATCHED.has(path.basename(fileName));
}

/**
 * SARIF uris are relative to the repository root, which can be above the opened folder.
 * Try the workspace folder, then each parent, and return the first path where the file exists.
 * Absolute uris and `..` segments are refused: a result may only point inside the tree.
 */
export function resolveFinding(
  workspaceDir: string,
  uri: string,
  exists: (p: string) => boolean,
): string | undefined {
  const parts = uri.split(/[\\/]+/);
  if (!uri || path.isAbsolute(uri) || /^[a-zA-Z]:/.test(uri) || parts.includes("..")) {
    return undefined;
  }
  let dir = workspaceDir;
  for (;;) {
    const candidate = path.join(dir, ...parts);
    if (exists(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) return undefined;
    dir = parent;
  }
}

/** Trailing-edge debounce. `cancel` drops a pending call (used on dispose). */
export function debounce(fn: () => void, ms: number): { call(): void; cancel(): void } {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return {
    call() {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        timer = undefined;
        fn();
      }, ms);
    },
    cancel() {
      if (timer) clearTimeout(timer);
      timer = undefined;
    },
  };
}
