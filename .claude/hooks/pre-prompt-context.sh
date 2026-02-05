#!/bin/bash
# =============================================================================
# NEO-AIOS: Pre-Prompt Context Injection
# =============================================================================
# This hook runs BEFORE Claude processes each user prompt.
# Use it to inject dynamic context that should be available for every response.
#
# Hook Event: UserPromptSubmit
# Output: stdout is injected into Claude's context before processing
# =============================================================================

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.aios/session-state.json"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Read agent info
AGENT=$(jq -r '.activeAgent // empty' "$STATE_FILE" 2>/dev/null)

# If no active agent, exit silently (Claude default behavior)
if [ -z "$AGENT" ] || [ "$AGENT" = "null" ]; then
  exit 0
fi

# Get current task if any
CURRENT_TASK=$(jq -r '.currentTask // empty' "$STATE_FILE" 2>/dev/null)

# Minimal context injection (to not bloat every prompt)
# Only inject if there's an active task to remind about
if [ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "null" ]; then
  echo "[Context: @$AGENT | Task: $CURRENT_TASK]"
fi

exit 0
