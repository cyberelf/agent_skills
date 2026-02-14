#!/bin/bash
# Check status and validate completion of a Claude Code task
# Usage: ./check-completion.sh <change-name>

CHANGE_NAME="${1:?Change name required}"
OUTPUT_FILE="${CHANGE_NAME}.jsonl"
PID_FILE=".claude_${CHANGE_NAME}.pid"
TASKS_FILE="openspec/changes/${CHANGE_NAME}/tasks.md"

echo "🔍 Checking completion: $CHANGE_NAME"
echo ""

# Check process status
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    echo "⏳ Still running (PID: $PID)"
    echo "   Use: ./monitor.sh $CHANGE_NAME"
    exit 0
  else
    echo "✓ Process completed (PID: $PID)"
  fi
else
  echo "ℹ️  No PID file found"
fi

echo ""

# Check exit code from output file
if [ -f "$OUTPUT_FILE" ]; then
  FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
  echo "📄 Output file: $OUTPUT_FILE ($FILE_SIZE bytes)"
  
  # Look for completion indicators
  if grep -q "verify.*complete\|verified.*success" "$OUTPUT_FILE" 2>/dev/null; then
    echo "✅ Verification completed successfully"
  fi
  
  # Check for errors
  ERROR_COUNT=$(grep -ci error "$OUTPUT_FILE" 2>/dev/null || echo 0)
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  $ERROR_COUNT error(s) found in output"
    echo "   Review: grep -i error $OUTPUT_FILE"
  fi
fi

echo ""

# Check OpenSpec artifacts
if [ -d "openspec/changes/${CHANGE_NAME}" ]; then
  echo "📁 OpenSpec artifacts:"
  ls -lh "openspec/changes/${CHANGE_NAME}/" | tail -n +2
  
  echo ""
  
  if [ -f "$TASKS_FILE" ]; then
    echo "✅ Task Status:"
    TOTAL=$(grep -E '^\s*-\s*\[[ x]\]' "$TASKS_FILE" | wc -l)
    DONE=$(grep -E '^\s*-\s*\[x\]' "$TASKS_FILE" | wc -l)
    PERCENT=$((DONE * 100 / TOTAL))
    echo "   $DONE / $TOTAL tasks completed ($PERCENT%)"
    
    if [ "$DONE" -eq "$TOTAL" ]; then
      echo "   ✓ All tasks complete!"
    else
      echo ""
      echo "   Incomplete tasks:"
      grep -E '^\s*-\s*\[ \]' "$TASKS_FILE" | head -n 5
    fi
  fi
else
  echo "❌ No OpenSpec artifacts found"
  echo "   Expected: openspec/changes/${CHANGE_NAME}/"
fi

echo ""

# Final status
if [ -f "$TASKS_FILE" ]; then
  TOTAL=$(grep -E '^\s*-\s*\[[ x]\]' "$TASKS_FILE" | wc -l)
  DONE=$(grep -E '^\s*-\s*\[x\]' "$TASKS_FILE" | wc -l)
  
  if [ "$DONE" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
    echo "✅ Ready for archive: claude -p --dangerously-skip-permissions \"/opsx:archive $CHANGE_NAME\""
  else
    echo "⏸️  Not ready for archive (incomplete tasks)"
  fi
fi
