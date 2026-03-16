---
name: deepresearch
description: Conduct structured deep research on any topic — threat landscapes, technology comparisons, vendor analysis, and proposed solutions. Produces a multi-part report grounded in confirmed sources, with no premature design assumptions. Use when asked to "deepresearch", "research deeply", or produce a comprehensive multi-part research report on a topic.
allowed-tools: Agent, WebFetch, WebSearch, Read, Write, Edit, Glob, Grep, Bash
---

# Deep Research Skill

Conduct rigorous, multi-part research on a complex topic, producing a report grounded entirely in confirmed sources. No design assumptions are made before research is complete. All claims have source links.

## Core Principle: Research First, Design Last

**DO NOT design solutions or architectures before completing all research phases.** Preset conclusions constrain what you find. The design phase begins only after Parts 1–3 are fully researched and documented.

## Report Structure (5 Parts)

Every deepresearch report follows this structure:

### Part 1: Landscape — Platform/Technology/Subject Comparison
- Architecture, technical internals, deployment model
- User scenarios and use cases
- Ecosystem: marketplace, plugins, integrations, community
- Comparison tables across variants/competitors
- Include both Western and Chinese-origin variants when relevant

### Part 2: Threat Modeling
- Confirmed CVEs with CVSS scores and fixed versions (primary sources: NVD, vendor advisories, security researchers)
- Attack taxonomy: categorize every threat surface (A–J or similar)
- Case studies: reconstruct confirmed attack chains step by step
- Delta analysis: what is genuinely new vs. pre-existing threat categories
- Map to OWASP (relevant Top 10 list), MITRE ATLAS (tactics/techniques)
- Gap analysis: what threats have NO current defense or CVE tracking

### Part 3: Vendor Solutions
- Traditional security vendors (endpoint, network, identity)
- AI-native security startups
- Platform/internet company approaches
- Financial sector and regulatory requirements
- Gap analysis matrix: 10 attack categories × coverage rating
- Emerging approaches (not yet commercial)

### Part 4: Proposed Architecture (ONLY after Parts 1–3 complete)
- Design principles — each grounded in a specific research finding
- Reference architecture with diagram (ASCII art or structured description)
- Novel innovations — each targeting a confirmed gap from Part 3
  - State what gap it addresses, what research it's based on, the mechanism, why it's novel, and its limitations
- Personal vs. enterprise deployment variants
- Threat-to-defense coverage matrix
- Implementation roadmap

### Part 5: Future Forecast
- Technology evolution trajectory (near/mid/long-term)
- Security evolution forecast table
- Market sizing and predictions (cite Gartner, IDC, vendor data)
- Regulatory and standards evolution (OWASP, MITRE, NIST, relevant law)
- Academic research summary: what works, what doesn't

## Execution Method: Parallel Research Agents

Launch 4–5 parallel research agents, one per Part (or per major topic area), using the Agent tool with `subagent_type: "general-purpose"`. Each agent:

1. Searches for primary sources (vendor blogs, CVE databases, academic papers, regulatory texts)
2. Fetches and reads source content — does not rely on training data alone
3. Saves raw research to `/raw_research/XX_topic.md` in the working directory
4. Returns a summary of key findings

Agents run in parallel (`run_in_background: true`) for Parts 1–4 research, then the coordinator compiles findings into the main report.

## Source Quality Requirements

All claims must be backed by:
- **CVEs**: NVD, MITRE CVE, vendor security advisories, security researcher disclosures
- **Attack details**: Primary researcher blog posts, conference papers (Black Hat, DEF CON, USENIX, CCS)
- **Vendor products**: Official vendor documentation, product pages, press releases, investor relations
- **Academic findings**: arXiv preprints, ACL/NAACL/NeurIPS/ICLR proceedings, OpenReview
- **Market data**: Gartner, IDC, Forrester reports; vendor ARR disclosures; funding announcements
- **Regulatory**: Official regulatory text (EUR-Lex, NIST, CISA, Federal Register)

**Do not cite Wikipedia, unattributed blog posts, or secondary summaries as primary sources.**

## File Structure

```
{working_dir}/
├── RESEARCH_PLAN.md          # Initial research plan (v0.1 → v0.2 after corrections)
├── RESEARCH_REPORT.md        # Main compiled report (updated as agents complete)
└── raw_research/
    ├── 01_platform_architecture.md
    ├── 02_threat_landscape.md
    ├── 03_vendor_solutions.md
    ├── 04_[domain_specific].md
    └── 05_frameworks_forecast.md
```

## How to Invoke

When the user asks:
- `/deepresearch [topic]` — start full research on the topic
- `/deepresearch [topic] focus: [area]` — emphasize a specific area
- `/deepresearch [topic] output: [format]` — specify output format (HTML, PDF, Markdown)

### Step 1: Understand and Correct Scope

Before writing any plan:
- Clarify ambiguous platform/product names (fetch the actual product website if needed)
- Confirm whether the focus is enterprise, consumer, or both
- Identify if there are Chinese-origin variants worth including
- Ask: "What threats or use cases are most important to you?"

### Step 2: Write RESEARCH_PLAN.md

Document:
- Correct identification of all platforms/subjects
- Research questions for each Part
- Known starting points (URLs, CVEs, vendor names)
- What NOT to assume before research

### Step 3: Launch Parallel Research Agents

```
Agent 1: Part 1 (Platform/Landscape)    → background
Agent 2: Part 2 (Threat Modeling)       → background
Agent 3: Part 3 (Vendor Solutions)      → background
Agent 4: Part 4/5 domain-specific       → background
Agent 5: Frameworks/Forecast            → background
```

### Step 4: Compile Main Report

As agents complete:
1. Save raw research to `/raw_research/` immediately
2. Integrate into `RESEARCH_REPORT.md` Part by Part
3. Do NOT start Part 4 (Architecture) until Parts 1–3 are complete and reviewed

### Step 5: Design Phase (Part 4)

Only after research is complete:
1. List the confirmed gaps from Part 3 Gap Analysis
2. List the best academic/practical approaches found in research
3. Derive design principles (each grounded in a specific finding)
4. Propose innovations — one per confirmed gap
5. Build coverage matrix: does each innovation close its gap?

### Step 6: Output

- Default output: `RESEARCH_REPORT.md` (Markdown)
- If user requests HTML: create bilingual or single-language HTML page
- If user requests summary: extract executive summary + key tables

## Lessons from Execution (Guards Research Project, March 2026)

**Common errors to avoid:**
1. **Wrong platform identification**: Always fetch the actual website before writing the plan. "openclaw" ≠ OpenHands (a coding agent framework); it was a different product entirely.
2. **Premature architecture**: Do not write Part 4 before Parts 1–3. Preset innovations constrain research findings and produce generic outputs.
3. **Wrong focus (coding vs. general-purpose)**: Clarify whether the subject is coding agents, general-purpose agents, enterprise agents, or consumer agents. They have fundamentally different threat models.
4. **Blocked sources**: Chinese sources behind WeChat auth walls or Baidu CAPTCHAs cannot be fetched. Search for equivalent open-web sources instead.
5. **Rate limits on long-running agents**: Save raw research immediately when an agent completes; do not rely on the agent being resumable.

**What worked well:**
- Parallel agents saved ~70% of time vs. sequential research
- Starting each agent with "fetch this specific URL first" (e.g., the Zscaler guide, the Oasis Security disclosure) grounded the research in confirmed primary sources
- Keeping Part 4 empty enforced the research-first discipline and produced genuinely novel architecture innovations (5 innovations targeting gaps with no existing vendor solution)
- Documenting the gap analysis matrix before designing ensured each innovation addressed a real, confirmed gap

## Example Invocations

```
/deepresearch security for personal AI endpoint agents including OpenClaw and Claude Code
/deepresearch supply chain security for npm packages
/deepresearch quantum-safe cryptography for financial services
/deepresearch Chinese AI regulation impact on enterprise data governance
```
