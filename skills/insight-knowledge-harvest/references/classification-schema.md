# Classification Schema

Use these controlled values when registering raw materials for a viewpoint-oriented knowledge base.

## material_kind

| Value | Meaning |
|---|---|
| practitioner_essay | Independent or practitioner-written analysis with reusable arguments. |
| vendor_engineering | First-party engineering post with implementation detail, architecture, metrics, or lessons. |
| vendor_changelog | Release note or launch post that changes technical assumptions or points to deeper material. |
| research_paper | Academic paper, lab report, system card, model card, or technical report. |
| benchmark | Benchmark site, leaderboard, methodology, dataset card, or evaluation harness. |
| standard_protocol | Protocol spec, interoperability standard, semantic convention, or API standard. |
| governance_framework | Governance, risk, compliance, legal, or regulatory guidance. |
| security_research | Vulnerability write-up, exploit research, audit report, threat model, or incident postmortem. |
| case_study | Production implementation story with concrete architecture, metrics, or lessons. |
| analyst_report | Analyst or consultancy report with disclosed methodology. |
| repo_release | GitHub release, changelog, or commit feed entry from a relevant project. |

## topic_domain

| Value | Meaning |
|---|---|
| architecture | Agent architecture, harness design, orchestration, state, memory, workflow design. |
| evals | Evaluation methods, test harnesses, LLM-as-judge, benchmark design, regression testing. |
| security | Prompt injection, tool abuse, sandboxing, identity, excessive agency, data exfiltration. |
| governance | Risk management, compliance, approval workflows, auditability, human oversight. |
| protocols | MCP, A2A, AG-UI, OpenTelemetry GenAI, tool/function schemas, interoperability. |
| observability | Tracing, metrics, monitoring, telemetry, audit logs, production feedback loops. |
| model_foundation | Model internals, reasoning, RLHF, tool-use capabilities, model strategy. |
| org_adoption | Team process, operating model, adoption maturity, change management, platform strategy. |
| product_design | Human-in-loop UX, agent control surfaces, user trust, workflow ergonomics. |
| benchmark_results | Scoreboard changes, methodology lessons, benchmark limitations. |
| legal_market | Regulation, standards adoption, market sizing, analyst framing. |

## evidence_type

| Value | Meaning |
|---|---|
| code | Public code, harness, repo, implementation, or reproducible example. |
| benchmark_data | Leaderboard, dataset, eval result, methodology, or ablation. |
| incident | Real incident, exploit, audit finding, failure report, or postmortem. |
| standard_text | Formal standard, protocol clause, regulatory language, or control definition. |
| case_metrics | Production metrics, latency, cost, accuracy, reliability, adoption, or business outcome. |
| expert_argument | Reasoned practitioner or researcher argument without full empirical backing. |
| survey_data | Analyst, industry, or academic survey with sample and methodology. |
| changelog_delta | Product or API change with operational impact. |

## credibility_tier

| Value | Rule of thumb |
|---|---|
| P1 | Primary, high-signal, accountable, current, and worth automatic or priority intake. |
| P2 | Useful but needs filtering, bias notes, or selective intake. |
| P3 | Manual review only, slow cadence, paywalled, broad, or high bias risk. |
| reject | Does not meet provenance, quality, relevance, or compliance requirements. |

## ingestion_priority

| Value | Meaning |
|---|---|
| critical | Download and verify first; likely foundational for the collection target. |
| high | Download and verify after critical items. |
| medium | Keep in the ingest list; download when it fills a gap or supports a stronger source. |
| low | Metadata-only or watch unless explicitly requested. |
| manual | Manual review needed before download or verification. |
| reject | Do not ingest beyond rejection metadata. |

## lifecycle_status

| Value | Meaning |
|---|---|
| candidate | Found but not quality-checked yet. |
| accepted | Passed quality gate and can enter the raw-material registry. |
| deep_read | Accepted and worth detailed extraction later. |
| watch | Potentially useful but not enough evidence or maturity yet. |
| revisit | Needs later revalidation because of freshness, access, license, or activity uncertainty. |
| rejected | Reviewed and rejected with reason. |
| archived | Previously useful but no longer active or current. |

## ingest_status

Use this field in `source/ingest.md` and downloaded/verified material records to track pipeline state.

| Value | Meaning |
|---|---|
| candidate_found | Candidate URL found and canonical metadata started. |
| queued_download | Candidate passed initial gate and is waiting for download. |
| downloaded | Markdown copy or metadata-only record has been created under `source/raw/`. |
| metadata_only | Only metadata may be stored because of paywall, license, access, or compliance limits. |
| download_failed | Download attempted and failed; keep reason and next action. |
| queued_verification | Raw Markdown exists and is waiting for verifier review and in-place metadata update. |
| verified | Raw record metadata has been updated in place after verification. |
| verification_failed | Verification attempted and failed; keep reason and next action. |
| rejected | Reviewed and rejected; keep reason to avoid duplicate work. |
| watch | Track for future development, but do not download or verify yet. |
| revisit | Re-check later because freshness, access, license, or methodology is uncertain. |
| archived | Previously ingested but no longer active or current. |

## download_status

| Value | Meaning |
|---|---|
| not_started | No download attempted yet. |
| downloaded | Source content or allowed excerpt/metadata has been saved under `source/raw/`. |
| metadata_only | Only metadata and curator notes were saved. |
| failed | Download failed because of technical or access issues. |
| blocked | Source blocks automation or access. |
| manual_required | Human/manual download or legal review is required. |

## verification_status

| Value | Meaning |
|---|---|
| not_started | Verification not started. |
| queued | Raw material is ready for verifier review. |
| in_review | Verifier is actively checking source quality and metadata. |
| verified | Verification completed and the raw record metadata was updated in place. |
| rejected | Verifier rejected the material with reason. |
| needs_followup | Verification found unresolved issues or gaps. |
| failed | Verification failed because of missing content, access, or tooling issues. |

## insight_potential

| Value | Rule of thumb |
|---|---|
| high | Contains multiple clear claims, trade-offs, models, or design rules. |
| medium | Contains one useful claim or supports another stronger source. |
| low | Mostly contextual, newsy, or operational; keep only if needed for provenance. |

## source_bias

Use a short phrase such as:

- vendor_product_bias
- vendor_research_bias
- consulting_sales_bias
- analyst_paywall_bias
- security_research_bias
- benchmark_organizer_bias
- practitioner_experience_bias
- standards_body_bias
- community_open_source_bias

## compliance_status

Use these values as curation caveats, not automatic download blockers. In the internal experimental harvest workflow, a publicly reachable page with unclear or absent reuse-license text can still be captured as raw material; record `needs_review` or another appropriate caveat in registers or ingest notes. Continue to use metadata-only for paywalled, authentication-gated, blocked, CAPTCHA-protected, or technically inaccessible sources.

| Value | Meaning |
|---|---|
| clear | Metadata, raw capture, summary, and excerpts are acceptable for intended use. |
| limited_excerpt | Use short excerpts only; avoid long copied passages. |
| metadata_only | Store source identity metadata, URL, processing state, and access caveat only. |
| paywalled | Do not store proprietary body text; cite title, date, and accessible metadata. |
| blocked | Source is inaccessible or blocks automation; manual review only. |
| needs_review | License, terms, or reuse constraints are unclear; for public pages this is a caveat to record, not by itself a metadata-only trigger. |