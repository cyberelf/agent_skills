#!/bin/bash

###############################################################################
# Agent Worker - Containerized Coding Agent Orchestrator
# 
# This tool creates isolated Docker containers with Claude Code agents,
# sets up git branches, and executes development tasks autonomously.
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RUN_ID="run-$(date +%s)"
PROJECT_PATH="${PWD}"
BRANCH_NAME="agent-task-$(date +%s)"
TASK_DESCRIPTION=""
API_KEY="${ANTHROPIC_API_KEY}"
BASE_URL="${ANTHROPIC_BASE_URL}"
CONTAINER_NAME="agent-worker-$(date +%s)"
TIMEZONE="${TZ:-UTC}"
RUN_DIR=""  # Will be set in validate_prerequisites
STATS_FILE=""  # Will be set when RUN_DIR is created

# Statistics
START_TIME=""
END_TIME=""
TOKEN_USAGE=0
LOC_ADDED=0
LOC_REMOVED=0
FILES_CHANGED=0
EXIT_CODE=0

# Logging functions
log_info() {
    echo -e "${BLUE}📋 [$(date -Iseconds)]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ [$(date -Iseconds)]${NC} $1"
}

log_error() {
    echo -e "${RED}❌ [$(date -Iseconds)]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠️  [$(date -Iseconds)]${NC} $1"
}

log_agent() {
    echo -e "${BLUE}🤖 [$(date -Iseconds)]${NC} $1"
}

log_git() {
    echo -e "${GREEN}🌿 [$(date -Iseconds)]${NC} $1"
}

log_docker() {
    echo -e "${BLUE}🐳 [$(date -Iseconds)]${NC} $1"
}

# Usage information
show_help() {
    cat << EOF
Agent Worker - Containerized Coding Agent Orchestrator

Usage: ./agent_worker.sh [options]

Options:
  --project <path>        Path to project directory (default: current directory)
  --branch <name>         Name for the new git branch (default: agent-task-<timestamp>)
  --task <description>    Task description for the agent (required)
  --api-key <key>         Anthropic API key (or set ANTHROPIC_API_KEY env var)
  --base-url <url>        Base URL for Claude API (or set ANTHROPIC_BASE_URL env var)
  --timezone <tz>         Timezone for container (default: system timezone)
  --help, -h              Show this help message

Example:
  ./agent_worker.sh --task "Fix all TypeScript errors in src/ directory" --branch fix-ts-errors

Environment Variables:
  ANTHROPIC_API_KEY       API key for Claude Code
  ANTHROPIC_BASE_URL      Base URL for Claude API (optional, for custom endpoints)
  TZ                      Timezone setting
EOF
    exit 0
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project)
                PROJECT_PATH="$(realpath "$2")"
                shift 2
                ;;
            --branch)
                BRANCH_NAME="$2"
                shift 2
                ;;
            --task)
                TASK_DESCRIPTION="$2"
                shift 2
                ;;
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --base-url)
                BASE_URL="$2"
                shift 2
                ;;
            --timezone)
                TIMEZONE="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# Initialize run directory
init_run_dir() {
    RUN_DIR="$PROJECT_PATH/.agent_run/$RUN_ID"
    mkdir -p "$RUN_DIR"
    STATS_FILE="$RUN_DIR/stats.json"
    log_info "Run directory: $RUN_DIR"
}

# Find git repository root
find_git_root() {
    local current_path="$1"
    
    # Use git to find the repository root
    if git -C "$current_path" rev-parse --git-dir &> /dev/null; then
        git -C "$current_path" rev-parse --show-toplevel
        return 0
    fi
    
    return 1
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed or not in PATH"
        exit 1
    fi

    # Check API key
    if [ -z "$API_KEY" ]; then
        log_error "ANTHROPIC_API_KEY not set. Please provide API key via --api-key or environment variable."
        exit 1
    fi

    # Check project directory
    if [ ! -d "$PROJECT_PATH" ]; then
        log_error "Project directory does not exist: $PROJECT_PATH"
        exit 1
    fi

    # Find git repository root and use it as the mounted workspace
    if ! GIT_ROOT=$(find_git_root "$PROJECT_PATH"); then
        log_error "Project directory is not a git repository: $PROJECT_PATH"
        exit 1
    fi
    
    # Update PROJECT_PATH to the git root for proper mounting
    PROJECT_PATH="$GIT_ROOT"
    log_info "Using git repository root: $PROJECT_PATH"
    
    # Initialize run directory
    init_run_dir

    # Check task description
    if [ -z "$TASK_DESCRIPTION" ]; then
        log_error "Task description is required. Use --task option."
        exit 1
    fi

    log_success "Prerequisites validated"
}

# Create git branch
create_branch() {
    log_git "Creating new branch: $BRANCH_NAME"
    
    cd "$PROJECT_PATH"
    
    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log_git "Current branch: $CURRENT_BRANCH"
    
    # Create and checkout new branch
    if git checkout -b "$BRANCH_NAME" 2>/dev/null; then
        log_success "Branch $BRANCH_NAME created successfully"
    else
        log_error "Failed to create branch $BRANCH_NAME"
        exit 1
    fi
}

# Build Docker image
build_docker_image() {
    log_docker "Building Docker image..."
    
    DOCKERFILE_BASE="$PROJECT_PATH/agent_worker"
    DOCKERFILE_PATH="$DOCKERFILE_BASE/Dockerfile"
    
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        log_error "Dockerfile not found at: $DOCKERFILE_PATH"
        exit 1
    fi
    
    if docker build \
        --build-arg TZ="$TIMEZONE" \
        --build-arg CLAUDE_CODE_VERSION=latest \
        -t agent-worker:latest \
        -f "$DOCKERFILE_PATH" \
        "$DOCKERFILE_BASE" > "$RUN_DIR/docker-build.log" 2>&1; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed. See $RUN_DIR/docker-build.log for details"
        cat "$RUN_DIR/docker-build.log"
        exit 1
    fi
}

# Create and start container
create_container() {
    log_docker "Creating Docker container: $CONTAINER_NAME"
    
    # Create volume for command history if it doesn't exist
    docker volume create agent-worker-commandhistory &> /dev/null || true
    
    # Create container
    if docker run -d \
        --name "$CONTAINER_NAME" \
        -e ANTHROPIC_API_KEY="$API_KEY" \
        -e ANTHROPIC_BASE_URL="$BASE_URL" \
        -e TZ="$TIMEZONE" \
        -e TASK_DESCRIPTION="$TASK_DESCRIPTION" \
        -v "$PROJECT_PATH:/workspace:rw" \
        -v agent-worker-commandhistory:/commandhistory:rw \
        -w /workspace \
        agent-worker:latest \
        tail -f /dev/null > /dev/null; then
        log_success "Container $CONTAINER_NAME started"
    else
        log_error "Failed to create container"
        exit 1
    fi
}

# Copy agent script to container
copy_agent_script() {
    log_docker "Copying agent script to container..."
    
    AGENT_SCRIPT="$DOCKERFILE_BASE/agent_inside.sh"
    
    if [ ! -f "$AGENT_SCRIPT" ]; then
        log_error "Agent script not found: $AGENT_SCRIPT"
        cleanup_container
        exit 1
    fi
    
    if docker cp "$AGENT_SCRIPT" "$CONTAINER_NAME:/workspace/agent_inside.sh"; then
        docker exec "$CONTAINER_NAME" chmod +x /workspace/agent_inside.sh
        log_success "Agent script copied successfully"
    else
        log_error "Failed to copy agent script"
        cleanup_container
        exit 1
    fi
}

# Execute agent in container
execute_agent() {
    log_agent "Starting agent execution..."
    log_agent "Task: $TASK_DESCRIPTION"
    
    START_TIME=$(date +%s)
    
    # Execute agent and capture output
    if docker exec \
        -e TASK_DESCRIPTION="$TASK_DESCRIPTION" \
        -e ANTHROPIC_API_KEY="$API_KEY" \
        -e ANTHROPIC_BASE_URL="$BASE_URL" \
        -e AGENT_RUN_DIR="/workspace/.agent_run/$RUN_ID" \
        "$CONTAINER_NAME" \
        /workspace/agent_inside.sh | tee "$RUN_DIR/agent-output.log"; then
        EXIT_CODE=0
        log_success "Agent execution completed successfully"
    else
        EXIT_CODE=$?
        log_error "Agent execution failed with exit code $EXIT_CODE"
    fi
    
    END_TIME=$(date +%s)
    
    # Parse output for token usage
    if grep -q "tokens" "$RUN_DIR/agent-output.log"; then
        TOKEN_USAGE=$(grep -oP '\d+(?=\s+tokens)' "$RUN_DIR/agent-output.log" | tail -1 || echo "0")
    fi
}

# Collect git statistics
collect_git_stats() {
    log_git "Collecting git statistics..."
    
    cd "$PROJECT_PATH"
    
    # Get changed files count
    FILES_CHANGED=$(git diff --name-only HEAD 2>/dev/null | wc -l)
    
    # Get LOC changes
    if git diff --shortstat HEAD &> /dev/null; then
        DIFF_STAT=$(git diff --shortstat HEAD 2>/dev/null)
        LOC_ADDED=$(echo "$DIFF_STAT" | grep -oP '\d+(?= insertion)' || echo "0")
        LOC_REMOVED=$(echo "$DIFF_STAT" | grep -oP '\d+(?= deletion)' || echo "0")
    fi
    
    log_success "Git statistics collected"
}

# Print statistics
print_statistics() {
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║               AGENT EXECUTION REPORT                      ║"
    echo "╠═══════════════════════════════════════════════════════════╣"
    printf "║ Branch:           %-38s ║\n" "$BRANCH_NAME"
    printf "║ Duration:         %-38s ║\n" "${MINUTES}m ${SECONDS}s"
    printf "║ Exit Code:        %-38s ║\n" "$EXIT_CODE"
    echo "╠═══════════════════════════════════════════════════════════╣"
    echo "║ TOKEN USAGE                                               ║"
    printf "║   Total:          %-38s ║\n" "$TOKEN_USAGE"
    echo "╠═══════════════════════════════════════════════════════════╣"
    echo "║ CODE CHANGES                                              ║"
    printf "║   Lines Added:    %-38s ║\n" "$LOC_ADDED"
    printf "║   Lines Removed:  %-38s ║\n" "$LOC_REMOVED"
    printf "║   Files Changed:  %-38s ║\n" "$FILES_CHANGED"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    
    # Show changed files
    if [ "$FILES_CHANGED" -gt 0 ]; then
        echo "Changed files:"
        cd "$PROJECT_PATH"
        git diff --name-status HEAD 2>/dev/null | while read -r status file; do
            case $status in
                M) echo "  📝 $file" ;;
                A) echo "  ➕ $file" ;;
                D) echo "  ➖ $file" ;;
                *) echo "  ❓ $file" ;;
            esac
        done
        echo ""
    fi
}

# Cleanup container
cleanup_container() {
    log_docker "Cleaning up container..."
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker stop "$CONTAINER_NAME" &> /dev/null || true
        docker rm "$CONTAINER_NAME" &> /dev/null || true
        log_success "Container removed"
    fi
    
    # Save run information
    if [ -n "$RUN_DIR" ] && [ -d "$RUN_DIR" ]; then
        cat > "$RUN_DIR/run-info.json" << EOF
{
  "run_id": "$RUN_ID",
  "timestamp": "$(date -Iseconds)",
  "task": "$TASK_DESCRIPTION",
  "branch": "$BRANCH_NAME",
  "exit_code": $EXIT_CODE
}
EOF
        log_info "Run information saved to: $RUN_DIR/run-info.json"
    fi
}

# Main execution
main() {
    # Set up cleanup trap
    trap cleanup_container EXIT INT TERM
    
    log_info "Starting Agent Worker..."
    
    # Parse arguments
    parse_args "$@"
    
    # Validate
    validate_prerequisites
    
    log_info "Project: $PROJECT_PATH"
    log_info "Task: $TASK_DESCRIPTION"
    
    # Create branch
    create_branch
    
    # Build Docker image
    build_docker_image
    
    # Create container
    create_container
    
    # Copy agent script
    copy_agent_script
    
    # Execute agent
    execute_agent
    
    # Collect statistics
    collect_git_stats
    
    # Print report
    print_statistics
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Agent worker completed successfully!"
    else
        log_error "Agent worker completed with errors"
        exit $EXIT_CODE
    fi
}

# Run main function
main "$@"
