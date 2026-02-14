#!/bin/bash
# Monitor a running Claude Code background process
# Usage: ./monitor.sh <change-name> [lines]

CHANGE_NAME="${1:?Change name required}"
LINES="${2:-20}"
OUTPUT_FILE="${CHANGE_NAME}.jsonl"
PID_FILE=".claude_${CHANGE_NAME}.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "❌ No PID file found: $PID_FILE"
  echo "   Change '$CHANGE_NAME' may not be running"
  exit 1
fi

PID=$(cat "$PID_FILE")

echo "📊 Monitoring: $CHANGE_NAME"
echo "   PID: $PID"
echo ""

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
  ELAPSED=$(ps -p "$PID" -o etime= | tr -d ' ')
  echo "✓ Running (elapsed: $ELAPSED)"
else
  echo "✗ Process stopped"
fi

echo ""
echo "📝 Recent output (last $LINES lines):"
echo "----------------------------------------"
tail -n "$LINES" "$OUTPUT_FILE" 2>/dev/null || echo "(no output file)"
echo "----------------------------------------"

# Show any errors
ERROR_COUNT=$(grep -i error "$OUTPUT_FILE" 2>/dev/null | wc -l || echo 0)
if [ "$ERROR_COUNT" -gt 0 ]; then
  echo ""
  echo "⚠️  Found $ERROR_COUNT error(s):"
  grep -i error "$OUTPUT_FILE" | tail -n 5
fi

# Show task progress if available
TASKS_FILE="openspec/changes/${CHANGE_NAME}/tasks.md"
if [ -f "$TASKS_FILE" ]; then
  echo ""
  echo "✅ Task Progress:"
  TOTAL=$(grep -E '^\s*-\s*\[[ x]\]' "$TASKS_FILE" | wc -l)
  DONE=$(grep -E '^\s*-\s*\[x\]' "$TASKS_FILE" | wc -l)
  echo "   $DONE / $TOTAL tasks completed"
fi
