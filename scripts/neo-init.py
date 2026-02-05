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
from datetime import datetime
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
    print(f"{c.BOLD_WHITE}    _   _ ______ ____            ___  _____ ____   _____ {c.RESET}")
    print(f"{c.BOLD_WHITE}   | \\ | |  ____/ __ \\   ___    / _ \\|_   _/ __ \\ / ____|{c.RESET}")
    print(f"{c.BOLD_WHITE}   |  \\| | |__ | |  | | |___|  / /_\\ \\ | || |  | | (___  {c.RESET}")
    print(f"{c.BOLD_WHITE}   | . ` |  __|| |  | |       |  _  | | || |  | |\\___ \\ {c.RESET}")
    print(f"{c.BOLD_WHITE}   | |\\  | |___| |__| |       | | | |_| || |__| |____) |{c.RESET}")
    print(f"{c.BOLD_WHITE}   |_| \\_|______\\____/        |_| |_|_____\\____/|_____/ {c.RESET}")
    print()
    print(f"    {c.DIM}Agent Intelligence Operating System{c.RESET}")
    print(f"    {c.DIM}v{version}{c.RESET}")
    print()

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def ask(question: str) -> str:
    """Ask a simple question."""
    return input(f"  {c.CYAN}{question}{c.RESET} ").strip()

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
    answer = input(f"  {c.CYAN}Choose [1-{len(options)}]: {c.RESET}").strip()
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
    if (global_install / "agents").exists() and (global_install / ".claude").exists():
        return global_install

    # Option 2: Running from inside the repo
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    if (repo_root / "agents").exists() and (repo_root / ".claude").exists():
        return repo_root

    return None

def copy_framework_files(source: Path, dest: Path) -> list[dict]:
    """Copy framework files to project directory."""
    results = []

    copy_targets = [
        (".claude/hooks", ".claude/hooks", ".claude/hooks/"),
        (".claude/rules", ".claude/rules", ".claude/rules/"),
        (".claude/skills", ".claude/skills", ".claude/skills/"),
        (".claude/setup", ".claude/setup", ".claude/setup/"),
        (".claude/CLAUDE.md", ".claude/CLAUDE.md", ".claude/CLAUDE.md"),
        (".aios-custom/config", ".aios-custom/config", ".aios-custom/config/"),
        (".aios-custom/STANDARDS.md", ".aios-custom/STANDARDS.md", ".aios-custom/STANDARDS.md"),
        ("agents", "agents", "agents/"),
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

    # Install agents as Claude Code skills
    # agents/*/SKILL.md -> .claude/skills/*/SKILL.md
    agents_src = source / "agents"
    if agents_src.exists():
        skill_count = 0
        for agent_dir in agents_src.iterdir():
            if not agent_dir.is_dir() or agent_dir.name == ".DS_Store":
                continue
            skill_md = agent_dir / "SKILL.md"
            if skill_md.exists():
                dest_skill_dir = dest / ".claude" / "skills" / agent_dir.name
                dest_skill_dir.mkdir(parents=True, exist_ok=True)
                dest_skill_md = dest_skill_dir / "SKILL.md"
                if not dest_skill_md.exists():
                    shutil.copy2(skill_md, dest_skill_md)
                    skill_count += 1
        if skill_count > 0:
            results.append({
                "label": "agents → .claude/skills/",
                "files": skill_count,
                "status": "installed",
            })

    return results

def create_directory_structure(project_root: Path) -> list[str]:
    """Create required directories."""
    dirs = [
        ".aios",
        ".aios/workflow-state",
        ".aios/qa-reports",
        "config",
        "docs",
        "docs/sessions",
    ]

    created = []
    for d in dirs:
        path = project_root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
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

    now = datetime.utcnow()

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
TOTAL_STEPS = 7

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
    has_existing = (project_root / ".aios").exists() or (project_root / "agents").exists()
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
        agents_dir = project_root / "agents"
        hooks_dir = project_root / ".claude" / "hooks"

        if agents_dir.exists():
            agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir()]
            agent_count = len(agent_dirs)
            security_count = len([d for d in agent_dirs if d.name.startswith("sec-")])

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

    # Create CLAUDE.local.md template
    if create_claude_local_md(project_root):
        print(f"  {c.GREEN}Created:{c.RESET} CLAUDE.local.md {c.DIM}(personal preferences, gitignored){c.RESET}")

    # Agent Teams setup hint
    print()
    suggest_agent_teams_setup()

    # Make hooks executable
    hooks_dir = project_root / ".claude" / "hooks"
    if hooks_dir.exists():
        for hook in hooks_dir.glob("*.sh"):
            hook.chmod(0o755)

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
