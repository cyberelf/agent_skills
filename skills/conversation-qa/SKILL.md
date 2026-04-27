---
name: conversation-qa
description: Generate a structured, illustrated Q&A HTML document from the current conversation. Scans the conversation for conceptual questions the user asked and Claude's answers, then produces a self-contained HTML file with styled cards and SVG diagrams for technical/architectural topics. If a Q&A HTML file already exists in the current project directory, appends the new Q&As to it instead of creating a new file. Trigger this skill whenever the user asks to "generate Q&A", "create Q&A from conversation", "save Q&A", "document our Q&A", "turn this chat into Q&A", or anything suggesting they want the conversation's questions and answers captured as a document — even if they don't use the exact phrase "Q&A skill".
allowed-tools: Read, Write, Edit, Glob, Bash
---

# Conversation Q&A Generator

Extract Q&A pairs from the current conversation and produce (or extend) a polished, self-contained HTML document with illustrated explanations.

## Why this skill exists

Long technical conversations contain valuable knowledge that's hard to retrieve later. This skill captures it as a navigable document — ordered questions, clear answers, and diagrams that make complex concepts stick. The append behavior means you can keep adding to the same document across multiple sessions without losing previous Q&As.

---

## Step 1: Identify Q&A pairs

Scan the conversation history and extract turns where the **user asked a conceptual or clarifying question** and **Claude gave a substantive answer**. Skip:
- Pure commands ("create a file", "run this", "generate the HTML") — these are task instructions, not questions
- Meta-questions about Claude's behavior
- Short confirmations or acknowledgements

For each valid Q&A pair, note:
- The user's question (paraphrase to be clean and direct if needed)
- Claude's answer (summarize the key points — the HTML will expand them)
- Whether the topic is architectural/systems/conceptual (→ add a diagram) or factual/procedural (→ diagram optional)

---

## Step 2: Check for existing Q&A file

Before creating anything, look for an existing Q&A file to append to:

1. Run `Glob` for `**/*qa*.html` and `**/*q_and_a*.html` and `**/*qa_explainer*.html` in the current working directory.
2. If the user mentioned a specific file name or path, use that.
3. If multiple files exist, use the most recently modified one (check with `ls -t`).
4. If a file is found: **append mode** — add new Q&As after the last existing one.
5. If no file is found: **create mode** — generate a fresh file.

In append mode, read the existing file to:
- Get the current question count (so new questions are numbered correctly)
- Extract the nav links so you can add to them
- Identify where to insert the new sections (before `</main>`)

---

## Step 3: Generate the HTML

### Create mode — full document

Use this base structure. The style is purposefully self-contained (no CDN dependencies):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[Topic] — Q&A</title>
<style>
/* Core palette */
:root {
  --navy: #1a2744; --navy2: #1a3a5e; --blue: #3b6fd4; --blue2: #6a9fe8;
  --pale: #eef3fb; --bg: #f2f5fb; --white: #ffffff; --text: #1e2a3a;
  --muted: #5a6a82; --border: #dce3ef;
  --green: #27ae60; --orange: #e67e22; --red: #e74c3c; --purple: #7c3aed;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: var(--bg); color: var(--text); line-height: 1.65; }

/* Header */
header { background: linear-gradient(135deg,#0c1528 0%,#1a2744 55%,#1e3460 100%);
         color: white; padding: 52px 40px 40px; text-align: center; }
.badge { display:inline-block; background:rgba(59,111,212,.3);
         border:1px solid rgba(106,159,232,.4); color:#a0c4ff;
         font-size:.75rem; padding:4px 14px; border-radius:20px;
         margin-bottom:16px; letter-spacing:.06em; text-transform:uppercase; }
header h1 { font-size:2rem; font-weight:700; letter-spacing:-.02em; margin-bottom:10px; }
header p  { color:#8aabb0; font-size:.92rem; max-width:560px; margin:0 auto; }

/* Nav */
nav { background:var(--white); border-bottom:2px solid var(--border); padding:0 28px;
      display:flex; overflow-x:auto; position:sticky; top:0; z-index:200; }
nav a { display:block; padding:13px 16px; text-decoration:none; color:var(--muted);
        font-size:.8rem; font-weight:500; white-space:nowrap;
        border-bottom:3px solid transparent; margin-bottom:-2px;
        transition:color .15s,border-color .15s; }
nav a:hover { color:var(--blue); border-bottom-color:var(--blue); }

/* Main */
main { max-width:1080px; margin:0 auto; padding:48px 20px 72px; }

/* Q&A cards */
.qa { margin-bottom:68px; }
.qa-hdr { display:flex; align-items:flex-start; gap:14px; margin-bottom:20px; }
.qnum { min-width:34px; height:34px; border-radius:50%;
        background:var(--blue); color:white; font-weight:700; font-size:.85rem;
        display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px; }
.qa-hdr h2 { font-size:1.2rem; font-weight:600; color:var(--navy); line-height:1.4; }
.card { background:var(--white); border:1px solid var(--border); border-radius:14px;
        overflow:hidden; box-shadow:0 1px 6px rgba(26,39,68,.07); }
.card-body { padding:28px 32px; }
.card-body p { margin-bottom:13px; font-size:.93rem; }
.card-body h3 { margin:22px 0 9px; font-size:.72rem; font-weight:700;
                text-transform:uppercase; letter-spacing:.06em; color:var(--blue); }
.card-body ul, .card-body ol { padding-left:22px; margin-bottom:13px; font-size:.91rem; }
.card-body li { margin-bottom:5px; }
.card-diagram { background:#eff3fa; border-top:1px solid var(--border);
                padding:30px 20px; display:flex; flex-direction:column;
                align-items:center; gap:24px; }
.card-diagram svg { max-width:100%; height:auto; }
.diag-cap { font-size:.75rem; color:var(--muted); font-style:italic; text-align:center; }

/* Table */
.tw { overflow-x:auto; margin:14px 0; }
table { width:100%; border-collapse:collapse; font-size:.86rem; }
th { background:var(--navy); color:white; padding:9px 14px; text-align:left;
     font-weight:600; font-size:.8rem; }
td { padding:9px 14px; border-bottom:1px solid var(--border); }
tr:last-child td { border-bottom:none; }
tr:hover td { background:#f4f7ff; }

/* Code */
pre { background:#0e1b35; color:#a8c7fa; padding:16px 20px; border-radius:8px;
      font-size:.78rem; overflow-x:auto; margin:12px 0; line-height:1.55;
      border-left:3px solid var(--blue); }

/* Callouts */
.callout { border-left:4px solid var(--blue); background:var(--pale);
           padding:12px 18px; border-radius:0 8px 8px 0; margin:14px 0; font-size:.89rem; }
.callout.warn { border-left-color:var(--orange); background:#fdf3e7; }
.callout.ok   { border-left-color:var(--green);  background:#edfaf3; }
.callout.note { border-left-color:var(--purple);  background:#f5f3ff; }

/* Two-column layout */
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:14px 0; }
@media(max-width:640px){ .two-col{ grid-template-columns:1fr; } }
.mini { background:#f7f9fd; border:1px solid var(--border); border-radius:8px; padding:15px; }
.mini h4 { font-size:.84rem; font-weight:700; margin-bottom:9px; color:var(--navy); }
.mini ul { padding-left:16px; font-size:.83rem; }
.mini li { margin-bottom:5px; }

footer { text-align:center; padding:28px; color:var(--muted); font-size:.82rem;
         border-top:1px solid var(--border); }
</style>
</head>
<body>

<header>
  <div class="badge">[Topic area · Date]</div>
  <h1>[Title]</h1>
  <p>[One-line description of what this Q&A covers]</p>
</header>

<nav>
  <!-- One <a href="#qN">Q{N} · Short question label</a> per question -->
</nav>

<main>
  <!-- Q&A sections go here -->
</main>

<footer>[Topic] Q&A · Generated from conversation · [Date]</footer>
</body>
</html>
```

### Each Q&A section

Use this structure for each question-answer pair. Number them sequentially:

```html
<section class="qa" id="qN">
  <div class="qa-hdr">
    <div class="qnum">N</div>
    <h2>[The user's question, clean and direct]</h2>
  </div>
  <div class="card">
    <div class="card-body">
      <!-- Answer content: paragraphs, lists, tables, code blocks, callouts -->
      <!-- Use <h3> for sub-sections within the answer -->
      <!-- Use <div class="callout"> for key takeaways or warnings -->
      <!-- Use <div class="two-col"><div class="mini">...</div></div> for comparisons -->
    </div>

    <!-- Include card-diagram only if a diagram adds real clarity -->
    <div class="card-diagram">
      <svg viewBox="0 0 700 300" width="700" height="300" xmlns="http://www.w3.org/2000/svg">
        <!-- SVG diagram here — use the dark navy palette above -->
      </svg>
      <div class="diag-cap">Caption explaining what the diagram shows</div>
    </div>

  </div>
</section>
```

### Append mode — inserting into existing file

When appending to an existing file:

1. Read the file.
2. Find the current highest `id="qN"` to determine the next question number.
3. Add new nav links inside `<nav>` before `</nav>`.
4. Insert new `<section class="qa" ...>` blocks before `</main>`.
5. Update the `<footer>` date if helpful.
6. Write the modified file back.

Use `Edit` with surgical find/replace — do not rewrite the entire file unless it's tiny.

---

## Step 4: Diagram guidance

For each Q&A, decide whether a diagram helps. A diagram is worth it when the answer involves:
- Layers, stacks, or hierarchies
- Data flow between systems
- A before/after comparison
- A class/instance or type/instance relationship
- A state machine or decision tree

For purely factual or list-based answers, skip the diagram.

When drawing SVGs:
- Use the dark navy palette from the CSS variables above (`#1a2744`, `#1a3a5e`, `#3b6fd4`, etc.)
- Include `<defs><marker>` for arrow heads when drawing flow arrows
- Label every box and arrow clearly
- Keep viewBox proportional — don't make diagrams too tall
- White text on dark boxes, dark text on light backgrounds

---

## Step 5: Output

- Save as `qa_<topic-slug>.html` in the current working directory (create mode), or update the existing file (append mode).
- Tell the user the file path and how many Q&As were added vs. already existed.
- Do not open a browser automatically unless the user asks.
