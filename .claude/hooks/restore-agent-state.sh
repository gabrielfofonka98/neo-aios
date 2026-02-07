#!/bin/bash
# =============================================================================
# NEO-AIOS: Restore Agent State After Compaction
# =============================================================================
# This hook runs after Claude Code compacts the context window.
# It injects the active agent info so Claude continues as the correct persona.
#
# Hook Event: SessionStart (matcher: compact)
# Output: stdout is injected into Claude's context
# =============================================================================

set -e

# Read hook input from stdin
INPUT=$(cat)

# Extract source (should be "compact" for this matcher)
SOURCE=$(echo "$INPUT" | jq -r '.source // empty' 2>/dev/null)

# Only run for compaction events
if [ "$SOURCE" != "compact" ]; then
  exit 0
fi

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.aios/session-state.json"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Read agent info
AGENT=$(jq -r '.activeAgent // empty' "$STATE_FILE" 2>/dev/null)
AGENT_FILE=$(jq -r '.agentFile // empty' "$STATE_FILE" 2>/dev/null)
CURRENT_TASK=$(jq -r '.currentTask // empty' "$STATE_FILE" 2>/dev/null)
PROJECT=$(jq -r '.projectContext.project // empty' "$STATE_FILE" 2>/dev/null)

# If no active agent, exit silently
if [ -z "$AGENT" ] || [ "$AGENT" = "null" ]; then
  exit 0
fi

# Inject context into Claude
echo "═══════════════════════════════════════════════════════════════"
echo "🔄 CONTEXT RESTORED AFTER COMPACTION"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Active Agent: @$AGENT"
[ -n "$AGENT_FILE" ] && [ "$AGENT_FILE" != "null" ] && echo "Agent File: $AGENT_FILE"
[ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "null" ] && echo "Current Task: $CURRENT_TASK"
[ -n "$PROJECT" ] && [ "$PROJECT" != "null" ] && echo "Project: $PROJECT"
echo ""
echo "INSTRUCTION: Continue as @$AGENT persona."
echo "- Do NOT greet or re-introduce yourself"
echo "- Do NOT ask 'how can I help' - continue the previous work"
echo "- Maintain the agent's scope restrictions"
echo "- If you were in the middle of a task, continue it"

# Agent memory reference (only if memory file exists)
MEMORY_FILE="$PROJECT_DIR/.claude/agent-memory/$AGENT/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  echo "- Read your agent memory at .claude/agent-memory/$AGENT/MEMORY.md for session continuity"
fi

echo "═══════════════════════════════════════════════════════════════"

exit 0
