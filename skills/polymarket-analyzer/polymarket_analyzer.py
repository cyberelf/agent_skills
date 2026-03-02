#!/usr/bin/env python3
"""
Polymarket Analyzer - 分析Polymarket预测市场并提供A股投资建议
"""

import subprocess
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os


def run_poly_command(args: List[str]) -> Tuple[bool, str]:
    """运行poly CLI命令"""
    try:
        cmd = ["polymarket"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except FileNotFoundError:
        return False, "polymarket command not found"
    except Exception as e:
        return False, str(e)


def get_all_markets() -> List[Dict]:
    """获取所有活跃市场"""
    # 使用JSON格式输出
    success, output = run_poly_command(["markets", "list", "--limit", "500", "--output", "json"])

    if not success:
        print(f"Warning: Failed to get markets from CLI: {output}")
        return []

    try:
        markets = json.loads(output)
        return markets if isinstance(markets, list) else []
    except json.JSONDecodeError as e:
        print(f"Error parsing markets JSON: {e}")
        return []


def load_stock_mapping() -> Dict:
    """加载中概股与A股映射"""
    default_mapping = {
        "byd": {"name": "比亚迪", "sector": "新能源车", "a_shares": ["比亚迪", "宁德时代", "亿纬锂能"]},
        "nio": {"name": "蔚来", "sector": "新能源车", "a_shares": ["江淮汽车", "文灿股份", "德赛西威"]},
        "xpeng": {"name": "小鹏", "sector": "新能源车", "a_shares": ["德赛西威", "华阳集团", "保隆科技"]},
        "li_auto": {"name": "理想", "sector": "新能源车", "a_shares": ["东安动力", "保隆科技", "德赛西威"]},
        "tencent": {"name": "腾讯", "sector": "游戏/互联网", "a_shares": ["三七互娱", "世纪华通", "完美世界"]},
        "alibaba": {"name": "阿里巴巴", "sector": "电商/云计算", "a_shares": ["石基信息", "三江购物", "新华都"]},
        "baidu": {"name": "百度", "sector": "AI/自动驾驶", "a_shares": ["科大讯飞", "德赛西威", "华阳集团"]},
        "xiaomi": {"name": "小米", "sector": "智能硬件", "a_shares": ["小米集团-W", "石头科技", "九号公司"]},
        "pinduoduo": {"name": "拼多多", "sector": "电商", "a_shares": ["供销大集", "农产品电商概念股"]},
        "jd": {"name": "京东", "sector": "电商/物流", "a_shares": ["德邦股份", "新宁物流", "华贸物流"]},
        "meituan": {"name": "美团", "sector": "本地生活", "a_shares": ["外卖配送概念股", "餐饮供应链"]},
    }

    # 尝试从文件加载
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(skill_dir, "china_stock_mapping.json")

    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("stocks", default_mapping)
        except Exception as e:
            print(f"Warning: Failed to load mapping file: {e}")

    return default_mapping


def search_china_markets(markets: List[Dict], stock_mapping: Dict) -> List[Dict]:
    """搜索与中国相关的市场"""
    china_markets = []
    seen = set()

    # 构建关键词列表
    keywords = list(stock_mapping.keys())
    keywords.extend(["china", "chinese", "hong kong", "shanghai", "shenzhen", "beijing", "taiwan"])

    for market in markets:
        question = market.get("question", "").lower()
        description = market.get("description", "").lower()
        text = f"{question} {description}"

        # 去重
        if question in seen:
            continue

        matched = []
        for keyword in keywords:
            if keyword in text:
                matched.append(keyword)

        if matched:
            market["matched_keywords"] = matched
            market["stock_info"] = {k: stock_mapping.get(k) for k in matched if k in stock_mapping}
            china_markets.append(market)
            seen.add(question)

    # 按交易量排序
    china_markets.sort(key=lambda x: float(x.get("volume", 0) or 0), reverse=True)
    return china_markets


def analyze_market_direction(market: Dict) -> Tuple[str, float]:
    """分析市场方向

    Returns:
        (direction, confidence): direction is 'bullish', 'bearish', or 'neutral'
    """
    question = market.get("question", "").lower()
    description = market.get("description", "").lower()
    text = f"{question} {description}"

    # 基于市场问题的关键词分析
    bullish_terms = [
        "above", "higher", "increase", "up", "positive", "beat", "exceed",
        "rise", "growth", "surge", "rally", "breakout", "moon", "bull",
        "突破", "上涨", "增长", "上升", "超过", "高于", "看多", "visit", "deal", "agreement"
    ]

    bearish_terms = [
        "below", "lower", "decrease", "down", "negative", "miss", "fall",
        "drop", "decline", "crash", "dump", "bear", "breakdown", "ban", "blockade", "invasion", "clash", "war",
        "跌破", "下跌", "下降", "低于", "看空", "崩盘", "入侵", "封锁", "冲突", "战争"
    ]

    bullish_count = sum(1 for term in bullish_terms if term in text)
    bearish_count = sum(1 for term in bearish_terms if term in text)

    # 获取市场概率数据
    outcomes = market.get("outcomes", [])
    outcome_prices = market.get("outcomePrices", [])

    prob_bias = 0.5
    if outcomes and outcome_prices and len(outcomes) >= 2:
        try:
            # 简单假设：第一个选项是"是"/上涨，第二个是"否"/下跌
            yes_price = float(outcome_prices[0]) if outcome_prices[0] else 0.5
            prob_bias = yes_price
        except (ValueError, TypeError):
            pass

    # 综合判断 - 对于地缘政治类市场需要特殊处理
    geo_conflict_terms = ["invade", "invasion", "war", "clash", "blockade", "coup", "military"]
    is_geo_conflict = any(term in text for term in geo_conflict_terms)

    if is_geo_conflict:
        # 地缘政治冲突市场：低概率发生 = 避险资产利好
        if prob_bias < 0.3:
            direction = "bullish"  # 冲突不太可能发生 = 利好
            confidence = 0.7
        elif prob_bias > 0.7:
            direction = "bearish"  # 冲突很可能发生 = 利空
            confidence = 0.7
        else:
            direction = "neutral"
            confidence = 0.5
    else:
        # 普通市场分析
        if bullish_count > bearish_count:
            direction = "bullish"
            confidence = min(0.5 + bullish_count * 0.15 + (prob_bias - 0.5) * 0.3, 0.95)
        elif bearish_count > bullish_count:
            direction = "bearish"
            confidence = min(0.5 + bearish_count * 0.15 + (0.5 - prob_bias) * 0.3, 0.95)
        else:
            direction = "neutral"
            confidence = 0.5

    return direction, confidence


def generate_recommendations(china_markets: List[Dict], stock_mapping: Dict) -> Dict:
    """生成投资建议"""

    recommendations = {
        "bullish": [],
        "bearish": [],
        "neutral": []
    }

    for market in china_markets:
        direction, confidence = analyze_market_direction(market)

        stock_info_list = []
        for keyword in market.get("matched_keywords", []):
            if keyword in stock_mapping:
                stock_info_list.append(stock_mapping[keyword])

        rec = {
            "market_question": market.get("question", ""),
            "market_slug": market.get("slug", ""),
            "direction": direction,
            "confidence": confidence,
            "volume": market.get("volume", 0),
            "liquidity": market.get("liquidity", 0),
            "matched_keywords": market.get("matched_keywords", []),
            "stock_info": stock_info_list
        }

        recommendations[direction].append(rec)

    # 按置信度排序
    for key in recommendations:
        recommendations[key].sort(key=lambda x: x["confidence"], reverse=True)

    return recommendations


def format_output(recommendations: Dict, stock_mapping: Dict) -> str:
    """格式化输出报告"""

    lines = []
    lines.append("=" * 80)
    lines.append("                     Polymarket A股投资分析报告")
    lines.append("          基于预测市场数据的中国概念股及A股投资建议")
    lines.append("=" * 80)
    lines.append("")

    # 统计信息
    bullish_count = len(recommendations["bullish"])
    bearish_count = len(recommendations["bearish"])
    neutral_count = len(recommendations["neutral"])
    total = bullish_count + bearish_count + neutral_count

    lines.append(f"📊 分析统计: 共分析 {total} 个中国相关市场")
    lines.append(f"   🟢 看涨信号: {bullish_count} 个")
    lines.append(f"   🔴 看跌信号: {bearish_count} 个")
    lines.append(f"   ⚪ 中性信号: {neutral_count} 个")
    lines.append("")

    # 看涨信号
    if recommendations["bullish"]:
        lines.append("-" * 80)
        lines.append("🟢 看涨信号 - 建议关注")
        lines.append("-" * 80)
        lines.append("")

        for i, rec in enumerate(recommendations["bullish"][:10], 1):
            lines.append(f"{i}. 【置信度 {rec['confidence']:.0%}】")
            lines.append(f"   预测问题: {rec['market_question'][:70]}")

            if rec['stock_info']:
                for info in rec['stock_info']:
                    lines.append(f"   📈 标的: {info['name']} ({info['sector']})")
                    lines.append(f"      相关A股: {', '.join(info['a_shares'][:5])}")

            lines.append(f"   交易量: ${float(rec['volume'] or 0):,.0f}")
            lines.append("")

    # 看跌信号
    if recommendations["bearish"]:
        lines.append("-" * 80)
        lines.append("🔴 看跌信号 - 建议规避")
        lines.append("-" * 80)
        lines.append("")

        for i, rec in enumerate(recommendations["bearish"][:10], 1):
            lines.append(f"{i}. 【置信度 {rec['confidence']:.0%}】")
            lines.append(f"   预测问题: {rec['market_question'][:70]}")

            if rec['stock_info']:
                for info in rec['stock_info']:
                    lines.append(f"   📉 标的: {info['name']} ({info['sector']})")
                    lines.append(f"      相关A股: {', '.join(info['a_shares'][:5])}")

            lines.append("")

    # 综合建议
    lines.append("=" * 80)
    lines.append("📊 综合分析与操作策略")
    lines.append("=" * 80)
    lines.append("")

    if bullish_count > bearish_count:
        sentiment = "偏向乐观"
        strategy = "适度加仓，重点关注新能源汽车、AI、互联网板块"
        color = "🟢"
    elif bearish_count > bullish_count:
        sentiment = "偏向谨慎"
        strategy = "控制仓位，规避高估值板块，关注防御性板块"
        color = "🔴"
    else:
        sentiment = "中性"
        strategy = "观望为主，等待明确信号，可适当配置均衡型资产"
        color = "⚪"

    lines.append(f"{color} 市场情绪: {sentiment}")
    lines.append(f"   建议策略: {strategy}")
    lines.append("")

    # 板块推荐
    sectors = {}
    for rec in recommendations["bullish"]:
        for info in rec['stock_info']:
            sector = info['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].extend(info['a_shares'])

    if sectors:
        lines.append("🎯 重点板块推荐:")
        for i, (sector, stocks) in enumerate(sectors.items(), 1):
            unique_stocks = list(set(stocks))[:5]
            lines.append(f"   {i}. {sector}: {', '.join(unique_stocks)}")
        lines.append("")

    # 风险提示
    lines.append("⚠️ 风险提示:")
    lines.append("   • 预测市场数据反映的是群体预期，并非实际结果")
    lines.append("   • 中概股与A股存在一定的相关性，但并非完全同步")
    lines.append("   • 投资决策应结合基本面、技术面等多重因素")
    lines.append("   • 本分析仅供参考，不构成投资建议")
    lines.append("")

    lines.append("=" * 80)
    lines.append("📈 数据更新: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("📊 数据来源: Polymarket 预测市场")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 80)
    print("                    Polymarket A股分析工具")
    print("              正在初始化并获取市场数据...")
    print("=" * 80)
    print()

    # 加载股票映射
    stock_mapping = load_stock_mapping()
    print(f"✓ 已加载 {len(stock_mapping)} 个中概股映射")

    # 获取市场数据
    print("📊 正在获取 Polymarket 市场数据...")
    markets = get_all_markets()
    print(f"✓ 获取到 {len(markets)} 个活跃市场")

    # 搜索中国相关市场
    print("🔍 正在筛选与中国相关的市场...")
    china_markets = search_china_markets(markets, stock_mapping)
    print(f"✓ 找到 {len(china_markets)} 个相关市场")

    # 生成投资建议
    print("💡 正在生成投资建议...")
    recommendations = generate_recommendations(china_markets, stock_mapping)

    # 格式化输出
    report = format_output(recommendations, stock_mapping)

    print()
    print(report)

    return recommendations


if __name__ == "__main__":
    main()
