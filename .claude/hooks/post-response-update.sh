#!/bin/bash
# =============================================================================
# NEO-AIOS: Post-Response State Update
# =============================================================================
# This hook runs AFTER Claude finishes each response.
# Use it to update session state, log activity, or trigger side effects.
#
# Hook Event: Stop
# Output: Not injected (runs silently)
# =============================================================================

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.aios/session-state.json"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Read current agent
AGENT=$(jq -r '.activeAgent // empty' "$STATE_FILE" 2>/dev/null)

# If no active agent, nothing to update
if [ -z "$AGENT" ] || [ "$AGENT" = "null" ]; then
  exit 0
fi

# Update lastActivity timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Use jq to update the file in place
jq --arg ts "$TIMESTAMP" '.lastActivity = $ts' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"

exit 0
