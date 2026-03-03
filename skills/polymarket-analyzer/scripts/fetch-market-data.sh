#!/usr/bin/env bash
# fetch-market-data.sh
# Fetch raw price and volume data for China-related market proxy instruments.
# Outputs data only — no signals, no judgments.
#
# Requires: pip install yfinance
#
# Usage:
#   ./scripts/fetch-market-data.sh                     # Default tickers, table output
#   ./scripts/fetch-market-data.sh --json              # JSON output (for agent parsing)
#   ./scripts/fetch-market-data.sh --tickers "FXI KWEB ^VIX"  # Custom tickers
#   ./scripts/fetch-market-data.sh --period 30d        # Longer history (default: 7d)

set -euo pipefail

OUTPUT_FORMAT="table"
PERIOD="7d"
CUSTOM_TICKERS=""

for arg in "$@"; do
    case "$arg" in
        --json)         OUTPUT_FORMAT="json" ;;
        --tickers)      shift; CUSTOM_TICKERS="$1" ;;
        --period)       shift; PERIOD="$1" ;;
    esac
done

if ! python3 -c "import yfinance" 2>/dev/null; then
    echo "Error: yfinance not installed. Run: pip install yfinance" >&2
    exit 1
fi

python3 - "$OUTPUT_FORMAT" "$PERIOD" "$CUSTOM_TICKERS" << 'PYEOF'
import sys
import json
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("Error: pip install yfinance", file=sys.stderr)
    sys.exit(1)

output_format = sys.argv[1] if len(sys.argv) > 1 else "table"
period        = sys.argv[2] if len(sys.argv) > 2 else "7d"
custom        = sys.argv[3] if len(sys.argv) > 3 else ""

# China proxy instruments — ordered by relevance to China market
DEFAULT_TICKERS = [
    ("FXI",      "iShares FTSE China Large-Cap ETF",      "China equity"),
    ("KWEB",     "KraneShares China Internet ETF",         "China tech equity"),
    ("^HSI",     "Hang Seng Index",                        "HK equity index"),
    ("HG=F",     "Copper Futures",                         "China industrial demand"),
    ("AUDUSD=X", "AUD/USD Exchange Rate",                  "China commodities proxy"),
    ("CNY=X",    "USD/CNY Exchange Rate",                  "Renminbi vs USD"),
    ("^VIX",     "CBOE Volatility Index",                  "Global risk appetite"),
    ("GC=F",     "Gold Futures",                           "Safe-haven demand"),
    ("^TNX",     "US 10-Year Treasury Yield",              "US rates pressure"),
    ("EEM",      "iShares Emerging Markets ETF",           "Broader EM proxy"),
    ("UUP",      "Invesco DB USD Index Bullish Fund ETF",  "US Dollar strength"),
]

if custom:
    tickers = [(t, t, "") for t in custom.split()]
else:
    tickers = DEFAULT_TICKERS

rows = []
for ticker, name, category in tickers:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval="1d", auto_adjust=True)
        if hist.empty or len(hist) < 2:
            continue
        c = hist["Close"]
        v = hist["Volume"]
        latest_price = c.iloc[-1]
        pct_1d  = (c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100
        pct_5d  = (c.iloc[-1] - c.iloc[max(0, len(c)-6)]) / c.iloc[max(0, len(c)-6)] * 100
        avg_vol = int(v.mean()) if not v.empty else 0
        rows.append({
            "ticker":    ticker,
            "name":      name,
            "category":  category,
            "price":     round(latest_price, 4),
            "pct_1d":    round(pct_1d, 4),
            "pct_5d":    round(pct_5d, 4),
            "avg_volume": avg_vol,
            "period":    period,
            "as_of":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    except Exception as e:
        rows.append({"ticker": ticker, "name": name, "error": str(e)})

if output_format == "json":
    print(json.dumps(rows, ensure_ascii=False, indent=2))
else:
    print()
    print(f"  China Market Proxy Data  |  period={period}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("  " + "─" * 72)
    print(f"  {'Ticker':<12} {'1D%':>7}  {'5D%':>7}  {'Avg Vol':>12}  Category")
    print("  " + "─" * 72)
    for r in rows:
        if "error" in r:
            print(f"  {r['ticker']:<12}  ERROR: {r['error']}")
        else:
            print(f"  {r['ticker']:<12} {r['pct_1d']:>+7.2f}% {r['pct_5d']:>+7.2f}%  {r['avg_volume']:>12,}  {r['category']}")
    print("  " + "─" * 72)
    print(f"  {len([r for r in rows if 'error' not in r])} instruments fetched")
    print()
PYEOF
