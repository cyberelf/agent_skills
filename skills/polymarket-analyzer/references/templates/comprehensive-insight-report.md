# Template A: Comprehensive Investment Insight Report

Use this template for **deep-dive analyses** triggered by Scenario 1 (Macro/Geopolitical) or Scenario 2 (Sector Catalyst) workflows. This is the primary output format.

**Judgment rules that cannot be waived:**
- No single-source conclusion is ever valid. Every directional call requires corroboration from ≥2 independent channels.
- All detected conflicts between sources must be explicitly documented and resolved — ignoring a conflict is a disqualifying error.
- Polymarket current probability means little without the trend. Always include the probability trajectory (where it was 7d and 30d ago) alongside the current value.

---

```markdown
# 🇨🇳 Multi-Source China Market Intelligence Report
**Date:** [YYYY-MM-DD HH:MM CST]
**Triggered by:** [Scenario 1: Macro | Scenario 2: Sector — specify sector]
**Target:** [e.g., "A-share EV sector" / "China-US tariff risk" / "SMIC semiconductor"]

---

## Executive Summary
**Primary Thesis:** [1–2 sentences derived ONLY from cross-channel convergence — do NOT state a thesis that rests on a single source]
**Source Convergence:** [List which channels agree on direction: e.g., "Polymarket ↑, FXI ↑, Reuters ↑ — 3/4 channels bullish"]
**Open Conflicts:** [List any channels that contradict the thesis — e.g., "CNY stable/strengthening, inconsistent with risk narrative"]
**Composite Confidence Score:** [1–10, where 10 requires all channels aligned with high Polymarket volume]
- Deductions: [e.g., "−2 CNY diverges; −1 Polymarket volume moderate ($200k)"]

---

## 1. Prediction Market Signals (Polymarket) — Current + Historical Trend
*Current probability is only meaningful in context of where it has been.*

### 1a. Active Contracts (current state)

| Event / Question | Probability | 24h Δ | 7d Δ | Volume | Reliability |
|-----------------|-------------|-------|------|--------|-------------|
| [Question text] | [X]% | [±pp] | [±pp] | [$Z] | [High >$500k / Med $50–500k / Low <$50k] |

**Trend interpretation:**
- Flat probability + high volume = market has made up its mind; less alpha in the direction signal
- Rapidly rising probability (>10pp in 7d) + rising volume = active re-pricing; high actionability
- High probability + falling volume = market thinning out; probability may be stale
- [Note: if no relevant active markets found, state this explicitly — absence of coverage is itself a signal]

### 1b. Historical Context — Resolved Similar Contracts
*What happened last time a similar event was priced? Use `--all` to retrieve past contracts.*

| Past Event | Resolved Probability | Actual Outcome | Lesson |
|------------|---------------------|----------------|--------|
| [Past contract title] | [X]% at close | [Resolved Yes/No] | [e.g., "PM overpriced Taiwan risk by ~20pp historically"] |

---

## 2. Financial Market Proxy Confirmation
*Implicit pricing — do traditional financial markets agree with Polymarket?*

| Instrument | Current | 1D% | 5D% | 14D% | Reading | vs. Polymarket |
|------------|---------|-----|-----|------|---------|----------------|
| FXI (China Large-Cap) | | | | | [Risk-On/Off] | [Confirms / Conflicts] |
| KWEB (China Internet) | | | | | | |
| CNY=X (USD/CNY) | | | | | [CNY strength] | |
| ^VIX (Volatility) | | | | | | |
| GC=F (Gold) | | | | | [Safe-haven] | |
| HG=F (Copper) | | | | | [Industrial demand] | |
| [Sector-specific] | | | | | | |

**Proxy Trend Assessment:** [Is the 14d trend consistent with the 5d trend, or is momentum reversing? State explicitly.]

---

## 3. News & Narrative Context
*State media vs. global media consensus. Bias explicitly noted. Conflicts flagged.*

| Source | Bias | Headline / Theme | Direction | Confidence in Source |
|--------|------|-----------------|-----------|---------------------|
| Xinhua / 新华 | Official PRC — expect optimistic framing | [Summary] | ↑↓ | [Notes on reliability] |
| Caixin / 财新 | Independent CN — investigative, higher credibility | [Summary] | | |
| Reuters China | Western wire — institutional, fast | [Summary] | | |
| SCMP / FT China | HK/Western — balanced but pro-market | [Summary] | | |
| [Sector source] | | [Summary] | | |

**State vs. International Media Gap:** [Explicitly state whether official PRC narrative and international narrative agree. A gap here is often the most important signal in the report.]

---

## 4. ⚠️ Cross-Source Conflict Register
*This section is MANDATORY. If sources fully agree, state "No conflicts detected — all channels aligned." Never leave blank.*

| Conflict | Source A says | Source B says | Likely Explanation | Resolution / Which to Trust |
|----------|--------------|---------------|-------------------|----------------------------|
| [e.g., FXI rising but Polymarket tariff odds also rising] | FXI +2.5% (bullish) | PM tariff probability 75% (bearish for exports) | Markets may be pricing in stimulus outweighing tariff drag | Weight PM higher for export-specific stocks; FXI reflects broader China buying |
| [Another conflict] | | | | |

**Conflict severity:** [None / Minor (reconcilable) / Major (invalidates thesis partially) / Critical (do not trade — conflicting signals too strong)]

---

## 5. 🎯 Multi-Dimensional Judgment & Actionable Equity Impact
*A directional call is only valid if supported by ≥2 independent channels. Single-source signals are flagged Watch-only.*

| Catalyst | Channels Supporting | Channels Conflicting | Sector | Tickers | Conviction | Setup |
|----------|--------------------|--------------------|--------|---------|------------|-------|
| [Event] | [PM + FXI + News] | [CNY flat] | [Sector] | [Ticker] | [H/M/L] | [Long/Short/Watch] |

**Conviction Rules:**
- **High (H):** ≥3 channels aligned + Polymarket volume >$500k + PM trend rising
- **Medium (M):** 2 channels aligned + no critical conflicts
- **Low (L/Watch):** Single-source signal, or major conflict unresolved — monitor only, do not act
- **No Signal:** All channels conflicting or insufficient data — state this explicitly

---

## 6. Risk Factors & Blind Spots
*Where data is incomplete, contradictory, or could invalidate the thesis.*

- **Coverage Gap:** [e.g., "No active Polymarket contracts for PBOC this week — PM dimension missing"]
- **Stale Trend:** [e.g., "Polymarket probability flat for 14d — market conviction set, less leading value"]
- **Narrative Risk:** [e.g., "Xinhua calm on trade likely managing expectations pre-announcement — binary event risk high"]
- **Liquidity Risk:** [e.g., "All EV PM contracts <$50k volume — PM dimension is noise, not signal"]
- **Model Risk:** [e.g., "FXI trend driven by broad EM flows unrelated to China-specific fundamentals"]

---

## 7. Data Provenance & Timestamps
*For auditability and reproducibility.*

| Source | Command Run | Timestamp (UTC) | Records |
|--------|-------------|-----------------|---------|
| Polymarket (active) | `python3 scripts/filter-markets.py --keywords ... --volume ...` | [HH:MM] | [N] |
| Polymarket (historical) | `python3 scripts/query-markets.py "..." --all` | [HH:MM] | [N] |
| Market Proxies | `python3 scripts/fetch-market-data.py --tickers "..." --period ...` | [HH:MM] | [N] |
| News (CN domestic) | `python3 scripts/fetch-cn-news.py --source ...` | [HH:MM] | [N] |
| News (Global/HK) | `python3 scripts/fetch-cn-news.py --source ...` | [HH:MM] | [N] |
```
