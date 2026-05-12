#!/usr/bin/env python3
"""Pre-crawl link index for insight-knowledge-harvest.

The tool records candidate URLs and existing harvest state in SQLite without
downloading raw material bodies. It may fetch seed/index/feed pages when asked,
but it never follows discovered candidate links recursively.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html.parser
import json
import re
import sqlite3
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DB = "source/.harvest/link-index.sqlite3"
DEFAULT_SOURCE_PRIORITY = ".github/skills/insight-knowledge-harvest/references/source-priority.md"
TEXT_SUFFIXES = {".md", ".txt", ".html", ".htm", ".xml", ".atom", ".rss", ".json", ".csv", ".tsv", ".opml"}
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
    "msclkid",
    "ref",
    "spm",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
USER_AGENT = "insight-knowledge-harvest-precrawl/1.0"
RAW_CLASSIFICATION_COLUMNS = ("material_kind", "topic_domain", "credibility_tier")
DETAILED_CLASSIFICATION_COLUMNS = (
    "evidence_type",
    "ingestion_priority",
    "lifecycle_status",
    "insight_potential",
    "source_bias",
    "compliance_status",
)
CLASSIFICATION_COLUMNS = RAW_CLASSIFICATION_COLUMNS + DETAILED_CLASSIFICATION_COLUMNS
LINK_COLUMN_DEFINITIONS = {
    **{column: f"{column} TEXT" for column in CLASSIFICATION_COLUMNS},
    "classification_source": "classification_source TEXT",
    "classification_updated_at": "classification_updated_at TEXT",
}


@dataclass(frozen=True)
class LinkObservation:
    canonical_url: str
    observed_url: str
    observed_from: str
    source_kind: str
    anchor_text: str = ""
    metadata: dict[str, str] | None = None


class LinkHTMLParser(html.parser.HTMLParser):
    def __init__(self, base_url: str | None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        href = attrs_dict.get("href")
        if tag.lower() not in {"a", "area", "link"} or not href:
            return
        title = attrs_dict.get("title", "") or attrs_dict.get("aria-label", "")
        self.links.append((resolve_url(href, self.base_url), clean_cell(title)))


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def clean_cell(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def resolve_url(url: str, base_url: str | None) -> str:
    url = (url or "").strip()
    if base_url:
        return urllib.parse.urljoin(base_url, url)
    return url


def normalize_url(url: str, base_url: str | None = None) -> str | None:
    url = resolve_url(url, base_url).strip().strip("<>\"'`")
    url = url.rstrip(".,;:!?)\\]")
    if not url:
        return None
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        return None
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    port = parsed.port
    netloc = hostname
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    path = urllib.parse.quote(urllib.parse.unquote(parsed.path or "/"), safe="/%:@")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_pairs = [(key, value) for key, value in query_pairs if key.lower() not in TRACKING_PARAMS and not key.lower().startswith("utm_")]
    query = urllib.parse.urlencode(sorted(filtered_pairs), doseq=True)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def domain_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def domain_allowed(url: str, include_domains: set[str], exclude_domains: set[str]) -> bool:
    domain = domain_of(url)
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in exclude_domains):
        return False
    if include_domains:
        return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in include_domains)
    return True


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    create_schema(conn)
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            workspace_root TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            stats_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS links (
            canonical_url TEXT PRIMARY KEY,
            url_hash TEXT NOT NULL UNIQUE,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            seen_count INTEGER NOT NULL DEFAULT 1,
            collection_id TEXT,
            status TEXT NOT NULL DEFAULT 'candidate_found',
            crawl_status TEXT NOT NULL DEFAULT 'not_started',
            download_status TEXT NOT NULL DEFAULT 'not_started',
            verification_status TEXT NOT NULL DEFAULT 'not_started',
            material_id TEXT,
            raw_path TEXT,
            source_name_hint TEXT,
            title_hint TEXT,
            publication_date_hint TEXT,
            language_hint TEXT,
            material_kind TEXT,
            topic_domain TEXT,
            credibility_tier TEXT,
            evidence_type TEXT,
            ingestion_priority TEXT,
            lifecycle_status TEXT,
            insight_potential TEXT,
            source_bias TEXT,
            compliance_status TEXT,
            classification_source TEXT,
            classification_updated_at TEXT,
            source_kind TEXT,
            last_observed_from TEXT,
            last_error TEXT,
            internal_metadata_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_url TEXT NOT NULL REFERENCES links(canonical_url) ON DELETE CASCADE,
            observed_url TEXT NOT NULL,
            observed_from TEXT,
            anchor_text TEXT,
            source_kind TEXT,
            run_id TEXT,
            observed_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_links_status ON links(status, crawl_status, download_status, verification_status);
        CREATE INDEX IF NOT EXISTS idx_links_collection ON links(collection_id);
        CREATE INDEX IF NOT EXISTS idx_observations_url ON observations(canonical_url);
        """
    )
    ensure_link_columns(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_links_classification ON links(material_kind, credibility_tier)")


def ensure_link_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(links)").fetchall()}
    for column, definition in LINK_COLUMN_DEFINITIONS.items():
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE links ADD COLUMN {definition}")


def merge_metadata(existing_json: str, new_metadata: dict[str, str] | None) -> str:
    try:
        metadata = json.loads(existing_json or "{}")
        if not isinstance(metadata, dict):
            metadata = {}
    except json.JSONDecodeError:
        metadata = {}
    for key, value in (new_metadata or {}).items():
        if value not in (None, ""):
            metadata[key] = value
    return json.dumps(metadata, ensure_ascii=False, sort_keys=True)


def upsert_observation(conn: sqlite3.Connection, observation: LinkObservation, collection_id: str | None, run_id: str) -> bool:
    now = utc_now()
    existing = conn.execute(
        "SELECT internal_metadata_json, seen_count, collection_id FROM links WHERE canonical_url = ?",
        (observation.canonical_url,),
    ).fetchone()
    metadata_json = merge_metadata(existing[0] if existing else "{}", observation.metadata)
    is_new = existing is None
    if is_new:
        conn.execute(
            """
            INSERT INTO links (
                canonical_url, url_hash, first_seen_at, last_seen_at, seen_count, collection_id,
                source_kind, last_observed_from, internal_metadata_json, updated_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
            """,
            (
                observation.canonical_url,
                url_hash(observation.canonical_url),
                now,
                now,
                collection_id,
                observation.source_kind,
                observation.observed_from,
                metadata_json,
                now,
            ),
        )
    else:
        next_collection_id = existing[2] or collection_id
        conn.execute(
            """
            UPDATE links
            SET last_seen_at = ?,
                seen_count = seen_count + 1,
                collection_id = ?,
                source_kind = COALESCE(?, source_kind),
                last_observed_from = ?,
                internal_metadata_json = ?,
                updated_at = ?
            WHERE canonical_url = ?
            """,
            (
                now,
                next_collection_id,
                observation.source_kind,
                observation.observed_from,
                metadata_json,
                now,
                observation.canonical_url,
            ),
        )
    conn.execute(
        """
        INSERT INTO observations (canonical_url, observed_url, observed_from, anchor_text, source_kind, run_id, observed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            observation.canonical_url,
            observation.observed_url,
            observation.observed_from,
            observation.anchor_text,
            observation.source_kind,
            run_id,
            now,
        ),
    )
    return is_new


def read_text_file(path: Path, max_bytes: int) -> str:
    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)
    return data[:max_bytes].decode("utf-8", errors="replace")


def iter_input_files(paths: Iterable[Path], max_bytes: int) -> Iterable[tuple[str, str]]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                    yield str(child), read_text_file(child, max_bytes)
        elif path.is_file():
            yield str(path), read_text_file(path, max_bytes)


def default_input_paths(workspace: Path) -> list[Path]:
    paths: list[Path] = []
    source_priority = workspace / DEFAULT_SOURCE_PRIORITY
    if source_priority.exists():
        paths.append(source_priority)
    ingest = workspace / "source" / "ingest.md"
    if ingest.exists():
        paths.append(ingest)
    registers = workspace / "source" / "registers"
    if registers.exists():
        paths.extend(sorted(registers.glob("*.md")))
    return paths


def extract_plain_urls(text: str, source_name: str) -> list[LinkObservation]:
    observations: list[LinkObservation] = []
    markdown_links = list(re.finditer(r"\[([^\]]{0,200})\]\((https?://[^\s)]+)\)", text, flags=re.IGNORECASE))
    seen_spans = {match.span(2) for match in markdown_links}
    for match in markdown_links:
        observed = match.group(2)
        canonical = normalize_url(observed)
        if canonical:
            observations.append(
                LinkObservation(
                    canonical_url=canonical,
                    observed_url=observed,
                    observed_from=source_name,
                    source_kind="text",
                    anchor_text=clean_cell(match.group(1)),
                    metadata={"extractor": "markdown"},
                )
            )
    for match in re.finditer(r"https?://[^\s<>'\"\])]+", text, flags=re.IGNORECASE):
        if match.span() in seen_spans:
            continue
        observed = match.group(0)
        canonical = normalize_url(observed)
        if canonical:
            observations.append(
                LinkObservation(
                    canonical_url=canonical,
                    observed_url=observed,
                    observed_from=source_name,
                    source_kind="text",
                    metadata={"extractor": "url_regex"},
                )
            )
    return observations


def extract_html_links(text: str, base_url: str, source_name: str) -> list[LinkObservation]:
    parser = LinkHTMLParser(base_url)
    try:
        parser.feed(text)
    except html.parser.HTMLParseError:
        return []
    observations: list[LinkObservation] = []
    for observed, anchor in parser.links:
        canonical = normalize_url(observed)
        if canonical:
            observations.append(
                LinkObservation(
                    canonical_url=canonical,
                    observed_url=observed,
                    observed_from=source_name,
                    source_kind="seed_page",
                    anchor_text=anchor,
                    metadata={"extractor": "html_href", "seed_url": base_url},
                )
            )
    return observations


def extract_feed_links(text: str, base_url: str, source_name: str) -> list[LinkObservation]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    observations: list[LinkObservation] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        href = element.attrib.get("href") if tag == "link" else None
        text_url = clean_cell(element.text) if tag in {"link", "guid", "id"} else ""
        observed = href or text_url
        canonical = normalize_url(observed, base_url) if observed else None
        if canonical:
            observations.append(
                LinkObservation(
                    canonical_url=canonical,
                    observed_url=observed,
                    observed_from=source_name,
                    source_kind="seed_feed",
                    metadata={"extractor": "xml_feed", "seed_url": base_url},
                )
            )
    return observations


def fetch_seed(seed_url: str, timeout: int, max_bytes: int) -> tuple[str, str]:
    request = urllib.request.Request(seed_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.IGNORECASE)
        charset = charset_match.group(1) if charset_match else "utf-8"
        data = response.read(max_bytes + 1)
    return data[:max_bytes].decode(charset, errors="replace"), content_type


def parse_front_matter(path: Path) -> dict[str, str]:
    text = read_text_file(path, 128 * 1024)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"\'')
    return metadata


def parse_markdown_tables(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in read_text_file(path, 512 * 1024).splitlines():
        if not line.startswith("|"):
            headers = []
            continue
        cells = [clean_cell(cell) for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if not headers:
            headers = cells
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        rows.append(dict(zip(headers, cells)))
    return rows


def parse_ingest_table(path: Path) -> list[dict[str, str]]:
    return [row for row in parse_markdown_tables(path) if "material_id" in row and "canonical_url" in row]


def extract_classification_fields(row: dict[str, str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for column in CLASSIFICATION_COLUMNS:
        value = clean_cell(row.get(column, ""))
        if value:
            fields[column] = value
    return fields


def update_classification_state(
    conn: sqlite3.Connection,
    *,
    classification_fields: dict[str, str],
    classification_source: str,
    canonical_url: str = "",
    material_id: str = "",
) -> int:
    if not classification_fields:
        return 0
    assignments = [f"{column} = COALESCE(NULLIF(?, ''), {column})" for column in classification_fields]
    assignments.extend(["classification_source = ?", "classification_updated_at = ?"])
    params = [classification_fields[column] for column in classification_fields]
    params.extend([classification_source, utc_now()])
    if canonical_url:
        where_clause = "canonical_url = ?"
        params.append(canonical_url)
    elif material_id:
        where_clause = "material_id = ?"
        params.append(material_id)
    else:
        return 0
    cursor = conn.execute(
        f"""
        UPDATE links
        SET {', '.join(assignments)}
        WHERE {where_clause}
        """,
        params,
    )
    return cursor.rowcount


def sync_existing_state(conn: sqlite3.Connection, workspace: Path, collection_id: str | None, run_id: str) -> dict[str, int]:
    stats = {"ingest_rows": 0, "raw_files": 0, "classification_rows": 0}
    ingest_path = workspace / "source" / "ingest.md"
    for row in parse_ingest_table(ingest_path):
        canonical = normalize_url(row.get("canonical_url", "")) or normalize_url(row.get("source_name", ""))
        if not canonical:
            continue
        metadata = {
            "ingest_path": str(ingest_path),
            "source_name_hint": row.get("source_name", ""),
            "title_hint": row.get("title", ""),
            "publication_date_hint": row.get("publication_date", ""),
        }
        observation = LinkObservation(
            canonical_url=canonical,
            observed_url=row.get("canonical_url", canonical),
            observed_from=str(ingest_path),
            source_kind="existing_ingest",
            metadata=metadata,
        )
        upsert_observation(conn, observation, collection_id, run_id)
        update_processing_state(
            conn,
            canonical,
            material_id=row.get("material_id", ""),
            raw_path=row.get("raw_path", ""),
            status=row.get("ingest_status", "") or None,
            download_status=row.get("download_status", "") or None,
            verification_status=row.get("verification_status", "") or None,
            title_hint=row.get("title", ""),
            source_name_hint=row.get("source_name", ""),
            publication_date_hint=row.get("publication_date", ""),
            classification_fields=extract_classification_fields(row),
            classification_source=str(ingest_path),
        )
        stats["ingest_rows"] += 1
    raw_dir = workspace / "source" / "raw"
    if raw_dir.exists():
        for raw_path in sorted(raw_dir.glob("*.md")):
            metadata = parse_front_matter(raw_path)
            canonical = normalize_url(metadata.get("canonical_url", ""))
            if not canonical:
                continue
            observation = LinkObservation(
                canonical_url=canonical,
                observed_url=metadata.get("canonical_url", canonical),
                observed_from=str(raw_path),
                source_kind="existing_raw",
                metadata={"raw_front_matter_path": str(raw_path)},
            )
            upsert_observation(conn, observation, metadata.get("collection_id") or collection_id, run_id)
            update_processing_state(
                conn,
                canonical,
                material_id=metadata.get("material_id", ""),
                raw_path=str(raw_path.relative_to(workspace)).replace("\\", "/"),
                status=metadata.get("ingest_status") or None,
                download_status=metadata.get("download_status") or None,
                verification_status=metadata.get("verification_status") or None,
                title_hint=metadata.get("title", ""),
                source_name_hint=metadata.get("source_name", ""),
                publication_date_hint=metadata.get("publication_date", ""),
                language_hint=metadata.get("language", ""),
                classification_fields=extract_classification_fields(metadata),
                classification_source=str(raw_path),
            )
            stats["raw_files"] += 1
    stats["classification_rows"] += sync_register_classifications(conn, workspace)
    return stats


def sync_register_classifications(conn: sqlite3.Connection, workspace: Path) -> int:
    registers_dir = workspace / "source" / "registers"
    if not registers_dir.exists():
        return 0
    updated_rows = 0
    for register_path in sorted(registers_dir.glob("*.md")):
        if register_path.name == "classification-schema.md":
            continue
        for row in parse_markdown_tables(register_path):
            classification_fields = extract_classification_fields(row)
            if not classification_fields:
                continue
            canonical = normalize_url(row.get("canonical_url", "")) or ""
            material_id = clean_cell(row.get("material_id", ""))
            if not canonical and not material_id:
                continue
            updated_rows += update_classification_state(
                conn,
                canonical_url=canonical,
                material_id=material_id,
                classification_fields=classification_fields,
                classification_source=str(register_path),
            )
    return updated_rows


def update_processing_state(
    conn: sqlite3.Connection,
    canonical_url: str,
    *,
    material_id: str = "",
    raw_path: str = "",
    status: str | None = None,
    download_status: str | None = None,
    verification_status: str | None = None,
    title_hint: str = "",
    source_name_hint: str = "",
    publication_date_hint: str = "",
    language_hint: str = "",
    classification_fields: dict[str, str] | None = None,
    classification_source: str = "",
) -> None:
    crawl_status = "not_started"
    if download_status in {"downloaded", "metadata_only", "blocked", "failed", "manual_required"}:
        crawl_status = download_status
    if verification_status in {"verified", "rejected", "needs_followup", "failed"}:
        crawl_status = verification_status
    conn.execute(
        """
        UPDATE links
        SET material_id = COALESCE(NULLIF(?, ''), material_id),
            raw_path = COALESCE(NULLIF(?, ''), raw_path),
            status = COALESCE(?, status),
            crawl_status = COALESCE(NULLIF(?, ''), crawl_status),
            download_status = COALESCE(?, download_status),
            verification_status = COALESCE(?, verification_status),
            title_hint = COALESCE(NULLIF(?, ''), title_hint),
            source_name_hint = COALESCE(NULLIF(?, ''), source_name_hint),
            publication_date_hint = COALESCE(NULLIF(?, ''), publication_date_hint),
            language_hint = COALESCE(NULLIF(?, ''), language_hint),
            updated_at = ?
        WHERE canonical_url = ?
        """,
        (
            material_id,
            raw_path,
            status,
            crawl_status,
            download_status,
            verification_status,
            title_hint,
            source_name_hint,
            publication_date_hint,
            language_hint,
            utc_now(),
            canonical_url,
        ),
    )
    if classification_fields:
        update_classification_state(
            conn,
            canonical_url=canonical_url,
            material_id=material_id,
            classification_fields=classification_fields,
            classification_source=classification_source,
        )


def begin_run(conn: sqlite3.Connection, command: str, workspace: Path) -> str:
    run_id = hashlib.sha256(f"{command}:{utc_now()}".encode("utf-8")).hexdigest()[:16]
    conn.execute(
        "INSERT INTO runs (run_id, command, workspace_root, started_at) VALUES (?, ?, ?, ?)",
        (run_id, command, str(workspace), utc_now()),
    )
    return run_id


def finish_run(conn: sqlite3.Connection, run_id: str, stats: dict[str, int]) -> None:
    conn.execute(
        "UPDATE runs SET finished_at = ?, stats_json = ? WHERE run_id = ?",
        (utc_now(), json.dumps(stats, sort_keys=True), run_id),
    )


def cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = resolve_db_path(workspace, args.db)
    with connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    print(f"initialized {db_path} ({count} links)")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = resolve_db_path(workspace, args.db)
    with connect(db_path) as conn:
        run_id = begin_run(conn, "sync", workspace)
        stats = sync_existing_state(conn, workspace, args.collection_id, run_id)
        finish_run(conn, run_id, stats)
        conn.commit()
    print(f"synced {stats['ingest_rows']} ingest rows, {stats['raw_files']} raw files, and {stats.get('classification_rows', 0)} classification rows into {db_path}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = resolve_db_path(workspace, args.db)
    include_domains = {domain.lower().lstrip(".") for domain in args.include_domain or []}
    exclude_domains = {domain.lower().lstrip(".") for domain in args.exclude_domain or []}
    paths: list[Path] = []
    if not args.no_default_inputs:
        paths.extend(default_input_paths(workspace))
    paths.extend(Path(path) if Path(path).is_absolute() else workspace / path for path in args.input or [])
    paths.extend(Path(path) if Path(path).is_absolute() else workspace / path for path in args.input_dir or [])
    if args.source_priority:
        source_priority = Path(args.source_priority)
        paths.append(source_priority if source_priority.is_absolute() else workspace / source_priority)
    stats = {"input_files": 0, "seed_fetches": 0, "seen": 0, "new": 0, "filtered": 0, "errors": 0, "ingest_rows": 0, "raw_files": 0, "classification_rows": 0}
    with connect(db_path) as conn:
        run_id = begin_run(conn, "scan", workspace)
        if not args.no_sync_existing:
            stats.update(sync_existing_state(conn, workspace, args.collection_id, run_id))
        collected_seed_urls: list[str] = []
        for source_name, text in iter_input_files(paths, args.max_file_bytes):
            stats["input_files"] += 1
            observations = extract_plain_urls(text, source_name)
            for observation in observations:
                if not domain_allowed(observation.canonical_url, include_domains, exclude_domains):
                    stats["filtered"] += 1
                    continue
                if upsert_observation(conn, observation, args.collection_id, run_id):
                    stats["new"] += 1
                stats["seen"] += 1
                collected_seed_urls.append(observation.canonical_url)
        for seed_url in args.seed_url or []:
            canonical = normalize_url(seed_url)
            if canonical:
                observation = LinkObservation(canonical, seed_url, "--seed-url", "seed_url", metadata={"extractor": "seed_arg"})
                if domain_allowed(observation.canonical_url, include_domains, exclude_domains):
                    if upsert_observation(conn, observation, args.collection_id, run_id):
                        stats["new"] += 1
                    stats["seen"] += 1
                    collected_seed_urls.append(observation.canonical_url)
        if args.fetch_seeds:
            for seed_url in sorted(set(collected_seed_urls)):
                try:
                    seed_text, content_type = fetch_seed(seed_url, args.timeout, args.max_seed_bytes)
                    stats["seed_fetches"] += 1
                    if "xml" in content_type or seed_text.lstrip().startswith("<"):
                        seed_observations = extract_feed_links(seed_text, seed_url, seed_url)
                    else:
                        seed_observations = []
                    seed_observations.extend(extract_html_links(seed_text, seed_url, seed_url))
                    seed_observations.extend(extract_plain_urls(seed_text, seed_url))
                    for observation in seed_observations:
                        if not domain_allowed(observation.canonical_url, include_domains, exclude_domains):
                            stats["filtered"] += 1
                            continue
                        if upsert_observation(conn, observation, args.collection_id, run_id):
                            stats["new"] += 1
                        stats["seen"] += 1
                except Exception as exc:  # noqa: BLE001 - CLI should keep scanning remaining seeds.
                    stats["errors"] += 1
                    print(f"warning: failed to scan seed {seed_url}: {exc}", file=sys.stderr)
        finish_run(conn, run_id, stats)
        conn.commit()
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    print(f"database: {db_path}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = resolve_db_path(workspace, args.db)
    with connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        print(f"total_links\t{total}")
        for label, column in [("status", "status"), ("crawl_status", "crawl_status"), ("download_status", "download_status"), ("verification_status", "verification_status")]:
            rows = conn.execute(f"SELECT {column}, COUNT(*) FROM links GROUP BY {column} ORDER BY COUNT(*) DESC, {column}").fetchall()
            for value, count in rows:
                print(f"{label}\t{value}\t{count}")
    return 0


def cmd_pending(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = resolve_db_path(workspace, args.db)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT canonical_url, seen_count, status, crawl_status, raw_path, title_hint, source_name_hint
            FROM links
            WHERE COALESCE(raw_path, '') = ''
              AND crawl_status IN ('not_started', 'candidate_found', 'queued_download')
            ORDER BY seen_count DESC, last_seen_at DESC
            LIMIT ?
            """,
            (args.limit,),
        ).fetchall()
    print("canonical_url\tseen_count\tstatus\tcrawl_status\traw_path\ttitle_hint\tsource_name_hint")
    for row in rows:
        print("\t".join(clean_cell(str(value or "")) for value in row))
    return 0


def resolve_db_path(workspace: Path, db_arg: str | None) -> Path:
    raw = Path(db_arg or DEFAULT_DB)
    if raw.is_absolute():
        return raw
    return workspace / raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index candidate source links before raw capture.")
    parser.add_argument("--workspace", default=".", help="Project workspace root. Default: current directory.")
    parser.add_argument("--db", default=None, help=f"SQLite database path. Default: {DEFAULT_DB}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create or migrate the link index database.")
    init_parser.set_defaults(func=cmd_init)

    sync_parser = subparsers.add_parser("sync", help="Sync existing source/ingest.md and source/raw metadata into the index.")
    sync_parser.add_argument("--collection-id", default=None)
    sync_parser.set_defaults(func=cmd_sync)

    scan_parser = subparsers.add_parser("scan", help="Scan text inputs and optional seed pages for candidate links.")
    scan_parser.add_argument("--collection-id", default=None)
    scan_parser.add_argument("--input", action="append", help="Text/Markdown/HTML/XML file to scan. May be repeated.")
    scan_parser.add_argument("--input-dir", action="append", help="Directory of text-like files to scan. May be repeated.")
    scan_parser.add_argument("--source-priority", default=None, help="Additional source-priority Markdown file to scan.")
    scan_parser.add_argument("--seed-url", action="append", help="Seed/index/feed URL to record and optionally scan. May be repeated.")
    scan_parser.add_argument("--fetch-seeds", action="store_true", help="Fetch seed/index/feed URLs once to extract links. Does not follow discovered links.")
    scan_parser.add_argument("--include-domain", action="append", help="Keep only this domain or subdomain. May be repeated.")
    scan_parser.add_argument("--exclude-domain", action="append", help="Drop this domain or subdomain. May be repeated.")
    scan_parser.add_argument("--no-default-inputs", action="store_true", help="Do not scan source-priority, ingest, and registers by default.")
    scan_parser.add_argument("--no-sync-existing", action="store_true", help="Do not sync existing ingest/raw state before scanning.")
    scan_parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    scan_parser.add_argument("--max-seed-bytes", type=int, default=1_000_000)
    scan_parser.add_argument("--timeout", type=int, default=20)
    scan_parser.set_defaults(func=cmd_scan)

    stats_parser = subparsers.add_parser("stats", help="Print aggregate link index counts.")
    stats_parser.set_defaults(func=cmd_stats)

    pending_parser = subparsers.add_parser("pending", help="Print candidate URLs without raw_path for quality-gate review.")
    pending_parser.add_argument("--limit", type=int, default=100)
    pending_parser.set_defaults(func=cmd_pending)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())