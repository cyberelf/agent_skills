# Source Priority For Raw Insight Materials

Use this reference to decide where to collect high-quality original materials first. The goal at this stage is source intake, quality control, and classification. Final viewpoint extraction is a later step.

## P1: Priority Intake and Deep-Read Candidates

| Source | Durable URL or feed | Why collect | Material to register | Caveat |
|---|---|---|---|---|
| Simon Willison | https://simonwillison.net/atom/everything/ | Frequent primary practitioner analysis of LLM security, MCP, agents, and tool boundaries. | Original analysis posts, incident-style examples, prompt-injection and MCP/tool-use materials. | High volume; reject link-only posts unless they point to canonical source material. |
| Hamel Husain | https://hamel.dev/ | Strong source for eval-first AI product practice and coding-agent evaluation. | Evals articles, coding-agent evaluation materials, framework-skeptic implementation guidance. | Irregular cadence. |
| Eugene Yan | https://eugeneyan.com/ | Production LLM and RAG systems with practical measurement focus. | RAG reliability articles, eval loops, human-in-loop implementation notes. | Lower cadence. |
| Chip Huyen | https://huyenchip.com/feed.xml | Systems-oriented AI engineering source covering context, latency, state, tools, and feedback loops. | Agent design posts, context-management materials, compound AI system discussions. | Sparse feed. |
| Martin Fowler | https://martinfowler.com/feed.atom | Enterprise architecture framing for AI-assisted and agentic systems. | Harness engineering, workflow-vs-agent articles, architecture decision materials. | Low AI-specific cadence. |
| Anthropic Research and Engineering | https://www.anthropic.com/research | First-party research and engineering materials on trustworthy agents, tool use, and Claude Code. | Research posts, engineering posts, system cards, tool-use guidance, release notes with architecture impact. | No standard RSS; vendor perspective. |
| Lilian Weng | https://lilianweng.github.io/index.xml | Foundational literature synthesis for planning, memory, tool use, reward hacking, and alignment. | Survey posts and research explainers. | Research-heavy and low cadence. |
| Jason Liu | https://jxnl.co/writing/ | Practical material on structured outputs, context engineering, and eval decomposition. | Writing posts, interviews, and implementation notes. | Some consulting bias. |
| Applied LLMs | https://applied-llms.org/ | Static cross-practitioner production reference. | Chapters or sections with concrete production lessons. | Static reference, not a feed. |

## P2: Selective Intake

| Topic | Source | URL | Material to register | Caveat |
|---|---|---|---|---|
| Security and governance | OWASP GenAI | https://genai.owasp.org | LLM Top 10, agentic AI threats, excessive agency materials, insecure plugin/tool guidance. | Pair with exploit research. |
| Security and exploitability | Trail of Bits | https://blog.trailofbits.com/feed/ | Browser-agent risks, tool-execution attack chains, sandboxing gaps, audit methodology. | Filter to AI posts. |
| Risk management | NIST AI RMF | https://www.nist.gov/itl/ai-risk-management-framework | AI RMF, GenAI profile, risk-control language, governance source sections. | Abstract until translated into implementation controls. |
| Frontier autonomy | METR | https://metr.org/research | Time-horizon capability reports, autonomous task risk materials, eval integrity posts. | Frontier focus. |
| Deception and scheming | Apollo Research | https://apolloresearch.ai/research | Scheming, monitorability, deceptive alignment research reports. | Governance-heavy, less operational. |
| Enterprise adoption | Thoughtworks Insights | https://www.thoughtworks.com/rss/insights.xml | Adoption maturity, context engineering, team-level AI operating pattern materials. | Intentionally lagging. |
| Architecture and org practice | O'Reilly Radar | https://www.oreilly.com/radar/feed/ | Context engineering, agent architecture, autonomy risk, enterprise adoption materials. | Contributor bias varies. |
| Engineering case studies | InfoQ | https://www.infoq.com/feed/ | Production architecture talks, deployment lessons, platform engineering materials. | Filter by author quality. |

## Benchmark-Derived Materials

| Benchmark | URL | Material to register |
|---|---|---|
| SWE-bench | https://www.swebench.com/ | Site, paper, repo, leaderboard, methodology, and harness materials. |
| BFCL | https://gorilla.cs.berkeley.edu/leaderboard.html | Leaderboard, methodology, dataset, function-calling evaluation materials. |
| AgentDojo | https://github.com/ethz-spylab/agentdojo | Repo, paper, attack tasks, defense notes, prompt-injection benchmark materials. |
| AgentHarm | https://huggingface.co/datasets/ai-safety-institute/AgentHarm | Dataset card, paper or report, harmful multi-step task taxonomy. |
| tau2-bench | https://github.com/sierra-research/tau2-bench | Repo, task environments, scoring methodology, business-rule reliability examples. |
| BrowserGym and WebArena | https://github.com/ServiceNow/BrowserGym | Repo, papers, tasks, harness docs, web-agent evaluation methodology. |

## De-emphasize

Keep these only for changelog awareness unless they publish architecture, system-card, benchmark, or postmortem-grade content:

- AWS News Blog
- OpenAI News RSS
- GCP Release Notes
- GitHub Blog launch posts
- Vendor product blogs without code, diagrams, metrics, or concrete lessons

## Acceptance Test

Before indexing an item, ask:

1. Is this an original or canonical source rather than a shallow repost?
2. Are author, organization, date, and URL clear enough for provenance?
3. Does it contain evidence, method, implementation detail, standard text, or practitioner experience?
4. Is it likely to produce future viewpoint or design-rule extraction?
5. Can its bias, license, and compliance constraints be recorded safely?
6. Does it fit one or more controlled classification categories?