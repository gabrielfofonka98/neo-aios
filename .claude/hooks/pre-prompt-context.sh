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

# Check if state file exists; create with defaults if missing
if [ ! -f "$STATE_FILE" ]; then
  mkdir -p "$PROJECT_DIR/.aios"
  echo '{"activeAgent":null,"agentFile":null,"activatedAt":null,"lastActivity":null,"currentTask":null,"projectContext":{"project":null,"epic":null,"story":null}}' > "$STATE_FILE"
fi

# ---------------------------------------------------------------------------
# Auto-detect agent activation from user prompt (slash commands & skill calls)
# This writes session-state.json BEFORE the LLM processes anything = zero tokens
# ---------------------------------------------------------------------------
USER_PROMPT="${CLAUDE_USER_PROMPT:-}"

if [ -n "$USER_PROMPT" ]; then
  # Extract agent name from multiple formats:
  # 1. Raw: /master, @dev at start of prompt
  # 2. Skill XML: <command-message>master</command-message> (Claude Code skill system)
  # 3. Command XML: <command-name>/master</command-name>
  DETECTED=$(echo "$USER_PROMPT" | grep -oE '^[/@]([-a-z]+)' | head -1 | sed 's|^[/@]||')
  if [ -z "$DETECTED" ]; then
    DETECTED=$(echo "$USER_PROMPT" | sed -n 's|.*<command-message>\([-a-z]*\)</command-message>.*|\1|p' | head -1)
  fi
  if [ -z "$DETECTED" ]; then
    DETECTED=$(echo "$USER_PROMPT" | sed -n 's|.*<command-name>/\([-a-z]*\)</command-name>.*|\1|p' | head -1)
  fi

  if [ -n "$DETECTED" ]; then
    # Handle clear-agent: reset state
    if [ "$DETECTED" = "clear-agent" ]; then
      jq '.activeAgent=null | .agentFile=null | .activatedAt=null | .lastActivity=null | .currentTask=null' "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
    else
      # Check if it's a valid skill/agent directory
      SKILL_DIR="$PROJECT_DIR/.claude/skills/$DETECTED"
      if [ -d "$SKILL_DIR" ]; then
        NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        AGENT_FILE=".claude/skills/$DETECTED/SKILL.md"
        jq --arg agent "$DETECTED" --arg file "$AGENT_FILE" --arg now "$NOW" \
          '.activeAgent=$agent | .agentFile=$file | .activatedAt=$now | .lastActivity=$now' \
          "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
      fi
    fi
  fi
fi

# Read agent info (may have just been updated above)
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
