# Source Raw Page Template

Use this template for files under project-root `source/raw/`.

Each raw file must represent exactly one canonical webpage, post, paper page, README, spec page, or document. The body should be the fetched main source content converted to Markdown, not a summary, curator note, quality score, classification record, or site overview.

```markdown
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
ingest_status: queued_verification
download_status: downloaded
verification_status: queued
raw_path:
reviewed_at:
---

# Page Title

Raw page content converted to Markdown goes here. Preserve the page's headings, paragraphs, lists, links, tables, code blocks, and other meaningful main-body structure where available.
```

## Field Rules

- Use standard YAML front matter delimited by `---`.
- Keep front matter minimal. By default, include only source identity fields and processing-state fields.
- Do not add quality scores, classification labels, bias notes, curation summaries, section pointers, evidence pointers, or candidate insights to raw front matter.
- Use ISO dates when known: `YYYY-MM-DD`.
- Keep `raw_path` project-root relative, for example `source/raw/EAIH-2026-05-08-001-example.md`.
- Leave `reviewed_at` blank until a verification pass updates the file in place.
- Leave unknown source identity fields blank rather than inventing them.

## Raw Body Rules

- Store one canonical URL per file.
- Store the fetched source body, not a summary of a site or source family.
- Prefer the page's main readable article/document content over navigation, cookie banners, sidebars, and unrelated footer links.
- Preserve links as Markdown links where possible.
- Preserve code blocks and tables when they are part of the source content.
- In this internal experimental workflow, unclear or absent reuse-license text on a publicly reachable page is not by itself a metadata-only trigger; capture the public page body and record caveats in `source/ingest.md` or `source/registers/`.
- By default, use this template only for sources published within the last 6 months unless the collection explicitly allows older exceptions.
- If a source is authentication-gated, paywalled, blocked, CAPTCHA-protected, or technically inaccessible after web fetch, scripted fetch, and browser fallback attempts, create a metadata-only record with `download_status: metadata_only`, `blocked`, or `manual_required`, and do not fabricate body content from summaries.

## Metadata-Only Fallback

Use this fallback only when raw content cannot be captured from publicly reachable content after the retrieval fallback chain.

```markdown
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
ingest_status: metadata_only
download_status: metadata_only
verification_status: needs_followup
raw_path:
reviewed_at:
---

# Download unavailable

Raw content was not stored. Reason:
```
