#!/bin/bash

export LC_NUMERIC=C

# Cores ANSI
RED=$'\033[31m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
CYAN=$'\033[36m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

# Lê JSON do Claude Code
INPUT=$(cat)

# === ACTIVE AGENT (from .aios/session-state.json) ===
# Walk up directory tree to find .aios/session-state.json
CWD_FOR_AGENT=$(echo "$INPUT" | jq -r '.cwd // ""')
ACTIVE_AGENT=""
SEARCH_DIR="$CWD_FOR_AGENT"
while [ -n "$SEARCH_DIR" ] && [ "$SEARCH_DIR" != "/" ]; do
    if [ -f "$SEARCH_DIR/.aios/session-state.json" ]; then
        ACTIVE_AGENT=$(jq -r '.activeAgent // empty' "$SEARCH_DIR/.aios/session-state.json" 2>/dev/null)
        break
    fi
    SEARCH_DIR=$(dirname "$SEARCH_DIR")
done

# Map agent ID to display name with emoji
# Complete mapping of ALL agents (skills + external)
case "$ACTIVE_AGENT" in
    # Core agents
    master|aios-master)   AGENT_DISPLAY="${CYAN}${BOLD}🎯 Orion${RESET}";;
    dev)                  AGENT_DISPLAY="${CYAN}${BOLD}⚡ Dex${RESET}";;
    architect)            AGENT_DISPLAY="${CYAN}${BOLD}🏛️ Aria${RESET}";;
    qa)                   AGENT_DISPLAY="${CYAN}${BOLD}🛡️ Quinn${RESET}";;
    qa-code)              AGENT_DISPLAY="${CYAN}${BOLD}🔬 Codex${RESET}";;
    qa-functional)        AGENT_DISPLAY="${CYAN}${BOLD}🧪 Tess${RESET}";;
    devops)               AGENT_DISPLAY="${CYAN}${BOLD}🔥 Gage${RESET}";;
    pm)                   AGENT_DISPLAY="${CYAN}${BOLD}📋 Morgan${RESET}";;
    po)                   AGENT_DISPLAY="${CYAN}${BOLD}📦 PO${RESET}";;
    sm)                   AGENT_DISPLAY="${CYAN}${BOLD}🔄 SM${RESET}";;
    data-engineer)        AGENT_DISPLAY="${CYAN}${BOLD}🗄️ Dara${RESET}";;
    doc)                  AGENT_DISPLAY="${CYAN}${BOLD}📝 Sage${RESET}";;
    spec)                 AGENT_DISPLAY="${CYAN}${BOLD}📐 Rune${RESET}";;
    ralph)                AGENT_DISPLAY="${CYAN}${BOLD}🤖 Ralph${RESET}";;
    ux)                   AGENT_DISPLAY="${CYAN}${BOLD}🎨 Pixel${RESET}";;
    landing)              AGENT_DISPLAY="${CYAN}${BOLD}🚀 Blaze${RESET}";;
    marketing)            AGENT_DISPLAY="${CYAN}${BOLD}📊 Spark${RESET}";;
    analyst)              AGENT_DISPLAY="${CYAN}${BOLD}📈 Oracle${RESET}";;
    sre)                  AGENT_DISPLAY="${CYAN}${BOLD}⚙️ Ops${RESET}";;
    cto|fofonka)          AGENT_DISPLAY="${CYAN}${BOLD}🧠 Fofonka${RESET}";;

    # Utility agents
    fixer)                AGENT_DISPLAY="${CYAN}${BOLD}🔧 Fixer${RESET}";;
    handoff)              AGENT_DISPLAY="${CYAN}${BOLD}📤 Handoff${RESET}";;
    clear-agent)          AGENT_DISPLAY="${CYAN}${BOLD}🧹 Clear${RESET}";;
    test)                 AGENT_DISPLAY="${CYAN}${BOLD}🧪 Test${RESET}";;
    staging)              AGENT_DISPLAY="${CYAN}${BOLD}🚦 Staging${RESET}";;

    # Security sub-agents (Quinn's team)
    sec-rls-guardian)            AGENT_DISPLAY="${YELLOW}${BOLD}🔒 Sentinel${RESET}";;
    sec-framework-scanner)       AGENT_DISPLAY="${YELLOW}${BOLD}🩹 Patch${RESET}";;
    sec-xss-hunter)              AGENT_DISPLAY="${YELLOW}${BOLD}🐍 Viper${RESET}";;
    sec-api-access-tester)       AGENT_DISPLAY="${YELLOW}${BOLD}🚪 Gatekeeper${RESET}";;
    sec-jwt-auditor)             AGENT_DISPLAY="${YELLOW}${BOLD}🔑 Cipher${RESET}";;
    sec-secret-scanner)          AGENT_DISPLAY="${YELLOW}${BOLD}👤 Shadow${RESET}";;
    sec-cors-csrf-checker)       AGENT_DISPLAY="${YELLOW}${BOLD}🧱 Barrier${RESET}";;
    sec-injection-detector)      AGENT_DISPLAY="${YELLOW}${BOLD}⚒️ Forge${RESET}";;
    sec-validation-enforcer)     AGENT_DISPLAY="${YELLOW}${BOLD}💂 Warden${RESET}";;
    sec-supply-chain-monitor)    AGENT_DISPLAY="${YELLOW}${BOLD}🐕 Watchdog${RESET}";;
    sec-upload-validator)        AGENT_DISPLAY="${YELLOW}${BOLD}🔍 Filter${RESET}";;
    sec-header-inspector)        AGENT_DISPLAY="${YELLOW}${BOLD}🛡️ Shield${RESET}";;
    sec-client-exposure-scanner) AGENT_DISPLAY="${YELLOW}${BOLD}👻 Ghost${RESET}";;
    sec-rate-limit-tester)       AGENT_DISPLAY="${YELLOW}${BOLD}⏱️ Throttle${RESET}";;
    sec-redirect-checker)        AGENT_DISPLAY="${YELLOW}${BOLD}🧭 Compass${RESET}";;
    sec-error-leak-detector)     AGENT_DISPLAY="${YELLOW}${BOLD}🤫 Muffle${RESET}";;
    sec-deploy-auditor)          AGENT_DISPLAY="${YELLOW}${BOLD}⚓ Harbor${RESET}";;
    sec-ai-code-reviewer)        AGENT_DISPLAY="${YELLOW}${BOLD}🔮 Oracle-AI${RESET}";;

    # External agents (~/.claude/agents/)
    professor)            AGENT_DISPLAY="${CYAN}${BOLD}👨‍🏫 Professor${RESET}";;
    oalanicolas)          AGENT_DISPLAY="${CYAN}${BOLD}👤 OalaNicolas${RESET}";;
    pedro-valerio)        AGENT_DISPLAY="${CYAN}${BOLD}👤 PedroValerio${RESET}";;
    sop-extractor)        AGENT_DISPLAY="${CYAN}${BOLD}📋 SOP${RESET}";;
    squad-architect)      AGENT_DISPLAY="${CYAN}${BOLD}🏗️ SquadArch${RESET}";;
    squad-diagnostician)  AGENT_DISPLAY="${CYAN}${BOLD}🔬 SquadDiag${RESET}";;

    # Fallback: show raw ID if not mapped
    "")                   AGENT_DISPLAY="";;
    *)                    AGENT_DISPLAY="${CYAN}${BOLD}🤖 ${ACTIVE_AGENT}${RESET}";;
esac

# Extrai dados com jq
CTX_REMAINING=$(echo "$INPUT" | jq -r '.context_window.remaining_percentage // 100')
CTX_SIZE=$(echo "$INPUT" | jq -r '.context_window.context_window_size // 200000')

# Limite máximo útil: 180k tokens
MAX_USEFUL_TOKENS=180000

# Calcula tokens usados na janela atual
TOKENS_USED=$((CTX_SIZE * (100 - CTX_REMAINING) / 100))

# Calcula porcentagem em relação a 180k
CTX_PERCENT=$((TOKENS_USED * 100 / MAX_USEFUL_TOKENS))
MODEL=$(echo "$INPUT" | jq -r '.model.display_name // "unknown"')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
SESSION_COST=$(echo "$INPUT" | jq -r '.cost.total_cost_usd // 0')
DURATION_MS=$(echo "$INPUT" | jq -r '.cost.total_duration_ms // 0')
LINES_ADDED=$(echo "$INPUT" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$INPUT" | jq -r '.cost.total_lines_removed // 0')

# Formata duração
DURATION_SEC=$((DURATION_MS / 1000))
DURATION_MIN=$((DURATION_SEC / 60))
DURATION_HOUR=$((DURATION_MIN / 60))
if [ "$DURATION_HOUR" -gt 0 ]; then
    DURATION_FMT="${DURATION_HOUR}h $((DURATION_MIN % 60))m"
elif [ "$DURATION_MIN" -gt 0 ]; then
    DURATION_FMT="${DURATION_MIN}m $((DURATION_SEC % 60))s"
else
    DURATION_FMT="${DURATION_SEC}s"
fi

# Formata tokens (K/M)
if [ "$TOKENS_USED" -gt 1000000 ]; then
    TOKENS_FMT=$(awk "BEGIN {printf \"%.1fM\", $TOKENS_USED/1000000}")
elif [ "$TOKENS_USED" -gt 1000 ]; then
    TOKENS_FMT=$(awk "BEGIN {printf \"%.0fk\", $TOKENS_USED/1000}")
else
    TOKENS_FMT="${TOKENS_USED}"
fi

# Diretório curto
SHORT_CWD=$(echo "$CWD" | sed "s|$HOME|~|")

# Git branch
BRANCH=""
if [ -n "$CWD" ] && [ -d "$CWD/.git" ]; then
    BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null)
fi

# Formata custo
SESSION_COST_FMT=$(awk "BEGIN {printf \"%.2f\", $SESSION_COST}")

# === CPU e Memória (background, com timeout) ===
TOP_OUTPUT=$(top -l 1 -n 0 2>/dev/null)
CPU=$(echo "$TOP_OUTPUT" | grep "CPU usage" | awk '{print $3}' | tr -d '%')
CPU=${CPU:-"--"}
MEM_USED=$(echo "$TOP_OUTPUT" | grep "PhysMem" | awk '{print $2}' | tr -d 'G')
MEM_TOTAL=$(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f", $1/1024/1024/1024}')
if [ -n "$MEM_USED" ] && [ -n "$MEM_TOTAL" ] && [ "$MEM_TOTAL" -gt 0 ]; then
    RAM_PERCENT=$(awk "BEGIN {printf \"%.0f\", ($MEM_USED / $MEM_TOTAL) * 100}")
else
    RAM_PERCENT="--"
fi

# === Formata contexto (vermelho se > 60%) ===
if [ "$CTX_PERCENT" -gt 60 ]; then
    CTX_DISPLAY="${RED}${CTX_PERCENT}%${RESET}"
else
    CTX_DISPLAY="${CTX_PERCENT}%"
fi

# === OUTPUT ===
AGENT_PREFIX=""
if [ -n "$AGENT_DISPLAY" ]; then
    AGENT_PREFIX="${AGENT_DISPLAY} | "
fi

if [ -n "$BRANCH" ]; then
    printf "%s%s %s | \$%s ⏱ %s | +%s-%s | %s | %s:%s | %s%% / %s%%\n" "$AGENT_PREFIX" "$CTX_DISPLAY" "$TOKENS_FMT" "$SESSION_COST_FMT" "$DURATION_FMT" "$LINES_ADDED" "$LINES_REMOVED" "$MODEL" "$SHORT_CWD" "$BRANCH" "$CPU" "$RAM_PERCENT"
else
    printf "%s%s %s | \$%s ⏱ %s | +%s-%s | %s | %s | %s%% / %s%%\n" "$AGENT_PREFIX" "$CTX_DISPLAY" "$TOKENS_FMT" "$SESSION_COST_FMT" "$DURATION_FMT" "$LINES_ADDED" "$LINES_REMOVED" "$MODEL" "$SHORT_CWD" "$CPU" "$RAM_PERCENT"
fi
