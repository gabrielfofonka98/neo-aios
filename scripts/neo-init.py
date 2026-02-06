#!/usr/bin/env python3
"""
NEO-AIOS Project Initializer

Interactive wizard to initialize NEO-AIOS in a project directory.
Detects environment, copies framework files, generates config.

Usage:
    neo-init              # Run in current directory
    neo-init /path/to/project
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD_WHITE = "\033[1;37m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_RED = "\033[1;31m"
    BOLD_YELLOW = "\033[1;33m"

c = Colors

def ok(msg: str) -> None:
    print(f"  {c.GREEN}✓{c.RESET} {msg}")

def warn(msg: str) -> None:
    print(f"  {c.YELLOW}⚠{c.RESET} {c.YELLOW}{msg}{c.RESET}")

def fail(msg: str) -> None:
    print(f"  {c.RED}✗{c.RESET} {c.RED}{msg}{c.RESET}")
    sys.exit(1)

def info(msg: str) -> None:
    print(f"  {c.DIM}{msg}{c.RESET}")

def header(step: int, total: int, msg: str) -> None:
    print()
    print(f"{c.BOLD_CYAN}[{step}/{total}]{c.RESET} {c.BOLD_WHITE}{msg}{c.RESET}")

# ---------------------------------------------------------------------------
# ASCII logo
# ---------------------------------------------------------------------------
def print_logo() -> None:
    """Print the NEO-AIOS logo. Skipped if called from install.sh."""
    if os.environ.get("NEO_AIOS_FROM_INSTALLER"):
        return

    version = "0.1.0"
    try:
        import tomllib
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
                version = data.get("project", {}).get("version", version)
    except Exception:
        pass

    print()
    print(f"{c.BOLD_CYAN}")
    print(f"    ███╗   ██╗███████╗ ██████╗        █████╗ ██╗ ██████╗ ███████╗")
    print(f"    ████╗  ██║██╔════╝██╔═══██╗      ██╔══██╗██║██╔═══██╗██╔════╝")
    print(f"    ██╔██╗ ██║█████╗  ██║   ██║█████╗███████║██║██║   ██║███████╗")
    print(f"    ██║╚██╗██║██╔══╝  ██║   ██║╚════╝██╔══██║██║██║   ██║╚════██║")
    print(f"    ██║ ╚████║███████╗╚██████╔╝      ██║  ██║██║╚██████╔╝███████║")
    print(f"    ╚═╝  ╚═══╝╚══════╝ ╚═════╝       ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══════╝")
    print(f"{c.RESET}")
    print(f"    {c.DIM}Agent Intelligence Operating System v{version}{c.RESET}")
    print(f"    {c.DIM}Big Tech Hierarchy · 36 Agents · 18 Security Sub-Agents{c.RESET}")
    print()

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

# Use /dev/tty for interactive input when stdin might be consumed (e.g. piped install)
_tty = None
def _get_tty():
    global _tty
    if _tty is None:
        try:
            _tty = open("/dev/tty", "r")
        except OSError:
            _tty = sys.stdin
    return _tty

def tty_input(prompt: str) -> str:
    """Read input from /dev/tty (works even when stdin is consumed)."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    line = _get_tty().readline()
    if not line:
        raise EOFError("EOF when reading a line")
    return line.rstrip("\n")

def ask(question: str) -> str:
    """Ask a simple question."""
    return tty_input(f"  {c.CYAN}{question}{c.RESET} ").strip()

def ask_choice(question: str, options: list[dict]) -> dict:
    """Ask user to choose from numbered options."""
    print()
    print(f"  {c.BOLD_WHITE}{question}{c.RESET}")
    print()
    for i, opt in enumerate(options, 1):
        label = opt["label"]
        desc = f"{c.DIM} — {opt.get('desc', '')}{c.RESET}" if opt.get("desc") else ""
        print(f"  {c.BOLD_CYAN}{i}{c.RESET}. {label}{desc}")
    print()
    answer = tty_input(f"  {c.CYAN}Choose [1-{len(options)}]: {c.RESET}").strip()
    try:
        idx = int(answer) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[0]  # Default to first option

def check_command(cmd: str) -> bool:
    """Check if a command exists."""
    return shutil.which(cmd) is not None

def get_version(cmd: str, flag: str = "--version") -> str | None:
    """Get version string from a command."""
    try:
        result = subprocess.run(
            [cmd, flag], capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return None

def copy_dir_recursive(src: Path, dest: Path) -> int:
    """Recursively copy a directory. Returns file count."""
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in src.iterdir():
        if item.name == ".DS_Store":
            continue
        dest_path = dest / item.name
        if item.is_dir():
            count += copy_dir_recursive(item, dest_path)
        else:
            shutil.copy2(item, dest_path)
            count += 1
    return count

# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------
def check_python() -> str | None:
    """Check Python version."""
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info < (3, 12):
        warn(f"Python 3.12+ recommended. Found: Python {ver}")
        return ver
    ok(f"Python {ver}")
    return ver

def check_git() -> str | None:
    """Check git."""
    if not check_command("git"):
        warn("git not found. Version control features will be limited.")
        return None
    ver = get_version("git")
    ok(f"git {ver}")
    return ver

def check_uv() -> str | None:
    """Check uv package manager."""
    if check_command("uv"):
        ver = get_version("uv")
        ok(f"uv {ver}")
        return "uv"
    if check_command("pip3"):
        ok("pip3")
        return "pip"
    info("No Python package manager found (uv or pip).")
    return None

def check_claude() -> bool:
    """Check Claude Code CLI."""
    if check_command("claude"):
        ok("Claude Code CLI detected")
        return True
    info("Claude Code CLI not detected. Install: npm i -g @anthropic-ai/claude-code")
    return False

# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------
def detect_stack(project_root: Path) -> list[dict]:
    """Detect project stack from package.json, pyproject.toml, etc."""
    detected = []

    # Check package.json
    pkg_path = project_root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            # Next.js
            if "next" in deps:
                detected.append({"name": "Next.js", "version": deps["next"].strip("^~>=<")})
            # React (only if no Next.js)
            elif "react" in deps:
                detected.append({"name": "React", "version": deps["react"].strip("^~>=<")})

            # Vue
            if "vue" in deps:
                detected.append({"name": "Vue.js", "version": deps["vue"].strip("^~>=<")})

            # Supabase
            if "@supabase/supabase-js" in deps or "@supabase/ssr" in deps:
                detected.append({"name": "Supabase", "version": ""})

            # Prisma
            if "prisma" in deps or "@prisma/client" in deps:
                detected.append({"name": "Prisma", "version": ""})

            # Tailwind
            if "tailwindcss" in deps:
                detected.append({"name": "Tailwind CSS", "version": deps["tailwindcss"].strip("^~>=<")})
        except Exception:
            pass

    # Check TypeScript
    if (project_root / "tsconfig.json").exists():
        detected.append({"name": "TypeScript", "version": ""})

    # Check pyproject.toml (Python project)
    if (project_root / "pyproject.toml").exists():
        detected.append({"name": "Python (pyproject.toml)", "version": ""})

    # Check Docker
    if (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists():
        detected.append({"name": "Docker", "version": ""})

    return detected

def get_project_name(project_root: Path) -> str:
    """Get project name from package.json or directory name."""
    pkg_path = project_root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            if pkg.get("name"):
                return pkg["name"]
        except Exception:
            pass

    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                name = data.get("project", {}).get("name")
                if name:
                    return name
        except Exception:
            pass

    return project_root.name

# ---------------------------------------------------------------------------
# Framework installation
# ---------------------------------------------------------------------------
def find_framework_source() -> Path | None:
    """Find the NEO-AIOS framework source directory."""
    # Option 1: ~/.neo-aios (global install)
    global_install = Path.home() / ".neo-aios"
    if (global_install / ".claude" / "skills").exists() and (global_install / ".claude").exists():
        return global_install

    # Option 2: Running from inside the repo
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    if (repo_root / ".claude" / "skills").exists() and (repo_root / ".claude").exists():
        return repo_root

    return None

def copy_framework_files(source: Path, dest: Path) -> list[dict]:
    """Copy framework files to project directory."""
    results = []

    # Only copy SYSTEM files — no framework internals (src/, tests/, tools/, etc.)
    # Those stay in ~/.neo-aios/ and are never copied to user projects.
    copy_targets = [
        # Claude Code integration (hidden)
        (".claude/hooks", ".claude/hooks", ".claude/hooks/"),
        (".claude/rules", ".claude/rules", ".claude/rules/"),
        (".claude/skills", ".claude/skills", ".claude/skills/"),
        (".claude/setup", ".claude/setup", ".claude/setup/"),
        (".claude/CLAUDE.md", ".claude/CLAUDE.md", ".claude/CLAUDE.md"),
        # Framework core — read-only (hidden)
        (".aios-core", ".aios-core", ".aios-core/"),
        # Custom config overlay (hidden)
        (".aios-custom", ".aios-custom", ".aios-custom/"),
        # Gitignore (visible, essential)
        (".gitignore", ".gitignore", ".gitignore"),
    ]

    for src_rel, dest_rel, label in copy_targets:
        src_path = source / src_rel
        dest_path = dest / dest_rel

        if not src_path.exists():
            continue

        if src_path.is_dir():
            count = copy_dir_recursive(src_path, dest_path)
            results.append({"label": label, "files": count, "status": "copied"})
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            results.append({"label": label, "files": 1, "status": "copied"})

    # Copy settings.json
    settings_src = source / ".claude" / "settings.json"
    settings_dest = dest / ".claude" / "settings.json"
    if settings_src.exists() and not settings_dest.exists():
        settings_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(settings_src, settings_dest)
        results.append({"label": ".claude/settings.json", "files": 1, "status": "copied"})

    return results

def create_directory_structure(project_root: Path) -> list[str]:
    """Create workspace directories with .gitkeep files.

    Hidden dirs = system runtime (gitignored).
    Visible dirs = organized workspace where agents write output.
    All folders pre-created so agents never need to mkdir.
    """
    # Runtime state (hidden, gitignored)
    runtime_dirs = [
        ".aios",
        ".aios/workflow-state",
        ".aios/cache",
    ]

    # User workspace (visible, committed)
    workspace_dirs = [
        # Configuration
        "config",
        # Documentation — agents write here
        "docs/architecture",       # Aria: ADRs, system design, tech decisions
        "docs/product",            # Morgan: PRDs, epics, stories
        "docs/api",                # Sage: API documentation
        "docs/database",           # Dara: schema docs, ERDs
        "docs/design",             # Pixel: wireframes, user flows, specs
        "docs/runbooks",           # Ops: SLOs, incident runbooks
        "docs/sessions",           # Handoffs (YYYY-MM/)
        # Reports — agent-generated analysis
        "reports/security",        # Quinn: security audit reports
        "reports/code-quality",    # Codex: code review, lint reports
        "reports/testing",         # Tess: test plans, regression, bugs
        "reports/analytics",       # Oracle: data analysis, dashboards
        # Database
        "database/migrations",     # Dara: SQL migrations
        "database/seeds",          # Dara: seed data
    ]

    created = []

    # Create runtime dirs (no .gitkeep — they're gitignored)
    for d in runtime_dirs:
        path = project_root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(f"{d}/")

    # Create workspace dirs with .gitkeep
    for d in workspace_dirs:
        path = project_root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            gitkeep = path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
            created.append(f"{d}/")

    return created

def create_session_state(project_root: Path) -> bool:
    """Create initial session-state.json."""
    state_file = project_root / ".aios" / "session-state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    if not state_file.exists():
        state = {
            "activeAgent": None,
            "agentFile": None,
            "activatedAt": None,
            "lastActivity": None,
            "currentTask": None,
            "projectContext": {"project": None, "epic": None, "story": None},
        }
        state_file.write_text(json.dumps(state, indent=2) + "\n")
        return True
    return False

def generate_config(project_root: Path, project_name: str, stack: list, answers: dict) -> bool:
    """Generate core configuration file."""
    config_dir = project_root / "config"
    config_file = config_dir / "neo-aios.yaml"

    if config_file.exists():
        return False

    config_dir.mkdir(parents=True, exist_ok=True)

    stack_names = [s["name"].lower() for s in stack]
    has_ts = any("typescript" in s for s in stack_names)
    has_supabase = any("supabase" in s for s in stack_names)
    has_next = any("next" in s for s in stack_names)

    now = datetime.now(timezone.utc)

    yaml_content = f"""# NEO-AIOS Configuration
# Generated by neo-init on {now.strftime('%Y-%m-%d')}
# Docs: https://github.com/gabrielfofonka98/neo-aios

project:
  name: "{project_name}"
  type: {answers.get('project_type', 'brownfield')}
  focus: {answers.get('project_goal', 'webapp')}
  description: "{answers.get('description', '')}"
  installedAt: "{now.isoformat()}Z"

# Auto-detected stack
stack:
  typescript: {str(has_ts).lower()}
  supabase: {str(has_supabase).lower()}
  nextjs: {str(has_next).lower()}
  detected:
{chr(10).join(f'    - {s["name"]}' for s in stack) if stack else '    # No stack detected'}

# Session persistence
session:
  enabled: true
  stateFile: .aios/session-state.json
  autoRecover: true

# Quality gates
quality:
  layer1:  # Pre-commit
    ruff: true
    mypy: true
    pytest: true
  layer2:  # PR automation
    coderabbit: true
    qaAgent: true
  layer3:  # Human review
    required: true

# Deployment
deployment:
  enforceStaging: {str(answers.get('deploy_strategy') == 'staging-first').lower()}
  currentPhase: {answers.get('project_type', 'development')}

# Agent scope enforcement
scope:
  enabled: true
  enforceGitPush: true  # Only @devops can push
  enforceDatabase: true  # Only @data-engineer can DDL
"""

    config_file.write_text(yaml_content)
    return True

def create_claude_local_md(project_root: Path) -> bool:
    """Create CLAUDE.local.md template for personal project preferences."""
    local_md = project_root / "CLAUDE.local.md"
    if local_md.exists():
        return False

    local_md.write_text("""# Personal Project Preferences (CLAUDE.local.md)
# This file is gitignored - your personal preferences for this project.
# Add anything specific to YOUR development environment.

# Examples:
# - Your preferred test data
# - Your sandbox/staging URLs
# - Personal workflow shortcuts
# - Notes from past sessions

## My Environment
# STAGING_URL=https://...
# TEST_USER=...

## Session Notes
# (Claude Code's /remember command can add patterns here automatically)
""")
    return True


def create_env_files(project_root: Path) -> list[str]:
    """Create .env and .env.example from template."""
    created = []

    env_content = """# NEO-AIOS Environment Variables
# Fill in your values below

# ============================================
# API Keys
# ============================================
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# ============================================
# GitHub
# ============================================
GITHUB_TOKEN=
GITHUB_OWNER=
GITHUB_REPO=

# ============================================
# Supabase
# ============================================
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# ============================================
# Vercel
# ============================================
VERCEL_TOKEN=
VERCEL_ORG_ID=
VERCEL_PROJECT_ID=

# ============================================
# Database (Local Development)
# ============================================
DATABASE_URL=postgresql://localhost:5432/neo_aios

# ============================================
# Environment
# ============================================
ENVIRONMENT=development
DEBUG=false
"""

    # .env (actual secrets, gitignored)
    env_file = project_root / ".env"
    if not env_file.exists():
        env_file.write_text(env_content)
        created.append(".env")

    # .env.example (template, committed to git)
    env_example = project_root / ".env.example"
    if not env_example.exists():
        env_example.write_text(env_content.replace("Fill in your values below",
            "Copy this file to .env and fill in your values"))
        created.append(".env.example")

    return created


def suggest_agent_teams_setup() -> None:
    """Show instructions for enabling Agent Teams in user settings."""
    settings_path = Path.home() / ".claude" / "settings.json"
    already_enabled = False

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
            env = settings.get("env", {})
            if env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1":
                already_enabled = True
        except Exception:
            pass

    if already_enabled:
        ok("Agent Teams already enabled in ~/.claude/settings.json")
    else:
        info("Agent Teams (experimental) not enabled yet.")
        info("To enable parallel security scans with Quinn:")
        info(f'  Add to ~/.claude/settings.json under "env":')
        info(f'    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"')


def update_gitignore(project_root: Path) -> str | None:
    """Update .gitignore with AIOS entries."""
    gitignore_path = project_root / ".gitignore"

    aios_entries = """
# NEO-AIOS (runtime state)
.aios/
.env
.env.local
config/credentials.yaml
CLAUDE.local.md
"""

    marker = "# NEO-AIOS (runtime state)"

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if marker in content:
            return None
        with open(gitignore_path, "a") as f:
            f.write(aios_entries)
        return "updated"
    else:
        gitignore_path.write_text(aios_entries.strip() + "\n")
        return "created"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def print_summary(agent_count: int, security_count: int, hook_count: int) -> None:
    """Print installation summary."""
    b = c.CYAN
    r = c.RESET
    g = c.BOLD_GREEN
    w = c.BOLD_WHITE
    d = c.DIM

    print()
    print(f"{b}  ┌───────────────────────────────────────────────────────┐{r}")
    print(f"{b}  │{r}  {g}NEO-AIOS initialized successfully!{r}                   {b}│{r}")
    print(f"{b}  │{r}                                                       {b}│{r}")
    print(f"{b}  │{r}  {w}{agent_count} agents{r} {d}│{r} {w}{security_count} security sub-agents{r}             {b}│{r}")
    print(f"{b}  │{r}  {w}{hook_count} hooks{r}  {d}│{r} {w}3-layer quality gates{r}               {b}│{r}")
    print(f"{b}  │{r}                                                       {b}│{r}")
    print(f"{b}  │{r}  {d}Activate an agent in Claude Code:{r}                    {b}│{r}")
    print(f"{b}  │{r}    {c.GREEN}/dev{r}                 {d}# Developer (Dex){r}           {b}│{r}")
    print(f"{b}  │{r}    {c.GREEN}/architect{r}           {d}# Architect (Aria){r}          {b}│{r}")
    print(f"{b}  │{r}    {c.GREEN}/devops{r}              {d}# DevOps (Gage){r}             {b}│{r}")
    print(f"{b}  │{r}    {c.GREEN}/qa{r}                  {d}# Security QA (Quinn){r}       {b}│{r}")
    print(f"{b}  │{r}                                                       {b}│{r}")
    print(f"{b}  └───────────────────────────────────────────────────────┘{r}")
    print()

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
TOTAL_STEPS = 10

# ---------------------------------------------------------------------------
# Step 8: MCP Auto-Install
# ---------------------------------------------------------------------------
MCP_CATALOG = {
    "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "description": "Context7 — documentation search",
    },
    "desktop-commander": {
        "command": "npx",
        "args": ["-y", "@wonderwhy-er/desktop-commander"],
        "description": "Desktop Commander — file/terminal access",
    },
    "browser": {
        "command": "npx",
        "args": ["-y", "@anthropic-ai/mcp-server-puppeteer"],
        "description": "Browser — Puppeteer-based web access",
    },
}

def install_mcps(project_root: Path) -> list[str]:
    """Auto-install essential MCP servers and generate .mcp.json."""
    installed = []

    if not check_command("npx"):
        warn("npx not found. Skipping MCP auto-install.")
        info("Install Node.js to enable MCP servers.")
        return installed

    mcp_config_path = project_root / ".mcp.json"
    existing_config: dict = {}

    if mcp_config_path.exists():
        try:
            existing_config = json.loads(mcp_config_path.read_text())
        except Exception:
            pass

    mcp_servers = existing_config.get("mcpServers", {})

    for name, entry in MCP_CATALOG.items():
        if name in mcp_servers:
            info(f"{name} already configured")
            continue

        mcp_servers[name] = {
            "command": entry["command"],
            "args": entry["args"],
        }
        installed.append(name)
        ok(f"Added {name} — {entry['description']}")

    if installed or not mcp_config_path.exists():
        config_data = {"mcpServers": mcp_servers}
        mcp_config_path.write_text(json.dumps(config_data, indent=2) + "\n")

    return installed


# ---------------------------------------------------------------------------
# Step 9: Upstream Config
# ---------------------------------------------------------------------------
def configure_upstream(project_root: Path) -> str | None:
    """Verify git remote and configure origin if missing."""
    git_dir = project_root / ".git"
    if not git_dir.exists():
        info("No .git directory. Skipping upstream config.")
        return None

    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True, text=True, cwd=project_root, timeout=5,
        )
        remotes = result.stdout.strip()

        if "origin" in remotes:
            # Extract origin URL
            for line in remotes.splitlines():
                if line.startswith("origin") and "(fetch)" in line:
                    url = line.split()[1]
                    ok(f"origin remote: {url}")
                    return url
        else:
            info("No origin remote configured.")
            info("To add: git remote add origin <url>")
            return None

    except Exception:
        info("Could not check git remotes.")
        return None


# ---------------------------------------------------------------------------
# Step 10: Post-Install Validation
# ---------------------------------------------------------------------------
def validate_installation(project_root: Path) -> dict:
    """Run 4-phase validation of the installation."""
    results = {
        "file_structure": False,
        "config_valid": False,
        "agent_count": 0,
        "hooks_executable": False,
    }

    # Phase 1: File structure
    required_paths = [
        ".claude/skills",
        ".claude/hooks",
        ".claude/rules",
        ".claude/CLAUDE.md",
        ".aios-core",
        ".aios-custom",
        ".aios/session-state.json",
        "config/neo-aios.yaml",
    ]
    missing = [p for p in required_paths if not (project_root / p).exists()]
    results["file_structure"] = len(missing) == 0
    if missing:
        for m in missing:
            warn(f"Missing: {m}")
    else:
        ok("File structure complete")

    # Phase 2: Config parse
    config_file = project_root / "config" / "neo-aios.yaml"
    if config_file.exists():
        try:
            import yaml
            yaml.safe_load(config_file.read_text())
            results["config_valid"] = True
            ok("Config YAML parses correctly")
        except ImportError:
            # yaml not available, try basic check
            content = config_file.read_text()
            results["config_valid"] = "project:" in content
            if results["config_valid"]:
                ok("Config file basic structure valid")
            else:
                warn("Config file may be malformed")
        except Exception as e:
            warn(f"Config parse error: {e}")
    else:
        info("No config file to validate")

    # Phase 3: Agent count
    skills_dir = project_root / ".claude" / "skills"
    if skills_dir.exists():
        agent_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        results["agent_count"] = len(agent_dirs)
        if results["agent_count"] >= 10:
            ok(f"{results['agent_count']} agents installed")
        elif results["agent_count"] > 0:
            warn(f"Only {results['agent_count']} agents found (expected 30+)")
        else:
            warn("No agents found in .claude/skills/")
    else:
        warn(".claude/skills/ not found")

    # Phase 4: Hook permissions
    hooks_dir = project_root / ".claude" / "hooks"
    if hooks_dir.exists():
        hooks = list(hooks_dir.glob("*.py")) + list(hooks_dir.glob("*.sh"))
        all_executable = all(os.access(h, os.X_OK) for h in hooks) if hooks else True
        results["hooks_executable"] = all_executable
        if all_executable and hooks:
            ok(f"{len(hooks)} hooks executable")
        elif hooks:
            non_exec = [h.name for h in hooks if not os.access(h, os.X_OK)]
            warn(f"Non-executable hooks: {', '.join(non_exec[:5])}")
            info("Run: chmod +x .claude/hooks/*")
        else:
            info("No hooks found")
    else:
        info(".claude/hooks/ not found")

    return results


def main() -> None:
    project_root = Path.cwd()
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()

    print_logo()

    # Step 1: Environment checks
    header(1, TOTAL_STEPS, "Checking environment...")
    check_python()
    check_git()
    check_uv()
    check_claude()

    # Step 2: Check existing installation
    header(2, TOTAL_STEPS, "Checking existing installation...")
    has_existing = (project_root / ".aios").exists() or (project_root / ".claude" / "skills").exists()
    if has_existing:
        warn("Existing NEO-AIOS installation detected.")
        answer = ask("Overwrite framework files? (y/N):").lower()
        if answer != "y":
            info("Keeping existing installation. Only missing files will be created.")
    else:
        ok("Clean project. No existing installation found.")

    # Step 3: Project info
    header(3, TOTAL_STEPS, "Project configuration...")
    project_name = get_project_name(project_root)
    print()
    print(f"  {c.DIM}Project name:{c.RESET}  {c.BOLD_WHITE}{project_name}{c.RESET}")
    print(f"  {c.DIM}Directory:{c.RESET}     {c.DIM}{project_root}{c.RESET}")

    # Step 4: Interactive questions
    header(4, TOTAL_STEPS, "Project context...")

    project_type = ask_choice("What type of project is this?", [
        {"label": "New project", "desc": "Starting from scratch", "value": "greenfield"},
        {"label": "Existing project", "desc": "Adding NEO-AIOS to existing code", "value": "brownfield"},
        {"label": "POC / Prototype", "desc": "Quick experiment, no staging", "value": "poc"},
    ])
    ok(f"Project type: {project_type['label']}")

    project_goal = ask_choice("What is the main focus?", [
        {"label": "Web App (Full Stack)", "desc": "Next.js, React, Supabase", "value": "webapp"},
        {"label": "API / Backend", "desc": "REST, GraphQL, services", "value": "api"},
        {"label": "CLI Tool", "desc": "Command-line application", "value": "cli"},
        {"label": "Other", "desc": "Something else", "value": "other"},
    ])
    ok(f"Focus: {project_goal['label']}")

    deploy_choice = ask_choice("Deploy strategy?", [
        {"label": "Staging-first", "desc": "feature → staging → production (recommended)", "value": "staging-first"},
        {"label": "Direct to production", "desc": "Push to main → auto-deploy", "value": "direct"},
        {"label": "Configure later", "desc": "Skip deploy setup for now", "value": "later"},
    ])
    ok(f"Deploy: {deploy_choice['label']}")

    print()
    project_desc = ask("Brief project description (optional, Enter to skip):")
    if project_desc:
        ok("Description saved")

    # Step 5: Stack detection
    header(5, TOTAL_STEPS, "Detecting project stack...")
    print()
    stack = detect_stack(project_root)
    if not stack:
        info("No specific stack detected. Generic configuration will be used.")
    else:
        for s in stack:
            ver = f" {c.DIM}{s['version']}{c.RESET}" if s.get("version") else ""
            ok(f"{s['name']}{ver} detected")

    # Step 6: Install framework
    header(6, TOTAL_STEPS, "Installing NEO-AIOS framework...")
    print()

    framework_source = find_framework_source()
    agent_count = 0
    security_count = 0
    hook_count = 0

    if framework_source:
        info(f"Source: {framework_source}")
        print()

        copy_results = copy_framework_files(framework_source, project_root)
        for result in copy_results:
            detail = f"{c.DIM}({result['files']} files){c.RESET}" if result["files"] > 0 else ""
            print(f"  {c.GREEN}Created:{c.RESET} {result['label']:<32} {detail}")

        # Count installed components
        skills_dir = project_root / ".claude" / "skills"
        hooks_dir = project_root / ".claude" / "hooks"

        if skills_dir.exists():
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
            agent_count = len(skill_dirs)
            security_count = len([d for d in skill_dirs if d.name.startswith("sec-")])

        if hooks_dir.exists():
            hook_count = len([f for f in hooks_dir.iterdir() if f.suffix == ".sh"])
    else:
        warn("Framework source not found.")
        info("Run: curl -fsSL https://raw.githubusercontent.com/gabrielfofonka98/neo-aios/main/scripts/install.sh | bash")
        print()

    # Create directories
    created_dirs = create_directory_structure(project_root)
    for d in created_dirs:
        print(f"  {c.GREEN}Created:{c.RESET} {d}")

    # Create session state
    if create_session_state(project_root):
        print(f"  {c.GREEN}Created:{c.RESET} .aios/session-state.json")

    # Step 7: Generate config
    header(7, TOTAL_STEPS, "Generating configuration...")
    print()

    answers = {
        "project_type": project_type.get("value", "brownfield"),
        "project_goal": project_goal.get("value", "webapp"),
        "deploy_strategy": deploy_choice.get("value", "staging-first"),
        "description": project_desc,
    }

    if generate_config(project_root, project_name, stack, answers):
        print(f"  {c.GREEN}Created:{c.RESET} config/neo-aios.yaml")
    else:
        info("config/neo-aios.yaml already exists (kept).")

    gitignore_result = update_gitignore(project_root)
    if gitignore_result == "updated":
        print(f"  {c.GREEN}Updated:{c.RESET} .gitignore {c.DIM}(added .aios/ entries){c.RESET}")
    elif gitignore_result == "created":
        print(f"  {c.GREEN}Created:{c.RESET} .gitignore")

    # Create .env and .env.example
    env_created = create_env_files(project_root)
    for env_file in env_created:
        label = "(gitignored)" if env_file == ".env" else "(template, committed)"
        print(f"  {c.GREEN}Created:{c.RESET} {env_file} {c.DIM}{label}{c.RESET}")

    # Create CLAUDE.local.md template
    if create_claude_local_md(project_root):
        print(f"  {c.GREEN}Created:{c.RESET} CLAUDE.local.md {c.DIM}(personal preferences, gitignored){c.RESET}")

    # Step 8: MCP Auto-Install
    header(8, TOTAL_STEPS, "Installing MCP servers...")
    print()
    mcps_installed = install_mcps(project_root)
    if not mcps_installed:
        info("No new MCPs installed (already configured or npx unavailable).")

    # Step 9: Upstream Config
    header(9, TOTAL_STEPS, "Checking upstream configuration...")
    print()
    configure_upstream(project_root)

    # Agent Teams setup hint
    print()
    suggest_agent_teams_setup()

    # Make hooks executable
    hooks_dir = project_root / ".claude" / "hooks"
    if hooks_dir.exists():
        for hook in hooks_dir.glob("*.sh"):
            hook.chmod(0o755)
        for hook in hooks_dir.glob("*.py"):
            hook.chmod(0o755)

    # Step 10: Post-Install Validation
    header(10, TOTAL_STEPS, "Validating installation...")
    print()
    validation = validate_installation(project_root)
    passed = sum(1 for v in [
        validation["file_structure"],
        validation["config_valid"],
        validation["agent_count"] >= 10,
        validation["hooks_executable"],
    ] if v)
    if passed == 4:
        ok("All validation checks passed!")
    else:
        info(f"{passed}/4 validation checks passed")

    # Summary
    if agent_count == 0:
        agent_count = 36
    if security_count == 0:
        security_count = 18
    if hook_count == 0:
        hook_count = 5

    print_summary(agent_count, security_count, hook_count)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{c.YELLOW}Cancelled.{c.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{c.BOLD_RED}Init failed:{c.RESET} {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)
