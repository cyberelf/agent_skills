---
name: polymarket-analyzer
description: Analyze Polymarket prediction market data to provide investment insights for Chinese concept stocks (中概股) and A-shares. This skill should be used when the user asks about Polymarket data, prediction markets, A-share (A股) investment advice based on prediction market sentiment, or 中概股 correlations.
---

# Polymarket Analyzer

Analyze Polymarket prediction market data to provide investment insights for Chinese concept stocks (中概股) and A-shares.

## When to Use

Use this skill when:
- The user asks about Polymarket data or prediction markets
- The user wants A-share (A股) investment advice based on prediction market sentiment
- The user asks about 中概股 (Chinese concept stocks) and their A-share correlations
- The user wants to analyze market sentiment for specific stocks like BYD, NIO, Alibaba, Tencent, etc.

## Overview

This skill helps analyze prediction market data from Polymarket to generate actionable investment insights for A-share investors. The approach involves:

1. **Data Collection**: Query Polymarket CLI or API to fetch relevant markets
2. **Filtering**: Identify markets related to China, Chinese companies, or macro factors affecting A-shares
3. **Analysis**: Interpret market probabilities, trends, and sentiment
4. **Mapping**: Correlate prediction market signals to specific A-share sectors and stocks
5. **Synthesis**: Generate comprehensive investment recommendations

## Prerequisites

### Install Polymarket CLI

The Polymarket CLI tool is required for fetching market data:

**Option 1: Homebrew (macOS/Linux)**
```bash
brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli
brew install polymarket
```

**Option 2: Shell script**
```bash
curl -sSL https://raw.githubusercontent.com/Polymarket/polymarket-cli/main/install.sh | sh
```

**Option 3: Build from source**
```bash
git clone https://github.com/Polymarket/polymarket-cli
cd polymarket-cli
cargo install --path .
```

### Verify Installation

```bash
polymarket --version
polymarket markets list --limit 5
```

## Available Tools

### 1. Query Markets Script

**Script**: `scripts/query-markets.sh`

Queries Polymarket for markets matching specific criteria. Returns structured data in table or JSON format.

**Usage**:
```bash
# Search for China-related markets
./scripts/query-markets.sh china

# Search with limit
./scripts/query-markets.sh "taiwan" 50

# Get JSON output for processing
./scripts/query-markets.sh "alibaba" 100 "json"
```

**Parameters**:
- `$1` - Search term (required)
- `$2` - Limit (optional, default: 50)
- `$3` - Output format: `table` or `json` (optional, default: table)

**Output**: Markets matching the search term with columns:
- Question
- Price (Yes)
- Volume
- Liquidity
- Status

### 2. Filter Markets Script

**Script**: `scripts/filter-markets.sh`

Advanced filtering with multiple keywords and categories. Useful for identifying A-share relevant markets.

**Usage**:
```bash
# Filter by multiple China-related keywords
./scripts/filter-markets.sh

# Custom keywords
./scripts/filter-markets.sh "keywords:byd,nio,xpeng,li auto,tencent,alibaba"

# High volume only
./scripts/filter-markets.sh "volume:100000"
```

**Parameters**:
- Accepts various filter criteria as arguments
- `keywords:` - Comma-separated list of keywords to match
- `volume:` - Minimum volume threshold
- `status:` - Market status filter

**Output**: Filtered markets with detailed information including:
- Market details
- Matched keywords
- Relevance score

### 3. Analyze Sentiment Script

**Script**: `scripts/analyze-sentiment.sh`

Analyzes market sentiment and extracts actionable insights. Processes market data to identify trends.

**Usage**:
```bash
# Analyze all China markets
./scripts/analyze-sentiment.sh china

# Analyze with detailed output
./scripts/analyze-sentiment.sh "taiwan" detailed

# Compare two topics
./scripts/analyze-sentiment.sh compare china,taiwan
```

**Parameters**:
- `$1` - Topic or comparison topics
- `$2` - Output detail level: `summary` or `detailed`

**Output**:
- Market sentiment summary
- Key trends identified
- Probability distributions
- Risk indicators

## Analysis Framework

### Market Categories to Monitor

When analyzing Polymarket for A-share investment insights, focus on these categories:

#### 1. China Macro Markets
- **GDP Growth**: Markets on China's economic growth rate
- **Interest Rates**: PBOC policy decisions and rate cuts
- **Inflation**: CPI and PPI trends
- **Currency**: RMB/USD exchange rate movements

**A-share Impact**: Broad market direction, banking sector, export-oriented companies

#### 2. Geopolitical Risk Markets
- **Taiwan Tensions**: Military conflict probabilities
- **US-China Relations**: Trade wars, tariffs, technology restrictions
- **South China Sea**: Territorial disputes
- **Cross-border Conflicts**: India-China, Japan-China tensions

**A-share Impact**: Defense sector, technology (chip restrictions), export-dependent industries

#### 3. Chinese Tech Companies (中概股)
- **EV Makers**: BYD, NIO, XPeng, Li Auto sales and stock performance
- **Tech Giants**: Alibaba, Tencent, Baidu, JD.com performance
- **Semiconductors**: SMIC and domestic chip manufacturing
- **AI Development**: Chinese AI companies and regulations

**A-share Impact**: Domestic EV supply chain, tech sector sentiment, semiconductor localization

#### 4. Policy and Regulation Markets
- **Antitrust Actions**: Big tech regulation developments
- **Real Estate Policy**: Evergrande crisis, property market support
- **Education Sector**: Private tutoring regulations
- **Healthcare**: Drug pricing, medical reform

**A-share Impact**: Sector rotation, policy-sensitive industries

### Analysis Methodology

#### Step 1: Data Collection

Query relevant markets using the scripts:

```bash
# China macro markets
./scripts/query-markets.sh "china gdp" 50 json > china_gdp.json
./scripts/query-markets.sh "china interest rate" 50 json > china_rates.json
./scripts/query-markets.sh "tariff china" 100 json > china_tariffs.json

# Geopolitical
./scripts/query-markets.sh "taiwan" 100 json > taiwan.json
./scripts/query-markets.sh "china invasion" 50 json > china_invasion.json

# Tech companies
./scripts/query-markets.sh "byd" 50 json > byd.json
./scripts/query-markets.sh "nio" 50 json > nio.json
./scripts/query-markets.sh "alibaba" 50 json > alibaba.json
```

#### Step 2: Probability Analysis

For each market, extract key metrics:

- **Current Probability**: The "Price (Yes)" from market data
- **Volume**: Trading volume indicates market confidence
- **Trend**: Price history shows direction of sentiment
- **Time to Resolution**: Markets closing soon have more reliable signals

**Interpretation Guidelines**:

| Probability | Interpretation | A-share Implication |
|-------------|-----------------|----------------------|
| <10% | Very unlikely | Negative for related sectors |
| 10-30% | Unlikely but possible | Caution warranted |
| 30-70% | Uncertain | Monitor closely |
| 70-90% | Likely | Positive for related sectors |
| >90% | Very likely | Strong positive signal |

#### Step 3: Cross-Market Correlation

Compare related markets to identify consistent trends:

**Example Analysis**:
- Taiwan invasion probability: 10% → Low immediate risk
- US-China trade deal probability: 30% → Moderate optimism
- China GDP growth >5%: 65% → Positive macro outlook

**Composite Signal**: Mixed with positive macro bias

#### Step 4: A-share Sector Mapping

Map prediction market signals to specific A-share sectors:

| Polymarket Signal | A-share Sector | Key Stocks |
|-------------------|----------------|------------|
| EV sales growth (BYD, NIO) | New Energy Vehicle | BYD, CATL, Ganfeng |
| US-China trade tensions | Export-oriented | Foxconn, Luxshare |
| Taiwan tensions | Defense | AVIC, NORINCO |
| Chip restrictions | Semiconductor localization | SMIC, Hua Hong |
| Antitrust enforcement | Tech platforms | Kuaishou, Bilibili |
| Property market support | Real estate | Vanke, Poly |

#### Step 5: Generate Recommendations

Synthesize findings into actionable recommendations:

**Structure**:
1. **Market Sentiment Summary**: Overall bullish/bearish/neutral
2. **Key Themes**: 2-3 major trends identified
3. **Sector Recommendations**: Specific A-share sectors to watch
4. **Risk Factors**: Potential downside risks
5. **Confidence Level**: High/Medium/Low based on data quality

## Common Analysis Scenarios

### Scenario 1: Monitoring EV Sector Sentiment

**Goal**: Assess market sentiment for BYD, NIO and related A-share EV supply chain

**Approach**:
```bash
# Query EV-related markets
./scripts/query-markets.sh "byd" 50 json > ev_byd.json
./scripts/query-markets.sh "nio" 50 json > ev_nio.json
./scripts/query-markets.sh "xpeng" 30 json > ev_xpeng.json
./scripts/query-markets.sh "li auto" 30 json > ev_li.json

# Analyze sentiment
./scripts/analyze-sentiment.sh compare byd,nio,xpeng,li_auto detailed
```

**Key Metrics**:
- Sales forecast probabilities
- Stock price target markets
- Market share prediction markets
- Delivery number estimates

**A-share Mapping**:
- Battery suppliers: CATL (300750.SZ), BYD (002594.SZ)
- Materials: Ganfeng (002460.SZ), Tianqi (002466.SZ)
- Components: Huayu (600741.SH), Fuyao (600660.SH)

### Scenario 2: Geopolitical Risk Assessment

**Goal**: Evaluate Taiwan tensions and potential impact on defense and tech sectors

**Approach**:
```bash
# Query geopolitical markets
./scripts/query-markets.sh "taiwan invasion" 100 json > taiwan.json
./scripts/query-markets.sh "china military" 50 json > china_military.json
./scripts/query-markets.sh "us china war" 50 json > us_china.json

# Filter for high-volume markets
./scripts/filter-markets.sh "keywords:taiwan,china,invasion,war" "volume:100000"
```

**Key Metrics**:
- Invasion probability by timeframe
- Military clash likelihood
- Diplomatic resolution probability
- US intervention likelihood

**A-share Mapping**:
- Defense: AVIC (600893.SH), NORINCO (600435.SH)
- Tech (chip localization): SMIC (688981.SH), Hua Hong (688347.SH)
- Rare earth: Northern Rare Earth (600111.SH)

### Scenario 3: Macro Policy Tracking

**Goal**: Monitor PBOC policy and economic indicators affecting broad market

**Approach**:
```bash
# Query macro markets
./scripts/query-markets.sh "china interest rate" 50 json > china_rates.json
./scripts/query-markets.sh "china gdp" 50 json > china_gdp.json
./scripts/query-markets.sh "pboc" 50 json > pboc.json
./scripts/query-markets.sh "china inflation" 50 json > china_inflation.json
```

**Key Metrics**:
- Rate cut/hike probabilities
- GDP growth forecasts
- Inflation expectations
- RMB/USD exchange rate predictions

**A-share Mapping**:
- Banks: ICBC (601398.SH), CCB (601939.SH) - benefit from rate spreads
- Real estate: Vanke (000002.SZ), Poly (600048.SH) - sensitive to rates
- Exporters: Midea (000333.SZ), Haier (600690.SH) - affected by RMB

## Output Formats

### Standard Report Structure

```
================================================================================
                     Polymarket A股投资分析报告
          基于预测市场数据的中国概念股及A股投资建议
================================================================================

📊 分析统计: 共分析 X 个中国相关市场
   🟢 看涨信号: X 个
   🔴 看跌信号: X 个
   ⚪ 中性信号: X 个

--------------------------------------------------------------------------------
🟢 看涨信号 - 建议关注
--------------------------------------------------------------------------------

1. 【置信度 XX%】
   预测问题: [Market Question]
   📈 标的: [Stock Name] ([Sector])
   相关A股: [List of A-shares]

--------------------------------------------------------------------------------
🔴 看跌信号 - 建议规避
--------------------------------------------------------------------------------
[Similar format]

================================================================================
📊 综合分析与操作策略
================================================================================

市场情绪统计:
   • 看涨信号: X 个
   • 看跌信号: X 个
   • 中性信号: X 个

[Color] 整体判断: 市场情绪 [sentiment]
   建议策略: [strategy]

🎯 重点板块推荐:
   1. [Sector]: [Stocks]

⚠️ 风险提示:
   • 预测市场数据反映的是群体预期，并非实际结果
   • 中概股与A股存在一定的相关性，但并非完全同步
   • 投资决策应结合基本面、技术面等多重因素

================================================================================
📈 数据更新: [Timestamp]
📊 数据来源: Polymarket 预测市场
================================================================================
```

## Troubleshooting

### "polymarket: command not found"

The CLI is not in your PATH. Check installation:

```bash
which polymarket
ls -la ~/.cargo/bin/polymarket
ls -la ~/.local/bin/polymarket

# Add to PATH if needed
export PATH="$PATH:$HOME/.cargo/bin"
export PATH="$PATH:$HOME/.local/bin"
```

### CLI Returns No Data

Possible causes:
1. **Network issues**: Check internet connectivity
2. **API rate limiting**: Wait a few minutes and retry
3. **Query too restrictive**: Broaden search terms

**Debug steps**:
```bash
# Test basic connectivity
polymarket status

# Try a simple query
polymarket markets list --limit 5

# Check if search returns anything
polymarket markets search "china" --limit 10
```

### Markets Found But No Signals Generated

This usually means the markets don't match the keyword filters in the analysis scripts.

**Solutions**:
1. Check what markets were found:
   ```bash
   ./scripts/query-markets.sh "china" 100 json | jq '.[].question'
   ```

2. Expand keyword list in SKILL.md analysis section

3. Try broader search terms:
   ```bash
   ./scripts/query-markets.sh "asia" 100
   ./scripts/query-markets.sh "trade war" 50
   ```

### Script Permission Errors

If bash scripts won't execute:

```bash
chmod +x scripts/*.sh

# Or run with bash explicitly
bash scripts/query-markets.sh china 50
```

### JSON Parsing Errors

If scripts fail with "jq: command not found":

```bash
# Install jq
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS

# Or use Python as fallback
python3 -m json.tool < data.json
```

## Best Practices

### 1. Data Freshness

Prediction markets update frequently. For real trading decisions:
- Run analysis before market open (9:30 AM China time)
- Check for major news events that might shift probabilities
- Re-run analysis if significant market-moving news occurs

### 2. Cross-Validation

Don't rely solely on prediction markets. Cross-check with:
- **Futures markets**: CSI 300 futures, A50 futures
- **Options flow**: Unusual options activity
- **ETF flows**: Northbound/Southbound capital flows
- **News sentiment**: Bloomberg/Reuters sentiment indices

### 3. Position Sizing

Prediction markets provide directional bias, not certainty:
- Use for **tactical allocation** (5-15% of portfolio)
- Don't bet the farm on a single signal
- Combine with stop-losses and risk management

### 4. Tracking Performance

Keep a log of predictions vs outcomes:
```
Date: 2024-01-15
Signal: Bullish on EV sector (65% confidence)
Action: Added BYD supply chain names
Outcome: TBD
Actual Return: TBD
```

This helps refine the analysis framework over time.

## References

- [Polymarket CLI GitHub](https://github.com/Polymarket/polymarket-cli)
- [Polymarket API Documentation](https://docs.polymarket.com/)
- [Prediction Market Theory](https://en.wikipedia.org/wiki/Prediction_market)
