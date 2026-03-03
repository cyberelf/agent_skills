#!/usr/bin/env bash
# fetch-cn-news.sh
# Fetch raw news headlines about China markets from Chinese and global sources.
# Outputs headlines only — no scoring, no sentiment judgment.
#
# Sources covered:
#   Chinese domestic : 财新(Caixin), 新浪财经, 第一财经(Yicai), 东方财富(Eastmoney),
#                      证券时报, 21世纪经济报道, 新华财经
#   Global/HK        : Reuters China, SCMP, FT China, Nikkei Asia China, Xinhua EN
#
# Usage:
#   ./scripts/fetch-cn-news.sh                  # All sources, table output
#   ./scripts/fetch-cn-news.sh --json           # JSON output (for agent parsing)
#   ./scripts/fetch-cn-news.sh --limit 30       # Headlines per source (default: 20)
#   ./scripts/fetch-cn-news.sh --source caixin  # Single source only

set -euo pipefail

OUTPUT_FORMAT="table"
LIMIT=20
FILTER_SOURCE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)    OUTPUT_FORMAT="json" ;;
        --limit)   shift; LIMIT="$1" ;;
        --source)  shift; FILTER_SOURCE="$1" ;;
        *)         ;;
    esac
    shift
done

python3 - "$OUTPUT_FORMAT" "$LIMIT" "$FILTER_SOURCE" << 'PYEOF'
import sys
import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime

output_format  = sys.argv[1] if len(sys.argv) > 1 else "table"
limit          = int(sys.argv[2]) if len(sys.argv) > 2 else 20
filter_source  = sys.argv[3].lower() if len(sys.argv) > 3 else ""

# ─── Source registry ─────────────────────────────────────────────────────────
# type: "rss" | "eastmoney_api"
SOURCES = [
    # ── Chinese domestic ──────────────────────────────────────────────────────
    {
        "id":       "caixin",
        "name":     "财新 Caixin Global",
        "region":   "CN",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://www.caixinglobal.com/rss/",
    },
    {
        "id":       "sina_finance",
        "name":     "新浪财经",
        "region":   "CN",
        "lang":     "zh",
        "type":     "rss",
        "url":      "https://rss.sina.com.cn/news/stock/stockmarket.xml",
    },
    {
        "id":       "yicai",
        "name":     "第一财经 Yicai",
        "region":   "CN",
        "lang":     "zh",
        "type":     "rss",
        "url":      "https://www.yicai.com/rss/news.xml",
    },
    {
        "id":       "eastmoney",
        "name":     "东方财富 Eastmoney",
        "region":   "CN",
        "lang":     "zh",
        "type":     "eastmoney_api",
        "url":      (
            "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
            "?client=web&columns=294&pageSize=30&fields=title,date,newsId,mediaName,summary"
        ),
    },
    {
        "id":       "stcn",
        "name":     "证券时报 Securities Times",
        "region":   "CN",
        "lang":     "zh",
        "type":     "rss",
        "url":      "http://www.stcn.com/content/rss.xml",
    },
    {
        "id":       "21cbh",
        "name":     "21世纪经济报道",
        "region":   "CN",
        "lang":     "zh",
        "type":     "rss",
        "url":      "http://rss.21cbh.com/list/115.xml",
    },
    {
        "id":       "xinhua_finance",
        "name":     "新华财经 Xinhua Finance",
        "region":   "CN",
        "lang":     "zh",
        "type":     "rss",
        "url":      "http://www.xinhuanet.com/money/news/rss.xml",
    },
    # ── Global / HK ───────────────────────────────────────────────────────────
    {
        "id":       "reuters_china",
        "name":     "Reuters China",
        "region":   "GLOBAL",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://feeds.reuters.com/reuters/CNTopGenNews",
    },
    {
        "id":       "scmp",
        "name":     "South China Morning Post",
        "region":   "HK",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://www.scmp.com/rss/5/feed",
    },
    {
        "id":       "ft_china",
        "name":     "Financial Times China",
        "region":   "GLOBAL",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://www.ft.com/rss/home/chinese-mainland",
    },
    {
        "id":       "nikkei_china",
        "name":     "Nikkei Asia China",
        "region":   "GLOBAL",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://asia.nikkei.com/rss/feed/section/china",
    },
    {
        "id":       "xinhua_en",
        "name":     "Xinhua English",
        "region":   "CN",
        "lang":     "en",
        "type":     "rss",
        "url":      "https://www.xinhuanet.com/english/rss/chinalatestnews.xml",
    },
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def http_get(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def clean_xml(text: str) -> str:
    # Fix unescaped ampersands and illegal XML chars
    text = re.sub(r'&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)', '&amp;', text)
    text = re.sub(r'[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD]', '', text)
    return text


def strip_tags(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text or '').strip()


def parse_rss(source: dict, raw: str, limit: int) -> list:
    try:
        root = ET.fromstring(clean_xml(raw))
    except ET.ParseError:
        return []

    ns   = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    articles = []

    for item in items[:limit]:
        def txt(tag, fallback=""):
            el = item.find(tag) or item.find(f"atom:{tag}", ns)
            return strip_tags(getattr(el, 'text', None) or fallback)

        def url_el():
            link = item.find("link") or item.find("atom:link", ns)
            if link is None:
                return ""
            return link.get("href") or getattr(link, 'text', '') or ""

        title   = txt("title")
        link    = url_el()
        pubdate = txt("pubDate") or txt("atom:published") or txt("published")
        summary = txt("description") or txt("atom:summary") or txt("summary")

        if not title:
            continue
        articles.append({
            "source":  source["name"],
            "source_id": source["id"],
            "region":  source["region"],
            "lang":    source["lang"],
            "title":   title[:200],
            "url":     link,
            "pubdate": pubdate,
            "summary": summary[:300] if summary else "",
        })

    return articles


def parse_eastmoney(source: dict, raw: str, limit: int) -> list:
    """Parse Eastmoney proprietary JSON API response."""
    articles = []
    try:
        wrapper = json.loads(raw)
        # Response may be wrapped in a JSONP callback or nested
        items = []
        if isinstance(wrapper, dict):
            items = (
                wrapper.get("data", {}).get("list", []) or
                wrapper.get("list", []) or
                wrapper.get("result", {}).get("data", []) or
                []
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


# ─── Main ───────────────────────────────────────────────────────────────────
if filter_source:
    sources_to_fetch = [s for s in SOURCES if filter_source in s["id"] or filter_source in s["name"].lower()]
else:
    sources_to_fetch = SOURCES

all_articles = []
source_stats = []

for source in sources_to_fetch:
    raw = http_get(source["url"])
    if not raw:
        source_stats.append({"source": source["name"], "count": 0, "status": "unreachable"})
        continue

    if source["type"] == "eastmoney_api":
        articles = parse_eastmoney(source, raw, limit)
    else:
        articles = parse_rss(source, raw, limit)

    source_stats.append({"source": source["name"], "count": len(articles), "status": "ok"})
    all_articles.extend(articles)

# ─── Output ─────────────────────────────────────────────────────────────────
if output_format == "json":
    print(json.dumps({
        "as_of":    datetime.now().isoformat(),
        "total":    len(all_articles),
        "sources":  source_stats,
        "articles": all_articles,
    }, ensure_ascii=False, indent=2))
else:
    print()
    print(f"  China Market News Headlines  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("  " + "─" * 76)

    # Source summary
    print(f"  {'Source':<32} {'Lang':<5} {'Region':<8} Articles  Status")
    print("  " + "─" * 76)
    for s in source_stats:
        src = next((x for x in sources_to_fetch if x["name"] == s["source"]), {})
        lang   = src.get("lang", "")
        region = src.get("region", "")
        status = "✓" if s["status"] == "ok" else "✗ unreachable"
        print(f"  {s['source']:<32} {lang:<5} {region:<8} {s['count']:>5}     {status}")

    print()
    print(f"  {'─── Headlines (' + str(len(all_articles)) + ' total) ':-<76}")
    print()

    for a in all_articles:
        lang_tag = f"[{a['lang'].upper()}]" if a["lang"] == "zh" else ""
        date_short = a["pubdate"][:16] if a["pubdate"] else ""
        print(f"  [{a['source_id']}] {lang_tag} {a['title']}")
        if a.get("summary"):
            print(f"    ↳ {a['summary'][:120]}")
        if date_short:
            print(f"    @ {date_short}")
        print()

    print("  " + "─" * 76)
    print(f"  Total: {len(all_articles)} headlines from {len([s for s in source_stats if s['status'] == 'ok'])} sources")
    print()
PYEOF
