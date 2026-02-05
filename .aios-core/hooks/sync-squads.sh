#!/usr/bin/env bash
# Sync squads/ → .claude/commands/
# Run: .aios-core/hooks/sync-squads.sh

set -e
cd "$(git rev-parse --show-toplevel)"

echo "🔄 Syncing squads → .claude/commands..."

# Sync function
sync_pack() {
  local pack="$1"
  local target="$2"
  local source_dir="squads/$pack"
  local target_dir=".claude/commands/$target"

  if [ -d "$source_dir/agents" ]; then
    rm -rf "$target_dir/agents"
    mkdir -p "$target_dir/agents"
    cp -r "$source_dir/agents/"* "$target_dir/agents/" 2>/dev/null || true
    echo "  ✓ $pack → $target (agents)"
  fi

  if [ -d "$source_dir/workflows" ]; then
    rm -rf "$target_dir/workflows"
    mkdir -p "$target_dir/workflows"
    cp -r "$source_dir/workflows/"* "$target_dir/workflows/" 2>/dev/null || true
    echo "  ✓ $pack → $target (workflows)"
  fi
}

# Mapping: squad → CommandFolder
sync_pack "artifacts" "Artifacts"
sync_pack "book-summary" "BookSummary"
sync_pack "compound" "Compound"
sync_pack "copy" "Copy"
sync_pack "creator-os" "CreatorOS"
sync_pack "db-sage" "DbSage"
sync_pack "design" "Design"
sync_pack "expansion-creator" "expansionCreator"
sync_pack "innerlens" "InnerLens"
sync_pack "mmos" "MMOS"
sync_pack "multi-lens-framework" "MultiLensFramework"
sync_pack "ralph" "Ralph"
sync_pack "super-agentes" "SA"
sync_pack "tools" "Tools"

# Sync AIOS from .aios-core
if [ -d ".aios-core/agents" ]; then
  rm -rf ".claude/commands/AIOS/agents"
  mkdir -p ".claude/commands/AIOS/agents"
  cp -r .aios-core/agents/* ".claude/commands/AIOS/agents/"
  echo "  ✓ .aios-core/agents → AIOS"
fi

echo "✅ Sync complete!"
