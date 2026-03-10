#!/usr/bin/env python3
"""
Query Polymarket markets matching specific criteria.
By default, only ACTIVE (open) markets are returned.

Usage:
  python3 query-markets.py <search-term> [--limit N] [--format table|json] [--all]

Examples:
  python3 query-markets.py "china"
  python3 query-markets.py "taiwan" --limit 100 --format json
  python3 query-markets.py "taiwan" --format json --all
"""

import argparse
import json
import shutil
import subprocess
import sys


def check_polymarket() -> None:
    if not shutil.which("polymarket"):
        print("Error: polymarket CLI not found. Please install it first.", file=sys.stderr)
        print("See: https://github.com/Polymarket/polymarket-cli", file=sys.stderr)
        sys.exit(1)


def run_search(term: str, limit: int) -> list:
    result = subprocess.run(
        ["polymarket", "-o", "json", "markets", "search", term, "--limit", str(limit)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def print_table(markets: list) -> None:
    if not markets:
        print("  No markets found.")
        return
    q_width = 60
    sep = "  " + "-" * 96
    fmt = f"  {{:<{q_width}}}  {{:>12}}  {{:>14}}  {{:<8}}"
    print(sep)
    print(fmt.format("Question", "Price (Yes)", "Volume", "Status"))
    print(sep)
    for m in markets:
        question = (m.get("question") or "N/A")[:q_width]
        price    = str((m.get("outcomePrices") or ["N/A"])[0])
        volume   = str(m.get("volume") or "0")
        status   = "Active" if m.get("active") else "Closed"
        print(fmt.format(question, price, volume, status))
    print(sep)
    print(f"  {len(markets)} market(s)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query Polymarket markets. Returns active markets only by default.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 query-markets.py "china"
  python3 query-markets.py "taiwan" --limit 100 --format json
  python3 query-markets.py "taiwan" --format json --all""",
    )
    parser.add_argument("search_term", help="Keywords to search for")
    parser.add_argument("--limit", "-n", type=int, default=50,
                        help="Maximum results to return (default: 50)")
    parser.add_argument("--format", "-f", choices=["table", "json"], default="table",
                        help="Output format (default: table)")
    parser.add_argument("--all", dest="include_all", action="store_true",
                        help="Include closed and resolved markets")
    args = parser.parse_args()

    check_polymarket()

    active_label = "all statuses" if args.include_all else "active-only"
    print(f"Searching Polymarket for: '{args.search_term}' (limit: {args.limit}, {active_label})",
          file=sys.stderr)

    # Fetch extra to compensate for post-filter attrition when filtering active-only
    fetch_limit = args.limit if args.include_all else args.limit * 3
    markets = run_search(args.search_term, fetch_limit)

    if not args.include_all:
        markets = [m for m in markets if m.get("active") is True]

    markets = markets[:args.limit]

    if args.format == "json":
        print(json.dumps(markets, ensure_ascii=False, indent=2))
    else:
        print_table(markets)


if __name__ == "__main__":
    main()
