#!/bin/bash
#
# Advanced filtering of Polymarket markets with multiple criteria
# Usage: ./filter-markets.sh [options]
#
# Options:
#   keywords:<word1,word2,...>  - Comma-separated keywords to match (default: china,taiwan,byd,nio)
#   volume:<number>             - Minimum volume threshold (default: 50000)
#   status:<active|closed>      - Market status filter (default: active)
#   limit:<number>              - Maximum results (default: 100)
#   output:<table|json>         - Output format (default: table)
#
# Examples:
#   ./filter-markets.sh keywords:taiwan,war,invasion volume:100000
#   ./filter-markets.sh keywords:byd,nio,xpeng,li\ auto limit:50
#   ./filter-markets.sh status:closed output:json

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
DEFAULT_KEYWORDS="china,taiwan,byd,nio,alibaba,tencent"
DEFAULT_MIN_VOLUME=50000
DEFAULT_STATUS="active"
DEFAULT_LIMIT=100
DEFAULT_OUTPUT="table"

# Check dependencies
check_dependencies() {
    if ! command -v polymarket &> /dev/null; then
        echo "Error: polymarket CLI not found. Please install it first." >&2
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        echo "Warning: jq not found. JSON filtering will be limited." >&2
    fi
}

# Parse arguments
parse_args() {
    KEYWORDS="$DEFAULT_KEYWORDS"
    MIN_VOLUME="$DEFAULT_MIN_VOLUME"
    STATUS="$DEFAULT_STATUS"
    LIMIT="$DEFAULT_LIMIT"
    OUTPUT="$DEFAULT_OUTPUT"

    for arg in "$@"; do
        case "$arg" in
            keywords:*)
                KEYWORDS="${arg#keywords:}"
                ;;
            volume:*)
                MIN_VOLUME="${arg#volume:}"
                ;;
            status:*)
                STATUS="${arg#status:}"
                ;;
            limit:*)
                LIMIT="${arg#limit:}"
                ;;
            output:*)
                OUTPUT="${arg#output:}"
                ;;
            *)
                echo "Warning: Unknown argument '$arg'" >&2
                ;;
        esac
    done
}

# Show usage
usage() {
    cat << EOF
Usage: $(basename "$0") [options]

Filter Polymarket markets with multiple criteria.

Options:
  keywords:<word1,word2,...>  Comma-separated keywords (default: $DEFAULT_KEYWORDS)
  volume:<number>            Minimum volume threshold (default: $DEFAULT_MIN_VOLUME)
  status:<active|closed>     Market status (default: $DEFAULT_STATUS)
  limit:<number>             Maximum results (default: $DEFAULT_LIMIT)
  output:<table|json>        Output format (default: $DEFAULT_OUTPUT)

Examples:
  $(basename "$0") keywords:taiwan,war,invasion volume:100000
  $(basename "$0") keywords:byd,nio,xpeng,li\ auto limit:50
  $(basename "$0") status:closed output:json
EOF
}

# Fetch and filter markets
fetch_and_filter() {
    local keywords="$1"
    local min_volume="$2"
    local status="$3"
    local limit="$4"
    local output="$5"

    echo "Filtering markets..." >&2
    echo "  Keywords: $keywords" >&2
    echo "  Min Volume: $min_volume" >&2
    echo "  Status: $status" >&2
    echo "  Limit: $limit" >&2
    echo "" >&2

    # Split keywords and fetch markets for each
    local all_markets="[]"
    IFS=',' read -ra KEYWORD_ARRAY <<< "$keywords"

    for keyword in "${KEYWORD_ARRAY[@]}"; do
        keyword=$(echo "$keyword" | xargs)  # trim whitespace
        echo "Searching for: '$keyword'..." >&2

        local result
        if result=$(polymarket -o json markets search "$keyword" --limit "$limit" 2>/dev/null); then
            if command -v jq &> /dev/null; then
                all_markets=$(echo "$all_markets" "$result" | jq -s 'add | unique_by(.conditionId // .slug // .question)')
            else
                all_markets="$result"
            fi
        fi
    done

    # Filter by volume and status if jq is available
    if command -v jq &> /dev/null; then
        local filtered
        filtered=$(echo "$all_markets" | jq --arg minvol "$min_volume" --arg status "$status" '
            [.[] | select(
                ((.volume // "0") | tonumber) >= ($minvol | tonumber) and
                (.active == true or $status == "all")
            )]
        ')
        all_markets="$filtered"
    fi

    # Output results
    if [[ "$output" == "json" ]]; then
        echo "$all_markets"
    else
        # Convert to table format
        if command -v jq &> /dev/null; then
            echo "$all_markets" | jq -r '
                ["Question", "Price (Yes)", "Volume", "Liquidity", "Status"],
                (.[] | [
                    (.question // "N/A")[:60],
                    .outcomePrices[0] // "N/A",
                    (.volume // "0"),
                    (.liquidity // "0"),
                    (if .active == true then "Active" else "Closed" end)
                ])
                | @tsv
            ' | column -t -s $'\t'
        else
            echo "$all_markets"
        fi
    fi
}

# Main function
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 0
    fi

    # Check for help
    for arg in "$@"; do
        if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
            usage
            exit 0
        fi
    done

    check_dependencies
    parse_args "$@"

    fetch_and_filter "$KEYWORDS" "$MIN_VOLUME" "$STATUS" "$LIMIT" "$OUTPUT"
}

# Run main
main "$@"
