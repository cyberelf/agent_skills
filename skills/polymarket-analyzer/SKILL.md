---
name: polymarket-analyzer
description: Analyze Polymarket prediction market data to provide investment insights for Chinese concept stocks (中概股) and A-shares. This skill should be used when the user asks about Polymarket data, prediction markets, A-share (A股) investment advice based on prediction market sentiment, or 中概股 correlations.
---

# Polymarket + Multi-Source China Market Sentiment Analyzer

Collect data from multiple information channels to support comprehensive sentiment analysis for Chinese concept stocks (中概股) and A-shares.

**The agent performs all judgment and interpretation.** The scripts in this skill are pure data collectors — they fetch raw information without making directional calls.

---

## When to Use

- The user asks about Polymarket prediction market data for China/HK topics
- The user wants sentiment context for A-share or 中概股 investment decisions
- The user requests multi-source market intelligence (news, macro, market proxies)
- The user asks about specific stocks: BYD, NIO, Alibaba, Tencent, SMIC, etc.

---

## Prerequisites

### Polymarket CLI (required for prediction market data)

```bash
brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli
brew install polymarket
# or
curl -sSL https://raw.githubusercontent.com/Polymarket/polymarket-cli/main/install.sh | sh
polymarket --version
```

### yfinance (optional — enables market proxy data)

```bash
pip install yfinance
```

---

## Skill Structure

```
polymarket-analyzer/
├── SKILL.md
├── references/
│   ├── china_stock_mapping.json   # 21 China concept stocks → A-share sector/ticker mapping
│   └── signal_weights.json        # Configurable source weights for composite analyzer
└── scripts/
    ├── polymarket_analyzer.py     # Full 7-source composite analyzer
    ├── query-markets.sh           # Raw Polymarket search by keyword
    ├── filter-markets.sh          # Raw Polymarket filter by keyword/volume/status
    ├── fetch-market-data.sh       # Raw price/volume for China proxy instruments
    └── fetch-cn-news.sh           # Raw headlines from Chinese domestic + global sources
```

---

## Information Channels

### Channel 1 — Polymarket Prediction Markets
**Scripts**: `scripts/query-markets.sh`, `scripts/filter-markets.sh`

Real-money crowd probabilities on macro, geopolitical, and corporate events. Best for tail risks such as Taiwan conflict, trade war escalation, and rate decisions.

### Channel 2 — Financial Market Proxies
**Script**: `scripts/fetch-market-data.sh`

Raw daily price and volume data for 11 China-sensitive instruments:

| Ticker | Instrument | Relevance |
|--------|-----------|-----------|
| FXI | iShares China Large-Cap ETF | Direct China equity sentiment |
| KWEB | KraneShares China Internet ETF | China tech/internet |
| ^HSI | Hang Seng Index | HK market |
| HG=F | Copper Futures | China industrial demand |
| AUDUSD=X | AUD/USD | China commodities activity |
| CNY=X | USD/CNY | Renminbi strength |
| ^VIX | CBOE Volatility Index | Global risk appetite |
| GC=F | Gold Futures | Safe-haven demand |
| ^TNX | US 10-yr Treasury Yield | US rate pressure on EM |
| EEM | iShares Emerging Markets ETF | EM flow proxy |
| UUP | US Dollar Index ETF | USD strength |

### Channel 3 — Chinese Domestic Financial News
**Script**: `scripts/fetch-cn-news.sh`

Raw headlines from domestic Chinese financial media:

| Source ID | Name | Coverage |
|-----------|------|---------|
| `caixin` | 财新 Caixin Global | Investigative finance/economy (EN+ZH) |
| `sina_finance` | 新浪财经 | Breaking A-share news, policy |
| `yicai` | 第一财经 | Macro, banking, real estate |
| `eastmoney` | 东方财富 | Retail investor hot topics |
| `stcn` | 证券时报 | Regulatory / official securities news |
| `21cbh` | 21世纪经济报道 | Industry deep dives |
| `xinhua_finance` | 新华财经 | State macro/policy announcements |

### Channel 4 — Global / HK China-Focused News
**Script**: `scripts/fetch-cn-news.sh` (same script, global sources)

| Source ID | Name | Coverage |
|-----------|------|---------|
| `reuters_china` | Reuters China | Breaking, macro, corporate |
| `scmp` | South China Morning Post | HK/Greater China business |
| `ft_china` | Financial Times China | Western institutional view |
| `nikkei_china` | Nikkei Asia China | Japan/Asia regional perspective |
| `xinhua_en` | Xinhua English | Official Chinese government narrative |

### Channels 5–7 — Embedded in Composite Analyzer
Invoked automatically by `scripts/polymarket_analyzer.py`:
- **CNN Fear & Greed Index** — US market psychology; extreme readings affect EM risk appetite
- **Reddit Social Sentiment** — r/investing, r/wallstreetbets, r/china, r/ChineseStocks, r/emergingmarkets
- **World Bank Macro** — China GDP, CPI, export growth, FDI, US real interest rate

---

## Scripts Usage

### `scripts/query-markets.sh` — Polymarket raw search
```bash
./scripts/query-markets.sh "china"
./scripts/query-markets.sh "taiwan" 100 json
./scripts/query-markets.sh "byd" 50 json
./scripts/query-markets.sh "pboc rate" 50 json
```

### `scripts/filter-markets.sh` — Polymarket multi-filter
```bash
./scripts/filter-markets.sh keywords:taiwan,invasion volume:100000
./scripts/filter-markets.sh keywords:byd,nio,xpeng,alibaba,tencent
./scripts/filter-markets.sh status:active volume:50000 output:json
```

### `scripts/fetch-market-data.sh` — Market proxy raw data
```bash
./scripts/fetch-market-data.sh --json
./scripts/fetch-market-data.sh --period 30d
./scripts/fetch-market-data.sh --tickers "FXI KWEB ^VIX"
```

### `scripts/fetch-cn-news.sh` — China news raw headlines
```bash
./scripts/fetch-cn-news.sh --json --limit 20
./scripts/fetch-cn-news.sh --source caixin --limit 30
./scripts/fetch-cn-news.sh --source eastmoney
```

### `scripts/polymarket_analyzer.py` — Full composite run
Executes all seven channels and prints a structured report:
```bash
python3 scripts/polymarket_analyzer.py
```
Channels unavailable at runtime degrade gracefully with no crash.

---

## Analysis Workflow

To produce a China market sentiment assessment, follow these steps:

### Step 1 — Collect Polymarket signals
```bash
./scripts/query-markets.sh "taiwan" 50 json
./scripts/query-markets.sh "china usa tariff" 100 json
./scripts/query-markets.sh "pboc" 50 json
./scripts/query-markets.sh "byd" 50 json
```

### Step 2 — Collect market proxy data
```bash
./scripts/fetch-market-data.sh --json
```
Note FXI/KWEB 5D trend, CNY direction, VIX level, Copper momentum.

### Step 3 — Collect news headlines
```bash
./scripts/fetch-cn-news.sh --json --limit 20
```
Key themes: PBOC signals, trade policy, regulatory actions, property market, geopolitical shifts.

### Step 4 — Synthesise judgment (agent task)
After collecting all raw data:
1. Identify where multiple channels agree directionally
2. Flag diverging channels as uncertainty areas
3. Load `references/china_stock_mapping.json` to map signals to A-share sectors and tickers
4. Distinguish near-term signals (Polymarket) from structural signals (macro)
5. Produce a recommendation with explicit per-source rationale

---

## References

### `references/china_stock_mapping.json`
Maps 21 China concept stocks to A-share sectors, tickers, supply chain names, HK listings, and correlation coefficients. Companies covered: BYD, NIO, XPeng, Li Auto, Tencent, Alibaba, Baidu, Xiaomi, Pinduoduo, JD.com, Meituan, NetEase, Kuaishou, Bilibili, SMIC, Huawei supply chain, Evergrande, Anta, Haier, Midea, Foxconn. Also includes macro factor mappings for: PBOC rate cuts, US-China trade war, Taiwan tensions, China stimulus.

### `references/signal_weights.json`
Configurable source weights for the composite analyzer. Four profiles:

| Profile | Description |
|---------|-------------|
| `default` | Polymarket 35%, market_data 25%, news 20%, fear_greed 10%, … |
| `news_heavy` | Elevates news to 35% when Polymarket coverage is thin |
| `market_only` | 90% weight on market proxies only |
| `sentiment_focus` | Emphasis on social + Fear & Greed for retail sentiment reads |

---

## A-share Sector Quick Reference

| Market Signal | A-share Sector | Key Tickers |
|---------------|---------------|------------|
| EV sales / BYD / NIO | New Energy + Battery | BYD 002594.SZ, CATL 300750.SZ |
| Taiwan tensions | Defense | AVIC 600893.SH, CSGC 000768.SZ |
| US chip restrictions | Semiconductor localization | SMIC 688981.SH, Hua Hong 688347.SH |
| Trade war / tariffs | Export manufacturing | Luxshare 002475.SZ, Hisense 600060.SH |
| PBOC rate cut | Banks + Real estate | ICBC 601398.SH, Vanke 000002.SZ |
| China stimulus | Infrastructure | CRCC 601186.SH, CREC 601390.SH |
| Copper surge | Industrial metals | Jiangxi Copper 600362.SH |

---

## Troubleshooting

**Polymarket CLI not found**
```bash
export PATH="$PATH:$HOME/.cargo/bin:$HOME/.local/bin"
```

**yfinance not installed** — `fetch-market-data.sh` will print an error and exit cleanly; all other channels still work.

**Chinese news sources unreachable** — Some domestic RSS feeds block non-CN IPs. Use a HK/mainland proxy, or focus on: `caixin`, `reuters_china`, `scmp`, `xinhua_en`.
