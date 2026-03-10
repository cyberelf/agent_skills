#!/usr/bin/env python3
"""
Fetch raw news headlines about China markets from Chinese and global sources.
Outputs headlines only — no scoring, no sentiment judgment.

Sources covered:
  Chinese domestic : 财新(Caixin), 新浪财经, 第一财经(Yicai), 东方财富(Eastmoney),
                     证券时报, 21世纪经济报道, 新华财经
  Global/HK        : Reuters China, SCMP, FT China, Nikkei Asia China, Xinhua EN

Usage:
  python3 fetch-cn-news.py                        # All sources, table output
  python3 fetch-cn-news.py --format json          # JSON output (for agent parsing)
  python3 fetch-cn-news.py --limit 30             # Headlines per source (default: 20)
  python3 fetch-cn-news.py --source caixin        # Single source only
  python3 fetch-cn-news.py --source caixin,scmp   # Multiple sources
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Source registry ───────────────────────────────────────────────────────────
SOURCES = [
    # Chinese domestic
    {
        "id": "caixin", "name": "财新 Caixin Global",
        "region": "CN", "lang": "en", "type": "rss",
        "url": "https://www.caixinglobal.com/rss/",
    },
    {
        "id": "sina_finance", "name": "新浪财经",
        "region": "CN", "lang": "zh", "type": "rss",
        "url": "https://rss.sina.com.cn/news/stock/stockmarket.xml",
    },
    {
        "id": "yicai", "name": "第一财经 Yicai",
        "region": "CN", "lang": "zh", "type": "rss",
        "url": "https://www.yicai.com/rss/news.xml",
    },
    {
        "id": "eastmoney", "name": "东方财富 Eastmoney",
        "region": "CN", "lang": "zh", "type": "eastmoney_api",
        "url": (
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
            "?client=web&columns=294&pageSize=30&fields=title,date,newsId,mediaName,summary"
        ),
    },
    {
        "id": "stcn", "name": "证券时报 Securities Times",
        "region": "CN", "lang": "zh", "type": "rss",
        "url": "http://www.stcn.com/content/rss.xml",
    },
    {
        "id": "21cbh", "name": "21世纪经济报道",
        "region": "CN", "lang": "zh", "type": "rss",
        "url": "http://rss.21cbh.com/list/115.xml",
    },
    {
        "id": "xinhua_finance", "name": "新华财经 Xinhua Finance",
        "region": "CN", "lang": "zh", "type": "rss",
        "url": "http://www.xinhuanet.com/money/news/rss.xml",
    },
    # Global / HK
    {
        "id": "reuters_china", "name": "Reuters China",
        "region": "GLOBAL", "lang": "en", "type": "rss",
        "url": "https://feeds.reuters.com/reuters/CNTopGenNews",
    },
    {
        "id": "scmp", "name": "South China Morning Post",
        "region": "HK", "lang": "en", "type": "rss",
        "url": "https://www.scmp.com/rss/5/feed",
    },
    {
        "id": "ft_china", "name": "Financial Times China",
        "region": "GLOBAL", "lang": "en", "type": "rss",
        "url": "https://www.ft.com/rss/home/chinese-mainland",
    },
    {
        "id": "nikkei_china", "name": "Nikkei Asia China",
        "region": "GLOBAL", "lang": "en", "type": "rss",
        "url": "https://asia.nikkei.com/rss/feed/section/china",
    },
    {
        "id": "xinhua_en", "name": "Xinhua English",
        "region": "CN", "lang": "en", "type": "rss",
        "url": "https://www.xinhuanet.com/english/rss/chinalatestnews.xml",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def clean_xml(text: str) -> str:
    text = re.sub(r"&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)", "&amp;", text)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]", "", text)
    return text


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def parse_rss(source: dict, raw: str, limit: int) -> list:
    try:
        root = ET.fromstring(clean_xml(raw))
    except ET.ParseError:
        return []

    ns    = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    articles = []

    for item in items[:limit]:
        def txt(tag: str, fallback: str = "") -> str:
            el = item.find(tag) or item.find(f"atom:{tag}", ns)
            return strip_tags(getattr(el, "text", None) or fallback)

        def get_url() -> str:
            link = item.find("link") or item.find("atom:link", ns)
            if link is None:
                return ""
            return link.get("href") or getattr(link, "text", "") or ""

        title = txt("title")
        if not title:
            continue

        articles.append({
            "source":    source["name"],
            "source_id": source["id"],
            "region":    source["region"],
            "lang":      source["lang"],
            "title":     title[:200],
            "url":       get_url(),
            "pubdate":   txt("pubDate") or txt("published"),
            "summary":   (txt("description") or txt("summary"))[:300],
        })

    return articles


def parse_eastmoney(source: dict, raw: str, limit: int) -> list:
    articles = []
    try:
        wrapper = json.loads(raw)
        items: list = []
        if isinstance(wrapper, dict):
            items = (
                wrapper.get("data", {}).get("list", [])
                or wrapper.get("list", [])
                or wrapper.get("result", {}).get("data", [])
                or []
            )
        elif isinstance(wrapper, list):
            items = wrapper

        for item in items[:limit]:
            title = item.get("title") or item.get("Title", "")
            if not title:
                continue
            news_id = item.get("newsId") or item.get("NewsID", "")
            articles.append({
                "source":    source["name"],
                "source_id": source["id"],
                "region":    source["region"],
                "lang":      source["lang"],
                "title":     strip_tags(title)[:200],
                "url":       f"https://finance.eastmoney.com/a/{news_id}.html" if news_id else "",
                "pubdate":   item.get("date") or item.get("Date", ""),
                "summary":   strip_tags(item.get("summary") or item.get("Summary") or "")[:300],
            })
    except Exception:
        pass
    return articles


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch raw China market news headlines from domestic and global sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 fetch-cn-news.py
  python3 fetch-cn-news.py --format json
  python3 fetch-cn-news.py --source caixin --limit 30
  python3 fetch-cn-news.py --source caixin,scmp
  python3 fetch-cn-news.py --source eastmoney""",
    )
    parser.add_argument("--format", "-f", choices=["table", "json"], default="table",
                        help="Output format (default: table)")
    parser.add_argument("--limit", "-n", type=int, default=20,
                        help="Headlines per source (default: 20)")
    parser.add_argument("--source", "-s", default="",
                        help="Comma-separated source IDs to fetch (default: all)")
    args = parser.parse_args()

    filter_ids = {s.strip().lower() for s in args.source.split(",") if s.strip()}
    if filter_ids:
        sources_to_fetch = [
            s for s in SOURCES
            if s["id"] in filter_ids or any(f in s["name"].lower() for f in filter_ids)
        ]
    else:
        sources_to_fetch = SOURCES

    all_articles: list = []
    source_stats: list = []

    for source in sources_to_fetch:
        raw = http_get(source["url"])
        if not raw:
            source_stats.append({"source": source, "count": 0, "status": "unreachable"})
            continue

        if source["type"] == "eastmoney_api":
            articles = parse_eastmoney(source, raw, args.limit)
        else:
            articles = parse_rss(source, raw, args.limit)

        source_stats.append({"source": source, "count": len(articles), "status": "ok"})
        all_articles.extend(articles)

    if args.format == "json":
        print(json.dumps({
            "as_of":    datetime.now().isoformat(),
            "total":    len(all_articles),
            "sources":  [
                {"id": s["source"]["id"], "name": s["source"]["name"],
                 "count": s["count"], "status": s["status"]}
                for s in source_stats
            ],
            "articles": all_articles,
        }, ensure_ascii=False, indent=2))
        return

    # ── Table output ──────────────────────────────────────────────────────────
    print()
    print(f"  China Market News Headlines  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sep = "  " + "─" * 76
    print(sep)
    print(f"  {'Source':<32} {'Lang':<5} {'Region':<8} Articles  Status")
    print(sep)
    for s in source_stats:
        src    = s["source"]
        status = "✓" if s["status"] == "ok" else "✗ unreachable"
        print(f"  {src['name']:<32} {src['lang']:<5} {src['region']:<8} {s['count']:>5}     {status}")

    print()
    print(f"  {'─── Headlines (' + str(len(all_articles)) + ' total) ':-<76}")
    print()

    for a in all_articles:
        lang_tag   = "[ZH] " if a["lang"] == "zh" else ""
        date_short = a["pubdate"][:16] if a["pubdate"] else ""
        print(f"  [{a['source_id']}] {lang_tag}{a['title']}")
        if a.get("summary"):
            print(f"    ↳ {a['summary'][:120]}")
        if date_short:
            print(f"    @ {date_short}")
        print()

    print(sep)
    ok_count = sum(1 for s in source_stats if s["status"] == "ok")
    print(f"  Total: {len(all_articles)} headlines from {ok_count} source(s)")
    print()


if __name__ == "__main__":
    main()
