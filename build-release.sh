#!/bin/bash
# Build and package TinyNotes for distribution

set -e

VERSION=${1:-"1.0.0"}

echo "======================================"
echo "Building TinyNotes v${VERSION}"
echo "======================================"

# Check if py2app is installed
if ! ./venv/bin/pip show py2app > /dev/null 2>&1; then
    echo "Installing py2app..."
    ./venv/bin/pip install py2app
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "Building .app bundle..."
./venv/bin/python setup.py py2app

# Verify build
if [ ! -d "dist/TinyNotes.app" ]; then
    echo "ERROR: Build failed - TinyNotes.app not found"
    exit 1
fi

# Test the app
echo "Testing app launch..."
open dist/TinyNotes.app
sleep 3
pkill -f "TinyNotes.app"

# Create release directory
mkdir -p releases

# Create zip for distribution
echo "Creating release package..."
cd dist
zip -r "../releases/TinyNotes-${VERSION}.zip" TinyNotes.app
cd ..

# Calculate SHA256
echo ""
echo "======================================"
echo "Build Complete!"
echo "======================================"
echo ""
echo "Release package: releases/TinyNotes-${VERSION}.zip"
echo ""
echo "SHA256 (for Homebrew Cask):"
shasum -a 256 "releases/TinyNotes-${VERSION}.zip"
echo ""
echo "Next steps:"
echo "1. Test: open dist/TinyNotes.app"
echo "2. Upload releases/TinyNotes-${VERSION}.zip to GitHub release v${VERSION}"
echo "3. Update Homebrew Cask with the SHA256 hash above"
echo ""
