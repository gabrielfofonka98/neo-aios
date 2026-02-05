#!/bin/bash
# =============================================================================
# NEO-AIOS: Scope Enforcer Hook
# =============================================================================
# This hook runs BEFORE tool execution (PreToolUse).
# It enforces agent scope rules (e.g., only DevOps can git push).
#
# Hook Event: PreToolUse (matcher: Bash)
# Exit Codes:
#   0 = Allow operation
#   2 = Block operation (stderr shown to user)
# =============================================================================

set -e

# Read hook input from stdin
INPUT=$(cat)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.aios/session-state.json"

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# If not a Bash command, allow
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

# Get active agent
AGENT="default"
if [ -f "$STATE_FILE" ]; then
  AGENT=$(jq -r '.activeAgent // "default"' "$STATE_FILE" 2>/dev/null)
  [ "$AGENT" = "null" ] && AGENT="default"
fi

# =============================================================================
# SCOPE RULES
# =============================================================================

# Rule 1: Only DevOps (Gage) can git push
if echo "$COMMAND" | grep -qE "git\s+push"; then
  if [ "$AGENT" != "devops" ]; then
    echo "🚫 SCOPE VIOLATION: git push" >&2
    echo "" >&2
    echo "Only @devops (Gage) can push to remote repositories." >&2
    echo "Current agent: @$AGENT" >&2
    echo "" >&2
    echo "To push changes, activate DevOps:" >&2
    echo "  /devops" >&2
    echo "  *push" >&2
    exit 2
  fi
fi

# Rule 2: Only DevOps can create PRs
if echo "$COMMAND" | grep -qE "gh\s+pr\s+create"; then
  if [ "$AGENT" != "devops" ]; then
    echo "🚫 SCOPE VIOLATION: PR creation" >&2
    echo "" >&2
    echo "Only @devops (Gage) can create pull requests." >&2
    echo "Current agent: @$AGENT" >&2
    exit 2
  fi
fi

# Rule 3: Only Data Engineer can run DDL
if echo "$COMMAND" | grep -qiE "(CREATE|ALTER|DROP)\s+(TABLE|INDEX|VIEW|FUNCTION|TRIGGER)"; then
  if [ "$AGENT" != "data-engineer" ]; then
    echo "🚫 SCOPE VIOLATION: Database DDL" >&2
    echo "" >&2
    echo "Only @data-engineer (Dara) can execute DDL commands." >&2
    echo "Current agent: @$AGENT" >&2
    exit 2
  fi
fi

# All checks passed
exit 0
