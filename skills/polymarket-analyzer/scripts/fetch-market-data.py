#!/usr/bin/env python3
"""
Fetch raw price and volume data for China-related market proxy instruments.
Outputs data only — no signals, no judgments.

Requires: pip install yfinance

Usage:
  python3 fetch-market-data.py                           # Default tickers, table output
  python3 fetch-market-data.py --format json             # JSON output (for agent parsing)
  python3 fetch-market-data.py --tickers "FXI KWEB ^VIX" # Custom tickers
  python3 fetch-market-data.py --period 30d              # Longer history (default: 7d)
"""

import argparse
import json
import sys
from datetime import datetime

# China proxy instruments — ordered by relevance to China market
DEFAULT_TICKERS = [
    ("FXI",       "iShares FTSE China Large-Cap ETF",         "China equity"),
    ("KWEB",      "KraneShares China Internet ETF",            "China tech equity"),
    ("^HSI",      "Hang Seng Index",                           "HK equity index"),
    ("HG=F",      "Copper Futures",                            "China industrial demand"),
    ("AUDUSD=X",  "AUD/USD Exchange Rate",                     "China commodities proxy"),
    ("CNY=X",     "USD/CNY Exchange Rate",                     "Renminbi vs USD"),
    ("^VIX",      "CBOE Volatility Index",                     "Global risk appetite"),
    ("GC=F",      "Gold Futures",                              "Safe-haven demand"),
    ("^TNX",      "US 10-Year Treasury Yield",                 "US rates pressure"),
    ("EEM",       "iShares Emerging Markets ETF",              "Broader EM proxy"),
    ("UUP",       "Invesco DB USD Index Bullish Fund ETF",     "US Dollar strength"),
]


def fetch_data(tickers: list[tuple], period: str) -> list[dict]:
    try:
        import yfinance as yf
    except ImportError:
        print("Error: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
        sys.exit(1)

    rows = []
    for ticker, name, category in tickers:
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(period=period, interval="1d", auto_adjust=True)
            if hist.empty or len(hist) < 2:
                rows.append({"ticker": ticker, "name": name, "error": "insufficient data"})
                continue
            c   = hist["Close"]
            v   = hist["Volume"]
            p1  = (c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100
            p5  = (c.iloc[-1] - c.iloc[max(0, len(c) - 6)]) / c.iloc[max(0, len(c) - 6)] * 100
            rows.append({
                "ticker":     ticker,
                "name":       name,
                "category":   category,
                "price":      round(float(c.iloc[-1]), 4),
                "pct_1d":     round(p1, 4),
                "pct_5d":     round(p5, 4),
                "avg_volume": int(v.mean()) if not v.empty else 0,
                "period":     period,
                "as_of":      datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        except Exception as e:
            rows.append({"ticker": ticker, "name": name, "error": str(e)})
    return rows


def print_table(rows: list[dict], period: str) -> None:
    print()
    print(f"  China Market Proxy Data  |  period={period}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sep = "  " + "─" * 72
    print(sep)
    print(f"  {'Ticker':<12} {'1D%':>8}  {'5D%':>8}  {'Avg Vol':>14}  Category")
    print(sep)
    for r in rows:
        if "error" in r:
            print(f"  {r['ticker']:<12}  ERROR: {r['error']}")
        else:
            print(
                f"  {r['ticker']:<12} {r['pct_1d']:>+8.2f}% {r['pct_5d']:>+8.2f}%"
                f"  {r['avg_volume']:>14,}  {r['category']}"
            )
    print(sep)
    ok = sum(1 for r in rows if "error" not in r)
    print(f"  {ok}/{len(rows)} instruments fetched")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch raw China market proxy data via yfinance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 fetch-market-data.py
  python3 fetch-market-data.py --format json
  python3 fetch-market-data.py --tickers "FXI KWEB ^VIX"
  python3 fetch-market-data.py --period 30d""",
    )
    parser.add_argument("--format", "-f", choices=["table", "json"], default="table",
                        help="Output format (default: table)")
    parser.add_argument("--period", "-p", default="7d",
                        help="History period, e.g. 7d, 30d, 90d (default: 7d)")
    parser.add_argument("--tickers", "-t", default="",
                        help="Space-separated custom tickers (default: all 11 China proxies)")
    args = parser.parse_args()

    if args.tickers:
        tickers = [(t, t, "") for t in args.tickers.split()]
    else:
        tickers = DEFAULT_TICKERS

    rows = fetch_data(tickers, args.period)

    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows, args.period)


if __name__ == "__main__":
    main()
