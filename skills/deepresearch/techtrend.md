# Tech Trend / Ecosystem Research Mode

Used when the topic involves technology trends, ecosystem mapping, market forecasting, hardware/software landscape analysis, or adoption trajectories. No security threat modeling — the goal is to understand **what exists, how it works, and where it's going**.

---

## 5-Part Structure

### Part 1: Ecosystem Landscape
- What is the subject? Correct identification of all platforms, products, or technologies
- Architecture overview: how the pieces fit together end-to-end
- Major players: Western and Chinese-origin variants where relevant
- Deployment models: consumer, enterprise, embedded, cloud-hybrid
- Adoption signals: GitHub stars, downloads, market share, developer surveys
- Comparison tables across variants and competitors

### Parts 2–4: Ecosystem Dimensions *(defined per-topic in RESEARCH_PLAN.md)*

**These parts are NOT fixed.** Before launching agents, identify the 3 most important dimensions of the specific ecosystem and define them explicitly in RESEARCH_PLAN.md.

**Choosing dimensions:** Ask "what are the 3 layers or axes that most determine how this ecosystem works and where it's going?"

Examples by topic:

| Topic | Part 2 | Part 3 | Part 4 |
|-------|--------|--------|--------|
| Endpoint LLM | Hardware (NPU/SoC/GPU) | Models (architectures, quantization) | Runtimes & Frameworks |
| Autonomous vehicles | Sensors & perception | Compute platforms | Software stacks |
| Edge AI chips | Silicon architecture | SDK/software ecosystem | Target verticals |
| Quantum computing | Hardware (qubit types) | Algorithms & software | Applications |
| Generative AI tools | Foundation models | Developer platforms | Enterprise adoption |
| Mobile payments | Infrastructure & protocols | Provider ecosystem | Consumer/merchant adoption |

Each dimension part covers:
- Technical deep dive with real specs, benchmarks, or data
- Major players and competitive positioning
- Gaps, bottlenecks, and unmet needs
- Application-specific relevance

### Part 5: Forecast
- Technology trajectory table: year × platform/product × capability milestone × confidence
- Market sizing with analyst citations and CAGRs (Gartner, IDC, MarketsandMarkets, etc.)
- Key inflection points: dated, with confidence levels (Confirmed / Probable / Extrapolation / Speculative)
- Strategic winners and losers: separate tables per axis with explicit reasoning
- OS-native vs. open ecosystem dynamics (where applicable)
- Regulatory landscape: EU AI Act, US policy, China regulations — impact on the ecosystem
- Academic research frontiers: specific papers (arXiv IDs, venue, key result, relevance)
- Risks and uncertainties that could change the trajectory

---

## Research Plan Guidelines

Before writing RESEARCH_PLAN.md:
- Fetch actual product/platform websites to confirm what they are
- Identify the 3 ecosystem dimensions for Parts 2–4 — justify the choice
- Confirm scope: consumer, enterprise, or both; Western and/or Chinese market
- List known starting URLs, analyst reports, benchmark sources

RESEARCH_PLAN.md must include:
- Explicit definition of what Parts 2–4 cover for this specific topic
- Research questions per part
- Known starting points: URLs, benchmark leaderboards, analyst report names, key vendor names
- "What NOT to assume before research" section

---

## Agent Prompt Scaffolding

### Agent 1 — Ecosystem Landscape
```
Research the full ecosystem landscape: what the subject is, how the pieces fit together,
who the major players are, and current adoption signals.
Fetch official websites, GitHub repos, developer surveys, industry reports.
Starting URLs: [list specific URLs from the plan]
Searches: "[topic] ecosystem overview 2025", "[topic] major players comparison", ...
Save to: {folder}/raw_research/01_landscape.md
Target: 2000+ words with comparison tables and source URLs.
```

### Agent 2 — [Dimension 2 from plan]
```
Research [dimension name — e.g., hardware, models, sensor technology].
Focus on: technical specs, benchmarks, major products, competitive positioning.
Starting URLs: [specific product pages, benchmark sites, spec sheets]
Searches: "[specific technical terms]", "[dimension] benchmark comparison 2025", ...
Save to: {folder}/raw_research/02_[dimension].md
Target: 2000+ words. Include real specs/numbers, comparison tables, source URLs.
Note publication dates — distinguish confirmed shipped vs. announced vs. rumored.
```

### Agent 3 — [Dimension 3 from plan]
```
Research [dimension name — e.g., runtimes, software stacks, platform ecosystem].
Focus on: how it works technically, major players, adoption data, performance comparisons.
Starting URLs: [GitHub repos, official docs, developer surveys]
Searches: "[runtime/framework] comparison performance 2025", "[dimension] adoption statistics", ...
Save to: {folder}/raw_research/03_[dimension].md
Target: 2000+ words with technical depth and real data.
```

### Agent 4 — [Dimension 4 from plan — or Applications]
```
Research [dimension name — e.g., applications, use cases, verticals].
Focus on: real shipped products (not just announced), application categories, gap analysis.
Starting URLs: [product pages, press releases, app store listings, company blogs]
Searches: "[use case] shipped product [topic] 2025", "[vertical] [topic] real-world deployment", ...
Save to: {folder}/raw_research/04_[dimension].md
Target: 2000+ words. Distinguish confirmed shipped vs. demos vs. research prototypes.
Include a gap table: use case × current product coverage × what's missing.
```

### Agent 5 — Forecast 2026–2030
```
Research the future trajectory: hardware roadmaps, model capability trends, market sizing,
regulatory developments, and academic research frontiers.
Sources: Gartner/IDC/analyst reports, vendor investor presentations, roadmap announcements, arXiv.
Starting URLs: [analyst report pages, vendor roadmap pages, arXiv search URL]
Searches:
  "[topic] market size forecast 2030 IDC Gartner"
  "[topic] hardware roadmap 2026 2027"
  "[technology] research frontier arXiv 2025"
  "[key vendors] strategic outlook investor"
Save to: {folder}/raw_research/05_forecast.md
Target: 2000+ words. Include:
- Hardware/compute trajectory table (year × platform × milestone)
- Market sizing table with source citations and CAGRs
- Inflection points table with confidence levels
- Strategic winners/losers per axis with reasoning
- Academic papers table (paper × venue × key result × relevance)
```

---

## Compilation Rules

- Compile `RESEARCH_REPORT.md` **only after all 5 agents complete**
- The executive summary must include: top 5 structural findings + key stats with numbers
- Every table from raw research should appear in the compiled report (summarize, don't omit)
- Forecast confidence levels: Confirmed (official roadmap) / Probable (logical extrapolation) / Extrapolation (trend-based) / Speculative (aspirational)
- Cite specific analyst reports by name (Gartner, IDC, etc.) — do not write "analysts say"

---

## Lessons Learned (Tech Trend Mode)

1. **Define dimensions before launching agents.** The endpoint LLM research (March 2026) used Hardware / Models / Runtimes / Applications — all 5 agents produced focused, non-overlapping research because dimensions were defined upfront.
2. **Real numbers matter.** Agents must fetch and report actual specs (tokens/sec, TOPS, market CAGRs) — not just describe the landscape qualitatively. "Apple M4 Max: 546 GB/s, ~70 tok/s on 7B Q4" is useful; "Apple has a fast chip" is not.
3. **Distinguish confirmed vs. announced vs. speculative.** Hardware roadmaps mix confirmed silicon (shipped), announced specs (press release), and rumored specs (leaks). Label each explicitly.
4. **Chinese variants are often underresearched.** Qwen, DeepSeek, MediaTek, and similar often lack English primary sources. Search for their English-language technical blogs, GitHub READMEs, and international press coverage.
5. **Gap analysis is as valuable as coverage analysis.** The most actionable finding in the endpoint LLM research was the gap table: privacy AI journaling, consumer ambient AI, on-device personalization — all technically feasible, no shipped product.
6. **Market sizing has wide analyst variance.** Report the range with sources rather than picking one number. Edge AI 2030: $59B (MarketsandMarkets hardware-only) to $157B (all edge AI including software/services) — both are valid at different scope definitions.
