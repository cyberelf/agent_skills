---
name: insight-knowledge-harvest
description: 'Build and expand an insight-ready raw-material layer by discovering page-level sources, deduplicating them with an internal pre-crawl link index, capturing raw Markdown, verifying metadata in place, and keeping ingest/register state aligned. Use for additive source harvesting, raw webpage capture, source registry maintenance, source/ingest tracking, source/raw downloads, and in-place verification rather than final synthesis.'
argument-hint: 'Collection topic/scope, freshness window, source bases or URLs, additive vs repair mode, and any download/verification constraints'
user-invocable: true
---

# Insight Knowledge Harvest

Use this skill to build and incrementally expand a curated raw-material layer for future viewpoint and insight extraction.

This is a source-ingestion and verification workflow, not a final insight-writing workflow. Its job is to inspect the current KB as context, promote or discover candidate page-level sources, deduplicate them, capture accepted pages into raw Markdown, and keep ingest plus verification state aligned across the project.

The operating model is intentionally simple:

- `source/raw/` stores one raw page capture per canonical source page or document, plus minimal identity, processing-state, and high-level classification metadata.
- `source/ingest.md` tracks minimal pipeline state for every candidate or accepted material.
- `source/registers/` holds curator-facing notes such as rejection reasons, gap lists, deep-read queues, and the classification schema vocabulary.
- `source/.harvest/` optionally stores hidden operational deduplication state and detailed classification metadata in SQLite for broader discovery runs.

In default additive mode, existing materials are treated as read-only context for topic promotion, deduplication, and gap detection. The skill normally adds new page-level captures, verifies newly downloaded files in place, and avoids rewriting prior raw materials unless the user explicitly asks for repair or re-verification.

Raw files must remain raw captures, not summaries. Curator judgment belongs in ingest, register notes, or the internal SQLite index, while the raw file keeps only source identity, processing-state metadata, and the high-level classification trio: `material_kind`, `topic_domain`, and `credibility_tier`.

At a glance, this skill is best when you need to:

- grow an evidence base before insight extraction,
- keep one-file-per-page provenance clean,
- run incremental source discovery without reprocessing the whole archive,
- and preserve a separation between raw source content and curator-written interpretation.

## Output Language Policy

- By default, all generated curation prose must be in Simplified Chinese.
- This Chinese-default rule applies to `source/ingest.md`, `source/registers/*.md`, rejection logs, gap lists, deep-read queues, candidate-topic promotion notes, and any curator-written notes.
- Do not translate the raw captured source body in `source/raw/`; preserve the source page language there.
- Keep controlled identifiers and schema keys in their canonical English forms when they are part of filenames, YAML field names, status values, or controlled vocabularies.
- When a mixed-language output is unavoidable, prefer: English for identifiers and schema values, Chinese for explanations and notes.

## Non-Negotiable Output Rules

- `source/raw/` contains raw page captures, not summaries, analysis notes, quality scores, detailed classification blocks, or site overviews.
- Each raw file represents exactly one canonical webpage, post, paper page, README, spec page, or document.
- If multiple pages matter, create multiple raw files.
- Raw files use standard Markdown YAML front matter delimited by `---`.
- Raw front matter stays minimal: only source identity fields, processing-state fields, and the high-level classification fields `material_kind`, `topic_domain`, and `credibility_tier`.
- Verification updates the raw file's processing metadata in place; do not create a parallel verified copy or `source/verified/` record by default.
- Curation, detailed classification, scoring, rejection reasons, and insight directions belong in `source/.harvest/link-index.sqlite3`, `source/registers/`, or `source/ingest.md`, not in `source/raw/`.
- Pre-crawl link discovery state belongs in an internal SQLite database under `source/.harvest/` by default; do not copy hidden operational metadata from that database into `source/raw/`, `source/ingest.md`, or downstream insight notes unless the user explicitly asks for an audit/export.
- Detailed classification fields other than `material_kind`, `topic_domain`, and `credibility_tier` belong in the internal SQLite link index by default. This includes `evidence_type`, `ingestion_priority`, `lifecycle_status`, `insight_potential`, `source_bias`, and `compliance_status`.
- The source-side classification schema must exist under `source/registers/`; do not rely only on the skill-local reference file.
- By default, do not keep materials older than 6 months from the retrieval date unless the user explicitly requests historical coverage or no newer canonical source exists and the exception is recorded.
- Do not store harvested outputs inside the skill directory.

## Default Additive Mode

When the user asks to continue, expand, update, or add to a collection, default to discovering and capturing new page-level source materials.

- Treat existing `source/` content as read-only context for topic promotion, deduplication, next material ID selection, and gap detection.
- Do not optimize, rewrite, re-summarize, normalize, or re-verify existing raw captures by default.
- Only modify existing raw files when the user explicitly asks for repair/reverification, when a new candidate collides with an existing material record, or when a narrow metadata correction is necessary to register a newly captured source correctly.
- Verification in the default workflow applies to newly downloaded or newly queued raw captures, not to the whole existing archive.
- If existing materials look weak or malformed while adding new sources, record a concise Chinese follow-up note in `source/ingest.md` or the relevant register; keep moving on new-source capture unless the user redirects to cleanup.

## When to Use

- Build or expand the source-material registry behind a knowledge base of durable ideas, viewpoints, and insights.
- Continue adding new source captures to an existing collection without reworking prior materials.
- Collect original articles, posts, papers, benchmark pages, standards pages, protocol docs, security research, case studies, and practitioner essays.
- Decide whether a candidate source page is worth indexing, deep reading, or rejecting.
- Download high-value candidate pages into project-root `source/raw/` as one Markdown file per canonical webpage or document.
- Verify downloaded raw page captures in a follow-up pass and update verification metadata in place inside project-root `source/raw/` files.
- Maintain `source/ingest.md` as the source-ingestion status list.

## Do Not Use

- Pure daily launch monitoring or generic news aggregation.
- Writing final viewpoint summaries before provenance, quality, and source capture have been checked.
- Treating a whole site, repository, documentation tree, or landing page as one material when the useful unit is a specific post, page, paper, README, or spec page.
- Bundling multiple webpages into one raw file.
- Link dumps without quality decisions and processing state.
- Keeping sources older than 6 months by default when fresher primary material is available.

## Project Output Layout

```text
source/
├── .harvest/                  # internal SQLite link index and operational crawl state
├── ingest.md                  # minimal status list for every candidate/material
├── raw/                       # one raw Markdown page capture per canonical URL
└── registers/                 # collection-level candidate registers, classification schema, and gap/deep-read queues
```

Use the [source material template](./assets/source-material-template.md) for raw files in `source/raw/`.
Use the [ingest list template](./assets/ingest-list-template.md) for `source/ingest.md`.
Copy [classification schema](./references/classification-schema.md) into `source/registers/classification-schema.md` when initializing the project root if it is missing, incomplete, or outdated.

The optional pre-crawl link index database defaults to `source/.harvest/link-index.sqlite3`. It is an internal deduplication and processing-state cache, not a reader-facing deliverable.

## Current KB Topic Promotion

When the user gives a broad collection direction, a vague theme, or no explicit candidate topics, do not treat discovery as starting from zero.

- Inspect the current KB first: existing `source/registers/`, `source/ingest.md`, verified items in `source/raw/`, and any adjacent collection notes already present in the project root.
- Use the inspection as read-only context unless the user explicitly asks for cleanup.
- Promote new candidate topics based on the current KB's signals: repeated domains, explicit gap lists, weak evidence clusters, under-covered counterpoints, stale clusters that need fresh sources, and collections that have raw materials but no balancing or benchmark sources.
- Prefer promoted topics that compound the current KB instead of creating disconnected one-off collections.
- Record promoted candidate topics and why they were promoted in Chinese inside the relevant register or ingest notes.
- If the current KB already contains a nearby collection, bias discovery toward complementing it: add missing counterpoints, non-vendor evidence, benchmark methodology, security failure cases, standards, or operational case studies before expanding into unrelated areas.
- If the current KB is effectively empty, fall back to the default source bases in `source-priority.md`.

## Pre-Crawl Link Index CLI

Before accepting or downloading new material candidates, use the bundled CLI to build or update an internal link index when the task involves more than a handful of URLs, a default-source-base expansion, or an incremental collection update.

CLI asset:

```text
scripts/precrawl_link_index.py
```

Default database:

```text
source/.harvest/link-index.sqlite3
```

Purpose:

- Scan source-priority files, ingest/register notes, supplied URL lists, and optionally seed/index/feed pages for possible links.
- Canonicalize URLs, strip common tracking parameters, remove fragments, and deduplicate by canonical URL.
- Record internal operational state in SQLite: seen count, observations, collection hint, crawl/download/verification status, material ID, raw path, title/source/date hints, detailed classification metadata, errors, and other metadata that should not clutter user-facing notes.
- Sync existing `source/ingest.md` and `source/raw/*.md` metadata into the database so incremental runs avoid re-adding already downloaded, metadata-only, rejected, or verified materials.
- Export a small pending URL list for agent quality-gate review without exposing hidden operational metadata by default.

Typical commands:

```bash
python scripts/precrawl_link_index.py --workspace . init
python scripts/precrawl_link_index.py --workspace . scan --collection-id <collection-id>
python scripts/precrawl_link_index.py --workspace . scan --collection-id <collection-id> --fetch-seeds
python scripts/precrawl_link_index.py --workspace . pending --limit 100
python scripts/precrawl_link_index.py --workspace . sync --collection-id <collection-id>
python scripts/precrawl_link_index.py --workspace . stats
```

Important constraints:

- The pre-crawl CLI does not replace the existing download workflow. It indexes candidate links and state only; accepted pages are still captured through the current web fetch, scripted fetch, browser fallback, and verifier flow.
- `scan --fetch-seeds` may fetch seed/index/feed pages once to enumerate links, but it must not recursively follow discovered candidate pages, save raw article bodies, or treat seed-page extraction as verification.
- The database is authoritative only for deduplication and processing state. The human-readable `source/ingest.md` remains the minimal candidate/material status list, and `source/raw/` remains the source of raw page content.
- Do not surface `internal_metadata_json`, observation history, URL hashes, referrer lists, stripped query parameters, or other operational fields in downstream analysis unless the user asks for a diagnostics export. Raw front matter may surface only the approved high-level classification trio.
- After actual download or verification, run the CLI `sync` command or otherwise update the database so `material_id`, `raw_path`, `download_status`, `verification_status`, and detailed classification fields stay aligned with `source/ingest.md`, `source/raw/`, and `source/registers/`.

## Minimal Raw Front Matter

Use only these fields by default unless the user explicitly requests more:

```yaml
---
material_id:
collection_id:
title:
canonical_url:
source_name:
author_or_org:
publication_date:
retrieved_at:
language:
material_kind:
topic_domain:
credibility_tier:
ingest_status:
download_status:
verification_status:
raw_path:
reviewed_at:
---
```

Field intent:

- `material_id`, `collection_id`, `title`, `canonical_url`, `source_name`, `author_or_org`, `publication_date`, `retrieved_at`, and `language` identify the source.
- `material_kind`, `topic_domain`, and `credibility_tier` provide durable high-level classification for filtering raw files. Use controlled values from the classification schema; `topic_domain` may contain comma-separated controlled values when one material clearly spans multiple domains.
- `ingest_status`, `download_status`, `verification_status`, `raw_path`, and `reviewed_at` track pipeline state.

Do not put quality scores, detailed classification fields, bias notes, curation summaries, evidence pointers, or candidate insights in raw-file front matter. Store `evidence_type`, `ingestion_priority`, `lifecycle_status`, `insight_potential`, `source_bias`, and `compliance_status` in `source/.harvest/link-index.sqlite3` by default, with human-readable summaries in registers only when useful.

## Material Unit

A material unit is one canonical source page or document that can be evaluated independently:

- Article or practitioner essay page.
- Research paper page, PDF, technical report, system card, or model card.
- Benchmark page, leaderboard methodology page, dataset card, or evaluation harness README.
- Standard, protocol specification page, governance framework page, or regulatory guidance page.
- Security advisory, exploit write-up, audit report, or incident postmortem page.
- Vendor engineering post or product changelog page only when it contains reusable technical or governance substance.

For documentation sites, multi-page standards, GitHub repositories, or portals, choose the exact page that matters. Examples: a specific README, methodology page, protocol page, risk page, release note, or paper page. Do not summarize the entire site into one raw file.

## Quality Gate

Only keep items that satisfy most of these tests:

1. Provenance: canonical URL, accountable author or institution, and publication date or version are identifiable.
2. Originality: the item is primary material or adds substantial original analysis, not merely a summary of summaries.
3. Freshness: by default it was published within the last 6 months relative to `retrieved_at`; older sources require an explicit exception note.
4. Durability: it remains useful beyond a single release announcement.
5. Evidence: it provides systems, evals, incidents, code, benchmark data, standards language, or practitioner experience.
6. Viewpoint potential: it contains claims, trade-offs, mental models, failure modes, or design rules worth extracting later.
7. Bias transparency: vendor, consulting, analyst, security-research, or practitioner incentives can be stated plainly.
8. Access fit: the page is publicly reachable or can be tracked as metadata-only when authentication, paywalls, blocking, or technical capture failures prevent raw capture.

## Default Source Bases When URLs Are Absent

If the user provides a collection topic, scope, or research direction but no candidate URLs, do not stop and ask only for links. Use [source priority](./references/source-priority.md) as the default base list for candidate discovery.

- Treat the URLs and feeds in `source-priority.md` as discovery bases, not automatically as raw material units.
- Start with P1 sources that match the collection target, then use P2 or benchmark-derived sources when the topic calls for governance, security, adoption, architecture, case studies, or evaluation materials.
- For feeds, sites, repositories, documentation portals, or broad landing pages, enumerate relevant page-level entries first. Capture only the specific article, post, paper page, README, methodology page, spec page, dataset card, or report that passes the quality gate.
- Capture a base URL itself only when that base page is the actual source material, such as a static reference page, benchmark landing page with durable methodology, or canonical project README.
- Record selected bases, rejected bases, caveats, and missing-source gaps in `source/registers/<collection-id>.md` or `source/ingest.md` notes, not in raw-file front matter.

## Procedure

1. Define the collection target: topic, audience, scope, time window, source languages, and exclusion rules. Default the time window to the last 6 months unless the user asks for a historical or foundational set.
2. Initialize `source/`, `source/raw/`, `source/registers/`, `source/ingest.md`, `source/.harvest/link-index.sqlite3`, and `source/registers/classification-schema.md` at the project root as needed. Ensure the source-side classification schema contains the full current controlled vocabulary from the reference file.
3. Inspect the current KB as read-only context and promote new candidate topics from existing collections, gaps, and verified materials before widening discovery. If no candidate URLs are provided, combine those promoted topics with the default source bases in `source-priority.md`, then resolve selected items to page-level URLs before ingest. Prefer items published within the active time window.
4. Run the pre-crawl link index CLI for broad or incremental discovery. Sync existing ingest/raw state, scan default source bases and curator notes, optionally scan seed/index/feed pages with `--fetch-seeds`, and use the database to suppress duplicate URLs before spending agent attention on quality decisions.
5. Canonicalize each surviving candidate to a page-level URL. Avoid generic site roots unless the root page itself is the source material.
6. Apply the quality gate and record accept, reject, watch, revisit, or deep_read decisions in the ingest list or register. Assign `material_kind`, `topic_domain`, and `credibility_tier` when enough evidence is available, and put detailed classification fields into the SQLite link index. Write curator-facing notes in Chinese by default.
7. Download accepted pages through the embedded downloader role using the existing retrieval workflow. Save each page as `source/raw/<material-id>-<slug>.md` with minimal YAML front matter, the high-level classification trio, and raw page body Markdown.
8. For publicly reachable pages in this internal experimental workflow, attempt best-effort raw capture even when the reuse license is unspecified. Record license, copyright, and access caveats in `source/.harvest/link-index.sqlite3`, `source/ingest.md`, or `source/registers/`, not in raw front matter.
9. For authentication-gated, paywalled, blocked, CAPTCHA-protected, or technically inaccessible sources, create metadata-only status records and do not fabricate body content from summaries.
10. Verify newly downloaded or newly queued raw captures. Confirm that each new file is a one-page capture, update its raw front matter in place with corrected identity, high-level classification, verification status, and review date, and record concise verification notes in Chinese in `source/ingest.md` or `source/registers/`.
11. Sync the pre-crawl SQLite index after download and verification so incremental runs know which canonical URLs already map to a `material_id`, `raw_path`, terminal status, and detailed classification state.
12. Deduplicate and cluster related pages in registers, while preserving one raw file per canonical URL.
13. Extract final insights only if the user asks for that later, using verified raw captures plus ingest/register notes as input.

## Retrieval Tool Order

Use a best-effort retrieval chain for accepted public pages:

1. Web fetch first: use the available web fetch tool to retrieve the page's main readable content and source metadata.
2. Scripted fetch fallback: when web fetch is incomplete, blocked by rendering, or unsuitable for a source such as a GitHub README, use a scripted HTTP fetch or source-native raw endpoint to retrieve the same material unit. Keep `canonical_url` as the original page-level URL even if a raw endpoint is used as the retrieval mechanism.
3. Browser fallback: when the page requires normal browser rendering, use browser tools to load the canonical page, inspect the rendered DOM, and capture the readable page body.
4. Metadata-only fallback: use metadata-only only when the material cannot be captured from publicly reachable content after those attempts, or when access requires login, payment, CAPTCHA solving, credentialed sessions, or bypassing technical access controls.

When scripts or browser tools are used, keep the output shape unchanged: one raw Markdown file per canonical material, minimal raw front matter with the high-level classification trio, and caveats in the SQLite index plus ingest/register notes.

## Internal Experimental Capture Policy

This skill is for an internal experimental raw-material layer. For publicly reachable pages, an absent or unclear reuse license is not by itself a reason to skip raw capture. Prefer capturing the main page body and record caveats separately.

Do not use this policy to bypass authentication, paywalls, CAPTCHA gates, robots-style technical blocks, or other access controls. If only summaries, snippets, search results, or third-party reposts are available, keep the item metadata-only or add a follow-up task for manual review.

## Source Material Downloader Subagent

The downloader subagent is part of this skill. `agents/source-material-downloader.agent.md` is only an invocation wrapper and must follow this section when it is used for high-value candidate downloads.

Responsibilities:

- Fetch the assigned canonical page and save one standalone Markdown file under `source/raw/`.
- Before fetching, check existing `source/ingest.md`, `source/raw/`, and the pre-crawl link index when present so a canonical URL is not downloaded twice.
- Use web fetch first, scripted fetch second, and browser-assisted capture third when needed.
- Preserve the page's main readable content as Markdown, including headings, paragraphs, lists, links, tables, and code blocks where available.
- Add only the minimal YAML front matter described above, including `material_kind`, `topic_domain`, and `credibility_tier` when assigned by the parent workflow or obvious from the accepted candidate row.
- For publicly reachable pages, capture best-effort raw content even when the reuse license is unspecified; record caveats outside raw front matter.
- Use metadata-only for authentication-gated, paywalled, blocked, CAPTCHA-protected, or technically inaccessible sources.
- Skip sources older than 6 months by default unless the parent task explicitly allows a historical exception or no newer canonical source exists and the exception is recorded.
- Add or update the assigned new material row in `source/ingest.md` with pipeline state, paths, retrieval date, and any download caveat.
- After downloading or creating a metadata-only record, sync or update the pre-crawl link index with `material_id`, `raw_path`, `download_status`, `verification_status`, and any detailed classification fields when the database exists.

The downloader does not perform final verification, quality scoring, detailed classification, or insight writing. It may copy or lightly infer the high-level classification trio required by raw front matter.

## Source Material Verifier Subagent

The verifier subagent is part of this skill. `agents/source-material-verifier.agent.md` is only an invocation wrapper and must follow this section as the follow-up verification step.

Responsibilities:

- Confirm that each newly downloaded or explicitly assigned file in `source/raw/` is a raw page capture for one canonical URL.
- Re-check the canonical URL when needed to confirm provenance, date, authorship, access caveats, and body match.
- Enforce the default 6-month freshness window unless the parent task explicitly allows an older-source exception and the reason is recorded.
- Confirm that public-page captures were not downgraded to metadata-only solely because a reuse license was absent or unclear.
- Update the raw file's front matter in place with corrected identity fields, `verification_status`, and `reviewed_at`.
- Keep verification notes outside raw content, using `source/ingest.md` or `source/registers/`.
- Update the corresponding new material row in `source/ingest.md` with `verification_status`, `reviewed_at`, and next action.
- After verification, sync or update the pre-crawl link index so incremental runs see the final status.
- Mark weak items as `rejected`, `watch`, `revisit`, or `needs_followup` with reasons.

The verifier does not write final insight notes unless the user explicitly asks for insight extraction after verification.

## Classification And Scoring

Classification is split by storage boundary:

- Raw front matter carries only `material_kind`, `topic_domain`, and `credibility_tier`.
- The internal SQLite link index carries detailed classification fields: `evidence_type`, `ingestion_priority`, `lifecycle_status`, `insight_potential`, `source_bias`, and `compliance_status`.
- `source/registers/classification-schema.md` carries the controlled vocabulary and may include Chinese curator-facing summaries, but the SQLite index is the default machine-readable store for detailed classification state.

When classification is useful, use [classification schema](./references/classification-schema.md) and ensure the full schema is copied into `source/registers/classification-schema.md` inside the project root. Keep only the high-level classification trio in `source/raw/`; keep detailed classifications in the SQLite index and optional human-readable register notes.

When adding classification to a collection:

- Do not add only a partial subset when the collection needs the schema. Copy the full schema headings and controlled values into the source-side schema file first, then use the relevant subset in collection notes.
- If the source-side classification schema already exists, merge in any missing sections or controlled values rather than overwriting local additions blindly.
- Keep the controlled values in English and explain them in Chinese in the source-side copy when producing Chinese KB outputs.
- Run `python scripts/precrawl_link_index.py --workspace . sync --collection-id <collection-id>` after classification edits so register/raw classification state is reflected in `source/.harvest/link-index.sqlite3`.

When scoring is useful, score each dimension from 0 to 5 in the register or ingest notes:

| Dimension | What to check |
|---|---|
| provenance | Author, institution, canonical URL, date, version. |
| evidence | Data, code, benchmark, incident, standard text, or implementation detail. |
| durability | Expected shelf life beyond short-term news. |
| relevance | Fit to the collection target and enterprise AI-agent KB. |
| viewpoint_potential | Clear claims, trade-offs, mental models, or design implications. |
| bias_transparency | Incentives and limitations can be described. |
| compliance_fit | Access, paywall, excerpting, and storage constraints are manageable; unspecified license on public pages is a caveat, not an automatic blocker for this internal experimental workflow. |

Default decision rules:

- 28-35: accept and deep_read.
- 22-27: accept.
- 16-21: watch or revisit.
- Below 16: reject unless explicitly requested.

## Default Deliverables

- `source/ingest.md` with one row per canonical candidate page and minimal status fields.
- Internal `source/.harvest/link-index.sqlite3` when pre-crawl scanning is used, containing deduplication, processing-state, and detailed classification metadata that is not meant for downstream reading by default.
- `source/registers/classification-schema.md` containing the full current classification schema used by the collection.
- `source/registers/<collection-id>.md` with candidate source list and accept, reject, watch, revisit, or deep_read decisions.
- `source/raw/<material-id>-<slug>.md` raw Markdown page captures, one canonical URL per file, with minimal YAML front matter and the high-level classification trio updated in place after verification.
- Rejection log with short reasons.
- Gap list for missing counterpoints, weak evidence, absent methodology, or unvalidated claims.
- Optional deep-read queue for later viewpoint extraction.

## References

- [Source priority](./references/source-priority.md)
- [Classification schema](./references/classification-schema.md)
- [Source material template](./assets/source-material-template.md)
- [Ingest list template](./assets/ingest-list-template.md)
