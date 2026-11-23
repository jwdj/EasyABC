#!/bin/bash
# EasyABC non-interactive DMG builder using create-dmg.
# Replaces the Finder/AppleScript layout step of build.sh.
# Prerequisite: brew install create-dmg
# Usage: ./make_dmg.sh <output.dmg>
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <output.dmg>"
    exit 1
fi
OUT="$1"

VERSION=$(grep "^program_version[[:space:]]*=" easyabc_version.py | sed -E "s/.*'([^']+)'.*/\1/")
VOL_NAME="EasyABC ${VERSION}"

if [ ! -d dist/EasyABC.app ]; then
    echo "ERROR: dist/EasyABC.app missing. Run build_mac_app.sh first." >&2
    exit 1
fi

BACKGROUND="img/Background-DMG.png"
if [ ! -f "$BACKGROUND" ]; then
    echo "ERROR: Background image missing: $BACKGROUND" >&2
    exit 1
fi

STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

# Mirror the old "cp -R dmg/ $TEMP_VOL/" : extra DMG contents live in dmg/
if [ -d dmg ]; then
    cp -R dmg/* "$STAGING/"
fi

cp -R dist/EasyABC.app "$STAGING/"

if [ ! -f "$STAGING/Ghostscript.pkg" ]; then
    echo "Ghostscript.pkg not present, downloading it from https://pages.uoregon.edu/koch/"
    curl --fail -sL https://pages.uoregon.edu/koch/Ghostscript-10.07.1.pkg \
        -o "$STAGING/Ghostscript.pkg"
fi

# Icon layout mirrors the previous AppleScript (window 200,100 -> 1100,700)
create-dmg \
    --volname "$VOL_NAME" \
    --background "$BACKGROUND" \
    --window-pos 200 100 \
    --window-size 900 600 \
    --icon-size 104 \
    --text-size 16 \
    --icon "EasyABC.app" 170 250 \
    --app-drop-link 420 250 \
    --icon "README" 670 250 \
    --icon "Ghostscript.pkg" 420 420 \
    --icon "Install_Ghostscript.webloc" 170 420 \
    --icon "Fix_EasyABC_damaged.scpt" 670 420 \
    --no-internet-enable \
    "$OUT" "$STAGING"

echo "DMG created: $OUT"
