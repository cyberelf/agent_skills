#!/usr/bin/env python3
"""
Filter Polymarket markets with multiple criteria.
By default, only ACTIVE markets with volume >= 50,000 are returned.

Usage:
  python3 filter-markets.py [--keywords k1,k2,...] [--volume N]
                            [--status active|closed|all] [--limit N]
                            [--format table|json]

Examples:
  python3 filter-markets.py --keywords taiwan,invasion --volume 100000
  python3 filter-markets.py --keywords byd,nio,xpeng --limit 50
  python3 filter-markets.py --status closed --format json
"""

import argparse
import json
import shutil
import subprocess
import sys

DEFAULT_KEYWORDS   = "china,taiwan,byd,nio,alibaba,tencent"
DEFAULT_MIN_VOLUME = 50_000
DEFAULT_STATUS     = "active"
DEFAULT_LIMIT      = 100


def check_polymarket() -> None:
    if not shutil.which("polymarket"):
        print("Error: polymarket CLI not found. Please install it first.", file=sys.stderr)
        sys.exit(1)


def run_search(term: str, limit: int) -> list:
    result = subprocess.run(
        ["polymarket", "-o", "json", "markets", "search", term.strip(), "--limit", str(limit)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def deduplicate(markets: list) -> list:
    seen, out = set(), []
    for m in markets:
        key = m.get("conditionId") or m.get("slug") or m.get("question")
        if key and key not in seen:
            seen.add(key)
            out.append(m)
    return out


def apply_filters(markets: list, min_volume: int, status: str) -> list:
    out = []
    for m in markets:
        if float(m.get("volume") or 0) < min_volume:
            continue
        active = m.get("active") is True
        if status == "active" and not active:
            continue
        if status == "closed" and active:
            continue
        out.append(m)
    return out


def print_table(markets: list) -> None:
    if not markets:
        print("  No markets matched the criteria.")
        return
    q_width = 56
    sep = "  " + "-" * 108
    fmt = f"  {{:<{q_width}}}  {{:>12}}  {{:>14}}  {{:>12}}  {{:<8}}"
    print(sep)
    print(fmt.format("Question", "Price (Yes)", "Volume", "Liquidity", "Status"))
    print(sep)
    for m in markets:
        question  = (m.get("question") or "N/A")[:q_width]
        price     = str((m.get("outcomePrices") or ["N/A"])[0])
        volume    = str(m.get("volume") or "0")
        liquidity = str(m.get("liquidity") or "0")
        status    = "Active" if m.get("active") else "Closed"
        print(fmt.format(question, price, volume, liquidity, status))
    print(sep)
    print(f"  {len(markets)} market(s) matched")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter Polymarket markets with multiple criteria. Active-only by default.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 filter-markets.py --keywords taiwan,invasion --volume 100000
  python3 filter-markets.py --keywords byd,nio,xpeng --limit 50
  python3 filter-markets.py --status closed --format json""",
    )
    parser.add_argument("--keywords", "-k", default=DEFAULT_KEYWORDS,
                        help=f"Comma-separated keywords (default: {DEFAULT_KEYWORDS})")
    parser.add_argument("--volume", "-v", type=int, default=DEFAULT_MIN_VOLUME,
                        help=f"Minimum volume threshold (default: {DEFAULT_MIN_VOLUME})")
    parser.add_argument("--status", "-s", choices=["active", "closed", "all"],
                        default=DEFAULT_STATUS,
                        help=f"Market status filter (default: {DEFAULT_STATUS})")
    parser.add_argument("--limit", "-n", type=int, default=DEFAULT_LIMIT,
                        help=f"Max results per keyword fetch (default: {DEFAULT_LIMIT})")
    parser.add_argument("--format", "-f", choices=["table", "json"], default="table",
                        help="Output format (default: table)")
    args = parser.parse_args()

    check_polymarket()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    print(
        f"Filtering markets... keywords={keywords}, volume>={args.volume}, status={args.status}",
        file=sys.stderr,
    )

    all_markets: list = []
    for kw in keywords:
        print(f"  Searching: '{kw}'...", file=sys.stderr)
        all_markets.extend(run_search(kw, args.limit))

    all_markets = deduplicate(all_markets)
    filtered    = apply_filters(all_markets, args.volume, args.status)

    if args.format == "json":
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:
        print_table(filtered)


if __name__ == "__main__":
    main()
