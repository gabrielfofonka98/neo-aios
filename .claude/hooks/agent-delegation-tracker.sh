#!/bin/bash
# =============================================================================
# NEO-AIOS: Agent Delegation Tracker
# =============================================================================
# This hook runs when a subagent is spawned (SubagentStart).
# Use it to track delegation chains and enforce hierarchy rules.
#
# Hook Event: SubagentStart
# Output: stdout is logged for delegation tracking
# =============================================================================

set -e

# Read hook input from stdin
INPUT=$(cat)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.aios/session-state.json"
DELEGATION_LOG="$PROJECT_DIR/.aios/delegation-log.jsonl"

# Create .aios directory if needed
mkdir -p "$PROJECT_DIR/.aios"

# Get parent agent
PARENT_AGENT="default"
if [ -f "$STATE_FILE" ]; then
  PARENT_AGENT=$(jq -r '.activeAgent // "default"' "$STATE_FILE" 2>/dev/null)
  [ "$PARENT_AGENT" = "null" ] && PARENT_AGENT="default"
fi

# Extract subagent info
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.subagent_type // "unknown"')
DESCRIPTION=$(echo "$INPUT" | jq -r '.description // ""')

# Log delegation
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "{\"timestamp\":\"$TIMESTAMP\",\"parent\":\"$PARENT_AGENT\",\"subagent\":\"$SUBAGENT_TYPE\",\"description\":\"$DESCRIPTION\"}" >> "$DELEGATION_LOG"

# Output for context (optional - helps with debugging)
# echo "[Delegation: @$PARENT_AGENT → $SUBAGENT_TYPE]"

exit 0
