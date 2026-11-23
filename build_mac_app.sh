#!/bin/bash
# EasyABC non-interactive app builder (py2app + Helpers + ad-hoc codesign).
# Replaces the interactive parts of build.sh: no read prompts, no Finder/AppleScript.
# Usage: ./build_app.sh <universal2|arm64|x86_64>
# Env override: HELPER_DIR (default: resolved from arch, see below)
set -euo pipefail

ARCH="${1:-}"
if [ -z "$ARCH" ]; then
    echo "Usage: $0 <universal2|arm64|x86_64>"
    exit 1
fi

case "$ARCH" in
  universal2) BIN_DIR="${HELPER_DIR:-bin}" ;;   # expects universal (lipo'd) binaries in HELPER_DIR
  arm64)      BIN_DIR="bin/mac_arm64" ;;
  x86_64)     BIN_DIR="bin/mac_x86_64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

APP="dist/EasyABC.app"

echo "== Building py2app ($ARCH) =="
python setup.py py2app

echo "== Creating lproj files to enable translations =="
for d in locale/*/; do
    [ -f "${d}LC_MESSAGES/easyabc.mo" ] || continue
    name=$(basename "$d")
    mkdir -p "$APP/Contents/Resources/${name}.lproj"
done
mkdir -p "$APP/Contents/Resources/English.lproj"

echo "== Copying binaries to Helpers =="
#FAU 20240103: there shall be no executable within Resources folder. Keep them in Helpers or MacOS
mkdir -p "$APP/Contents/Helpers"

# Binaries required for EasyABC core functionality
REQUIRED_HELPERS=(abcm2ps abc2abc abc2midi midi2abc)
for h in "${REQUIRED_HELPERS[@]}"; do
    if [ ! -f "${BIN_DIR}/$h" ]; then
        echo "ERROR: ${BIN_DIR}/$h is required but missing" >&2
        exit 1
    fi
    cp "${BIN_DIR}/$h" "$APP/Contents/Helpers/"
done

lipo -info "${BIN_DIR}/$h" | grep -q "arm64" && lipo -info "${BIN_DIR}/$h" | grep -q "x86_64"

# Optional: NWC import only, not available on Apple Silicon
if [ -f "${BIN_DIR}/nwc2xml" ]; then
    cp "${BIN_DIR}/nwc2xml" "$APP/Contents/Helpers/"
    echo "nwc2xml: included (NWC import available)"
else
    echo "nwc2xml: not included (NWC import unavailable on this arch)"
fi

echo "Helpers content:"
ls -lh "$APP/Contents/Helpers"

echo "== Removing quarantine =="
xattr -cr "$APP"

echo "== Signing included binaries =="
find "$APP" -type f \( -name "*.dylib" -o -name "*.so" \) -exec \
    codesign --force --sign - {} \;
codesign --force --sign - "$APP/Contents/MacOS/python"
for fw in "$APP"/Contents/Frameworks/*.framework; do
    [ -d "$fw" ] && codesign --force --sign - "$fw"
done
codesign --force --sign - "$APP/Contents/Helpers/"*

echo "== Signing App =="
codesign --force --sign - "$APP"

echo "== Verifying signature =="
codesign --verify --verbose "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

spctl -a -vv "$APP" || true # expected rejection: ad-hoc signature only

echo "App built: $APP ($ARCH)"
