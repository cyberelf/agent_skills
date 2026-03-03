```skill
---
name: polymarket-analyzer
description: Analyze Polymarket prediction market data to provide investment insights for Chinese concept stocks (中概股) and A-shares. This skill should be used when the user asks about Polymarket data, prediction markets, A-share (A股) investment advice based on prediction market sentiment, or 中概股 correlations.
---

# Polymarket + Multi-Source China Market Sentiment Analyzer

Collect data from multiple information channels to support comprehensive sentiment analysis for Chinese concept stocks (中概股) and A-shares.

**The agent performs all judgment and interpretation.** The scripts and tools in this skill are pure data collectors — they fetch raw information without making directional calls.

---

## When to Use

Use this skill when:
- The user asks about Polymarket prediction market data for China/HK topics
- The user wants sentiment context for A-share or 中概股 investment decisions
- The user requests multi-source market intelligence (news, macro, market proxies)
- The user asks about specific stocks: BYD, NIO, Alibaba, Tencent, SMIC, etc.

---

## Prerequisites

### 1. Polymarket CLI (required for prediction market data)

```bash
# macOS / Linux via Homebrew
brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli
brew install polymarket

# Or via install script
curl -sSL https://raw.githubusercontent.com/Polymarket/polymarket-cli/main/install.sh | sh

# Verify
polymarket --version
```

### 2. yfinance (optional — enables market proxy data)

```bash
pip install yfinance
```

---

## Information Channels

The skill aggregates data from seven channel categories. The agent reads raw outputs and synthesises the judgment.

### Channel 1 — Polymarket Prediction Markets
**Tool**: `scripts/query-markets.sh`, `scripts/filter-markets.sh`  
**What it provides**: Real-money crowd probabilities on macro, geopolitical, and corporate events. Best signal for tail risks (Taiwan conflict, trade war escalation, rate decisions).  
**Typical queries**: `china`, `taiwan`, `byd`, `nio`, `alibaba`, `tariff`, `pboc`

### Channel 2 — Global Financial Market Proxies
**Tool**: `scripts/fetch-market-data.sh`  
**What it provides**: Raw daily price and volume data for 11 China-sensitive instruments:

| Ticker | Instrument | Why It Matters |
|--------|-----------|----------------|
| FXI | iShares China Large-Cap ETF | Direct China equity sentiment |
| KWEB | KraneShares China Internet ETF | China tech/internet sentiment |
| ^HSI | Hang Seng Index | HK market barometer |
| HG=F | Copper Futures | China industrial demand proxy |
| AUDUSD=X | AUD/USD | Australia exports → China activity |
| CNY=X | USD/CNY | Renminbi strength |
| ^VIX | CBOE Volatility Index | Global risk appetite |
| GC=F | Gold Futures | Safe-haven demand |
| ^TNX | US 10-yr Treasury Yield | US rate pressure on EM |
| EEM | iShares Emerging Markets ETF | Broader EM flow |
| UUP | US Dollar Index ETF | USD strength (EM headwind) |

### Channel 3 — Chinese Domestic Financial News
**Tool**: `scripts/fetch-cn-news.sh` (Chinese sources)  
**What it provides**: Raw headlines in Chinese and English from domestic Chinese financial media.

| Source | Coverage |
|--------|---------|
| 财新 Caixin Global | Deep-dive investigative finance/economy (EN+ZH) |
| 新浪财经 Sina Finance | Breaking A-share news, policy announcements |
| 第一财经 Yicai | Macro, banking, real estate |
| 东方财富 Eastmoney | Retail investor-driven stock news, hot topics |
| 证券时报 Securities Times | Official securities regulatory news |
| 21世纪经济报道 21st Century | Business investigative, industry deep dives |
| 新华财经 Xinhua Finance | State-backed macro/policy announcements |

### Channel 4 — Global / HK China-Focused News
**Tool**: `scripts/fetch-cn-news.sh` (global sources, `--source` flag optional)  
**What it provides**: English-language international perspective on China market events.

| Source | Coverage |
|--------|---------|
| Reuters China | Breaking news, macro, corporate |
| South China Morning Post | HK/Greater China business |
| Financial Times China | Western institutional perspective |
| Nikkei Asia China | Japan/Asia regional perspective |
| Xinhua English | Official Chinese government narrative |

### Channel 5 — CNN Fear & Greed Index
**Used by**: `polymarket_analyzer.py` (embedded collector)  
**What it provides**: US market psychology score 0–100; extreme readings (< 20 fear, > 80 greed) often precede reversal and affect China equity risk appetite.

### Channel 6 — Reddit Social Sentiment
**Used by**: `polymarket_analyzer.py` (embedded collector)  
**Subreddits**: r/investing, r/wallstreetbets, r/china, r/ChineseStocks, r/emergingmarkets  
**What it provides**: Retail sentiment temperature, often a contrarian indicator.

### Channel 7 — World Bank Macro Indicators
**Used by**: `polymarket_analyzer.py` (embedded collector)  
**What it provides**: Lagging but authoritative macro data: China GDP growth, CPI, export growth, FDI inflows, US real interest rate differential.

---

## Scripts Reference

### `scripts/query-markets.sh`
Query Polymarket for markets by keyword. Returns raw market data.

```bash
./scripts/query-markets.sh "china"                     # table output
./scripts/query-markets.sh "taiwan" 100 json          # JSON, 100 results
./scripts/query-markets.sh "byd" 50 json              # EV-specific
./scripts/query-markets.sh "pboc rate" 50 json        # Monetary policy
```

### `scripts/filter-markets.sh`
Filter Polymarket by multiple keywords, minimum volume, and status.

```bash
./scripts/filter-markets.sh                                        # defaults
./scripts/filter-markets.sh keywords:taiwan,invasion volume:100000
./scripts/filter-markets.sh keywords:byd,nio,xpeng,alibaba,tencent
./scripts/filter-markets.sh status:active volume:50000 output:json
```

### `scripts/fetch-market-data.sh`
Fetch raw price and percent-change data for China proxy instruments via yfinance.

```bash
./scripts/fetch-market-data.sh                         # table, 7-day window
./scripts/fetch-market-data.sh --json                  # JSON output
./scripts/fetch-market-data.sh --period 30d            # 30-day window
./scripts/fetch-market-data.sh --tickers "FXI KWEB ^VIX"  # custom set
```

**Output fields**: ticker, price, pct_1d, pct_5d, avg_volume, category

### `scripts/fetch-cn-news.sh`
Fetch raw headlines from Chinese domestic and global China-focused news sources.

```bash
./scripts/fetch-cn-news.sh                             # all sources, table
./scripts/fetch-cn-news.sh --json                      # JSON (machine-readable)
./scripts/fetch-cn-news.sh --limit 30                  # 30 headlines per source
./scripts/fetch-cn-news.sh --source caixin             # single source only
./scripts/fetch-cn-news.sh --source sina_finance       # Sina Finance only
```

**Available `--source` IDs**: `caixin`, `sina_finance`, `yicai`, `eastmoney`, `stcn`, `21cbh`, `xinhua_finance`, `reuters_china`, `scmp`, `ft_china`, `nikkei_china`, `xinhua_en`

---

## Analysis Workflow

The agent drives the full analysis. Scripts only collect; the agent interprets.

### Step 1 — Collect Polymarket Data

Run targeted Polymarket queries covering the topics of interest:

```bash
# Geopolitical signals
./scripts/query-markets.sh "taiwan" 50 json
./scripts/query-markets.sh "china war" 50 json
./scripts/query-markets.sh "china usa tariff" 100 json

# Macro signals
./scripts/query-markets.sh "china gdp" 50 json
./scripts/query-markets.sh "pboc" 50 json
./scripts/query-markets.sh "china interest rate" 50 json

# Corporate / sector signals
./scripts/query-markets.sh "byd" 50 json
./scripts/query-markets.sh "alibaba" 50 json
./scripts/query-markets.sh "tencent" 50 json
```

### Step 2 — Collect Market Proxy Data

```bash
./scripts/fetch-market-data.sh --json
```

Pay attention to: FXI/KWEB 5D trend, CNY direction, VIX level, Copper 5D.

### Step 3 — Collect News Headlines

```bash
# Chinese domestic sources
./scripts/fetch-cn-news.sh --json --limit 20

# Focus on a major source if needed
./scripts/fetch-cn-news.sh --source caixin --limit 30
./scripts/fetch-cn-news.sh --source eastmoney --limit 30
```

Key themes to look for: PBOC policy signals, trade policy, regulatory actions, property market news, geopolitical escalation or de-escalation.

### Step 4 — Optional: Run Full Composite Analyzer

The `polymarket_analyzer.py` script runs all seven collectors and outputs a composite score. Use when a complete snapshot is needed:

```bash
python3 skills/polymarket-analyzer/polymarket_analyzer.py
```

This requires Polymarket CLI + network access. Sources that are unavailable degrade gracefully.

### Step 5 — Agent Synthesises Judgment

Having collected data from all channels, the agent should:

1. **Identify consistent signals** — where multiple channels agree directionally
2. **Identify conflicting signals** — where channels diverge (higher uncertainty)
3. **Map to stocks** — use `china_stock_mapping.json` to find A-share correlations
4. **Weight by relevance horizon** — Polymarket = near-term; macro = longer-term
5. **Produce recommendation** — with explicit rationale per data source

---

## Stock and Sector Mapping

`china_stock_mapping.json` maps 21 Chinese company names to:
- A-share tickers and sector
- Supply chain companies
- HK-listed ticker
- Correlation coefficient to foreign market moves

**Companies covered**: BYD, NIO, XPeng, Li Auto, Tencent, Alibaba, Baidu, Xiaomi, Pinduoduo, JD.com, Meituan, NetEase, Kuaishou, Bilibili, SMIC, Huawei supply chain, Evergrande, Anta, Haier, Midea, Foxconn

**Macro factor mappings**: PBOC rate cuts, US-China trade war escalation, Taiwan tensions, China fiscal stimulus

---

## Configuration

### Signal Weights (`data/signal_weights.json`)

The composite analyzer uses configurable source weights. Four profiles are available:

| Profile | Use Case |
|---------|---------|
| `default` | Balanced (Polymarket 35%, market_data 25%, news 20%, fear_greed 10%, …) |
| `news_heavy` | When Polymarket data is thin; elevates news to 35% |
| `market_only` | When only yfinance data is reliable (90% weight on proxies) |
| `sentiment_focus` | Emphasises social + F&G for retail sentiment reads |

Edit `data/signal_weights.json` to customize or add profiles.

---

## A-share Sector Quick Reference

| Market Signal | Sensitive A-share Sector | Key Tickers |
|---------------|--------------------------|------------|
| EV sales / BYD / NIO | New Energy Vehicles + battery | BYD 002594.SZ, CATL 300750.SZ |
| Taiwan tensions | Defense | AVIC 600893.SH, CSGC 000768.SZ |
| US chip restrictions | Semiconductor localization | SMIC 688981.SH, Hua Hong 688347.SH |
| Trade war / tariffs | Export manufacturing | Luxshare 002475.SZ, Hisense 600060.SH |
| PBOC rate cut | Banks + Real estate | ICBC 601398.SH, Vanke 000002.SZ |
| China stimulus | Infrastructure | CRCC 601186.SH, CREC 601390.SH |
| RMB appreciation | Importers | Aviation, auto importers |
| Copper surge | Industrial metals | Jiangxi Copper 600362.SH |

---

## Troubleshooting

### Polymarket CLI not found
```bash
export PATH="$PATH:$HOME/.cargo/bin:$HOME/.local/bin"
polymarket --version
```

### yfinance not installed
```bash
pip install yfinance
# fetch-market-data.sh will report the error and exit cleanly without it
```

### Chinese news sources unreachable
Some Chinese domestic RSS feeds may block non-CN IP addresses. Options:
- Use a proxy or VPN exit node in mainland China or HK
- Focus on sources that reliably respond: `caixin`, `reuters_china`, `scmp`, `xinhua_en`
- Check: `./scripts/fetch-cn-news.sh --source caixin`

### Script permission error
```bash
chmod +x skills/polymarket-analyzer/scripts/*.sh
```

### No Polymarket markets found
- Broaden the search term
- Check connectivity: `polymarket markets list --limit 5`
- The market may not exist yet; use proxy channels (news, financial data) instead

---

## References

- [Polymarket CLI](https://github.com/Polymarket/polymarket-cli)
- [Polymarket API Docs](https://docs.polymarket.com/)
- [Caixin Global](https://www.caixinglobal.com/)
- [东方财富 Eastmoney](https://www.eastmoney.com/)
- [新浪财经 Sina Finance](https://finance.sina.com.cn/)
- [第一财经 Yicai](https://www.yicai.com/)
```