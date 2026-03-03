#!/usr/bin/env python3
"""
Comprehensive Market Sentiment Analyzer
综合市场情绪分析器 — 多数据源融合 A股/中概股投资洞察

Data Sources (with source weights):
  1. Polymarket       (0.35) — Real-money prediction markets
  2. Market Proxies   (0.25) — VIX, FXI, Copper, AUD/USD via yfinance
  3. News RSS         (0.20) — Reuters, SCMP, FT, WSJ Asia, Caixin
  4. Fear & Greed     (0.10) — CNN Fear & Greed Index
  5. Reddit Sentiment (0.05) — r/investing, r/wallstreetbets, r/china
  6. Macro Indicators (0.05) — World Bank GDP/Trade/Inflation data

All sources degrade gracefully when unavailable (no API keys required).
Optional: pip install yfinance  → enables market proxy data source
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any



# ── Optional dependencies ───────────────────────────────────────────────────
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


# ══════════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SentimentSignal:
    """A single sentiment signal from one data source or market."""
    source: str
    category: str         # 'macro' | 'geopolitical' | 'sector' | 'sentiment'
    direction: str        # 'bullish' | 'bearish' | 'neutral'
    confidence: float     # 0.0–1.0
    weight: float         # Source-level reliability weight
    title: str
    detail: str
    raw_score: float = 0.0    # -1.0 (very bearish) to +1.0 (very bullish)
    data: Dict = field(default_factory=dict)


@dataclass
class CompositeSentiment:
    """Aggregated sentiment across all sources."""
    weighted_score: float
    direction: str        # 'bullish' | 'bearish' | 'neutral'
    confidence: float     # 0.0–1.0
    signals: List[SentimentSignal] = field(default_factory=list)
    source_breakdown: Dict[str, float] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
#  SENTIMENT KEYWORDS
# ══════════════════════════════════════════════════════════════════════════════

BULLISH_KEYWORDS = [
    # English — macro/policy
    "stimulus", "recovery", "growth", "expansion", "deal", "agreement", "reform",
    "boost", "support", "rally", "beat", "upgrade", "positive", "surge", "strong",
    "record", "optimistic", "open", "invest", "rate cut", "easing", "cutting rates",
    "inflow", "capital inflow", "buyback", "dividend", "profit", "exceed expectations",
    "rebound", "turnaround", "momentum", "acceleration", "deregulation",
    "fiscal support", "monetary easing", "accumulate", "breakthrough", "outperform",
    # English — geopolitical/diplomatic
    "ceasefire", "truce", "diplomacy", "normalize", "cooperation", "peace talks",
    "trade agreement", "tariff reduction", "tariff cut", "market access",
    "tech cooperation", "summit", "constructive meeting",
    # Chinese
    "刺激", "增长", "复苏", "利好", "上涨", "超预期", "降息", "宽松",
    "资金流入", "突破", "强势", "看多", "乐观", "扩张", "加速",
    "改革", "开放", "支持", "增持", "买入", "上调", "利率下调",
    "北向资金", "外资流入", "政策支持", "专项债", "量化宽松",
]

BEARISH_KEYWORDS = [
    # English — macro/policy
    "tariff", "sanctions", "ban", "restrict", "decline", "miss", "risk",
    "slowdown", "recession", "default", "crisis", "delisting", "investigation",
    "fine", "downgrade", "negative", "crash", "weak", "sell-off", "outflow",
    "rate hike", "tighten", "unemployment", "decouple", "blacklist", "crackdown",
    "systemic risk", "contagion", "liquidity crisis", "debt spiral", "bubble",
    "fraud", "supply chain disruption", "export control", "entity list",
    "capital outflow", "currency depreciation",
    # English — geopolitical
    "tension", "conflict", "blockade", "invasion", "war", "escalate",
    "military", "sanction", "tariff war", "trade war", "arms race",
    "flashpoint", "confrontation", "aggression",
    # Chinese
    "制裁", "关税", "下跌", "利空", "风险", "危机", "违约", "崩盘",
    "资金流出", "南向资金流出", "抛售", "通胀", "加息", "退市", "调查",
    "处罚", "下调", "看空", "减持", "卖出", "紧缩", "脱钩", "打压",
    "入侵", "战争", "冲突", "封锁", "系统性风险", "流动性危机",
]

NEGATION_RE = re.compile(
    r'\b(not|no|never|without|fail|didn\'t|won\'t|doesn\'t|cannot|can\'t|'
    r'hardly|barely|neither|nor|nothing|nowhere)\b',
    re.IGNORECASE
)

INTENSITY_UP_RE = re.compile(
    r'\b(very|extremely|highly|significantly|sharply|massively|strongly|'
    r'dramatically|substantially|considerably|remarkably)\b',
    re.IGNORECASE
)

INTENSITY_DOWN_RE = re.compile(
    r'\b(slightly|somewhat|mildly|marginally|gently|modestly|relatively)\b',
    re.IGNORECASE
)

GEO_CONFLICT_RE = re.compile(
    r'\b(invade|invasion|war|military clash|blockade|coup|military action|'
    r'strike|missile|armed conflict|troops|naval|aircraft carrier)\b',
    re.IGNORECASE
)


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def http_get(url: str, timeout: int = 12, headers: Optional[Dict] = None) -> Optional[str]:
    """HTTP GET with graceful failure; returns decoded text or None."""
    req_headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    if headers:
        req_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def score_text_sentiment(text: str) -> float:
    """
    Keyword-based sentiment scorer with negation detection and intensity weighting.
    Returns float in [-1.0, +1.0]: positive = bullish, negative = bearish.
    """
    if not text:
        return 0.0

    text_lower = text.lower()

    def score_keywords(keywords: List[str], sign: float) -> float:
        total = 0.0
        for kw in keywords:
            pattern = re.escape(kw.lower())
            for m in re.finditer(pattern, text_lower):
                start = max(0, m.start() - 50)
                context = text_lower[start:m.start()]

                negated = bool(NEGATION_RE.search(context))
                intensity = (
                    1.5 if INTENSITY_UP_RE.search(context)
                    else (0.65 if INTENSITY_DOWN_RE.search(context) else 1.0)
                )
                contribution = sign * intensity * (-1.0 if negated else 1.0)
                total += contribution
        return total

    bullish_score = score_keywords(BULLISH_KEYWORDS, +1.0)
    bearish_score = score_keywords(BEARISH_KEYWORDS, +1.0)

    net = bullish_score - bearish_score
    total_magnitude = bullish_score + bearish_score

    if total_magnitude == 0:
        return 0.0

    # Normalize with dampening to avoid extreme scores
    raw = net / (total_magnitude + 3)
    return max(-1.0, min(1.0, raw))


def direction_from_score(score: float, threshold: float = 0.12) -> Tuple[str, float]:
    """Convert raw score to (direction, confidence) pair."""
    if score > threshold:
        direction = "bullish"
        confidence = min(0.50 + abs(score) * 0.45, 0.95)
    elif score < -threshold:
        direction = "bearish"
        confidence = min(0.50 + abs(score) * 0.45, 0.95)
    else:
        direction = "neutral"
        confidence = 0.50
    return direction, confidence


def run_command(args: List[str], timeout: int = 120) -> Tuple[bool, str]:
    """Run a CLI command; return (success, output_string)."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return (result.returncode == 0,
                result.stdout if result.returncode == 0 else result.stderr)
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except FileNotFoundError:
        return False, f"Command not found: {args[0]}"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════════════════════════
#  DATA COLLECTORS
# ══════════════════════════════════════════════════════════════════════════════

class PolymarketCollector:
    """
    Polymarket prediction market data (highest-weight source).

    Real-money prediction markets are the strongest directional signal because
    participants have financial skin in the game. High-volume markets are most
    reliable. Geopolitical conflict markets use inverted probability logic
    (low conflict probability = risk-on = bullish for equities).
    """
    WEIGHT = 0.35
    SOURCE = "polymarket"

    def collect(self, stock_mapping: Dict) -> List[SentimentSignal]:
        signals: List[SentimentSignal] = []

        success, output = run_command(
            ["polymarket", "markets", "list", "--limit", "500", "--output", "json"]
        )
        if not success:
            return signals

        try:
            markets = json.loads(output)
            if not isinstance(markets, list):
                return signals
        except json.JSONDecodeError:
            return signals

        keywords = list(stock_mapping.keys()) + [
            "china", "chinese", "hong kong", "shanghai", "shenzhen", "beijing",
            "taiwan", "sino", "prc", "pboc", "renminbi", "yuan", "csi",
            "alibaba", "tencent", "baidu", "huawei", "byd", "nio", "xpeng",
            "smic", "li auto", "meituan", "jd.com", "pinduoduo", "evergrande",
            "xiaomi", "anta", "haier", "midea", "foxconn",
            "hong kong dollar", "hkex", "a-share", "a share", "csi 300",
            "hang seng", "msci china", "ftse china", "emerging market",
            "trade war", "tariff", "us china", "chips act", "export control",
            "aukus", "south china sea",
        ]
        keywords = list(set(keywords))

        seen: set = set()
        for market in markets:
            question = market.get("question", "").lower()
            description = market.get("description", "").lower()
            text = f"{question} {description}"

            if question in seen:
                continue

            matched = [kw for kw in keywords if kw in text]
            if not matched:
                continue
            seen.add(question)

            outcomes = market.get("outcomes", [])
            outcome_prices = market.get("outcomePrices", [])
            prob_bias = 0.5
            if outcomes and outcome_prices and len(outcomes) >= 2:
                try:
                    prob_bias = float(outcome_prices[0]) if outcome_prices[0] else 0.5
                except (ValueError, TypeError):
                    pass

            text_score = score_text_sentiment(text)
            is_conflict = bool(GEO_CONFLICT_RE.search(text))

            if is_conflict:
                conflict_score = -(prob_bias - 0.5) * 2
                raw_score = conflict_score * 0.7 + text_score * 0.3
            else:
                prob_score = (prob_bias - 0.5) * 2
                raw_score = prob_score * 0.6 + text_score * 0.4

            direction, confidence = direction_from_score(raw_score * 0.85)

            volume = float(market.get("volume", 0) or 0)
            liquidity = float(market.get("liquidity", 0) or 0)
            vol_boost = min(0.12, volume / 400_000)
            confidence = min(confidence + vol_boost, 0.95)

            stock_info = [stock_mapping[k] for k in matched if k in stock_mapping]

            signals.append(SentimentSignal(
                source=self.SOURCE,
                category="geopolitical" if is_conflict else "macro",
                direction=direction,
                confidence=confidence,
                weight=self.WEIGHT,
                title=market.get("question", "")[:100],
                detail=(
                    f"Probability: {prob_bias:.1%} | "
                    f"Volume: ${volume:,.0f} | "
                    f"Liquidity: ${liquidity:,.0f} | "
                    f"Keywords: {', '.join(matched[:5])}"
                ),
                raw_score=raw_score,
                data={
                    "question": market.get("question"),
                    "slug": market.get("slug"),
                    "volume": volume,
                    "liquidity": liquidity,
                    "prob_bias": prob_bias,
                    "matched_keywords": matched,
                    "stock_info": stock_info,
                    "is_conflict": is_conflict,
                }
            ))

        signals.sort(key=lambda s: s.data.get("volume", 0), reverse=True)
        return signals


class NewsRSSCollector:
    """
    Multi-source RSS news feed sentiment analysis.

    Fetches from 10 financial news sources, filters for China/A-share relevance,
    then applies keyword + negation-aware sentiment scoring.

    Sources: Reuters, SCMP, FT, WSJ Asia, Nikkei Asia, AP, Xinhua, China Daily
    """
    WEIGHT = 0.20
    SOURCE = "news_rss"
    MAX_ARTICLES_PER_FEED = 15
    MAX_TOTAL_ARTICLES = 80

    FEEDS = [
        ("Reuters Business",   "https://feeds.reuters.com/reuters/businessNews"),
        ("Reuters World",      "https://feeds.reuters.com/Reuters/worldNews"),
        ("SCMP Business",      "https://www.scmp.com/rss/91/feed"),
        ("SCMP China",         "https://www.scmp.com/rss/4/feed"),
        ("WSJ Asia Business",  "https://feeds.a.dj.com/rss/RSSAsiaBusiness.xml"),
        ("FT Companies",       "https://www.ft.com/companies?format=rss"),
        ("Nikkei Asia",        "https://asia.nikkei.com/rss/feed/nar"),
        ("AP Business",        "https://rsshub.app/apnews/topics/business-news"),
        ("Xinhua Economy",     "http://www.xinhuanet.com/english/rss/economyrss.xml"),
        ("China Daily Biz",    "http://www.chinadaily.com.cn/rss/bizchina_rss.xml"),
    ]

    CHINA_FILTER = re.compile(
        r'\b(china|chinese|hong kong|shanghai|shenzhen|beijing|alibaba|tencent|'
        r'baidu|huawei|sinopec|petrochina|byd|nio|xpeng|csi|hang.?seng|'
        r'renminbi|yuan|pboc|trade war|tariff|prc|smic|taiwan|a.?share|'
        r'中国|港股|沪深|人民币|南向|北向|科创|创业板)\b',
        re.IGNORECASE
    )

    def collect(self) -> SentimentSignal:
        all_headlines: List[str] = []
        feed_results: List[Tuple[str, int]] = []

        for feed_name, feed_url in self.FEEDS:
            content = http_get(feed_url, timeout=10)
            if not content:
                continue
            headlines = self._parse_rss(content)
            china_headlines = [
                h for h in headlines
                if self.CHINA_FILTER.search(h)
            ][:self.MAX_ARTICLES_PER_FEED]

            if china_headlines:
                all_headlines.extend(china_headlines)
                feed_results.append((feed_name, len(china_headlines)))

            if len(all_headlines) >= self.MAX_TOTAL_ARTICLES:
                break

        if not all_headlines:
            return SentimentSignal(
                source=self.SOURCE, category="macro", direction="neutral",
                confidence=0.25, weight=self.WEIGHT,
                title="News RSS: No relevant headlines fetched",
                detail="All feeds unavailable or no China-related news found",
                raw_score=0.0
            )

        scores = [score_text_sentiment(h) for h in all_headlines[:self.MAX_TOTAL_ARTICLES]]
        avg_score = sum(scores) / len(scores)
        direction, confidence = direction_from_score(avg_score)
        confidence = min(confidence * 0.85, 0.82)

        bullish = sum(1 for s in scores if s > 0.12)
        bearish = sum(1 for s in scores if s < -0.12)
        neutral_count = len(scores) - bullish - bearish
        active_feeds = ", ".join(n for n, _ in feed_results[:4])

        return SentimentSignal(
            source=self.SOURCE,
            category="macro",
            direction=direction,
            confidence=confidence,
            weight=self.WEIGHT,
            title=f"News RSS: {direction.upper()} ({len(feed_results)} feeds, {len(scores)} articles)",
            detail=(
                f"Bullish: {bullish} | Bearish: {bearish} | Neutral: {neutral_count} "
                f"| Feeds: {active_feeds}"
            ),
            raw_score=avg_score,
            data={
                "num_headlines": len(all_headlines),
                "feeds_active": len(feed_results),
                "feed_details": feed_results,
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral_count,
                "top_headlines": all_headlines[:8],
            }
        )

    def _parse_rss(self, content: str) -> List[str]:
        """Parse RSS/Atom XML; return list of headline+summary strings."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            try:
                clean = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]+', ' ', content)
                root = ET.fromstring(clean)
            except ET.ParseError:
                return []

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        headlines: List[str] = []

        for item in root.findall('.//item'):
            title = item.findtext('title', '') or ''
            desc = item.findtext('description', '') or ''
            desc = re.sub(r'<[^>]+>', ' ', desc)
            combined = f"{title}. {desc}"[:400]
            if combined.strip():
                headlines.append(combined)

        for entry in root.findall('.//atom:entry', ns):
            title_el = entry.find('atom:title', ns)
            summary_el = entry.find('atom:summary', ns) or entry.find('atom:content', ns)
            title = (title_el.text or '') if title_el is not None else ''
            summary = (summary_el.text or '') if summary_el is not None else ''
            combined = f"{title}. {summary}"[:400]
            if combined.strip():
                headlines.append(combined)

        return [h.strip() for h in headlines if h.strip()]


class MarketDataCollector:
    """
    Financial market proxy data via yfinance.

    China sentiment proxies:
    - FXI / KWEB      : Direct China equity ETFs (strongest signal)
    - Hang Seng (HSI) : HK-listed Chinese companies
    - Copper (HG=F)   : "Dr. Copper" — China demand proxy
    - AUD/USD         : Australia exports to China (activity proxy)
    - USD/CNY         : RMB strength (inverted)
    - VIX             : Global fear index (inverted)
    - Gold            : Safe-haven demand (inverted)
    - US 10yr yield   : Discount rate / global tightening pressure
    - EEM             : Broad emerging markets
    - UUP             : Dollar strength (inverse EM assets)

    Requires: pip install yfinance
    """
    WEIGHT = 0.25
    SOURCE = "market_data"

    # (ticker, display_name, direction_multiplier, china_relevance_weight)
    PROXIES = [
        ("FXI",      "FTSE China Large-Cap ETF",   +1.0, 1.00),
        ("KWEB",     "China Internet ETF",          +1.0, 0.90),
        ("^HSI",     "Hang Seng Index (HK)",        +1.0, 0.80),
        ("HG=F",     "Copper / Dr. Copper",         +1.0, 0.75),
        ("AUDUSD=X", "AUD/USD (China activity)",    +1.0, 0.65),
        ("CNY=X",    "USD/CNY (RMB strength inv.)", -1.0, 0.65),
        ("^VIX",     "CBOE VIX (Fear, inverted)",   -1.0, 0.55),
        ("GC=F",     "Gold (safe-haven, inv.)",     -0.5, 0.45),
        ("^TNX",     "US 10yr Treasury Yield",      -0.4, 0.40),
        ("EEM",      "Emerging Markets ETF",        +0.8, 0.50),
        ("UUP",      "USD Index ETF (inv.)",        -0.6, 0.45),
    ]

    def collect(self) -> SentimentSignal:
        if not HAS_YFINANCE:
            return SentimentSignal(
                source=self.SOURCE, category="macro", direction="neutral",
                confidence=0.25, weight=self.WEIGHT,
                title="Market Data: yfinance not installed",
                detail="Run: pip install yfinance  to enable live market proxy data",
                raw_score=0.0
            )

        weighted_scores: List[float] = []
        total_relevance = 0.0
        proxy_details: List[str] = []
        vix_value: Optional[float] = None

        for ticker, name, mult, relevance in self.PROXIES:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d", interval="1d", auto_adjust=True)
                if hist.empty or len(hist) < 2:
                    continue

                latest = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                pct_1d = (latest - prev) / prev if prev != 0 else 0.0
                oldest = float(hist['Close'].iloc[0])
                pct_5d = (latest - oldest) / oldest if oldest != 0 else 0.0

                combined = pct_1d * 0.60 + pct_5d * 0.40
                signal = combined * mult

                weighted_scores.append(signal * relevance)
                total_relevance += relevance

                arrow = "↑" if pct_1d > 0 else "↓"
                proxy_details.append(f"{name}: {arrow}{abs(pct_1d):.2%} (5d:{pct_5d:+.2%})")

                if ticker == "^VIX":
                    vix_value = latest
            except Exception:
                continue

        if not weighted_scores or total_relevance == 0:
            return SentimentSignal(
                source=self.SOURCE, category="macro", direction="neutral",
                confidence=0.25, weight=self.WEIGHT,
                title="Market Data: Could not fetch proxy data",
                detail="All yfinance requests failed",
                raw_score=0.0
            )

        avg_weighted = sum(weighted_scores) / total_relevance
        amplified = max(-1.0, min(1.0, avg_weighted * 18))
        direction, confidence = direction_from_score(amplified, threshold=0.10)

        vix_note = f" | VIX: {vix_value:.1f}" if vix_value is not None else ""
        detail_str = " | ".join(proxy_details[:6]) + vix_note

        return SentimentSignal(
            source=self.SOURCE,
            category="macro",
            direction=direction,
            confidence=confidence,
            weight=self.WEIGHT,
            title=f"Market Proxies: {direction.upper()} (score: {amplified:+.3f})",
            detail=detail_str,
            raw_score=amplified,
            data={"proxy_details": proxy_details, "vix": vix_value}
        )


class FearGreedCollector:
    """
    CNN Fear & Greed Index.
    Scale: 0 (Extreme Fear) → 100 (Extreme Greed)
    Contrarian signals at extremes: <20 = buy zone, >80 = sell zone.
    """
    WEIGHT = 0.10
    SOURCE = "fear_greed"
    CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    def collect(self) -> SentimentSignal:
        score_val: Optional[float] = None
        classification: Optional[str] = None
        previous_close: Optional[float] = None

        content = http_get(
            self.CNN_URL, timeout=10,
            headers={"Referer": "https://www.cnn.com/markets/fear-and-greed"}
        )
        if content:
            try:
                data = json.loads(content)
                fg = data.get("fear_and_greed", {})
                score_val = float(fg.get("score", 50))
                classification = fg.get("rating", "Neutral")
                previous_close = float(fg.get("previous_close", score_val))
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                pass

        if score_val is None:
            return SentimentSignal(
                source=self.SOURCE, category="sentiment", direction="neutral",
                confidence=0.25, weight=self.WEIGHT,
                title="Fear & Greed: Data unavailable",
                detail="CNN F&G API did not respond",
                raw_score=0.0
            )

        raw_score = (score_val - 50) / 50

        if score_val <= 25:
            direction, confidence, zone = "bearish", 0.78, "Extreme Fear"
        elif score_val <= 40:
            direction, confidence, zone = "bearish", 0.62, "Fear"
        elif score_val <= 60:
            direction, confidence, zone = "neutral", 0.50, "Neutral"
        elif score_val <= 75:
            direction, confidence, zone = "bullish", 0.62, "Greed"
        else:
            direction, confidence, zone = "bullish", 0.78, "Extreme Greed"

        trend = ""
        if previous_close is not None:
            delta = score_val - previous_close
            trend = f" | Δ: {delta:+.1f}"

        contrarian = ""
        if score_val < 20:
            contrarian = " ⚠️ CONTRARIAN BUY"
        elif score_val > 80:
            contrarian = " ⚠️ CONTRARIAN SELL"

        return SentimentSignal(
            source=self.SOURCE, category="sentiment", direction=direction,
            confidence=confidence, weight=self.WEIGHT,
            title=f"CNN Fear & Greed: {score_val:.0f}/100 [{zone}]{contrarian}",
            detail=f"Score: {score_val:.1f} | Zone: {zone}{trend}",
            raw_score=raw_score,
            data={"score": score_val, "zone": zone, "previous_close": previous_close}
        )


class RedditSentimentCollector:
    """
    Reddit social sentiment via public JSON API (no auth required).
    Filters for China/A-share mentions, applies upvote-weighted scoring.
    Subreddits: r/investing, r/wallstreetbets, r/stocks, r/china, r/economics
    """
    WEIGHT = 0.05
    SOURCE = "social_sentiment"

    SUBREDDITS = [
        ("investing",      25),
        ("wallstreetbets", 20),
        ("stocks",         20),
        ("china",          15),
        ("economics",      15),
    ]

    CHINA_PATTERN = re.compile(
        r'\b(china|chinese|alibaba|tencent|byd|nio|hang.?seng|hong.?kong|'
        r'a.?share|csi.?300|smic|huawei|taiwan|yuan|renminbi|pboc|'
        r'eem|fxi|kweb|sino|prc|trade war|tariff)\b',
        re.IGNORECASE
    )

    def collect(self) -> SentimentSignal:
        all_posts: List[Tuple[str, int, float]] = []

        for sub, limit in self.SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
            content = http_get(
                url, timeout=10,
                headers={"User-Agent": "SentimentAnalyzerBot/2.0 (educational)"}
            )
            if not content:
                continue
            try:
                data = json.loads(content)
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    p = post.get("data", {})
                    text = f"{p.get('title', '')} {p.get('selftext', '')}"[:500]
                    if self.CHINA_PATTERN.search(text):
                        upvotes = int(p.get("score", 0))
                        ratio = float(p.get("upvote_ratio", 0.5))
                        all_posts.append((text, upvotes, ratio))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        if not all_posts:
            return SentimentSignal(
                source=self.SOURCE, category="sentiment", direction="neutral",
                confidence=0.20, weight=self.WEIGHT,
                title="Reddit: No China-related posts found",
                detail="No China-relevant posts in Reddit hot feeds",
                raw_score=0.0
            )

        total_weight = 0.0
        weighted_score_sum = 0.0
        for text, upvotes, ratio in all_posts:
            sentiment = score_text_sentiment(text)
            post_weight = max(1.0, min(float(upvotes), 5000.0)) * ratio
            weighted_score_sum += sentiment * post_weight
            total_weight += post_weight

        raw_score = weighted_score_sum / total_weight if total_weight > 0 else 0.0
        direction, confidence = direction_from_score(raw_score)
        confidence = min(confidence, 0.62)

        bullish = sum(1 for t, _, _ in all_posts if score_text_sentiment(t) > 0.12)
        bearish = sum(1 for t, _, _ in all_posts if score_text_sentiment(t) < -0.12)
        neutral_count = len(all_posts) - bullish - bearish

        return SentimentSignal(
            source=self.SOURCE, category="sentiment", direction=direction,
            confidence=confidence, weight=self.WEIGHT,
            title=f"Reddit Sentiment: {direction.upper()} ({len(all_posts)} China posts)",
            detail=(
                f"Upvote-weighted score: {raw_score:+.3f} | "
                f"Bullish: {bullish} | Bearish: {bearish} | Neutral: {neutral_count}"
            ),
            raw_score=raw_score,
            data={"num_posts": len(all_posts), "bullish": bullish, "bearish": bearish}
        )


class MacroIndicatorsCollector:
    """
    Macro economic indicators via World Bank free API.
    Structural/lagging context (no API key required).
    Indicators: China GDP growth, CPI, exports, FDI; US real interest rate.
    """
    WEIGHT = 0.05
    SOURCE = "macro_indicators"

    WB_URL = (
        "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        "?format=json&mrv=4&per_page=4"
    )

    INDICATORS = [
        ("CN", "NY.GDP.MKTP.KD.ZG",    "China GDP Growth %",         +1.0),
        ("CN", "FP.CPI.TOTL.ZG",       "China CPI Inflation %",      -0.5),
        ("CN", "NE.EXP.GNFS.ZS",       "China Exports / GDP %",      +0.6),
        ("CN", "BX.KLT.DINV.WD.GD.ZS", "China FDI Inflows / GDP %",  +0.8),
        ("US", "FR.INR.RINR",           "US Real Interest Rate %",    -0.5),
    ]

    def collect(self) -> SentimentSignal:
        scores: List[float] = []
        details: List[str] = []

        for country, indicator, name, multiplier in self.INDICATORS:
            url = self.WB_URL.format(country=country, indicator=indicator)
            content = http_get(url, timeout=15)
            if not content:
                continue
            try:
                parsed = json.loads(content)
                if len(parsed) < 2 or not parsed[1]:
                    continue
                records = [r for r in parsed[1] if r.get("value") is not None]
                if not records:
                    continue

                value = float(records[0]["value"])
                year = records[0].get("date", "N/A")

                if "GDP" in name:
                    normalized = (value - 2.0) / 5.0
                elif "CPI" in name:
                    normalized = -(value - 2.0) / 3.0
                elif "Exports" in name:
                    normalized = (value - 18.0) / 10.0
                elif "FDI" in name:
                    normalized = (value - 2.0) / 3.0
                elif "Real Interest" in name:
                    normalized = -(value) / 4.0
                else:
                    normalized = value / 10.0

                signal = max(-1.0, min(1.0, normalized * multiplier))
                scores.append(signal)
                details.append(f"{name} ({year}): {value:.2f}%")
            except (json.JSONDecodeError, KeyError, IndexError, ValueError, TypeError):
                continue

        if not scores:
            return SentimentSignal(
                source=self.SOURCE, category="macro", direction="neutral",
                confidence=0.20, weight=self.WEIGHT,
                title="Macro Indicators: No data returned",
                detail="World Bank API unavailable",
                raw_score=0.0
            )

        avg_score = sum(scores) / len(scores)
        direction, confidence = direction_from_score(avg_score)
        confidence = min(confidence, 0.68)

        return SentimentSignal(
            source=self.SOURCE, category="macro", direction=direction,
            confidence=confidence, weight=self.WEIGHT,
            title=f"Macro Indicators: {direction.upper()} (World Bank)",
            detail=" | ".join(details) or "No data",
            raw_score=avg_score,
            data={"indicators": details}
        )


class NorthboundFlowCollector:
    """
    Northbound/Southbound Stock Connect flow proxy.
    Uses FXI & KWEB volume anomaly × price direction as inflow/outflow signal.
    True northbound data requires Tushare/Wind; this is a public-data proxy.
    """
    WEIGHT = 0.05
    SOURCE = "northbound_flow"

    def collect(self) -> SentimentSignal:
        if not HAS_YFINANCE:
            return SentimentSignal(
                source=self.SOURCE, category="sector", direction="neutral",
                confidence=0.20, weight=self.WEIGHT,
                title="Northbound Flow: yfinance not installed",
                detail="Install yfinance for ETF flow proxy",
                raw_score=0.0
            )

        signals: List[float] = []
        details: List[str] = []

        for ticker, name in [("FXI", "China Large-Cap ETF"), ("KWEB", "China Internet ETF")]:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="20d", interval="1d")
                if hist.empty or len(hist) < 10:
                    continue

                avg_vol = float(hist['Volume'].iloc[-11:-1].mean())
                curr_vol = float(hist['Volume'].iloc[-1])
                vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0

                curr_close = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2])
                price_change = (curr_close - prev_close) / prev_close

                flow_signal = price_change * min(vol_ratio, 3.0)
                signals.append(flow_signal)

                vol_label = "HIGH" if vol_ratio > 1.3 else ("NORMAL" if vol_ratio > 0.7 else "LOW")
                arrow = "↑" if price_change > 0 else "↓"
                details.append(f"{name}: {arrow}{abs(price_change):.2%} vol={vol_label}({vol_ratio:.1f}x)")
            except Exception:
                continue

        if not signals:
            return SentimentSignal(
                source=self.SOURCE, category="sector", direction="neutral",
                confidence=0.20, weight=self.WEIGHT,
                title="Northbound Flow: Data unavailable",
                detail="ETF data unavailable for flow estimation",
                raw_score=0.0
            )

        avg = sum(signals) / len(signals)
        amplified = max(-1.0, min(1.0, avg * 20))
        direction, confidence = direction_from_score(amplified, threshold=0.08)
        confidence = min(confidence, 0.65)

        return SentimentSignal(
            source=self.SOURCE, category="sector", direction=direction,
            confidence=confidence, weight=self.WEIGHT,
            title=f"ETF Flow Proxy: {direction.upper()} (northbound estimate)",
            detail=" | ".join(details),
            raw_score=amplified,
            data={"details": details}
        )


# ══════════════════════════════════════════════════════════════════════════════
#  SIGNAL AGGREGATION
# ══════════════════════════════════════════════════════════════════════════════

class SignalAggregator:
    """
    Weighted multi-source signal aggregation.

    Algorithm:
      1. Each signal contributes: raw_score × confidence × source_weight
      2. Weighted mean across all contributions
      3. Cross-source agreement bonus (up to +18% confidence when 3+ sources agree)
      4. Thresholded direction assignment with confidence (0.08 threshold)

    Weights are overridable via data/signal_weights.json.
    """

    DEFAULT_WEIGHTS = {
        "polymarket":       0.35,
        "market_data":      0.25,
        "news_rss":         0.20,
        "fear_greed":       0.10,
        "northbound_flow":  0.05,
        "social_sentiment": 0.04,
        "macro_indicators": 0.01,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def aggregate(self, signals: List[SentimentSignal]) -> CompositeSentiment:
        if not signals:
            return CompositeSentiment(
                weighted_score=0.0, direction="neutral", confidence=0.30
            )

        for sig in signals:
            if sig.source in self.weights:
                sig.weight = self.weights[sig.source]

        total_eff_weight = 0.0
        weighted_sum = 0.0
        source_breakdown: Dict[str, float] = {}

        for sig in signals:
            eff_w = sig.weight * sig.confidence
            contribution = sig.raw_score * eff_w
            weighted_sum += contribution
            total_eff_weight += eff_w

            source_breakdown.setdefault(sig.source, 0.0)
            source_breakdown[sig.source] += contribution

        if total_eff_weight == 0:
            return CompositeSentiment(
                weighted_score=0.0, direction="neutral",
                confidence=0.30, signals=signals
            )

        final_score = max(-1.0, min(1.0, weighted_sum / total_eff_weight))
        direction, confidence = direction_from_score(final_score, threshold=0.08)

        # Cross-source agreement bonus
        non_poly_dirs = [
            s.direction for s in signals
            if s.direction != "neutral" and s.source != "polymarket"
        ]
        if len(non_poly_dirs) >= 3:
            ratio = non_poly_dirs.count(direction) / len(non_poly_dirs)
            confidence = min(confidence * (1.0 + ratio * 0.18), 0.95)

        norm = {k: round(v / total_eff_weight, 4) for k, v in source_breakdown.items()}

        return CompositeSentiment(
            weighted_score=round(final_score, 4),
            direction=direction,
            confidence=round(confidence, 3),
            signals=signals,
            source_breakdown=norm,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Formats the comprehensive multi-source sentiment analysis report."""

    SOURCE_ICONS = {
        "polymarket":       "🔮",
        "news_rss":         "📰",
        "market_data":      "📈",
        "fear_greed":       "🧠",
        "social_sentiment": "💬",
        "macro_indicators": "🏦",
        "northbound_flow":  "🌊",
    }

    SOURCE_LABELS = {
        "polymarket":       "Polymarket Prediction Markets",
        "news_rss":         "News RSS Sentiment",
        "market_data":      "Market Proxy Data",
        "fear_greed":       "CNN Fear & Greed Index",
        "social_sentiment": "Reddit Social Sentiment",
        "macro_indicators": "World Bank Macro Indicators",
        "northbound_flow":  "ETF Flow Proxy (Northbound Est.)",
    }

    def generate(self, composite: CompositeSentiment, stock_mapping: Dict) -> str:
        lines: List[str] = []
        W = 82

        def sep(char: str = "═"):
            lines.append(char * W)

        dir_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(composite.direction, "⚪")
        dir_zh = {
            "bullish": "看涨 BULLISH",
            "bearish": "看跌 BEARISH",
            "neutral": "中性 NEUTRAL",
        }.get(composite.direction, "中性 NEUTRAL")

        # Title
        sep()
        lines.append("   综合市场情绪分析报告 / Comprehensive Market Sentiment Analysis")
        lines.append("   多源数据融合 · 中概股 & A股投资洞察  |  Multi-Source Signal Fusion")
        sep()
        lines.append("")

        # Composite Score Box
        score_bar = self._score_bar(composite.weighted_score)
        lines.append("  ┌" + "─" * (W - 4) + "┐")
        lines.append(f"  │  {dir_icon} Overall Direction: {dir_zh:<28} Confidence: {composite.confidence:.0%}    │")
        lines.append(f"  │  Composite Score: [{score_bar}] {composite.weighted_score:+.4f}              │")
        lines.append(f"  │  Scale: -1.0 ═══ Extreme Bear ═══ 0.0 ═══ Extreme Bull ═══ +1.0   │")
        lines.append("  └" + "─" * (W - 4) + "┘")
        lines.append("")

        # Source Breakdown Table
        sep("─")
        lines.append("  📊 Signal Breakdown by Data Source | 各数据源信号明细")
        sep("─")
        lines.append("")
        lines.append(f"  {'Source':<34} {'Direction':<12} {'Confidence':<12} {'Weight':<8} Score")
        lines.append("  " + "─" * (W - 4))

        non_poly = [s for s in composite.signals if s.source != "polymarket"]
        poly_signals = [s for s in composite.signals if s.source == "polymarket"]

        for sig in non_poly:
            icon = self.SOURCE_ICONS.get(sig.source, "📊")
            d_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(sig.direction, "⚪")
            label = self.SOURCE_LABELS.get(sig.source, sig.source)
            lines.append(
                f"  {icon} {label:<32} {d_icon} {sig.direction:<10} "
                f"{sig.confidence:<12.0%} {sig.weight:<8.0%} {sig.raw_score:+.3f}"
            )
            lines.append(f"      ↳ {sig.detail[:74]}")
            lines.append("")

        if poly_signals:
            bull_p = sum(1 for s in poly_signals if s.direction == "bullish")
            bear_p = sum(1 for s in poly_signals if s.direction == "bearish")
            avg_poly = sum(s.raw_score for s in poly_signals) / len(poly_signals)
            poly_dir, poly_conf = direction_from_score(avg_poly)
            d_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(poly_dir, "⚪")
            lines.append(
                f"  🔮 {'Polymarket (' + str(len(poly_signals)) + ' markets)':<32} "
                f"{d_icon} {poly_dir:<10} {poly_conf:<12.0%} {'35%':<8} {avg_poly:+.3f}"
            )
            lines.append(
                f"      ↳ {bull_p} bullish | {bear_p} bearish | "
                f"{len(poly_signals) - bull_p - bear_p} neutral signals"
            )
            lines.append("")

        # Polymarket Detail
        if poly_signals:
            sep("─")
            lines.append("  🔮 Polymarket Top Signals (Ranked by Volume)")
            sep("─")
            lines.append("")

            bullish_poly = [s for s in poly_signals if s.direction == "bullish"][:6]
            bearish_poly = [s for s in poly_signals if s.direction == "bearish"][:6]

            if bullish_poly:
                lines.append("  🟢 Top Bullish Markets:")
                for i, sig in enumerate(bullish_poly, 1):
                    stock_tags: List[str] = []
                    for si in sig.data.get("stock_info", []):
                        if si:
                            stock_tags.extend(si.get("a_shares", [])[:2])
                    a_str = f" → A股: {', '.join(stock_tags[:4])}" if stock_tags else ""
                    lines.append(f"     {i}. [{sig.confidence:.0%}] {sig.title[:68]}")
                    lines.append(f"        {sig.detail[:74]}")
                    if a_str:
                        lines.append(f"        {a_str}")
                lines.append("")

            if bearish_poly:
                lines.append("  🔴 Top Bearish Markets:")
                for i, sig in enumerate(bearish_poly, 1):
                    lines.append(f"     {i}. [{sig.confidence:.0%}] {sig.title[:68]}")
                    lines.append(f"        {sig.detail[:74]}")
                lines.append("")

        # News Headlines Preview
        news_sigs = [s for s in non_poly if s.source == "news_rss"]
        if news_sigs and news_sigs[0].data.get("top_headlines"):
            sep("─")
            lines.append("  📰 Sample China-Related Headlines Analyzed")
            sep("─")
            lines.append("")
            for h in news_sigs[0].data["top_headlines"][:6]:
                h_clean = re.sub(r'\s+', ' ', h.strip())[:76]
                lines.append(f"     • {h_clean}")
            lines.append("")

        # Sector Recommendations
        sep("═")
        lines.append("  📋 A股板块配置建议 / A-Share Sector Allocation Guidance")
        sep("═")
        lines.append("")

        if composite.direction == "bullish":
            lines.append("  📈 总体策略: 积极布局 / Active Positioning")
            lines.append(f"     Confidence {composite.confidence:.0%} — Multiple sources aligned bullish")
            lines.append("")

            sectors: Dict[str, List[str]] = {}
            for sig in poly_signals:
                if sig.direction == "bullish":
                    for si in sig.data.get("stock_info", []):
                        if si:
                            sector = si.get("sector", "其他")
                            sectors.setdefault(sector, []).extend(si.get("a_shares", []))

            if sectors:
                lines.append("  🎯 Polymarket-derived sector focus:")
                for i, (sector, stocks) in enumerate(list(sectors.items())[:6], 1):
                    unique = list(dict.fromkeys(stocks))[:5]
                    lines.append(f"     {i}. {sector}: {', '.join(unique)}")
            else:
                lines.append("  🎯 Generic bullish allocation:")
                lines.append("     1. 新能源汽车:  比亚迪(002594) · 宁德时代(300750) · 亿纬锂能(300014)")
                lines.append("     2. 互联网/AI:   科大讯飞(002230) · 三七互娱(002555)")
                lines.append("     3. 半导体:      中芯国际(688981) · 北方华创(002371) · 澜起科技(688008)")
                lines.append("     4. 消费复苏:    美的集团(000333) · 海尔智家(600690) · 贵州茅台(600519)")
            lines.append("")

        elif composite.direction == "bearish":
            lines.append("  📉 总体策略: 防御为主 / Defensive Positioning")
            lines.append(f"     Confidence {composite.confidence:.0%} — Multiple sources aligned bearish")
            lines.append("")
            lines.append("  🛡️  Defensive allocation:")
            lines.append("     1. 黄金/贵金属:  山东黄金(600547) · 中金黄金(600489) · 赤峰黄金(600988)")
            lines.append("     2. 国债/利率债:  中短期利率债 · 政策性金融债")
            lines.append("     3. 低波动蓝筹:   工商银行(601398) · 建设银行(601939) · 农业银行(601288)")
            lines.append("     4. 防御性消费:   伊利股份(600887) · 中国神华(601088) · 长江电力(600900)")
            lines.append("")

        else:
            lines.append("  ⚪ 总体策略: 均衡观望 / Neutral — Wait for Clarity")
            lines.append(f"     Confidence {composite.confidence:.0%} — Mixed signals, no clear directional bias")
            lines.append("")
            lines.append("  ⚖️  Balanced allocation:")
            lines.append("     1. 维持中性仓位 (40–60% 权益配置)")
            lines.append("     2. 高股息标的:   银行、能源、公用事业")
            lines.append("     3. 科技精选:     分批布局，等待政策催化")
            lines.append("")

        # Source Contribution
        if composite.source_breakdown:
            sep("─")
            lines.append("  📊 Source Contribution Breakdown | 各源得分贡献")
            sep("─")
            lines.append("")
            for src, contrib in sorted(
                composite.source_breakdown.items(), key=lambda x: abs(x[1]), reverse=True
            ):
                icon = self.SOURCE_ICONS.get(src, "📊")
                label = self.SOURCE_LABELS.get(src, src)
                bar = self._mini_bar(contrib)
                lines.append(f"  {icon} {label:<38} {bar} {contrib:+.4f}")
            lines.append("")

        # Risk Disclosure
        sep("─")
        lines.append("  ⚠️  风险提示 / Risk Disclosure")
        sep("─")
        lines.append("")
        lines.append("  • 本分析整合预测市场、新闻情绪、市场价格代理等多元数据，不构成投资建议")
        lines.append("  • Polymarket 反映市场群体预期；实际结果可能与预测出现显著偏差")
        lines.append("  • 中概股与A股相关性不稳定，地缘政治出现黑天鹅可引发非线性波动")
        lines.append("  • RSS新闻情绪存在时间滞后，建议配合实时资讯综合研判")
        lines.append("  • 宏观数据以季度/年度为频率，反映长期趋势而非短期择时信号")
        lines.append("  • 任何投资决策还须结合个股基本面、技术分析与个人风险承受能力")
        lines.append("")

        # Footer
        sep()
        lines.append(f"  📅 Analysis Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  📡 Data Sources:   Polymarket · RSS Feeds · yfinance · CNN F&G · Reddit · World Bank")
        lines.append(
            f"  🎯 Final Score:    {composite.weighted_score:+.4f}  |  "
            f"Direction: {composite.direction.upper()}  |  "
            f"Confidence: {composite.confidence:.0%}"
        )
        sep()

        return "\n".join(lines)

    @staticmethod
    def _score_bar(score: float, width: int = 20) -> str:
        center = width // 2
        pos = max(0, min(width - 1, int((score + 1.0) / 2.0 * width)))
        bar = list("─" * width)
        bar[center] = "│"
        bar[pos] = "█"
        return "".join(bar)

    @staticmethod
    def _mini_bar(contrib: float, width: int = 12) -> str:
        filled = min(int(abs(contrib) * width * 3), width)
        char = "▶" if contrib > 0 else "◀"
        if contrib > 0:
            return " " * (width - filled) + char * filled + " "
        return " " + char * filled + " " * (width - filled) + " "


# ══════════════════════════════════════════════════════════════════════════════
#  STOCK MAPPING LOADER
# ══════════════════════════════════════════════════════════════════════════════

def load_stock_mapping() -> Dict:
    """Load China concept stock → A-share mapping from JSON file."""
    default_mapping = {
        "byd":       {"name": "比亚迪",   "sector": "新能源车",    "a_shares": ["比亚迪",   "宁德时代", "亿纬锂能"]},
        "nio":       {"name": "蔚来",     "sector": "新能源车",    "a_shares": ["江淮汽车", "文灿股份", "德赛西威"]},
        "xpeng":     {"name": "小鹏",     "sector": "新能源车",    "a_shares": ["德赛西威", "华阳集团", "保隆科技"]},
        "li_auto":   {"name": "理想",     "sector": "新能源车",    "a_shares": ["东安动力", "保隆科技", "德赛西威"]},
        "tencent":   {"name": "腾讯",     "sector": "游戏/互联网", "a_shares": ["三七互娱", "世纪华通", "完美世界"]},
        "alibaba":   {"name": "阿里巴巴", "sector": "电商/云计算", "a_shares": ["石基信息", "三江购物", "新华都"]},
        "baidu":     {"name": "百度",     "sector": "AI/自动驾驶", "a_shares": ["科大讯飞", "德赛西威", "华阳集团"]},
        "xiaomi":    {"name": "小米",     "sector": "智能硬件",    "a_shares": ["石头科技", "九号公司", "小熊电器"]},
        "jd":        {"name": "京东",     "sector": "电商/物流",   "a_shares": ["德邦股份", "新宁物流", "华贸物流"]},
        "meituan":   {"name": "美团",     "sector": "本地生活",    "a_shares": ["顺丰控股", "圆通速递", "韵达股份"]},
        "pinduoduo": {"name": "拼多多",   "sector": "电商",        "a_shares": ["供销大集", "申通快递"]},
    }

    skill_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(skill_dir, "china_stock_mapping.json")

    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("stocks", default_mapping)
        except Exception as e:
            print(f"  ⚠️  Warning: mapping file load failed ({e}), using defaults")

    return default_mapping


def load_signal_weights() -> Dict[str, float]:
    """Load custom signal weights from data/signal_weights.json if present."""
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    weights_file = os.path.join(skill_dir, "data", "signal_weights.json")
    if os.path.exists(weights_file):
        try:
            with open(weights_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def main() -> CompositeSentiment:
    """Run the full multi-source sentiment analysis pipeline."""
    print("═" * 82)
    print("  综合市场情绪分析器 v2.0  /  Comprehensive Market Sentiment Analyzer")
    print("  多数据源融合 · A股投资洞察  |  Multi-Source Fusion for A-Share Insights")
    print("═" * 82)
    print()

    if not HAS_YFINANCE:
        print("  ℹ️  Tip: pip install yfinance  → enables live market proxy data (source #2)")
        print()

    stock_mapping = load_stock_mapping()
    custom_weights = load_signal_weights()
    print(f"  ✓ Loaded {len(stock_mapping)} China concept stock → A-share mappings")
    if custom_weights:
        print(f"  ✓ Loaded custom signal weights from data/signal_weights.json")

    all_signals: List[SentimentSignal] = []

    # 1. Polymarket
    print("\n  🔮 [1/7] Querying Polymarket prediction markets...")
    poly = PolymarketCollector()
    poly_signals = poly.collect(stock_mapping)
    all_signals.extend(poly_signals)
    bull_p = sum(1 for s in poly_signals if s.direction == "bullish")
    bear_p = sum(1 for s in poly_signals if s.direction == "bearish")
    print(f"       → {len(poly_signals)} China-related markets | {bull_p} bullish, {bear_p} bearish")

    # 2. News RSS
    print("  📰 [2/7] Analyzing news RSS feeds (Reuters, SCMP, FT, WSJ, Nikkei…)...")
    news = NewsRSSCollector()
    news_sig = news.collect()
    all_signals.append(news_sig)
    print(f"       → {news_sig.title}")

    # 3. Market Proxies
    print("  📈 [3/7] Fetching market proxy data (FXI, VIX, Copper, AUD/USD…)...")
    market = MarketDataCollector()
    market_sig = market.collect()
    all_signals.append(market_sig)
    print(f"       → {market_sig.title}")

    # 4. Fear & Greed
    print("  🧠 [4/7] Fetching CNN Fear & Greed Index...")
    fg = FearGreedCollector()
    fg_sig = fg.collect()
    all_signals.append(fg_sig)
    print(f"       → {fg_sig.title}")

    # 5. Reddit
    print("  💬 [5/7] Analyzing Reddit investor sentiment (r/investing, r/stocks…)...")
    reddit = RedditSentimentCollector()
    reddit_sig = reddit.collect()
    all_signals.append(reddit_sig)
    print(f"       → {reddit_sig.title}")

    # 6. Macro Indicators
    print("  🏦 [6/7] Fetching World Bank macro indicators (GDP, Inflation, Trade…)...")
    macro = MacroIndicatorsCollector()
    macro_sig = macro.collect()
    all_signals.append(macro_sig)
    print(f"       → {macro_sig.title}")

    # 7. Northbound Flow Proxy
    print("  🌊 [7/7] Estimating northbound capital flow (ETF volume proxy)...")
    nb = NorthboundFlowCollector()
    nb_sig = nb.collect()
    all_signals.append(nb_sig)
    print(f"       → {nb_sig.title}")

    # Aggregate
    print("\n  ⚡ Aggregating signals with weighted fusion model...")
    aggregator = SignalAggregator(weights=custom_weights or None)
    composite = aggregator.aggregate(all_signals)
    print(
        f"  ✓ Composite: {composite.direction.upper()} | "
        f"Score: {composite.weighted_score:+.4f} | "
        f"Confidence: {composite.confidence:.0%}"
    )

    # Report
    reporter = ReportGenerator()
    report = reporter.generate(composite, stock_mapping)
    print()
    print(report)

    return composite


if __name__ == "__main__":
    main()
