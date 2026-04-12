#!/usr/bin/env npx tsx
/**
 * Normalize collected chat histories into a unified, simplified format.
 * Input:  directory produced by get_hist.ts (default: ./copilot-chat-history)
 * Output: directory with per-session markdown + index.json (default: ./chat-normalized)
 *
 * Usage: npx tsx normalize_hist.ts [input-dir] [output-dir]
 */

import fs from "fs";
import path from "path";

// ─── Types ────────────────────────────────────────────────────────────────────

type Source = "claude-code" | "copilot-cli" | "vscode";

interface ToolCall {
  name: string;
  input: Record<string, unknown>;
}

interface ChatMessage {
  role: "user" | "assistant" | "subagent" | "error" | "summary";
  timestamp?: string;
  agentId?: string;        // for subagent messages
  text?: string;
  toolCalls?: ToolCall[];
  toolResults?: Array<{ name: string; success: boolean; output: string }>;
}

interface NormalizedSession {
  sessionId: string;
  source: Source;
  timestamp: string;       // earliest message time
  endTimestamp?: string;   // latest message time
  cwd?: string;
  branch?: string;
  model?: string;
  messages: ChatMessage[];
  // derived stats
  userMessageCount: number;
  toolCallCount: number;
  errorCount: number;
  errors: string[];
  file: string;            // output file path relative to output dir
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function truncate(s: string, max = 300): string {
  if (!s) return "";
  const clean = s.replace(/\s+/g, " ").trim();
  return clean.length > max ? clean.slice(0, max) + `… [+${clean.length - max}]` : clean;
}

function summarizeInput(input: Record<string, unknown>): string {
  // Surface the most meaningful field for each common tool
  const priority = ["command", "file_path", "pattern", "path", "query",
                    "description", "prompt", "skill", "url", "to"];
  for (const key of priority) {
    if (input[key] != null) return truncate(String(input[key]), 120);
  }
  return truncate(JSON.stringify(input), 120);
}

function readJsonLines(filePath: string): unknown[] {
  try {
    return fs.readFileSync(filePath, "utf8")
      .split("\n")
      .filter(Boolean)
      .map((l) => JSON.parse(l));
  } catch {
    return [];
  }
}

function safeText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text ?? "")
      .join("\n");
  }
  return "";
}

// ─── Claude Code JSONL parser ─────────────────────────────────────────────────

function parseClaudeCode(filePath: string): NormalizedSession | null {
  const lines = readJsonLines(filePath) as any[];
  if (!lines.length) return null;

  // Collect metadata from first user message
  let sessionId = "";
  let cwd: string | undefined;
  let branch: string | undefined;
  let model: string | undefined;
  let firstTs = "";
  let lastTs = "";

  const messages: ChatMessage[] = [];

  // Merge streaming chunks: same message.id → same turn
  // Key: messageId → accumulated content blocks
  const seen = new Map<string, { role: string; ts: string; blocks: any[]; agentId?: string }>();
  const order: string[] = []; // ordered unique message IDs

  for (const rec of lines) {
    const ts: string = rec.timestamp ?? "";
    if (ts && (!firstTs || ts < firstTs)) firstTs = ts;
    if (ts && ts > lastTs) lastTs = ts;

    if (rec.sessionId && !sessionId) sessionId = rec.sessionId;
    if (rec.cwd && !cwd) cwd = rec.cwd;
    if (rec.gitBranch && !branch) branch = rec.gitBranch;

    // Skip infrastructure records
    if (["file-history-snapshot", "queue-operation", "last-prompt", "system"].includes(rec.type)) continue;

    if (rec.type === "user" || rec.type === "assistant") {
      const msg = rec.message;
      if (!msg) continue;
      if (msg.model && !model) model = msg.model;

      const msgId: string = msg.id ?? rec.uuid ?? Math.random().toString(36);
      const content: any[] = Array.isArray(msg.content)
        ? msg.content
        : [{ type: "text", text: String(msg.content ?? "") }];

      if (!seen.has(msgId)) {
        seen.set(msgId, { role: rec.type, ts, blocks: [] });
        order.push(msgId);
      }
      seen.get(msgId)!.blocks.push(...content);

      // Track error flag
      if (rec.isApiErrorMessage) {
        seen.get(msgId)!.role = "error";
      }
    }

    if (rec.type === "progress") {
      const inner = rec.data?.message;
      if (!inner) continue;
      const agentId: string = rec.data?.agentId ?? "?";
      const msg = inner.message ?? inner;
      const role: string = inner.type ?? "assistant";
      if (!["user", "assistant"].includes(role)) continue;
      if (msg.model && !model) model = msg.model;

      const content: any[] = Array.isArray(msg.content)
        ? msg.content
        : [{ type: "text", text: String(msg.content ?? "") }];

      const msgId: string = (msg.id ?? inner.uuid ?? rec.uuid) + "#" + agentId;
      if (!seen.has(msgId)) {
        seen.set(msgId, { role: "subagent", ts, blocks: [], agentId });
        order.push(msgId);
      }
      seen.get(msgId)!.blocks.push(...content);
    }
  }

  if (!sessionId) sessionId = path.basename(filePath, ".jsonl");

  // Build messages from merged turns
  for (const msgId of order) {
    const entry = seen.get(msgId)!;
    const msg = buildMessage(entry.role, entry.ts, entry.blocks, entry.agentId);
    if (msg) messages.push(msg);
  }

  return buildSession("claude-code", sessionId, firstTs, lastTs, cwd, branch, model, messages, filePath);
}

function buildMessage(
  role: string,
  ts: string,
  blocks: any[],
  agentId?: string
): ChatMessage | null {
  // Gather text and tool calls/results from content blocks
  const texts: string[] = [];
  const toolCalls: ToolCall[] = [];
  const toolResults: Array<{ name: string; success: boolean; output: string }> = [];
  const toolUseIds = new Set<string>(); // deduplicate

  for (const block of blocks) {
    if (!block || !block.type) continue;
    switch (block.type) {
      case "text":
        if (block.text?.trim()) texts.push(block.text.trim());
        break;
      case "tool_use":
        if (!toolUseIds.has(block.id)) {
          toolUseIds.add(block.id);
          toolCalls.push({ name: block.name ?? "?", input: block.input ?? {} });
        }
        break;
      case "tool_result": {
        const content = Array.isArray(block.content)
          ? block.content.filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n")
          : String(block.content ?? "");
        toolResults.push({
          name: block.tool_use_id ?? "tool",
          success: !block.is_error,
          output: truncate(content, 200),
        });
        break;
      }
      // skip: thinking, thinking_summary, image, etc.
    }
  }

  const text = texts.join("\n\n");
  if (!text && !toolCalls.length && !toolResults.length) return null;

  const mapped: ChatMessage = {
    role: (role === "error" ? "error" : role === "subagent" ? "subagent" : role) as ChatMessage["role"],
    timestamp: ts || undefined,
    agentId,
    text: text ? truncate(text, 500) : undefined,
    toolCalls: toolCalls.length ? toolCalls : undefined,
    toolResults: toolResults.length ? toolResults : undefined,
  };
  return mapped;
}

// ─── Copilot CLI events.jsonl parser ─────────────────────────────────────────

function parseCopilotCli(eventsPath: string): NormalizedSession | null {
  const events = readJsonLines(eventsPath) as any[];
  if (!events.length) return null;

  let sessionId = "";
  let cwd: string | undefined;
  let branch: string | undefined;
  let model: string | undefined;
  let firstTs = "";
  let lastTs = "";

  const messages: ChatMessage[] = [];

  // Accumulate assistant turn state
  let currentTurnText = "";
  let currentTurnTools: ToolCall[] = [];
  let currentTurnTs = "";
  let inTurn = false;

  // Map toolCallId -> toolName for result matching
  const toolNameMap = new Map<string, string>();

  function flushTurn() {
    if (!inTurn) return;
    if (currentTurnText || currentTurnTools.length) {
      messages.push({
        role: "assistant",
        timestamp: currentTurnTs || undefined,
        text: currentTurnText ? truncate(currentTurnText, 500) : undefined,
        toolCalls: currentTurnTools.length ? currentTurnTools : undefined,
      });
    }
    currentTurnText = "";
    currentTurnTools = [];
    currentTurnTs = "";
    inTurn = false;
  }

  for (const ev of events) {
    const ts: string = ev.timestamp ?? "";
    if (ts && (!firstTs || ts < firstTs)) firstTs = ts;
    if (ts && ts > lastTs) lastTs = ts;

    switch (ev.type) {
      case "session.start":
        sessionId = ev.data?.sessionId ?? "";
        cwd = ev.data?.context?.cwd;
        branch = ev.data?.context?.branch;
        break;

      case "session.model_change":
        model = ev.data?.newModel;
        break;

      case "session.compaction_complete":
        if (ev.data?.summaryContent) {
          flushTurn();
          messages.push({
            role: "summary",
            timestamp: ts || undefined,
            text: truncate(ev.data.summaryContent, 400),
          });
        }
        break;

      case "session.task_complete":
        if (ev.data?.summary) {
          flushTurn();
          messages.push({
            role: "summary",
            timestamp: ts || undefined,
            text: "[TASK COMPLETE] " + truncate(ev.data.summary, 300),
          });
        }
        break;

      case "user.message":
        flushTurn();
        if (ev.data?.content) {
          messages.push({
            role: "user",
            timestamp: ts || undefined,
            text: ev.data.content,  // original, not transformedContent
          });
        }
        break;

      case "assistant.turn_start":
        flushTurn();
        inTurn = true;
        currentTurnTs = ts;
        break;

      case "assistant.turn_end":
        flushTurn();
        break;

      case "assistant.message": {
        inTurn = true;
        if (!currentTurnTs) currentTurnTs = ts;
        const text = ev.data?.content ?? "";
        if (text.trim()) currentTurnText += (currentTurnText ? " " : "") + text.trim();
        for (const tr of (ev.data?.toolRequests ?? [])) {
          const args: Record<string, unknown> = tr.arguments ?? {};
          currentTurnTools.push({ name: tr.name, input: args });
          toolNameMap.set(tr.toolCallId, tr.name);
        }
        break;
      }

      case "tool.execution_complete": {
        const toolId: string = ev.data?.toolCallId ?? "";
        const toolName: string = ev.data?.model
          ? toolNameMap.get(toolId) ?? toolId
          : toolNameMap.get(toolId) ?? toolId;
        const success: boolean = ev.data?.success ?? true;
        const result: string = ev.data?.result?.content ?? "";
        const errorMsg: string = ev.data?.result?.error ?? "";
        const output = success ? truncate(result, 200) : truncate(errorMsg || result, 200);
        // Attach result to last assistant message or buffer
        if (messages.length) {
          const last = messages[messages.length - 1];
          if (!last.toolResults) last.toolResults = [];
          last.toolResults.push({ name: toolNameMap.get(toolId) ?? toolId, success, output });
        }
        if (!success) {
          messages.push({
            role: "error",
            timestamp: ts || undefined,
            text: `Tool '${toolName}' failed: ${output}`,
          });
        }
        break;
      }

      case "subagent.started":
        flushTurn();
        messages.push({
          role: "subagent",
          timestamp: ts || undefined,
          agentId: ev.data?.agentName,
          text: `[SUBAGENT START] ${ev.data?.agentDisplayName ?? ""}: ${ev.data?.agentDescription ?? ""}`,
        });
        break;

      case "subagent.completed":
        messages.push({
          role: "subagent",
          timestamp: ts || undefined,
          agentId: ev.data?.agentName,
          text: `[SUBAGENT END] ${ev.data?.agentDisplayName ?? ""}`,
        });
        break;
    }
  }
  flushTurn();

  if (!sessionId) sessionId = path.basename(path.dirname(eventsPath));

  return buildSession("copilot-cli", sessionId, firstTs, lastTs, cwd, branch, model, messages, eventsPath);
}

// ─── VS Code chatSessions parser ──────────────────────────────────────────────

function parseVsCode(filePath: string): NormalizedSession | null {
  const lines = readJsonLines(filePath) as any[];
  if (!lines.length) return null;

  const messages: ChatMessage[] = [];
  let sessionId = "";
  let firstTs = "";
  let lastTs = "";

  for (const line of lines) {
    const v = line.v ?? line;
    sessionId = sessionId || v.sessionId || "";

    const requests: any[] = v.requests ?? [];
    for (const req of requests) {
      const ts: string = new Date(req.timestamp ?? req.requestProps?.timestamp ?? 0).toISOString();
      if (ts > "1970" && (!firstTs || ts < firstTs)) firstTs = ts;
      if (ts > lastTs) lastTs = ts;

      // User turn
      const userText = req.message?.text ?? req.message ?? "";
      if (userText) {
        messages.push({ role: "user", timestamp: ts || undefined, text: String(userText) });
      }

      // Assistant response
      const response = req.response ?? req.result;
      if (response) {
        const respText = response.value ?? safeText(response.message);
        const toolCalls: ToolCall[] = (response.result?.toolCalls ?? []).map((tc: any) => ({
          name: tc.name ?? tc.function?.name ?? "?",
          input: tc.parameters ?? tc.function?.arguments ?? {},
        }));

        if (respText || toolCalls.length) {
          messages.push({
            role: "assistant",
            timestamp: ts || undefined,
            text: respText ? truncate(String(respText), 500) : undefined,
            toolCalls: toolCalls.length ? toolCalls : undefined,
          });
        }
      }
    }
  }

  if (!messages.length) return null;
  if (!sessionId) sessionId = path.basename(filePath, ".jsonl");

  return buildSession("vscode", sessionId, firstTs, lastTs, undefined, undefined, undefined, messages, filePath);
}

// ─── Session builder & stats ─────────────────────────────────────────────────

function buildSession(
  source: Source,
  sessionId: string,
  firstTs: string,
  lastTs: string,
  cwd: string | undefined,
  branch: string | undefined,
  model: string | undefined,
  messages: ChatMessage[],
  sourceFile: string
): NormalizedSession {
  const errors: string[] = [];
  let toolCallCount = 0;

  for (const m of messages) {
    if (m.role === "error" && m.text) errors.push(m.text);
    toolCallCount += m.toolCalls?.length ?? 0;
    // Also pick up error tool results
    for (const tr of m.toolResults ?? []) {
      if (!tr.success) errors.push(`Tool '${tr.name}' failed: ${tr.output}`);
    }
  }

  const userMessageCount = messages.filter((m) => m.role === "user").length;
  const fileName = `sessions/${sessionId}.md`;

  return {
    sessionId,
    source,
    timestamp: firstTs,
    endTimestamp: lastTs || undefined,
    cwd,
    branch,
    model,
    messages,
    userMessageCount,
    toolCallCount,
    errorCount: errors.length,
    errors,
    file: fileName,
  };
}

// ─── Markdown renderer ────────────────────────────────────────────────────────

function renderSession(session: NormalizedSession): string {
  const lines: string[] = [];

  const duration = session.timestamp && session.endTimestamp
    ? (() => {
        const ms = new Date(session.endTimestamp).getTime() - new Date(session.timestamp).getTime();
        const min = Math.round(ms / 60000);
        return min > 0 ? ` (${min} min)` : "";
      })()
    : "";

  lines.push(`# Session: ${session.sessionId}`);
  lines.push(`**Source**: ${session.source}  **Time**: ${session.timestamp}${duration}`);
  if (session.cwd) lines.push(`**CWD**: ${session.cwd}`);
  if (session.branch) lines.push(`**Branch**: ${session.branch}  **Model**: ${session.model ?? "unknown"}`);
  lines.push(`**Messages**: ${session.userMessageCount} user  **Tools**: ${session.toolCallCount}  **Errors**: ${session.errorCount}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  for (const msg of session.messages) {
    const time = msg.timestamp
      ? new Date(msg.timestamp).toISOString().slice(11, 19) + "Z"
      : "";
    const timeStr = time ? ` ${time}` : "";

    switch (msg.role) {
      case "user":
        lines.push(`**[USER${timeStr}]**`);
        lines.push(msg.text ?? "");
        break;

      case "assistant":
        lines.push(`**[ASSISTANT${timeStr}]**`);
        if (msg.toolCalls?.length) {
          for (const tc of msg.toolCalls) {
            lines.push(`  → \`${tc.name}\` – ${summarizeInput(tc.input)}`);
          }
        }
        if (msg.text) lines.push(msg.text);
        if (msg.toolResults?.length) {
          for (const tr of msg.toolResults) {
            const icon = tr.success ? "✓" : "✗";
            lines.push(`  ${icon} ${tr.name}: ${tr.output}`);
          }
        }
        break;

      case "subagent": {
        const label = msg.agentId ? `SUBAGENT:${msg.agentId}` : "SUBAGENT";
        lines.push(`**[${label}${timeStr}]**`);
        if (msg.toolCalls?.length) {
          for (const tc of msg.toolCalls) {
            lines.push(`  → \`${tc.name}\` – ${summarizeInput(tc.input)}`);
          }
        }
        if (msg.text) lines.push(msg.text);
        if (msg.toolResults?.length) {
          for (const tr of msg.toolResults) {
            const icon = tr.success ? "✓" : "✗";
            lines.push(`  ${icon} ${tr.name}: ${tr.output}`);
          }
        }
        break;
      }

      case "error":
        lines.push(`**[ERROR${timeStr}]** ${msg.text ?? ""}`);
        break;

      case "summary":
        lines.push(`**[SUMMARY${timeStr}]**`);
        lines.push(`> ${(msg.text ?? "").replace(/\n/g, "\n> ")}`);
        break;
    }

    lines.push("");
  }

  return lines.join("\n");
}

// ─── Discovery: walk input dir for session files ──────────────────────────────

interface FoundSession {
  type: "claude-jsonl" | "copilot-cli-events" | "vscode-chat";
  path: string;
}

function discoverSessions(inputDir: string): FoundSession[] {
  const found: FoundSession[] = [];

  function walkClaudeCode(dir: string) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isFile() && entry.name.endsWith(".jsonl") && !entry.name.startsWith("history")) {
        found.push({ type: "claude-jsonl", path: full });
      } else if (entry.isDirectory() && entry.name === "subagents") {
        // skip subagent files - they're already referenced via progress records in the parent
      } else if (entry.isDirectory()) {
        // session subdirs (UUID dirs) may also have .jsonl directly - skip, parent handles it
      }
    }
  }

  function walkCopilotCli(dir: string) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        const eventsFile = path.join(dir, entry.name, "events.jsonl");
        if (fs.existsSync(eventsFile)) {
          found.push({ type: "copilot-cli-events", path: eventsFile });
        }
      } else if (entry.isFile() && entry.name === "events.jsonl") {
        // top-level events.jsonl (single session dir passed directly)
        found.push({ type: "copilot-cli-events", path: path.join(dir, entry.name) });
      }
    }
  }

  function walkVsCode(dir: string) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isFile() && entry.name.endsWith(".jsonl")) {
        found.push({ type: "vscode-chat", path: path.join(dir, entry.name) });
      }
    }
  }

  const claudeDir = path.join(inputDir, "claude-code");
  const cliDir = path.join(inputDir, "copilot-cli");
  const vsDir = path.join(inputDir, "vscode-extension", "chatSessions");

  walkClaudeCode(claudeDir);
  walkCopilotCli(cliDir);
  walkVsCode(vsDir);

  return found;
}

// ─── Main ────────────────────────────────────────────────────────────────────

function main() {
  const rawArgs = process.argv.slice(2);

  let incremental = false;
  let since: Date | null = null;
  const positional: string[] = [];

  for (const arg of rawArgs) {
    if (arg === "--incremental") {
      incremental = true;
    } else if (arg.startsWith("--since=")) {
      const d = new Date(arg.slice("--since=".length));
      if (!isNaN(d.getTime())) since = d;
    } else if (!arg.startsWith("-")) {
      positional.push(arg);
    }
  }

  const inputDir = path.resolve(positional[0] ?? "./copilot-chat-history");
  const outputDir = path.resolve(positional[1] ?? "./chat-normalized");

  if (!fs.existsSync(inputDir)) {
    console.error(`Input directory not found: ${inputDir}`);
    console.error("Run get_hist.ts first to collect chat histories.");
    process.exit(1);
  }

  console.log(`Input:  ${inputDir}`);
  console.log(`Output: ${outputDir}`);
  if (incremental) console.log("Mode:   incremental");
  if (since) console.log(`Since:  ${since.toISOString()}`);
  console.log();

  // Load existing index for incremental mode
  let existingEntries: Omit<NormalizedSession, "messages">[] = [];
  let existingIds = new Set<string>();

  if (incremental) {
    const indexPath = path.join(outputDir, "index.json");
    if (fs.existsSync(indexPath)) {
      try {
        const raw = JSON.parse(fs.readFileSync(indexPath, "utf8"));
        existingEntries = raw.sessions ?? [];
        existingIds = new Set(existingEntries.map((s: any) => s.sessionId));
        console.log(`Incremental: ${existingIds.size} sessions already indexed`);
        console.log();
      } catch {
        console.warn("WARN: could not read existing index.json — processing all sessions");
      }
    }
  }

  const sessionFiles = discoverSessions(inputDir);
  console.log(`Found ${sessionFiles.length} session files`);
  console.log();

  fs.mkdirSync(path.join(outputDir, "sessions"), { recursive: true });

  const newEntries: Omit<NormalizedSession, "messages">[] = [];
  let parsedCount = 0;
  let skippedCount = 0;

  for (const sf of sessionFiles) {
    let session: NormalizedSession | null = null;

    try {
      if (sf.type === "claude-jsonl") session = parseClaudeCode(sf.path);
      else if (sf.type === "copilot-cli-events") session = parseCopilotCli(sf.path);
      else if (sf.type === "vscode-chat") session = parseVsCode(sf.path);
    } catch (e: any) {
      console.warn(`  WARN: failed to parse ${sf.path}: ${e.message}`);
    }

    if (!session || !session.messages.length) {
      skippedCount++;
      continue;
    }

    // Skip already-indexed sessions in incremental mode
    if (incremental && existingIds.has(session.sessionId)) {
      skippedCount++;
      continue;
    }

    // Apply --since filter
    if (since && session.timestamp && new Date(session.timestamp) < since) {
      skippedCount++;
      continue;
    }

    // Write per-session markdown
    const mdPath = path.join(outputDir, session.file);
    fs.writeFileSync(mdPath, renderSession(session));

    const { messages, ...meta } = session;
    newEntries.push(meta);
    parsedCount++;
  }

  // Merge with existing entries and sort
  const allEntries = [...existingEntries, ...newEntries];
  allEntries.sort((a, b) => (a.timestamp > b.timestamp ? 1 : -1));

  // Write index.json
  fs.writeFileSync(
    path.join(outputDir, "index.json"),
    JSON.stringify({ generated: new Date().toISOString(), sessions: allEntries }, null, 2)
  );

  // Write or append combined.md
  const combinedPath = path.join(outputDir, "combined.md");

  if (incremental && newEntries.length > 0 && fs.existsSync(combinedPath)) {
    // Append new sessions with a dated divider
    const divider = [
      "",
      "---",
      `*Updated ${new Date().toISOString()} — ${newEntries.length} new session(s)*`,
      "---",
      "",
    ].join("\n");
    const appendParts: string[] = [divider];
    for (const meta of newEntries) {
      appendParts.push(fs.readFileSync(path.join(outputDir, meta.file), "utf8"));
      appendParts.push("\n---\n");
    }
    fs.appendFileSync(combinedPath, appendParts.join("\n"));
  } else {
    // Full rewrite
    const combinedParts: string[] = [
      "# Combined Chat History\n",
      `Generated: ${new Date().toISOString()}  Sessions: ${allEntries.length}\n`,
      "---\n",
    ];
    for (const meta of allEntries) {
      const mdContent = fs.readFileSync(path.join(outputDir, meta.file), "utf8");
      combinedParts.push(mdContent);
      combinedParts.push("\n---\n");
    }
    fs.writeFileSync(combinedPath, combinedParts.join("\n"));
  }

  // Print summary
  console.log(`New:     ${parsedCount} sessions`);
  console.log(`Skipped: ${skippedCount} (empty or already indexed)`);
  if (incremental) console.log(`Total:   ${allEntries.length} sessions in index`);
  console.log();

  // Error report (new sessions only)
  const withErrors = newEntries.filter((s) => s.errorCount > 0);
  if (withErrors.length) {
    console.log(`New sessions with errors: ${withErrors.length}`);
    for (const s of withErrors) {
      console.log(`  [${s.source}] ${s.sessionId.slice(0, 8)} (${s.timestamp.slice(0, 10)}): ${s.errorCount} error(s)`);
      for (const e of s.errors.slice(0, 3)) {
        console.log(`    • ${e.slice(0, 100)}`);
      }
    }
    console.log();
  }

  // Stats by source (all sessions)
  const bySrc = new Map<string, { count: number; tools: number; errors: number }>();
  for (const s of allEntries) {
    const entry = bySrc.get(s.source) ?? { count: 0, tools: 0, errors: 0 };
    entry.count++;
    entry.tools += s.toolCallCount;
    entry.errors += s.errorCount;
    bySrc.set(s.source, entry);
  }
  console.log("By source (total):");
  for (const [src, stats] of bySrc) {
    console.log(`  ${src.padEnd(14)} ${stats.count} sessions  ${stats.tools} tool calls  ${stats.errors} errors`);
  }

  console.log();
  console.log("Output:");
  console.log(`  ${path.join(outputDir, "sessions/")}   (${allEntries.length} .md files)`);
  console.log(`  ${path.join(outputDir, "index.json")}`);
  console.log(`  ${path.join(outputDir, "combined.md")}`);
}

main();
