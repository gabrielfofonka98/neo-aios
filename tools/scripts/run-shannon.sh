#!/usr/bin/env bash
# run-shannon.sh — Wrapper for Shannon DAST pentester
# Loads project .env, validates prerequisites, manages Docker lifecycle

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SHANNON_DIR="$PROJECT_ROOT/tools/shannon"
RAW_OUTPUT_DIR="$PROJECT_ROOT/reports/security/shannon/raw"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[shannon]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[shannon]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[shannon]${NC} $1"; }
log_error() { echo -e "${RED}[shannon]${NC} $1"; }

# Load .env from project root
load_env() {
  if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
    log_info "Loaded credentials from $PROJECT_ROOT/.env"
  else
    log_warn "No .env found at $PROJECT_ROOT/.env"
  fi
}

# Validate prerequisites
check_prerequisites() {
  local missing=0

  if ! command -v docker &>/dev/null; then
    log_error "Docker not installed"
    missing=1
  elif ! docker info &>/dev/null 2>&1; then
    log_error "Docker daemon not running"
    missing=1
  else
    log_ok "Docker: available"
  fi

  if [[ ! -f "$SHANNON_DIR/shannon" ]]; then
    log_error "Shannon CLI not found at $SHANNON_DIR/shannon"
    missing=1
  else
    log_ok "Shannon CLI: found"
  fi

  if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    log_error "ANTHROPIC_API_KEY not set (check .env)"
    missing=1
  else
    log_ok "API key: configured"
  fi

  return $missing
}

# Ensure output directories exist
ensure_dirs() {
  mkdir -p "$RAW_OUTPUT_DIR"
}

# Start Shannon pentest
cmd_start() {
  local url="" repo=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --url=*) url="${1#*=}"; shift ;;
      --url)   url="$2"; shift 2 ;;
      --repo=*) repo="${1#*=}"; shift ;;
      --repo)   repo="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$url" ]]; then
    log_error "Usage: run-shannon.sh start --url=<URL> [--repo=<PATH>]"
    exit 1
  fi

  load_env
  check_prerequisites || exit 1
  ensure_dirs

  log_info "Starting Shannon pentest against: $url"

  local shannon_args="URL=$url"
  if [[ -n "$repo" ]]; then
    shannon_args="$shannon_args REPO=$repo"
  fi

  cd "$SHANNON_DIR"
  bash shannon "$shannon_args" 2>&1 | tee "$RAW_OUTPUT_DIR/shannon-$(date +%Y%m%d-%H%M%S).log"
}

# Start with auth config
cmd_start_with_auth() {
  local url="" repo="" config=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --url=*) url="${1#*=}"; shift ;;
      --url)   url="$2"; shift 2 ;;
      --repo=*) repo="${1#*=}"; shift ;;
      --repo)   repo="$2"; shift 2 ;;
      --config=*) config="${1#*=}"; shift ;;
      --config)   config="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$url" || -z "$config" ]]; then
    log_error "Usage: run-shannon.sh start-with-auth --url=<URL> --config=<PATH> [--repo=<PATH>]"
    exit 1
  fi

  load_env
  check_prerequisites || exit 1
  ensure_dirs

  log_info "Starting Shannon pentest (with auth) against: $url"
  log_info "Auth config: $config"

  cd "$SHANNON_DIR"
  bash shannon "URL=$url REPO=${repo:-}" --config "$config" 2>&1 | tee "$RAW_OUTPUT_DIR/shannon-auth-$(date +%Y%m%d-%H%M%S).log"
}

# Show logs
cmd_logs() {
  cd "$SHANNON_DIR"
  if [[ -d audit-logs ]]; then
    ls -la audit-logs/
    echo ""
    log_info "Latest log:"
    # shellcheck disable=SC2012
    local latest
    latest=$(ls -t audit-logs/*.log 2>/dev/null | head -1)
    if [[ -n "$latest" ]]; then
      tail -50 "$latest"
    else
      log_warn "No log files found"
    fi
  else
    log_warn "No audit-logs directory found"
  fi
}

# Query specific finding
cmd_query() {
  local id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id=*) id="${1#*=}"; shift ;;
      --id)   id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$id" ]]; then
    log_error "Usage: run-shannon.sh query --id=<FINDING_ID>"
    exit 1
  fi

  cd "$SHANNON_DIR"
  if [[ -d audit-logs ]]; then
    grep -r "$id" audit-logs/ 2>/dev/null || log_warn "Finding $id not found"
  else
    log_warn "No audit-logs directory"
  fi
}

# Stop Shannon containers
cmd_stop() {
  log_info "Stopping Shannon containers..."
  cd "$SHANNON_DIR"
  docker compose down 2>/dev/null || docker-compose down 2>/dev/null || log_warn "No containers to stop"
  log_ok "Containers stopped"
}

# Stop and clean volumes
cmd_stop_clean() {
  log_info "Stopping Shannon containers and removing volumes..."
  cd "$SHANNON_DIR"
  docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null || log_warn "No containers to stop"
  log_ok "Containers stopped, volumes removed"
}

# Show status
cmd_status() {
  log_info "Shannon container status:"
  docker ps --filter "name=shannon" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || log_warn "No Shannon containers found"
  echo ""
  log_info "Docker status:"
  docker info --format "{{.ServerVersion}}" 2>/dev/null && log_ok "Docker running" || log_error "Docker not running"
}

# Show Temporal UI URL
cmd_temporal_ui() {
  local port="${TEMPORAL_UI_PORT:-8233}"
  log_info "Temporal UI: http://localhost:$port"
  log_info "(Ensure Shannon is running with 'run-shannon.sh start')"
}

# Show help
cmd_help() {
  cat <<'HELP'
Shannon DAST Wrapper — NEO-AIOS Integration

COMMANDS:
  start --url=<URL> [--repo=<PATH>]           Launch Shannon pentest
  start-with-auth --url=<URL> --config=<PATH> Launch with auth config
  stop                                         Stop Shannon containers
  stop-clean                                   Stop + remove volumes
  status                                       Show container status
  logs                                         Show latest audit logs
  query --id=<ID>                              Query specific finding
  temporal-ui                                  Show Temporal UI URL
  help                                         Show this help

PREREQUISITES:
  - Docker installed and running
  - ANTHROPIC_API_KEY in .env
  - Shannon submodule at tools/shannon/

OUTPUT:
  Raw logs  → reports/security/shannon/raw/ (gitignored)
  Reports   → reports/security/shannon/     (versioned)

EXAMPLES:
  run-shannon.sh start --url=https://example.com
  run-shannon.sh start --url=https://example.com --repo=/path/to/repo
  run-shannon.sh start-with-auth --url=https://example.com --config=config/shannon-auth.yaml
  run-shannon.sh logs
  run-shannon.sh stop
HELP
}

# Main dispatch
case "${1:-help}" in
  start)           shift; cmd_start "$@" ;;
  start-with-auth) shift; cmd_start_with_auth "$@" ;;
  stop)            cmd_stop ;;
  stop-clean)      cmd_stop_clean ;;
  status)          cmd_status ;;
  logs)            cmd_logs ;;
  query)           shift; cmd_query "$@" ;;
  temporal-ui)     cmd_temporal_ui ;;
  help|--help|-h)  cmd_help ;;
  *)               log_error "Unknown command: $1"; cmd_help; exit 1 ;;
esac
