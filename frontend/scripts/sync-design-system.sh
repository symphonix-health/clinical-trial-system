#!/bin/sh
# Sync minimal Symphonix Health design system assets from submodule to public/
# Run from frontend/scripts/.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$FRONTEND_DIR")"
SOURCE_ROOT="$REPO_ROOT/.agents/skills/symphonix-health-design"
DEST_ROOT="$FRONTEND_DIR/public/design-system"

for f in colors_and_type.css healthcare/tokens.css; do
  src="$SOURCE_ROOT/$f"
  dst="$DEST_ROOT/$f"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
done

FONT_SRC="$SOURCE_ROOT/assets/fonts"
FONT_DST="$DEST_ROOT/assets/fonts"
mkdir -p "$FONT_DST"
cp -r "$FONT_SRC/." "$FONT_DST/"
