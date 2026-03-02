#!/bin/bash
#
# Query Polymarket markets matching specific criteria
# Usage: ./query-markets.sh <search-term> [limit] [output-format]
#   search-term: Keywords to search for (required)
#   limit: Maximum number of results (default: 50)
#   output-format: "table" or "json" (default: table)
#
# Examples:
#   ./query-markets.sh "china" 100
#   ./query-markets.sh "taiwan" 50 json
#   ./query-markets.sh "byd" 30

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Check dependencies
check_dependencies() {
    if ! command -v polymarket &> /dev/null; then
        echo "Error: polymarket CLI not found. Please install it first." >&2
        echo "See: https://github.com/Polymarket/polymarket-cli" >&2
        exit 1
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $(basename "$0") <search-term> [limit] [output-format]

Query Polymarket markets matching specific criteria.

Arguments:
  search-term     Keywords to search for (required)
  limit          Maximum number of results (default: 50)
  output-format  "table" or "json" (default: table)

Examples:
  $(basename "$0") "china" 100
  $(basename "$0") "taiwan" 50 json
  $(basename "$0") "byd" 30
EOF
}

# Main function
main() {
    check_dependencies

    # Parse arguments
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local search_term="$1"
    local limit="${2:-50}"
    local output_format="${3:-table}"

    # Validate output format
    if [[ "$output_format" != "table" && "$output_format" != "json" ]]; then
        echo "Error: output-format must be 'table' or 'json'" >&2
        exit 1
    fi

    echo "Searching Polymarket for: '$search_term' (limit: $limit)" >&2

    # Execute search
    if [[ "$output_format" == "json" ]]; then
        polymarket -o json markets search "$search_term" --limit "$limit"
    else
        polymarket markets search "$search_term" --limit "$limit"
    fi
}

# Run main
main "$@"
