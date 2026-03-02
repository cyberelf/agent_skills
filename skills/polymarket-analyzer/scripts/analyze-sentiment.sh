#!/bin/bash
#
# Analyze market sentiment and extract actionable insights
# Usage: ./analyze-sentiment.sh <topic> [detail-level]
#
# Arguments:
#   topic        - Topic to analyze (e.g., "china", "taiwan", "byd")
#   detail-level - Output detail: "summary" or "detailed" (default: summary)
#
# Examples:
#   ./analyze-sentiment.sh china
#   ./analyze-sentiment.sh taiwan detailed
#   ./analyze-sentiment.sh compare china,taiwan

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
DEFAULT_DETAIL="summary"

# Check dependencies
check_dependencies() {
    if ! command -v polymarket &> /dev/null; then
        echo "Error: polymarket CLI not found." >&2
        exit 1
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $(basename "$0") <topic> [detail-level]

Analyze market sentiment and extract actionable insights.

Arguments:
  topic        Topic to analyze (e.g., "china", "taiwan", "byd")
  detail-level Output detail: "summary" or "detailed" (default: summary)

Examples:
  $(basename "$0") china
  $(basename "$0") taiwan detailed
  $(basename "$0") compare china,taiwan

EOF
}

# Analyze sentiment for a single topic
analyze_topic() {
    local topic="$1"
    local detail="$2"

    echo "Analyzing sentiment for: $topic"
    echo ""

    # Fetch markets
    local markets
    if ! markets=$(polymarket -o json markets search "$topic" --limit 50 2>/dev/null); then
        echo "Error: Failed to fetch markets for '$topic'" >&2
        return 1
    fi

    # Check if we got any results
    local count
    count=$(echo "$markets" | jq 'length')
    if [[ "$count" -eq 0 ]]; then
        echo "No markets found for: $topic"
        return 0
    fi

    echo "Found $count markets for '$topic'"
    echo ""

    # Calculate average probability (approximate from yes prices)
    local avg_prob
    avg_prob=$(echo "$markets" | jq -r '
        [.[] | select(.outcomePrices[0] != null) | (.outcomePrices[0] | tonumber)]
        | if length > 0 then (add / length) * 100 else 0 end
    ')

    # Calculate total volume
    local total_volume
    total_volume=$(echo "$markets" | jq -r '[.[].volume // 0] | add')

    # Determine sentiment
    local sentiment="neutral"
    if (( $(echo "$avg_prob > 60" | bc -l 2>/dev/null || echo "0") )); then
        sentiment="bullish"
    elif (( $(echo "$avg_prob < 40" | bc -l 2>/dev/null || echo "0") )); then
        sentiment="bearish"
    fi

    # Output summary
    echo "=== Sentiment Analysis for: $topic ==="
    echo ""
    echo "Overall Sentiment: $sentiment"
    echo "Average Probability: ${avg_prob}%"
    echo "Total Volume: \$$(echo "$total_volume" | awk '{printf "%.0f", $1}')"
    echo "Markets Analyzed: $count"
    echo ""

    # Detailed output if requested
    if [[ "$detail" == "detailed" ]]; then
        echo "=== Top Markets by Volume ==="
        echo ""
        echo "$markets" | jq -r '
            sort_by(.volume | tonumber) | reverse | .[:10] |
            .[] | "Question: \(.question[:80])\n  Price: \(.outcomePrices[0] // "N/A") | Volume: \(.volume // 0) | Status: \(.active // false)\n"
        '
        echo ""
    fi

    return 0
}

# Compare multiple topics
compare_topics() {
    local topics_str="$1"

    echo "Comparing topics: $topics_str"
    echo ""

    IFS=',' read -ra TOPICS <<< "$topics_str"

    printf "%-20s %-15s %-15s %-20s\n" "Topic" "Sentiment" "Avg Prob" "Total Volume"
    printf "%-20s %-15s %-15s %-20s\n" "--------------------" "---------------" "---------------" "--------------------"

    for topic in "${TOPICS[@]}"; do
        topic=$(echo "$topic" | xargs)  # trim

        local markets
        if markets=$(polymarket -o json markets search "$topic" --limit 30 2>/dev/null); then
            local avg_prob
            avg_prob=$(echo "$markets" | jq -r '[.[].outcomePrices[0] // empty | tonumber] | if length > 0 then (add / length) * 100 else 0 end')

            local total_volume
            total_volume=$(echo "$markets" | jq -r '[.[].volume // 0] | add')

            local sentiment="neutral"
            if (( $(echo "$avg_prob > 60" | bc -l 2>/dev/null || echo "0") )); then
                sentiment="bullish"
            elif (( $(echo "$avg_prob < 40" | bc -l 2>/dev/null || echo "0") )); then
                sentiment="bearish"
            fi

            printf "%-20s %-15s %-15.1f %-20.0f\n" "$topic" "$sentiment" "$avg_prob" "$total_volume"
        fi
    done
}

# Main function
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    # Check for help
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        usage
        exit 0
    fi

    check_dependencies

    local topic="$1"
    local detail="${2:-$DEFAULT_DETAIL}"

    if [[ "$topic" == compare:* ]]; then
        # Compare mode
        local topics_str="${topic#compare:}"
        compare_topics "$topics_str"
    else
        # Single topic analysis
        analyze_topic "$topic" "$detail"
    fi
}

# Run main
main "$@"
