#!/usr/bin/env bash
# ===========================================================================
# NEO-AIOS Installer
# One-line install: curl -fsSL https://raw.githubusercontent.com/gabrielfofonka98/neo-aios/main/scripts/install.sh | bash
# ===========================================================================
set -e

# CRITICAL: Save original directory BEFORE any cd
ORIGINAL_DIR="$(pwd)"

# ANSI colors
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
BOLD='\033[1m'
DIM='\033[2m'
WHITE='\033[37m'
RESET='\033[0m'

REPO_URL="https://github.com/gabrielfofonka98/neo-aios.git"
INSTALL_DIR="$HOME/.neo-aios"

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} ${YELLOW}$1${RESET}"; }
fail() { echo -e "  ${RED}✗${RESET} ${RED}$1${RESET}"; exit 1; }
info() { echo -e "  ${DIM}$1${RESET}"; }

echo ""
echo -e "${CYAN}${BOLD}"
cat << 'EOF'

    ███╗   ██╗███████╗ ██████╗        █████╗ ██╗ ██████╗ ███████╗
    ████╗  ██║██╔════╝██╔═══██╗      ██╔══██╗██║██╔═══██╗██╔════╝
    ██╔██╗ ██║█████╗  ██║   ██║█████╗███████║██║██║   ██║███████╗
    ██║╚██╗██║██╔══╝  ██║   ██║╚════╝██╔══██║██║██║   ██║╚════██║
    ██║ ╚████║███████╗╚██████╔╝      ██║  ██║██║╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝ ╚═════╝       ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══════╝

EOF
echo -e "${RESET}"
echo -e "    ${DIM}Agent Intelligence Operating System${RESET}"
echo -e "    ${DIM}Big Tech Hierarchy · 36 Agents · 18 Security Sub-Agents${RESET}"
echo -e "    ${DIM}Powered by Claude Opus 4.6${RESET}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Check prerequisites
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[1/6]${RESET} ${BOLD}Checking prerequisites...${RESET}"

# Git
if ! command -v git &>/dev/null; then
    fail "git not found. Install git first."
fi
ok "git $(git --version | awk '{print $3}')"

# Python 3.12+
if ! command -v python3 &>/dev/null; then
    fail "Python 3 not found. Install Python 3.12+ first."
fi
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    fail "Python 3.12+ required. Found: Python $PYTHON_VER"
fi
ok "Python $PYTHON_VER"

# uv (required for NEO-AIOS)
if ! command -v uv &>/dev/null; then
    warn "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &>/dev/null; then
        fail "Failed to install uv. Install manually: https://docs.astral.sh/uv/"
    fi
fi
ok "uv $(uv --version 2>&1 | head -1)"

# Claude Code CLI (optional)
if command -v claude &>/dev/null; then
    ok "Claude Code CLI detected"
else
    info "Claude Code CLI not detected (optional)"
    info "Install: npm i -g @anthropic-ai/claude-code"
fi

# ---------------------------------------------------------------------------
# Step 2: Clone or update repository
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[2/6]${RESET} ${BOLD}Downloading NEO-AIOS...${RESET}"

if [ -d "$INSTALL_DIR/.git" ]; then
    info "Existing installation found at $INSTALL_DIR"
    info "Updating..."
    cd "$INSTALL_DIR"
    git pull --quiet origin main 2>/dev/null || true
    ok "Updated to latest version"
else
    if [ -d "$INSTALL_DIR" ]; then
        info "Removing incomplete installation..."
        rm -rf "$INSTALL_DIR"
    fi
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    ok "Cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Show version
if [ -f "pyproject.toml" ]; then
    VERSION=$(grep -E "^version = " pyproject.toml | cut -d'"' -f2 || echo "0.1.0")
    info "Version: $VERSION"
fi

# ---------------------------------------------------------------------------
# Step 3: Install Python dependencies
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[3/6]${RESET} ${BOLD}Installing dependencies...${RESET}"

cd "$INSTALL_DIR"
uv sync --quiet --extra dev 2>/dev/null && ok "Python dependencies installed" || {
    warn "uv sync failed. Trying pip..."
    pip3 install -e ".[dev]" --quiet 2>/dev/null && ok "Installed with pip" || warn "Dependency installation failed (non-critical)"
}

# ---------------------------------------------------------------------------
# Step 4: Create CLI wrappers
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[4/6]${RESET} ${BOLD}Setting up CLI...${RESET}"

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

# Create neo-aios CLI wrapper
cat > "$BIN_DIR/neo-aios" << 'WRAPPER'
#!/usr/bin/env bash
# NEO-AIOS CLI wrapper
INSTALL_DIR="$HOME/.neo-aios"
cd "$INSTALL_DIR" && uv run python -m aios.cli "$@"
WRAPPER
chmod +x "$BIN_DIR/neo-aios"

# Create neo-init wrapper
cat > "$BIN_DIR/neo-init" << 'WRAPPER'
#!/usr/bin/env bash
# NEO-AIOS Project Initializer
INSTALL_DIR="$HOME/.neo-aios"
PROJECT_DIR="${1:-$(pwd)}"
(cd "$INSTALL_DIR" && uv run python scripts/neo-init.py "$PROJECT_DIR")
WRAPPER
chmod +x "$BIN_DIR/neo-init"

ok "Created neo-aios CLI at $BIN_DIR/neo-aios"
ok "Created neo-init at $BIN_DIR/neo-init"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your PATH"
    info "Add this to your shell config (~/.zshrc or ~/.bashrc):"
    info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ---------------------------------------------------------------------------
# Step 5: Verify global installation
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[5/6]${RESET} ${BOLD}Verifying global installation...${RESET}"

if [ -x "$BIN_DIR/neo-aios" ]; then
    ok "neo-aios CLI installed"
else
    warn "Could not verify CLI installation"
fi

if [ -x "$BIN_DIR/neo-init" ]; then
    ok "neo-init wizard installed"
else
    warn "Could not verify neo-init installation"
fi

# Count installed components
AGENT_COUNT=$(find "$INSTALL_DIR/agents" -maxdepth 1 -type d 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
SEC_COUNT=$(find "$INSTALL_DIR/agents" -maxdepth 1 -type d -name "sec-*" 2>/dev/null | wc -l | tr -d ' ')
HOOK_COUNT=$(find "$INSTALL_DIR/.claude/hooks" -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')

ok "Global install: ${AGENT_COUNT} agents, ${SEC_COUNT} security sub-agents, ${HOOK_COUNT} hooks"

# ---------------------------------------------------------------------------
# Step 6: Initialize project (interactive wizard)
# ---------------------------------------------------------------------------
echo -e "\n${CYAN}${BOLD}[6/6]${RESET} ${BOLD}Initializing project in ${WHITE}${ORIGINAL_DIR}${RESET}${BOLD}...${RESET}"
echo ""

# Run neo-init.py with the ORIGINAL directory (where the user ran install from)
# NEO_AIOS_FROM_INSTALLER=1 tells neo-init.py to skip its own logo (already shown)
cd "$INSTALL_DIR"
if [ -f "scripts/neo-init.py" ]; then
    NEO_AIOS_FROM_INSTALLER=1 uv run python scripts/neo-init.py "$ORIGINAL_DIR"
else
    fail "neo-init.py not found at $INSTALL_DIR/scripts/neo-init.py"
fi
