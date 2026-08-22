#!/bin/sh
# Sync minimal Symphonix Health design system assets from submodule to public/
# Cross-platform shell script for Linux/macOS environments.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT/.agents/skills/symphonix-health-design"
DEST_ROOT="$SCRIPT_DIR/../public/design-system"

for f in colors_and_type.css healthcare/tokens.css; do
  src="$SOURCE_ROOT/$f"
  dst="$DEST_ROOT/$f"
  mkdir -p "$(dirname "$dst")"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
  fi
done

font_src="$SOURCE_ROOT/assets/fonts"
font_dst="$DEST_ROOT/assets/fonts"
if [ -d "$font_src" ]; then
  mkdir -p "$font_dst"
  cp -r "$font_src/." "$font_dst/"
fi
