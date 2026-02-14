#!/bin/bash
# Delegate to Claude Code in background with proper monitoring setup
# Usage: ./delegate.sh <change-name> <max-turns> <workspace-path>

set -e

CHANGE_NAME="${1:?Change name required}"
MAX_TURNS="${2:-50}"
WORKSPACE="${3:-.}"
OUTPUT_FILE="${CHANGE_NAME}.jsonl"

cd "$WORKSPACE"

echo "🔧 Starting Claude Code for: $CHANGE_NAME"
echo "   Max turns: $MAX_TURNS"
echo "   Workspace: $(pwd)"
echo "   Output: $OUTPUT_FILE"
echo ""

# Start Claude Code in background
claude -p \
  --dangerously-skip-permissions \
  --max-turns "$MAX_TURNS" \
  --output-format stream-json \
  --verbose \
  "Use /opsx:new $CHANGE_NAME with requirements from requirements.md. Then /opsx:ff to generate all planning artifacts, then /opsx:apply to implement all tasks, then /opsx:verify to validate. Ensure all tasks complete." \
  > "$OUTPUT_FILE" 2>&1 &

PID=$!
echo "🚀 Started Claude Code (PID: $PID)"
echo "   Monitor: tail -f $OUTPUT_FILE"
echo "   Status: ps -p $PID"
echo "   Kill: kill $PID"
echo ""
echo "PID saved to: .claude_${CHANGE_NAME}.pid"
echo "$PID" > ".claude_${CHANGE_NAME}.pid"

# Show initial output
sleep 2
echo "📝 Initial output:"
tail -n 10 "$OUTPUT_FILE" || echo "   (no output yet)"
