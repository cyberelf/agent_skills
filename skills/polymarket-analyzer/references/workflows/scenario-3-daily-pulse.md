# Scenario 3: Daily Market Pulse / Fast Digest

**Use when:** The user wants a rapid pre-market briefing before Asian market open (typically 08:30–09:15 CST), an end-of-day summary, or a quick delta check on what changed since the previous session.

---

## First Principles Anchor

The goal is **actionable deltas, not data dumps.** The daily pulse must answer three questions in under 60 seconds of reading:
1. Did any Polymarket probabilities shift materially (>5 percentage points) since yesterday?
2. Are key proxies (FXI, CNY, VIX) trending in a consistent direction?
3. Is any major news event forcing a re-evaluation of existing positions?

---

## Step 1 — Run Full Composite Analyzer

Execute all seven channels in a single command:

```bash
python3 scripts/polymarket_analyzer.py --profile default
```

If the composite analyzer is unavailable, run channels manually in this priority order:

```bash
# Priority 1: Prediction market deltas (active only)
python3 scripts/filter-markets.py --keywords china,taiwan,tariff,pboc --volume 50000 --format json

# Priority 2: Key proxy snapshot
python3 scripts/fetch-market-data.py --tickers "FXI KWEB ^VIX CNY=X" --period 2d --format json

# Priority 3: Overnight news (last 12 hours)
python3 scripts/fetch-cn-news.py --source caixin,reuters_china,xinhua_en --limit 10
```

---

## Step 2 — Identify Deltas (24h and 7d)

Compare current readings against the previous session baseline. **Both 24h and 7d deltas matter** — a small 24h change within a strong 7d trend is often more significant than a large 24h spike with no trend.

| Metric | 24h Threshold | 7d Threshold | Notes |
|--------|--------------|-------------|-------|
| Polymarket probability | ≥5pp shift | ≥10pp shift (trend) | 7d trend is more reliable than 24h noise |
| FXI / KWEB price | ≥1.5% overnight | ≥3% weekly | |
| CNY/USD | ≥0.3% daily | ≥0.8% weekly | |
| VIX | ≥2 pts daily | ≥5 pts weekly | |
| Regulatory news | Any new CSRC/PBOC/NDRC announcement | Sustained silence → binary event risk building | |
| Geopolitical | Any Taiwan Strait / South China Sea / US-China event | Escalation frequency increasing? | |

Anything below both thresholds is **background noise** — do not include it in the output.

**PM 7d trend check**: For any contract with a ≥5pp 24h move, also check whether this is acceleration of a trend or a reversion:
```bash
# Fetch resolved + active to see trajectory pattern
python3 scripts/query-markets.py "china tariff" --all --limit 50 --format json
```

---

## Step 3 — Triage (Multi-Source Confirmation Required)

Classify each material delta into one of three buckets:

| Bucket | Criteria | Action |
|--------|----------|--------|
| **ALERT** | ≥2 independent sources pointing same direction + Polymarket volume >$100k | Run full Scenario 1 or Scenario 2 workflow immediately |
| **WATCH** | Single source moving, or PM volume too low to confirm, or sources conflict | Monitor; explicitly note which source is moving and which are flat; do not act without confirmation |
| **NOISE** | Movement below thresholds, low PM volume, no corroborating source | Discard from output |

**A single source moving is always WATCH, never ALERT — even if the magnitude is large.**

Example triage application:
- VIX up 4pts + PM tariff probability up 8pp + Reuters China trade headline → **ALERT** (3 sources aligned)
- FXI down 2% but PM flat + CNY stable + news neutral → **WATCH** (FXI may be noise or EM selloff unrelated to China)
- Xinhua headline on tech policy + no PM movement + proxies flat → **NOISE** (single official-media signal, not independently confirmed)

---

## Step 4 — Synthesise Briefing

Prepare the output using **Template B: Quick Brief** from `references/templates/quick-brief.md`.

The output must be **completeable in a 30-second read** — no more than 10 bullet points total.

---

## Escalation Path

If the daily pulse reveals an ALERT-level delta, immediately switch to the full analysis workflow:
- Macro/geopolitical risk → `references/workflows/scenario-1-macro-geopolitical.md`
- Sector-specific event → `references/workflows/scenario-2-sector-catalyst.md`
