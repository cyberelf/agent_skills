# Scenario 1: Macro & Geopolitical Risk Assessment (Top-Down)

**Use when:** Assessing macro tail risks — Taiwan conflict, US-China trade war escalation, PBOC policy shifts, USD/CNY stress, US elections.

---

## First Principles Anchor

Before running any script, define the **specific risk hypothesis** being tested. Examples:
- "What is the market-implied probability of new US chip sanctions on China this quarter?"
- "Is a PBOC surprise rate cut being priced into prediction markets?"
- "How elevated is contagion risk from a Taiwan Strait incident?"

This prevents data-gathering without purpose.

---

## Step 1 — Collect Explicit Risk Pricing (Polymarket)

Fetch **active-only** markets to avoid resolved/expired noise:

```bash
# High-volume macro events (minimum $50k volume)
python3 scripts/filter-markets.py --keywords taiwan,invasion,conflict --volume 50000

# Trade war & tariffs
python3 scripts/filter-markets.py --keywords tariff,trade,sanctions --volume 50000

# Monetary policy
python3 scripts/filter-markets.py --keywords pboc,rate,fed,interest --volume 30000

# Election / political risk
python3 scripts/filter-markets.py --keywords election,president,congress --volume 100000
```

**Quality gate**: Discard any result with volume < $25,000. Document the volume alongside each probability in the output.

---

## Step 1b — Establish Historical PM Trend (Mandatory)

A single probability snapshot is not a signal. Compare against history:

```bash
# Fetch all (active + resolved) contracts to see past outcomes
python3 scripts/query-markets.py "taiwan conflict" --all --limit 100 --format json
python3 scripts/query-markets.py "china tariff sanctions" --all --limit 100 --format json
python3 scripts/query-markets.py "pboc rate cut" --all --limit 100 --format json
```

For each active contract found in Step 1, answer these questions:

| Question | Source |
|----------|--------|
| What probability did analogous resolved contracts reach at peak before resolving? | `--all` results |
| Did those contracts resolve Yes or No? At what threshold probability? | `--all` results |
| Is the current probability above or below the historical "resolve Yes" average? | Comparison |

**Interpretation rules:**
- If current probability is materially (>15pp) above historical base rate for similar events → PM may be overpricing risk; weight other channels more heavily
- If current probability has been rising steadily for >7 days → active re-pricing in progress; trend is more reliable than any single snapshot
- If current probability is flat and volume is declining → market conviction is set; less informational value going forward
- If no historical analogues exist → note this as a Coverage Gap in the final report

---

## Step 2 — Collect Implicit Market Risk (Financial Proxies)

Focus on **safe-haven and capital-flight instruments** for macro risk:

```bash
python3 scripts/fetch-market-data.py --tickers "^VIX CNY=X GC=F UUP ^TNX" --period 7d --format json
```

| Ticker | What to Look For |
|--------|-----------------|
| `^VIX` | >25 = elevated fear; >35 = crisis mode |
| `CNY=X` | Rising USD/CNY = capital leaving China; a falling CNY weakens A-shares |
| `GC=F` | Rising Gold = safe-haven demand; signals risk-off globally |
| `UUP` | Rising USD = pressure on all EM assets including A-shares |
| `^TNX` | Rising US yields = higher discount rate on Chinese tech; headwind for 科创板 |

---

## Step 3 — Verify State Narrative

Determine the **official Chinese government and central-bank communication tone**:

```bash
# Official state/policy voice
python3 scripts/fetch-cn-news.py --source xinhua_en,xinhua_finance --limit 10

# Western institutional view for contrast
python3 scripts/fetch-cn-news.py --source reuters_china,ft_china --limit 10
```

**Key divergence signal**: If Xinhua is projecting stability while Reuters/FT is reporting escalation risk, the two narratives are diverging. This divergence itself is a market signal.

---

## Step 4 — Cross-Reference, Conflict Detection & Synthesis

Apply the **three-way divergence check**:

1. **Polymarket** (explicit probability) — Does the crowd assign high probability to the risk event?
2. **Market proxies** (implicit pricing) — Are financial markets pricing in the same risk?
3. **News narrative** (momentum) — Is the media narrative driving sentiment toward or away from the risk?

**Step 4a — Detect Conflicts First (do this before forming a thesis)**

Explicitly check every possible pair of sources for disagreement:

| Conflict Pair | How to Detect | Significance |
|--------------|---------------|-------------|
| PM high, proxies flat | PM >60% but FXI/VIX not moving | PM may be leading; or PM volume is too low to trust |
| Proxies stressed, PM flat | FXI/VIX spiking but no relevant PM contracts | PM coverage gap; use proxy signal as primary |
| State media calm, Western media bearish | Xinhua stable, Reuters escalation narrative | Official PRC expectation management likely — weight Reuters |
| PM rising historically but resolved No | Past analogues show mean reversion | Current elevated PM may be overpriced fear |
| PM trend up, but proxy trend reversing | PM still rising while FXI starts recovering | Market makers may be fading the PM move |

**Step 4b — Resolution Hierarchy**

When sources conflict, apply this precedence (most reliable to least):
1. **High-volume PM (>$500k) + trend momentum** — specific, continuous crowd updating
2. **Market proxies with clear 14d trend** — implicit but liquid and manipulation-resistant
3. **Western institutional media (Reuters, FT)** — fast, professional, less biased but can amplify
4. **State media (Xinhua)** — useful for official intent signals; unreliable for objective risk assessment
5. **Low-volume PM (<$50k)** — discard; treat as anecdote not signal

**Step 4c — Decision Rules**

- All three align → **High confidence** in direction; proceed to Scenario 1 full equity mapping
- Polymarket high, proxies flat → Prediction market may be leading; watch for proxy catch-up within 2–3 sessions; do not size positions yet
- Proxies spiking, Polymarket flat → Low PM volume likely; use proxy signal but note PM as unconfirmed; medium confidence only
- News bullish, PM and proxies bearish → Narrative likely wishful or managed; weight proxies + PM over media
- Any critical conflict unresolved → No directional call; document the conflict and escalate to the user

---

## Step 5 — Map to A-Share / HK Sectors

Load `references/china_stock_mapping.json` and apply the **Macro Factor Mappings** section:

| Risk Event | A-Share Sector Impact | Tickers |
|------------|----------------------|---------|
| Taiwan military escalation | Defense ↑, Tech ↓, Travel ↓ | AVIC 600893.SH |
| US-China tariffs | Export mfg ↓, Domestic consumer ↑ | Luxshare 002475.SZ |
| PBOC rate cut | Banks ↓ (NIM), Real estate ↑ | Vanke 000002.SZ |
| CNY devaluation | Exporters ↑, Importers ↓ | COSCO 601919.SH |
| US yield spike | 科创板 (STAR) ↓, Growth stocks ↓ | SMIC 688981.SH |

---

## Output

Use **Template A: Comprehensive Investment Insight Report** from `references/templates/comprehensive-insight-report.md`.
