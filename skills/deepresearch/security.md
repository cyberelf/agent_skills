# Security Research Mode

Used when the topic involves security threats, CVEs, attack surfaces, defenses, or vulnerability analysis.

---

## 5-Part Structure

### Part 1: Platform / Technology Landscape
- Architecture and technical internals of the subject platform/system
- Deployment models (consumer, enterprise, cloud, on-prem)
- Ecosystem: marketplace, plugins, integrations, community
- Comparison tables across variants and competitors
- Include Chinese-origin variants when relevant

### Part 2: Threat Modeling
- Confirmed CVEs with CVSS scores and fixed versions
  - Sources: NVD, MITRE CVE, vendor security advisories
- Attack taxonomy: categorize every threat surface (label A–J)
- Case studies: reconstruct confirmed attack chains step by step
- Delta analysis: what is genuinely new vs. pre-existing categories
- Map threats to OWASP Top 10 (relevant list) and MITRE ATLAS
- Gap analysis: threats with NO current defense or CVE tracking

### Part 3: Vendor Solutions
- Traditional security vendors (endpoint, network, identity)
- AI-native security startups
- Platform / internet company native defenses
- Financial sector and regulated industry requirements
- Gap analysis matrix: threat categories × vendor coverage rating
- Emerging approaches not yet commercial

### Part 4: Proposed Architecture *(only after Parts 1–3 are complete)*
- List confirmed gaps from Part 3 before designing anything
- Design principles — each grounded in a specific research finding
- Reference architecture with ASCII diagram
- Novel innovations — one per confirmed gap:
  - What gap it addresses
  - What research it builds on
  - The mechanism
  - Why it's novel
  - Limitations
- Personal vs. enterprise deployment variants
- Threat-to-defense coverage matrix
- Implementation roadmap

### Part 5: Future Forecast
- Technology evolution trajectory (near / mid / long-term)
- Security evolution forecast table
- Market sizing and predictions (Gartner, IDC, vendor data)
- Regulatory and standards evolution (OWASP, MITRE, NIST, relevant law)
- Academic research: what works, what doesn't, open problems

---

## Research Plan Guidelines

Before writing RESEARCH_PLAN.md:
- Fetch the actual product/platform website to verify names
- Confirm whether the focus is enterprise, consumer, or both
- Identify Chinese-origin variants worth including
- Clarify: coding agents vs. general-purpose agents vs. consumer apps (different threat models)
- List known CVE IDs, researcher names, or conference talks as starting points

RESEARCH_PLAN.md must include:
- Correct identification of all subjects (verified against primary sources)
- Research questions per part
- Known starting points: URLs, CVE IDs, vendor names, researcher handles
- Explicit "What NOT to assume before research" section

---

## Agent Prompt Scaffolding

### Agent 1 — Platform Landscape
```
Research the platform architecture, deployment model, ecosystem, and competitive landscape.
Fetch official documentation, GitHub repos, product pages.
Starting URLs: [list specific URLs from the plan]
Searches to perform: "[platform] architecture internals", "[platform] ecosystem plugins", ...
Save to: {folder}/raw_research/01_platform_architecture.md
Target: 2000+ words with comparison tables and source URLs.
```

### Agent 2 — Threat Modeling
```
Research all confirmed CVEs, attack techniques, and threat surfaces.
Primary sources: NVD (nvd.nist.gov), MITRE CVE, vendor advisories, Black Hat/DEF CON papers.
Starting URLs: [NVD search URL, specific CVE links, researcher blog posts]
Searches to perform: "CVE [platform] RCE", "[platform] security vulnerability", "[attack type] [platform]", ...
Save to: {folder}/raw_research/02_threat_landscape.md
Target: 2000+ words. Include CVSS scores, affected versions, and confirmed-in-wild indicators.
```

### Agent 3 — Vendor Solutions
```
Research commercial and emerging security products covering this threat surface.
Cover: endpoint/EDR vendors, AI-native startups, platform-native defenses, enterprise solutions.
Starting URLs: [vendor product pages, analyst reports, startup funding announcements]
Searches to perform: "[threat type] security vendor", "AI agent security startup 2025", ...
Save to: {folder}/raw_research/03_vendor_solutions.md
Target: 2000+ words. Include gap matrix: which vendors cover which attack categories.
```

### Agent 4 — Domain-Specific Research
```
Research [domain-specific aspect relevant to this topic].
[Customize per topic: e.g., regulatory requirements, Chinese variants, supply chain specifics]
Starting URLs: [specific to domain]
Save to: {folder}/raw_research/04_[domain].md
Target: 2000+ words.
```

### Agent 5 — Frameworks & Forecast
```
Research the future trajectory: technology evolution, market sizing, regulatory developments, academic research.
Sources: Gartner/IDC reports, standards bodies (OWASP, MITRE, NIST), arXiv, conference proceedings.
Starting URLs: [OWASP page, MITRE ATLAS, Gartner press releases, arXiv search]
Searches to perform: "[topic] market size 2025 2030", "[topic] regulatory framework", "academic research [topic] security", ...
Save to: {folder}/raw_research/05_frameworks_forecast.md
Target: 2000+ words with market tables, regulatory timeline, and academic paper citations.
```

---

## Compilation Rules

- Do NOT write Part 4 (architecture) until Parts 1–3 raw files are read and reviewed
- Part 4 innovations must each close a **confirmed gap** from Part 3's gap matrix
- Every design principle must cite a specific research finding (file + section)
- Architecture diagram should cover at minimum: agent layer, runtime layer, OS layer, network layer, cloud layer

---

## Lessons Learned (Security Mode)

1. **Verify platform names first.** "OpenClaw" ≠ OpenHands — fetch the actual website before writing a single line of the plan.
2. **Wrong agent focus.** Coding agents, general-purpose agents, enterprise agents, and consumer agents have fundamentally different threat models. Confirm which.
3. **Threat taxonomy before architecture.** Labeling attack categories (A through J) before designing defenses ensures each innovation maps to a real threat, not a presumed one.
4. **Gap matrix is the design input.** Part 4 innovations that don't target a confirmed gap in the matrix are generic and low-value.
5. **Parallel agents saved ~70% time** vs. sequential in the OpenClaw research (March 2026).
