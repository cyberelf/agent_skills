# Scenario 2: Sector-Specific Catalyst Tracker (Bottom-Up)

**Use when:** Analyzing a specific industry vertical — EVs, Semiconductors, Property, Internet/Tech, Consumer, Energy, or a specific company.

---

## First Principles Anchor

Identify the **single most important near-term catalyst** for the target sector. Examples:
- "NIO monthly delivery figures are due — what is Polymarket pricing for Q1 delivery targets?"
- "SMIC Q4 earnings beat — how has semiconductor sentiment shifted in prediction markets?"
- "Property developer defaults — what probability does Polymarket assign to a Evergrande-style contagion?"

This focuses data collection so that only relevant instruments are fetched.

---

## Step 1 — Targeted Prediction Market Search (Active)

Search with **industry-specific keywords** to find markets with direct sector relevance:

```bash
# EV / Auto sector
python3 scripts/query-markets.py "byd" --limit 50 --format json
python3 scripts/query-markets.py "nio delivery" --limit 50 --format json
python3 scripts/query-markets.py "xpeng li auto" --limit 50 --format json
python3 scripts/query-markets.py "ev sales china" --limit 50 --format json

# Semiconductor sector
python3 scripts/query-markets.py "semiconductor export china" --limit 50 --format json
python3 scripts/query-markets.py "chip ban smic" --limit 50 --format json
python3 scripts/query-markets.py "nvidia china" --limit 50 --format json

# Internet / Tech platform
python3 scripts/query-markets.py "alibaba antitrust" --limit 50 --format json
python3 scripts/query-markets.py "tencent gaming license" --limit 50 --format json
python3 scripts/query-markets.py "didi" --limit 50 --format json

# Property / Real estate
python3 scripts/query-markets.py "china property evergrande" --limit 50 --format json
python3 scripts/query-markets.py "country garden" --limit 50 --format json

# Energy & Commodities
python3 scripts/query-markets.py "copper china demand" --limit 50 --format json
python3 scripts/query-markets.py "lng china" --limit 50 --format json
```

**Quality gate**: Document each result's **active status and volume**. If no markets exist for a keyword, note the gap — absence of prediction market coverage itself implies that professional bettors see no near-term catalyst.

---

## Step 1b — Sector Historical Base Rate (Mandatory)

Before interpreting any active probability, establish the sector's base rate from resolved contracts:

```bash
# Fetch resolved contracts for same sector to see historical accuracy
python3 scripts/query-markets.py "ev china" --all --limit 100 --format json
python3 scripts/query-markets.py "semiconductor china" --all --limit 100 --format json
# Replace keywords with current target sector
```

**For each resolved contract returned, record:**
- Contract question, resolution (Yes/No), peak probability before resolution
- Was the crowd right? Did high probability (>70%) actually resolve Yes?

**Sector-specific calibration patterns to check:**
- EV delivery numbers: PM historically underprices beat probability at peak of news cycle
- Regulatory crackdowns: PM historically sharp and accurate (Didi/Edu-tech had >80% probability days before announcement)
- Property default contagion: PM historically overprices systemic spread; single developer ≠ sector ≠ systemic
- Chip/export controls: High base-rate Yes — US export restrictions have a >70% historical resolution rate when probabilities are above 60%

---

## Step 2 — Sector-Relevant Market Proxies

Select the proxy instruments most correlated with the target sector:

```bash
# EV / New Energy
python3 scripts/fetch-market-data.py --tickers "BYD.HK NIO XPEV LI HG=F" --period 14d --format json

# Tech / Internet
python3 scripts/fetch-market-data.py --tickers "KWEB BABA TCEHY BIDU" --period 14d --format json

# Broad China equity + FX (applicable to all sectors)
python3 scripts/fetch-market-data.py --tickers "FXI ^HSI CNY=X" --period 14d --format json

# Semiconductors / hardware
python3 scripts/fetch-market-data.py --tickers "SOXX SMH FXI" --period 14d --format json
```

**Momentum check**: Look for **5-day trend vs. 14-day trend**. A proxy that has diverged from its 14-day average by >±3% in the last 5 days signals acceleration — the catalyst may already be in motion.

---

## Step 3 — Industry-Deep News Flow

```bash
# Industry deep dives (Chinese domestic)
python3 scripts/fetch-cn-news.py --source 21cbh,yicai --limit 15

# Regulatory / official securities perspective
python3 scripts/fetch-cn-news.py --source stcn --limit 10

# International trade angle
python3 scripts/fetch-cn-news.py --source reuters_china,nikkei_china --limit 10
```

**Filter for**: Regulatory actions, supply chain news, policy announcements (subsidies, restrictions), leadership guidance, M&A events.

---

## Step 4 — Map to A-Share Tickers

Load `references/china_stock_mapping.json`. For sector-level analysis, apply the **company-level mappings**:

| Segment | Key Entities | A-Share / HK Tickers | Supply Chain Plays |
|---------|--------------|----------------------|--------------------|
| New Energy Vehicles | BYD, NIO, XPeng, Li Auto | 002594.SZ, NIO (NYSE), XPEV, LI | CATL 300750.SZ, Ganfeng 002460.SZ |
| Semiconductors | SMIC, Hua Hong | 688981.SH, 688347.SH | Anji Technology 688019.SH |
| Internet Platform | Alibaba, Tencent | 09988.HK, 00700.HK | — |
| Property | Vanke, Poly | 000002.SZ, 600048.SH | — |
| EV Battery | CATL, BYD | 300750.SZ, 002594.SZ | — |

---

## Step 5 — Evaluate Catalyst Timing & Multi-Source Verdict

**Rule: No catalyst call without ≥2 independent channels confirming direction.**

Before assigning any horizon or weight, perform an explicit cross-source check:

| Channel | Evidence Found | Direction | Confidence (H/M/L) |
|---------|---------------|-----------|-------------------|
| Polymarket (active, >$50k volume) | [Y/N, summary] | ↑↓ | |
| Polymarket (historical base rate) | [Y/N, summary] | ↑↓ | |
| Sector proxy (5d vs 14d trend) | [Y/N, summary] | ↑↓ | |
| Industry news (CN domestic) | [Y/N, summary] | ↑↓ | |
| International trade/policy news | [Y/N, summary] | ↑↓ | |

**Verdict rules:**
- ≥3 channels agree → High conviction, proceed to directional call
- Exactly 2 channels agree, no critical conflicts → Medium conviction, state which 2 and why
- 1 channel only → Label as "Unconfirmed Signal — Watch Only", do not make a directional call
- Channels conflict critically → No verdict; document the conflict explicitly and escalate

Assign a **catalyst timeline** only after the multi-source verdict is established:

| Horizon | Signal Type | Weight |
|---------|-------------|--------|
| <1 week | Polymarket delta movement + news momentum | 60% |
| 1–4 weeks | Market proxy trend + earnings/event calendar | 30% |
| 1–3 months | Macro factors (PBOC, trade tensions) | 10% |

---

## Output

Use **Template A: Comprehensive Investment Insight Report** from `references/templates/comprehensive-insight-report.md`.

If the user only wants a quick sector check, use **Template B: Quick Sector Brief** from `references/templates/quick-brief.md`.
