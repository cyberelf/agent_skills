#!/bin/bash

###############################################################################
# Agent Inside - Script that runs inside the Docker container
# 
# This script executes Claude Code with the assigned task and monitors
# the execution, capturing statistics and handling errors.
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment variables
TASK_DESCRIPTION="${TASK_DESCRIPTION:-}"
API_KEY="${ANTHROPIC_API_KEY:-}"
BASE_URL="${ANTHROPIC_BASE_URL:-}"
AGENT_RUN_DIR="${AGENT_RUN_DIR:-./.agent_run/local}"
WORKSPACE_DIR="/workspace"
START_TIME=$(date +%s)
TOKEN_USAGE=0
CONVERSATION_TURNS=0
FILES_MODIFIED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date -Iseconds) - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date -Iseconds) - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date -Iseconds) - $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date -Iseconds) - $1"
}

log_agent() {
    echo -e "${BLUE}[AGENT]${NC} $(date -Iseconds) - $1"
}

# Setup environment
setup_environment() {
    log_info "Setting up agent environment..."
    
    # Verify API key
    if [ -z "$API_KEY" ]; then
        log_error "ANTHROPIC_API_KEY not set in environment"
        exit 1
    fi
    
    # Verify workspace
    if [ ! -d "$WORKSPACE_DIR" ]; then
        log_error "Workspace directory $WORKSPACE_DIR not found"
        exit 1
    fi
    
    # Change to workspace directory
    cd "$WORKSPACE_DIR"
    log_info "Working directory: $(pwd)"
    
    # Configure git
    if command -v git &> /dev/null; then
        git config --global user.email "agent@worker.local" 2>/dev/null || true
        git config --global user.name "Agent Worker" 2>/dev/null || true
        log_success "Git configuration set"
    else
        log_warning "Git not found in container"
    fi
}

# Create task file
create_task_file() {
    log_info "Creating task description file..."
    
    # Ensure agent run directory exists
    mkdir -p "$AGENT_RUN_DIR"
    
    TASK_FILE="$AGENT_RUN_DIR/task.md"
    
    cat > "$TASK_FILE" << EOF
# Agent Task Assignment

## Task Description
$TASK_DESCRIPTION

## Instructions
- Complete the task described above
- Make necessary code changes
- Test your changes if possible
- Commit your work with descriptive messages
- Ensure code quality and follow best practices

## Notes
- You have full access to the workspace
- All changes will be tracked via git
- Use appropriate tools and commands as needed

---
Task assigned: $(date -Iseconds)
EOF
    
    log_success "Task file created: $TASK_FILE"
    echo "$TASK_FILE"
}

# Execute Claude Code
execute_claude_code() {
    log_agent "Starting Claude Code agent..."
    log_agent "Task: $TASK_DESCRIPTION"
    
    TASK_FILE=$(create_task_file)
    
    # Prepare the initial prompt
    PROMPT="I have a task for you. Please read the task description from $TASK_FILE and complete it.

Task summary: $TASK_DESCRIPTION

Please:
1. Analyze the codebase
2. Implement the required changes
3. Test if applicable
4. Commit your changes with clear messages

Work autonomously until the task is complete. When done, provide a summary of what you've accomplished."
    
    # Execute Claude Code
    log_agent "Executing Claude Code in non-interactive mode..."
    
    # Create output file in the run directory
    OUTPUT_FILE="$AGENT_RUN_DIR/claude-output.log"
    
    # Set timeout (default 1 hour)
    TIMEOUT="${AGENT_TIMEOUT:-3600}"
    
    # Run Claude Code with timeout
    if timeout "$TIMEOUT" claude --dangerously-skip-permissions "$PROMPT" 2>&1 | tee "$OUTPUT_FILE"; then
        EXIT_CODE=0
        log_success "Claude Code execution completed"
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            log_error "Claude Code execution timed out after ${TIMEOUT}s"
        else
            log_error "Claude Code execution failed with exit code $EXIT_CODE"
        fi
    fi
    
    # Parse output for statistics
    if [ -f "$OUTPUT_FILE" ]; then
        # Count conversation turns (approximate)
        CONVERSATION_TURNS=$(grep -ic "assistant:\|claude:" "$OUTPUT_FILE" 2>/dev/null || echo "0")
        
        # Extract token usage if reported
        TOKEN_LINE=$(grep -i "tokens" "$OUTPUT_FILE" | tail -1 || echo "")
        if [ -n "$TOKEN_LINE" ]; then
            TOKEN_USAGE=$(echo "$TOKEN_LINE" | grep -oP '\d+' | head -1 || echo "0")
        fi
    fi
    
    return $EXIT_CODE
}

# Collect statistics
collect_stats() {
    log_info "Collecting execution statistics..."
    
    cd "$WORKSPACE_DIR"
    
    # Count modified files
    if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
        FILES_MODIFIED=$(git diff --name-only HEAD 2>/dev/null | wc -l)
        
        # Get git statistics
        GIT_STAT=$(git diff --shortstat HEAD 2>/dev/null || echo "")
        if [ -n "$GIT_STAT" ]; then
            log_info "Git changes: $GIT_STAT"
        fi
    else
        log_warning "Not in a git repository, skipping git statistics"
    fi
    
    log_success "Statistics collected"
}

# Print summary
print_summary() {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    echo ""
    echo "========================================================================"
    echo "AGENT EXECUTION SUMMARY"
    echo "========================================================================"
    printf "Duration:           %dm %ds\n" "$MINUTES" "$SECONDS"
    printf "Token Usage:        %s\n" "${TOKEN_USAGE:-N/A}"
    printf "Conversation Turns: %d\n" "$CONVERSATION_TURNS"
    printf "Files Modified:     %d\n" "$FILES_MODIFIED"
    echo "========================================================================"
    echo ""
}

# Main execution
main() {
    log_info "Agent Executor starting..."
    
    # Setup environment
    setup_environment
    
    # Execute Claude Code
    if execute_claude_code; then
        FINAL_EXIT_CODE=0
    else
        FINAL_EXIT_CODE=$?
    fi
    
    # Collect statistics
    collect_stats
    
    # Print summary
    print_summary
    
    if [ $FINAL_EXIT_CODE -eq 0 ]; then
        log_success "Agent execution completed successfully!"
    else
        log_error "Agent execution completed with errors (exit code: $FINAL_EXIT_CODE)"
    fi
    
    exit $FINAL_EXIT_CODE
}

# Run main function
main "$@"
