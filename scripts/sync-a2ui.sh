#!/usr/bin/env bash
set -euo pipefail

# Default tag to v0.1.8 if not provided
TAG="${1:-v0.1.8}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENDOR_DIR="$ROOT_DIR/vendor/maui-a2ui-python"
A2UI_REPO_DIR="${A2UI_REPO_DIR:-$ROOT_DIR/../a2ui}"

echo "==> Updating a2ui vendor package to $TAG..."

if [ ! -d "$A2UI_REPO_DIR/.git" ]; then
    echo "Error: a2ui repo not found at $A2UI_REPO_DIR" >&2
    echo "Please set A2UI_REPO_DIR to the location of the googlemaps/a2ui git clone." >&2
    exit 1
fi

# Fetch and checkout target tag in a2ui repo
echo "==> Fetching tags from a2ui repository..."
git -C "$A2UI_REPO_DIR" fetch --tags
git -C "$A2UI_REPO_DIR" checkout "$TAG"

# Clean and copy files
echo "==> Copying agent/python_agent to vendor/maui-a2ui-python..."
rm -rf "$VENDOR_DIR"
mkdir -p "$VENDOR_DIR"
cp -r "$A2UI_REPO_DIR/agent/python_agent/"* "$VENDOR_DIR/"
rm -rf "$VENDOR_DIR/.venv" "$VENDOR_DIR/__pycache__"

# Save version info
echo "$TAG" > "$VENDOR_DIR/VERSION"
git -C "$A2UI_REPO_DIR" rev-parse HEAD >> "$VENDOR_DIR/VERSION"

# Update lockfile
echo "==> Updating uv.lock..."
(cd "$ROOT_DIR" && uv lock)

echo "==> Successfully synced maui-a2ui-python to $TAG"
