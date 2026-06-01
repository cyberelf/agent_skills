# Wiki Page Schema

Use this schema for every generated page under `wiki/`. It is richer than the CLI's fallback template and is intended for Agent-written `wiki.content` in patch JSON.

## Frontmatter

Required fields:

```yaml
---
entity_id: concept:stable-slug
entity_type: concept
status: active
label: Human Readable Label
aliases: []
source_refs:
  - source/path.md#L10-L14
updated_at: 2026-05-29
---
```

Optional fields:

- `summary`: one-sentence abstract for indexes and reports.
- `confidence`: number from `0` to `1` for the page-level synthesis confidence.
- `review_status`: `draft`, `reviewed`, `needs_source_check`, or `conflicted`.
- `owner_agent`: agent or run id that last performed semantic work.
- `related_entities`: list of entity ids mentioned by the page.
- `query_modes`: list of query modes that commonly surface this page.

## Required Sections

Use these sections in this order unless a project-local schema says otherwise:

```markdown
# Human Readable Label

## 摘要

## 定义

## 范围与边界

## 关键事实

## 关系

## 冲突与不确定性

## 证据引用

## 待更新事项

## 变更记录
```

Section rules:

- `摘要`: 2-5 sentences for quick query use.
- `定义`: stable definition, not a source-by-source summary.
- `范围与边界`: inclusion/exclusion notes, near-duplicates, and alias boundaries.
- `关键事实`: source-backed bullets. Prefer facts that will remain useful across queries.
- `关系`: entity ids plus relation names, matching graph edges where possible.
- `冲突与不确定性`: contradictions, weak evidence, or open interpretation.
- `证据引用`: source paths and line ranges. The structured patch evidence remains the canonical machine-readable reference.
- `待更新事项`: stale evidence, missing source checks, follow-up extraction work.
- `变更记录`: append-only brief entries for meaningful semantic changes.

## Page Rules

- `wiki/` pages are compiled knowledge, not source evidence. Never cite another wiki page as the source of truth for a new entity.
- Before updating an existing page, read it and preserve useful content. `apply` rewrites any page included in the patch.
- Keep relation prose consistent with patch edges. Do not write a relationship in `## 关系` if it cannot be represented as an evidence-backed edge.
- Prefer explicit uncertainty over smoothing over conflicting sources.