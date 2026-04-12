#!/usr/bin/env npx tsx
/**
 * Copy AI assistant chat histories for a specific workspace.
 * Handles: VS Code Copilot Extension, Copilot CLI, and Claude Code sessions.
 * Usage: npx tsx get_hist.ts <workspace-folder-name> [output-dir] [options]
 */

import fs from "fs";
import path from "path";
import os from "os";

// ─── Utilities ───────────────────────────────────────────────────────────────

function extractProjectName(folder: string): string {
  return folder
    .replace(/.*\//, "")
    .replace(/vscode-remote:\/\/wsl%2Bubuntu/g, "")
    .replace(/%20/g, " ")
    .replace(/^\./, "");
}

function encodeClaudeProjectPath(p: string): string {
  return "-" + p.replace(/^\//, "").replace(/\//g, "-");
}

function jsonExtract(data: string, key: string): string {
  const m = data.match(new RegExp(`"${key}":\\s*"([^"]+)"`));
  return m ? m[1] : "";
}

function readFileSafe(filePath: string): string {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch {
    return "";
  }
}

function readYamlCwd(filePath: string): string {
  const content = readFileSafe(filePath);
  const m = content.match(/^cwd:\s*(.+)$/m);
  return m ? m[1].trim() : "";
}

function copyRecursive(src: string, dest: string): void {
  fs.cpSync(src, dest, { recursive: true });
}

function countGlob(dir: string, pattern: RegExp): number {
  if (!fs.existsSync(dir)) return 0;
  return fs.readdirSync(dir).filter((f) => pattern.test(f)).length;
}

function subdirs(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => path.join(dir, e.name));
}

function dirSize(dir: string): string {
  let bytes = 0;
  function walk(d: string) {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else bytes += fs.statSync(full).size;
    }
  }
  try {
    walk(dir);
  } catch {}
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)}K`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)}M`;
  return `${(bytes / 1024 ** 3).toFixed(1)}G`;
}

// ─── Default paths ───────────────────────────────────────────────────────────

const HOME = os.homedir();
const IS_MACOS = process.platform === "darwin";

const DEFAULT_VS_CODE_BASE = IS_MACOS
  ? path.join(HOME, "Library/Application Support/Code/User/workspaceStorage")
  : "/mnt/c/Users";

const DEFAULT_CLI_SESSION_STATE = path.join(HOME, ".copilot/session-state");
const DEFAULT_CLAUDE_DIR = path.join(HOME, ".claude");

// ─── Argument parsing ────────────────────────────────────────────────────────

interface Args {
  projectName: string;
  outputDir: string;
  vscodePath: string;
  cliPath: string;
  claudePath: string;
  since: Date | null;   // only collect sessions starting after this time
}

function parseArgs(): Partial<Args> & { error?: string } {
  const args = process.argv.slice(2);
  const result: Partial<Args> = { since: null };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--vscode-path=")) {
      result.vscodePath = arg.slice("--vscode-path=".length);
    } else if (arg.startsWith("--cli-path=")) {
      result.cliPath = arg.slice("--cli-path=".length);
    } else if (arg.startsWith("--claude-path=")) {
      result.claudePath = arg.slice("--claude-path=".length);
    } else if (arg.startsWith("--output-dir=")) {
      result.outputDir = arg.slice("--output-dir=".length);
    } else if (arg.startsWith("--since=")) {
      const d = new Date(arg.slice("--since=".length));
      if (isNaN(d.getTime())) return { error: `Invalid --since date: ${arg}` };
      result.since = d;
    } else if (arg.startsWith("-")) {
      return { error: `Unknown option: ${arg}` };
    } else if (!result.projectName) {
      result.projectName = arg;
    } else if (!result.outputDir) {
      result.outputDir = arg;
    }
  }

  return result;
}

// ─── Session start-time probing ───────────────────────────────────────────────

/** Return the start timestamp of a Copilot CLI session directory, or null. */
function cliSessionStartTime(sessionDir: string): Date | null {
  const eventsFile = path.join(sessionDir, "events.jsonl");
  if (!fs.existsSync(eventsFile)) return null;
  try {
    const firstLine = fs.readFileSync(eventsFile, "utf8").split("\n")[0];
    if (!firstLine) return null;
    const obj = JSON.parse(firstLine);
    const ts: string =
      obj?.data?.startTime ?? obj?.timestamp ?? "";
    return ts ? new Date(ts) : null;
  } catch {
    return null;
  }
}

/** Return the start timestamp of a Claude Code JSONL session file, or null. */
function claudeSessionStartTime(filePath: string): Date | null {
  try {
    const firstLine = fs.readFileSync(filePath, "utf8").split("\n").find(Boolean) ?? "";
    if (!firstLine) return null;
    const obj = JSON.parse(firstLine);
    const ts: string = obj?.timestamp ?? "";
    return ts ? new Date(ts) : null;
  } catch {
    return null;
  }
}

// ─── VS Code path detection ──────────────────────────────────────────────────

function detectVscodePath(): string {
  if (IS_MACOS) {
    return fs.existsSync(DEFAULT_VS_CODE_BASE) ? DEFAULT_VS_CODE_BASE : "";
  }
  // WSL/Linux: search under /mnt/c/Users/<user>/AppData/...
  const candidates = ["cyber", process.env.USER ?? "", os.userInfo().username];
  for (const user of candidates) {
    if (!user) continue;
    const p = path.join(
      DEFAULT_VS_CODE_BASE,
      user,
      "AppData/Roaming/Code/User/workspaceStorage"
    );
    if (fs.existsSync(p)) return p;
  }
  if (fs.existsSync(DEFAULT_VS_CODE_BASE)) {
    for (const entry of fs.readdirSync(DEFAULT_VS_CODE_BASE, {
      withFileTypes: true,
    })) {
      if (!entry.isDirectory()) continue;
      const p = path.join(
        DEFAULT_VS_CODE_BASE,
        entry.name,
        "AppData/Roaming/Code/User/workspaceStorage"
      );
      if (fs.existsSync(p)) return p;
    }
  }
  return "";
}

// ─── List workspaces (no-arg mode) ───────────────────────────────────────────

function listWorkspaces(
  vscodePath: string,
  cliPath: string,
  claudeDir: string
): void {
  console.log(`VS Code Workspace Storage: ${vscodePath}`);
  if (fs.existsSync(vscodePath)) {
    console.log("VS Code Workspaces:");
    const names: string[] = [];
    for (const dir of subdirs(vscodePath)) {
      const wj = path.join(dir, "workspace.json");
      if (fs.existsSync(wj)) {
        const folder = jsonExtract(readFileSafe(wj), "folder");
        if (folder) names.push("  - " + extractProjectName(folder));
      }
    }
    names.sort().forEach((n) => console.log(n));
  } else {
    console.log("  (Directory not found - use --vscode-path to specify custom path)");
  }

  console.log();
  console.log(`Copilot CLI Session State: ${cliPath}`);
  if (fs.existsSync(cliPath)) {
    console.log("Copilot CLI Sessions:");
    const projects = new Set<string>();
    for (const sessionDir of subdirs(cliPath)) {
      const wyaml = path.join(sessionDir, "workspace.yaml");
      if (fs.existsSync(wyaml)) {
        const cwd = readYamlCwd(wyaml);
        if (cwd) projects.add(extractProjectName(cwd));
      }
    }
    [...projects].sort().forEach((p) => console.log(`  - ${p}`));
  } else {
    console.log("  (Directory not found - use --cli-path to specify custom path)");
  }

  console.log();
  console.log(`Claude Code Directory: ${claudeDir}`);
  const projectsDir = path.join(claudeDir, "projects");
  if (fs.existsSync(projectsDir)) {
    console.log("Claude Code Projects:");
    const names = new Set<string>();
    for (const projectDir of subdirs(projectsDir)) {
      const si = path.join(projectDir, "sessions-index.json");
      if (fs.existsSync(si)) {
        const orig = jsonExtract(readFileSafe(si), "originalPath");
        if (orig) { names.add(extractProjectName(orig)); continue; }
      }
      // Fallback: last segment of encoded dir name
      const encoded = path.basename(projectDir);
      names.add(extractProjectName(encoded.replace(/^-/, "").replace(/-/g, "/")));
    }
    [...names].sort().forEach((n) => console.log(`  - ${n}`));
  } else {
    console.log("  (Directory not found - use --claude-path to specify custom path)");
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────

function main(): void {
  const parsed = parseArgs();

  const vscodePath = parsed.vscodePath ?? detectVscodePath();
  const cliPath = parsed.cliPath ?? DEFAULT_CLI_SESSION_STATE;
  const claudeDir = parsed.claudePath ?? DEFAULT_CLAUDE_DIR;

  if (parsed.error) {
    console.error(parsed.error);
    console.error(`Usage: ${path.basename(process.argv[1])} <workspace-folder-name> [output-dir] [options]`);
    process.exit(1);
  }

  if (!parsed.projectName) {
    const script = path.basename(process.argv[1]);
    console.log(`Usage: npx tsx ${script} <workspace-folder-name> [output-dir] [options]`);
    console.log();
    console.log("Arguments:");
    console.log("  workspace-folder-name  Name of the project/workspace to copy chats from");
    console.log("  output-dir             Optional output directory (default: ./copilot-chat-history)");
    console.log();
    console.log("Options:");
    console.log("  --vscode-path=<path>   Custom VS Code workspaceStorage path");
    console.log("  --cli-path=<path>      Custom Copilot CLI session-state path");
    console.log("  --claude-path=<path>   Custom Claude Code directory path");
    console.log("  --output-dir=<path>    Explicit output directory (overrides positional argument)");
    console.log();
    console.log("Examples:");
    console.log(`  npx tsx ${script} crab`);
    console.log(`  npx tsx ${script} crab ~/workspace/crab/chat-history`);
    console.log(`  npx tsx ${script} crab --vscode-path=/custom/path/workspaceStorage`);
    console.log(`  npx tsx ${script} crab --output-dir=./output`);
    console.log();
    console.log("Detected paths:");
    listWorkspaces(vscodePath, cliPath, claudeDir);
    process.exit(1);
  }

  const projectName = parsed.projectName;
  const outputDirRaw = parsed.outputDir ?? "./copilot-chat-history";
  const outputDir = path.isAbsolute(outputDirRaw)
    ? outputDirRaw
    : path.join(process.cwd(), outputDirRaw);

  console.log("=== Configuration ===");
  console.log(`Project: ${projectName}`);
  console.log(`VS Code Workspace Storage: ${vscodePath}`);
  console.log(`Copilot CLI Session State: ${cliPath}`);
  console.log(`Claude Code Directory: ${claudeDir}`);
  console.log(`Output Directory: ${outputDir}`);
  console.log();

  let totalSessions = 0;

  // ── VS Code Copilot Extension ──────────────────────────────────────────────
  console.log("=== VS Code Copilot Extension ===");

  const vsCodeOutputDir = path.join(outputDir, "vscode-extension");
  fs.mkdirSync(vsCodeOutputDir, { recursive: true });

  let vsCodeSessionCount = 0;
  let vsCodeEditingCount = 0;

  if (fs.existsSync(vscodePath)) {
    let workspaceDir = "";
    for (const dir of subdirs(vscodePath)) {
      const wj = path.join(dir, "workspace.json");
      if (!fs.existsSync(wj)) continue;
      const content = readFileSafe(wj);
      if (content.toLowerCase().includes(projectName.toLowerCase())) {
        workspaceDir = dir;
        console.log(`Found workspace: ${dir}`);
        console.log(`  Project: ${jsonExtract(content, "folder")}`);
        break;
      }
    }

    if (workspaceDir) {
      const chatSessions = path.join(workspaceDir, "chatSessions");
      if (fs.existsSync(chatSessions)) {
        copyRecursive(chatSessions, path.join(vsCodeOutputDir, "chatSessions"));
        vsCodeSessionCount = countGlob(chatSessions, /\.jsonl$/);
        console.log(`Copied ${vsCodeSessionCount} chat session files`);
      }

      const editingSessions = path.join(workspaceDir, "chatEditingSessions");
      if (fs.existsSync(editingSessions)) {
        copyRecursive(editingSessions, path.join(vsCodeOutputDir, "chatEditingSessions"));
        vsCodeEditingCount = subdirs(editingSessions).length;
        console.log(`Copied ${vsCodeEditingCount} editing session directories`);
      }

      const wj = path.join(workspaceDir, "workspace.json");
      if (fs.existsSync(wj)) {
        fs.copyFileSync(wj, path.join(vsCodeOutputDir, "workspace.json"));
        console.log("Copied workspace.json");
      }

      totalSessions += vsCodeSessionCount;
    } else {
      console.log(`No VS Code workspace found for project '${projectName}'`);
    }
  } else {
    console.log("VS Code workspace storage directory not found");
  }

  // ── Copilot CLI Sessions ───────────────────────────────────────────────────
  console.log();
  console.log("=== Copilot CLI Sessions ===");

  const cliOutputDir = path.join(outputDir, "copilot-cli");
  fs.mkdirSync(cliOutputDir, { recursive: true });

  let cliSessionsFound = 0;

  if (fs.existsSync(cliPath)) {
    for (const sessionDir of subdirs(cliPath)) {
      const sessionId = path.basename(sessionDir);
      const wyaml = path.join(sessionDir, "workspace.yaml");
      if (!fs.existsSync(wyaml)) continue;

      const cwd = readYamlCwd(wyaml);
      if (!cwd || !cwd.toLowerCase().includes(projectName.toLowerCase())) continue;

      // Apply --since filter
      if (parsed.since) {
        const st = cliSessionStartTime(sessionDir);
        if (st !== null && st < parsed.since) continue;
      }

      console.log(`Found CLI session: ${sessionId}`);
      console.log(`  cwd: ${cwd}`);

      copyRecursive(sessionDir, path.join(cliOutputDir, sessionId));

      const standalone = path.join(cliPath, `${sessionId}.jsonl`);
      if (fs.existsSync(standalone)) {
        fs.copyFileSync(standalone, path.join(cliOutputDir, sessionId, `${sessionId}.jsonl`));
        console.log("  Copied events.jsonl (standalone format)");
      }

      if (fs.existsSync(path.join(sessionDir, "events.jsonl"))) {
        console.log("  Copied events.jsonl (new format)");
      }

      cliSessionsFound++;
    }

    if (cliSessionsFound === 0) {
      console.log(`No Copilot CLI sessions found for project '${projectName}'`);
    } else {
      console.log(`Copied ${cliSessionsFound} CLI session directories`);
      totalSessions += cliSessionsFound;
    }
  } else {
    console.log("Copilot CLI session state directory not found");
  }

  // ── Claude Code Sessions ───────────────────────────────────────────────────
  console.log();
  console.log("=== Claude Code Sessions ===");

  const claudeOutputDir = path.join(outputDir, "claude-code");
  fs.mkdirSync(claudeOutputDir, { recursive: true });

  let claudeSessionsFound = 0;
  let claudeProjectDir = "";

  if (fs.existsSync(claudeDir)) {
    const projectsDir = path.join(claudeDir, "projects");

    // Method 1: Match via sessions-index.json originalPath / projectPath
    if (fs.existsSync(projectsDir)) {
      for (const pd of subdirs(projectsDir)) {
        const si = path.join(pd, "sessions-index.json");
        if (!fs.existsSync(si)) continue;
        const data = readFileSafe(si);
        const origPath = jsonExtract(data, "originalPath");
        const projPath = jsonExtract(data, "projectPath");
        if (origPath && origPath.toLowerCase().includes(projectName.toLowerCase())) {
          claudeProjectDir = pd;
          console.log(`Found Claude project (via sessions-index originalPath): ${pd}`);
          console.log(`  Original path: ${origPath}`);
          break;
        }
        if (projPath && projPath.toLowerCase().includes(projectName.toLowerCase())) {
          claudeProjectDir = pd;
          console.log(`Found Claude project (via sessions-index projectPath): ${pd}`);
          console.log(`  Project path: ${projPath}`);
          break;
        }
      }
    }

    // Method 2: Match by encoded directory name suffix (-<projectName>)
    if (!claudeProjectDir && fs.existsSync(projectsDir)) {
      for (const pd of subdirs(projectsDir)) {
        const encoded = path.basename(pd);
        if (new RegExp(`-${projectName}$`, "i").test(encoded)) {
          claudeProjectDir = pd;
          console.log(`Found Claude project (via encoded name suffix): ${pd}`);
          break;
        }
      }
    }

    // Copy the project directory (with optional --since filtering per session file)
    if (claudeProjectDir) {
      const destProjectDir = path.join(claudeOutputDir, path.basename(claudeProjectDir));
      fs.mkdirSync(destProjectDir, { recursive: true });

      let sessionCount = 0;
      const sessionPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$/i;

      for (const entry of fs.readdirSync(claudeProjectDir, { withFileTypes: true })) {
        const src = path.join(claudeProjectDir, entry.name);
        const dst = path.join(destProjectDir, entry.name);

        if (entry.isFile() && sessionPattern.test(entry.name)) {
          // Session transcript — apply --since filter
          if (parsed.since) {
            const st = claudeSessionStartTime(src);
            if (st !== null && st < parsed.since) continue;
          }
          fs.copyFileSync(src, dst);
          sessionCount++;
        } else if (entry.isFile()) {
          // Metadata files (sessions-index.json, etc.) — always copy
          fs.copyFileSync(src, dst);
        } else if (entry.isDirectory()) {
          // Subdirectories (subagents/, etc.) — copy without filtering
          fs.cpSync(src, dst, { recursive: true });
        }
      }

      console.log(`Copied project directory with ${sessionCount} session files`);

      if (fs.existsSync(path.join(claudeProjectDir, "sessions-index.json"))) {
        console.log("  Copied sessions-index.json");
      }

      claudeSessionsFound += sessionCount;
    }

    // Method 3: Active sessions metadata
    const sessionsDir = path.join(claudeDir, "sessions");
    if (fs.existsSync(sessionsDir)) {
      for (const sessionJson of fs
        .readdirSync(sessionsDir)
        .filter((f) => f.endsWith(".json"))
        .map((f) => path.join(sessionsDir, f))) {
        const data = readFileSafe(sessionJson);
        const cwd = jsonExtract(data, "cwd");
        const sessionId = jsonExtract(data, "sessionId");
        if (!cwd || !sessionId || !cwd.toLowerCase().includes(projectName.toLowerCase())) continue;

        console.log(`Found active Claude session: ${sessionId}`);
        console.log(`  cwd: ${cwd}`);

        const envFile = path.join(claudeDir, "session-env", `${sessionId}.jsonl`);
        const envDir = path.join(claudeDir, "session-env", sessionId);
        const envOutDir = path.join(claudeOutputDir, "session-env");

        if (fs.existsSync(envFile)) {
          fs.mkdirSync(envOutDir, { recursive: true });
          fs.copyFileSync(envFile, path.join(envOutDir, `${sessionId}.jsonl`));
          console.log(`  Copied session-env/${sessionId}.jsonl`);
          claudeSessionsFound++;
        }
        if (fs.existsSync(envDir)) {
          fs.mkdirSync(envOutDir, { recursive: true });
          copyRecursive(envDir, path.join(envOutDir, sessionId));
          console.log(`  Copied session-env/${sessionId}/ directory`);
        }

        fs.mkdirSync(path.join(claudeOutputDir, "sessions"), { recursive: true });
        fs.copyFileSync(sessionJson, path.join(claudeOutputDir, "sessions", path.basename(sessionJson)));
        console.log("  Copied session metadata");
      }
    }

    // Copy matching history.jsonl entries
    const historyFile = path.join(claudeDir, "history.jsonl");
    if (fs.existsSync(historyFile)) {
      const lines = readFileSafe(historyFile)
        .split("\n")
        .filter((l) => l.toLowerCase().includes(`"project":"`) && l.toLowerCase().includes(projectName.toLowerCase()));
      if (lines.length > 0) {
        fs.mkdirSync(claudeOutputDir, { recursive: true });
        fs.writeFileSync(path.join(claudeOutputDir, "history.jsonl"), lines.join("\n") + "\n");
        console.log(`Copied ${lines.length} history entries from history.jsonl`);
        claudeSessionsFound += lines.length;
      }
    }

    // Copy file-history for matching sessions
    const fileHistoryDir = path.join(claudeDir, "file-history");
    const sessionsDir2 = path.join(claudeDir, "sessions");
    if (fs.existsSync(fileHistoryDir) && fs.existsSync(sessionsDir2)) {
      // Build a map of sessionId -> cwd from session JSONs for quick lookup
      const sessionCwdMap = new Map<string, string>();
      for (const f of fs.readdirSync(sessionsDir2).filter((f) => f.endsWith(".json"))) {
        const data = readFileSafe(path.join(sessionsDir2, f));
        const sid = jsonExtract(data, "sessionId");
        const cwd = jsonExtract(data, "cwd");
        if (sid && cwd) sessionCwdMap.set(sid, cwd);
      }

      for (const fhDir of subdirs(fileHistoryDir)) {
        const fhSession = path.basename(fhDir);
        const cwd = sessionCwdMap.get(fhSession) ?? "";
        if (cwd.toLowerCase().includes(projectName.toLowerCase())) {
          const dest = path.join(claudeOutputDir, "file-history");
          fs.mkdirSync(dest, { recursive: true });
          copyRecursive(fhDir, path.join(dest, fhSession));
          console.log(`Copied file-history/${fhSession}`);
        }
      }
    }

    if (claudeSessionsFound === 0 && !claudeProjectDir) {
      console.log(`No Claude Code sessions found for project '${projectName}'`);
    } else {
      totalSessions += claudeSessionsFound;
    }
  } else {
    console.log("Claude Code directory not found");
  }

  // ── Summary ────────────────────────────────────────────────────────────────
  console.log();
  console.log("=== Summary ===");

  if (totalSessions === 0) {
    console.log(`No chat histories found for project '${projectName}'`);
    if (fs.existsSync(outputDir)) fs.rmSync(outputDir, { recursive: true });
    process.exit(1);
  }

  console.log(`Done! Total size: ${dirSize(outputDir)}`);
  console.log(`Location: ${outputDir}`);
  console.log();
  console.log("Contents:");
  if (vsCodeSessionCount > 0) {
    console.log(`  VS Code Extension: ${vsCodeSessionCount} chat sessions, ${vsCodeEditingCount} editing sessions`);
  }
  if (cliSessionsFound > 0) {
    console.log(`  Copilot CLI: ${cliSessionsFound} session directories`);
  }
  if (claudeSessionsFound > 0 || claudeProjectDir) {
    console.log(`  Claude Code: ${claudeSessionsFound} sessions`);
  }
}

main();
