#!/usr/bin/env npx tsx
/**
 * retro — AI session history retrospective tool
 *
 * Manages persistent storage of collected/normalized chat sessions and
 * orchestrates the collect → normalize → report pipeline.
 *
 * Usage:
 *   npx tsx retro.ts <project-path> <subcommand> [options]
 *
 * Subcommands:
 *   run        Full pipeline: collect → normalize (then AI reads output to report)
 *   collect    Collect raw sessions only
 *   normalize  Normalize already-collected sessions only
 *   status     Show storage info and session counts
 *   cleanup    Remove collected data (prompts for confirmation)
 *
 * Options:
 *   --full           Ignore lastCollectedAt; collect/normalize all sessions
 *   --storage=<dir>  Override storage base (default: ~/.retro/<project-name>)
 *   --output=<dir>   For collect: override raw output dir
 *
 * Storage layout:
 *   ~/.retro/<project-name>/
 *     manifest.json        lastCollectedAt, lastNormalizedAt, lastReportAt, totalSessions
 *     raw/                 get_hist.ts output (persistent raw sessions)
 *     normalized/          normalize_hist.ts output
 *       sessions/          per-session .md files
 *       index.json         session metadata index
 *       combined.md        all sessions concatenated
 *     reports/             generated reports (written by AI skill)
 */

import fs from "fs";
import path from "path";
import os from "os";
import { spawnSync } from "child_process";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Manifest {
  projectPath: string;
  projectName: string;
  lastCollectedAt: string | null;
  lastNormalizedAt: string | null;
  lastReportAt: string | null;
  totalSessionsCollected: number;
  totalSessionsNormalized: number;
  createdAt: string;
  updatedAt: string;
}

// ─── Utilities ────────────────────────────────────────────────────────────────

const SCRIPT_DIR = path.dirname(process.argv[1]);
const GET_HIST = path.join(SCRIPT_DIR, "get_hist.ts");
const NORMALIZE_HIST = path.join(SCRIPT_DIR, "normalize_hist.ts");

function projectNameFromPath(p: string): string {
  return path.basename(path.resolve(p));
}

function storageBase(projectName: string): string {
  return path.join(os.homedir(), ".retro", projectName);
}

function readManifest(storageDir: string): Manifest | null {
  const mp = path.join(storageDir, "manifest.json");
  if (!fs.existsSync(mp)) return null;
  try {
    return JSON.parse(fs.readFileSync(mp, "utf8")) as Manifest;
  } catch {
    return null;
  }
}

function writeManifest(storageDir: string, m: Manifest): void {
  m.updatedAt = new Date().toISOString();
  fs.mkdirSync(storageDir, { recursive: true });
  fs.writeFileSync(path.join(storageDir, "manifest.json"), JSON.stringify(m, null, 2));
}

function dirSizeHuman(dir: string): string {
  let bytes = 0;
  function walk(d: string) {
    if (!fs.existsSync(d)) return;
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else bytes += fs.statSync(full).size;
    }
  }
  walk(dir);
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)}K`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)}M`;
  return `${(bytes / 1024 ** 3).toFixed(1)}G`;
}

function run(
  script: string,
  scriptArgs: string[],
  label: string
): boolean {
  console.log(`\n── ${label} ──`);
  console.log(`$ npx tsx ${path.basename(script)} ${scriptArgs.join(" ")}`);
  console.log();

  const result = spawnSync("npx", ["tsx", script, ...scriptArgs], {
    stdio: "inherit",
    shell: false,
  });

  if (result.error) {
    console.error(`Failed to run ${label}: ${result.error.message}`);
    return false;
  }
  if (result.status !== 0) {
    console.error(`${label} exited with status ${result.status}`);
    return false;
  }
  return true;
}

function countSessions(normalizedDir: string): number {
  const indexPath = path.join(normalizedDir, "index.json");
  if (!fs.existsSync(indexPath)) return 0;
  try {
    const raw = JSON.parse(fs.readFileSync(indexPath, "utf8"));
    return (raw.sessions ?? []).length;
  } catch {
    return 0;
  }
}

// ─── Subcommands ──────────────────────────────────────────────────────────────

function cmdStatus(storageDir: string, manifest: Manifest | null): void {
  console.log("=== Retro Storage Status ===");
  console.log(`Storage: ${storageDir}`);
  console.log();

  if (!manifest) {
    console.log("No manifest found. Run 'collect' or 'run' first.");
    return;
  }

  console.log(`Project:    ${manifest.projectName}  (${manifest.projectPath})`);
  console.log(`Created:    ${manifest.createdAt}`);
  console.log(`Updated:    ${manifest.updatedAt}`);
  console.log();

  const rawDir = path.join(storageDir, "raw");
  const normalizedDir = path.join(storageDir, "normalized");
  const reportsDir = path.join(storageDir, "reports");

  console.log("Collection:");
  console.log(`  Last collected:   ${manifest.lastCollectedAt ?? "(never)"}`);
  console.log(`  Raw storage:      ${dirSizeHuman(rawDir)}`);
  console.log();

  console.log("Normalization:");
  console.log(`  Last normalized:  ${manifest.lastNormalizedAt ?? "(never)"}`);
  const sessionCount = countSessions(normalizedDir);
  console.log(`  Sessions indexed: ${sessionCount}`);
  console.log(`  Normalized size:  ${dirSizeHuman(normalizedDir)}`);
  console.log();

  console.log("Reports:");
  console.log(`  Last report:      ${manifest.lastReportAt ?? "(never)"}`);
  if (fs.existsSync(reportsDir)) {
    const reports = fs.readdirSync(reportsDir).filter((f) => f.endsWith(".md"));
    console.log(`  Reports stored:   ${reports.length}`);
    for (const r of reports.sort().slice(-3)) {
      console.log(`    ${r}`);
    }
  }
}

function cmdCollect(
  projectPath: string,
  storageDir: string,
  manifest: Manifest,
  opts: { full: boolean; rawOutputOverride?: string }
): boolean {
  const rawDir = opts.rawOutputOverride ?? path.join(storageDir, "raw");
  const projectName = manifest.projectName;

  const collectArgs: string[] = [
    projectName,
    `--output-dir=${rawDir}`,
  ];

  // On incremental runs, add --since to avoid collecting very old sessions
  // (Claude Code filtering only; Copilot CLI will still collect sessions since this date)
  if (!opts.full && manifest.lastCollectedAt) {
    collectArgs.push(`--since=${manifest.lastCollectedAt}`);
  }

  const ok = run(GET_HIST, collectArgs, "Collecting sessions");
  if (!ok) return false;

  manifest.lastCollectedAt = new Date().toISOString();
  writeManifest(storageDir, manifest);
  return true;
}

function cmdNormalize(
  storageDir: string,
  manifest: Manifest,
  opts: { full: boolean; rawOverride?: string }
): boolean {
  const rawDir = opts.rawOverride ?? path.join(storageDir, "raw");
  const normalizedDir = path.join(storageDir, "normalized");

  const normalizeArgs: string[] = [rawDir, normalizedDir];

  if (!opts.full && manifest.lastNormalizedAt) {
    normalizeArgs.unshift("--incremental");
  }

  const ok = run(NORMALIZE_HIST, normalizeArgs, "Normalizing sessions");
  if (!ok) return false;

  manifest.lastNormalizedAt = new Date().toISOString();
  manifest.totalSessionsNormalized = countSessions(normalizedDir);
  writeManifest(storageDir, manifest);
  return true;
}

function cmdRun(
  projectPath: string,
  storageDir: string,
  manifest: Manifest,
  opts: { full: boolean }
): void {
  const now = new Date().toISOString();
  console.log(`=== Retro Run: ${manifest.projectName} ===`);
  console.log(`Time: ${now}`);
  if (opts.full) console.log("Mode: full (ignoring lastCollectedAt)");
  else if (manifest.lastCollectedAt) console.log(`Mode: incremental (since ${manifest.lastCollectedAt})`);
  else console.log("Mode: first run (collecting all sessions)");

  const collected = cmdCollect(projectPath, storageDir, manifest, opts);
  if (!collected) {
    console.error("\nCollection failed. Aborting.");
    process.exit(1);
  }

  const normalized = cmdNormalize(storageDir, manifest, opts);
  if (!normalized) {
    console.error("\nNormalization failed. Aborting.");
    process.exit(1);
  }

  const normalizedDir = path.join(storageDir, "normalized");
  const sessionCount = countSessions(normalizedDir);

  console.log("\n=== Pipeline Complete ===");
  console.log(`Sessions in index: ${sessionCount}`);
  console.log(`Normalized data:   ${normalizedDir}`);
  console.log(`  combined.md      ${path.join(normalizedDir, "combined.md")}`);
  console.log(`  index.json       ${path.join(normalizedDir, "index.json")}`);
  console.log();
  console.log("Next step: ask the AI agent to analyze and generate a report.");
  console.log("  The AI should read index.json for an overview, then sample");
  console.log("  individual session .md files for deep analysis.");
  console.log();
  console.log("Suggested prompt:");
  console.log(`  Analyze the sessions in ${normalizedDir} and write a report to`);
  console.log(`  ${path.join(storageDir, "reports", `${now.slice(0, 10)}-report.md`)}`);
}

function cmdCleanup(storageDir: string, manifest: Manifest | null): void {
  console.log(`Storage directory: ${storageDir}`);
  console.log(`Total size: ${dirSizeHuman(storageDir)}`);
  console.log();

  if (!fs.existsSync(storageDir)) {
    console.log("Nothing to clean up.");
    return;
  }

  const rawDir = path.join(storageDir, "raw");
  const normalizedDir = path.join(storageDir, "normalized");
  const reportsDir = path.join(storageDir, "reports");

  console.log("What to clean:");
  console.log(`  [1] Raw collected data only (${dirSizeHuman(rawDir)})`);
  console.log(`  [2] Normalized data only (${dirSizeHuman(normalizedDir)})`);
  console.log(`  [3] Reports only (${dirSizeHuman(reportsDir)})`);
  console.log(`  [4] Everything (${dirSizeHuman(storageDir)})`);
  console.log();
  console.log("To clean, run with --clean=<1|2|3|4|raw|normalized|reports|all>");
  console.log("Example: retro.ts <project> cleanup --clean=raw");
}

// ─── Argument parsing & dispatch ──────────────────────────────────────────────

function usage(): void {
  const script = path.basename(process.argv[1]);
  console.log(`Usage: npx tsx ${script} <project-path> <subcommand> [options]`);
  console.log();
  console.log("Subcommands:");
  console.log("  run         Full pipeline: collect → normalize");
  console.log("  collect     Collect raw sessions only");
  console.log("  normalize   Normalize collected sessions only");
  console.log("  status      Show storage info");
  console.log("  cleanup     Show cleanup options");
  console.log();
  console.log("Options:");
  console.log("  --full              Ignore lastCollectedAt; process all sessions");
  console.log("  --storage=<dir>     Override storage base (~/.retro/<project>)");
  console.log("  --clean=<target>    For cleanup: raw|normalized|reports|all");
  console.log();
  console.log("Examples:");
  console.log(`  npx tsx ${script} ~/workspace/crab run`);
  console.log(`  npx tsx ${script} ~/workspace/crab run --full`);
  console.log(`  npx tsx ${script} ~/workspace/crab status`);
  console.log(`  npx tsx ${script} ~/workspace/crab cleanup --clean=raw`);
  process.exit(1);
}

function main(): void {
  const args = process.argv.slice(2);

  if (args.length < 2) usage();

  const projectPathRaw = args[0];
  const subcommand = args[1];
  const rest = args.slice(2);

  const projectPath = path.resolve(projectPathRaw.replace(/^~/, os.homedir()));
  const projectName = projectNameFromPath(projectPath);

  let storageDirOverride: string | undefined;
  let full = false;
  let cleanTarget: string | undefined;

  for (const arg of rest) {
    if (arg === "--full") full = true;
    else if (arg.startsWith("--storage=")) storageDirOverride = arg.slice("--storage=".length);
    else if (arg.startsWith("--clean=")) cleanTarget = arg.slice("--clean=".length);
    else if (arg.startsWith("-")) {
      console.error(`Unknown option: ${arg}`);
      process.exit(1);
    }
  }

  const storageDir = storageDirOverride
    ? path.resolve(storageDirOverride)
    : storageBase(projectName);

  let manifest = readManifest(storageDir);

  // Auto-create manifest if missing
  if (!manifest) {
    manifest = {
      projectPath,
      projectName,
      lastCollectedAt: null,
      lastNormalizedAt: null,
      lastReportAt: null,
      totalSessionsCollected: 0,
      totalSessionsNormalized: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  switch (subcommand) {
    case "run":
      cmdRun(projectPath, storageDir, manifest, { full });
      break;

    case "collect":
      if (!cmdCollect(projectPath, storageDir, manifest, { full })) process.exit(1);
      break;

    case "normalize":
      if (!cmdNormalize(storageDir, manifest, { full })) process.exit(1);
      break;

    case "status":
      cmdStatus(storageDir, manifest);
      break;

    case "cleanup":
      if (cleanTarget) {
        const rawDir = path.join(storageDir, "raw");
        const normalizedDir = path.join(storageDir, "normalized");
        const reportsDir = path.join(storageDir, "reports");

        const targets: Record<string, string[]> = {
          raw: [rawDir],
          "1": [rawDir],
          normalized: [normalizedDir],
          "2": [normalizedDir],
          reports: [reportsDir],
          "3": [reportsDir],
          all: [storageDir],
          "4": [storageDir],
        };

        const dirs = targets[cleanTarget];
        if (!dirs) {
          console.error(`Unknown cleanup target: ${cleanTarget}`);
          console.error("Valid targets: raw, normalized, reports, all (or 1, 2, 3, 4)");
          process.exit(1);
        }

        for (const d of dirs) {
          if (fs.existsSync(d)) {
            console.log(`Removing: ${d}  (${dirSizeHuman(d)})`);
            fs.rmSync(d, { recursive: true });
            console.log("Done.");
          } else {
            console.log(`Already absent: ${d}`);
          }
        }

        // Reset relevant manifest fields
        if (cleanTarget === "raw" || cleanTarget === "1" || cleanTarget === "all" || cleanTarget === "4") {
          manifest.lastCollectedAt = null;
          manifest.totalSessionsCollected = 0;
        }
        if (cleanTarget === "normalized" || cleanTarget === "2" || cleanTarget === "all" || cleanTarget === "4") {
          manifest.lastNormalizedAt = null;
          manifest.totalSessionsNormalized = 0;
        }
        if (cleanTarget === "reports" || cleanTarget === "3" || cleanTarget === "all" || cleanTarget === "4") {
          manifest.lastReportAt = null;
        }

        if (cleanTarget !== "all" && cleanTarget !== "4") {
          writeManifest(storageDir, manifest);
        }
      } else {
        cmdCleanup(storageDir, manifest);
      }
      break;

    default:
      console.error(`Unknown subcommand: ${subcommand}`);
      usage();
  }
}

main();
