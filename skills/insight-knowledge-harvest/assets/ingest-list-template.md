# Source Ingest List Template

Use this template for project-root `source/ingest.md`. Keep one row per canonical source page or document. Update the row whenever download, verification, lifecycle, or local path status changes.

```markdown
# Source Ingest List

- collection_id:
- collection_target:
- owner:
- created_at:
- last_updated:
- notes:

| material_id | title | canonical_url | source_name | publication_date | retrieved_at | ingest_status | download_status | verification_status | raw_path | reviewed_at | next_action | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  | candidate_found | not_started | not_started |  |  |  |  |
```

## Status Rules

- Add candidates as soon as page-level canonical metadata is known.
- For broad or incremental discovery, check the internal pre-crawl link index first and avoid adding duplicate canonical URLs that already have a terminal download or verification state.
- By default, only promote candidates published within the last 6 months unless a historical exception is explicitly noted in `notes`.
- Set `ingest_status` to `queued_download` for candidates selected for raw capture.
- Set `download_status` to `downloaded`, `metadata_only`, `failed`, `blocked`, or `manual_required` after the downloader pass.
- Set `ingest_status` to `queued_verification` when a raw Markdown file exists and needs verifier review.
- Set `verification_status` to `queued`, `verified`, `rejected`, `needs_followup`, or `failed` after the verifier pass.
- Set `raw_path` as a project-root relative path, for example `source/raw/EAIH-2026-05-08-001-example.md`.
- Set `reviewed_at` when verification is completed or explicitly reviewed.
- Keep rejected and failed rows with concise reasons so the same source is not reprocessed accidentally.

## Column Scope

Do not add classification, quality-score, bias, or hidden pre-crawl operational columns by default. Put the high-level classification trio (`material_kind`, `topic_domain`, `credibility_tier`) in raw front matter, put detailed classification fields in `source/.harvest/link-index.sqlite3`, and use `source/registers/` or `notes` only for curator-facing summaries when they are useful.
