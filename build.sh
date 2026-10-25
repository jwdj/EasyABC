#!/bin/bash
set -e

if [ $# -eq 0 ]; then
    echo "To specify arch:"
    echo "  Usage: $0 <arch>"
    echo "For now continuing with bin"
    BIN_DIR="bin"
else
    ARCH="$1"

    case "$ARCH" in
      arm64)
        BIN_DIR="bin/mac_arm64"
        DMG_SUFFIX="arm64"
        ;;
      x86_64)
        BIN_DIR="bin/mac_x86_64"
        DMG_SUFFIX="x86_64"
        ;;
      *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
    esac
fi

VERSION=$(grep "^program_version[[:space:]]*=" easyabc_version.py | sed -E "s/.*'([^']+)'.*/\1/")
VOL_NAME="EasyABC ${VERSION}"
DMG_NAME="EasyABC_${VERSION}_${DMG_SUFFIX}.dmg"
#echo "DMG_NAME=${DMG_NAME}" >> "$GITHUB_ENV"


echo "Building py2app"
python setup.py py2app

echo "Creating lproj files to enable translations"
for d in locale/*/; do
    [ -f "${d}LC_MESSAGES/easyabc.mo" ] || continue
    name=$(basename "$d")
    mkdir -p "dist/EasyABC.app/Contents/Resources/${name}.lproj"
done
mkdir "dist/EasyABC.app/Contents/Resources/English.lproj"   

echo "Copying binaries to Helpers"
#FAU 20240103: there shall be no executable within Resources folder. Need to move them to Helpers or MacOS
mkdir -p dist/EasyABC.app/Contents/Helpers
#cp bin/* dist/EasyABC.app/Contents/Helpers
#find bin -maxdepth 1 -type f -exec cp {} dist/EasyABC.app/Contents/Helpers \;

# Binaries required for EasyABC core functionality
REQUIRED_HELPERS=(abcm2ps abc2abc abc2midi midi2abc)
for h in "${REQUIRED_HELPERS[@]}"; do
    if [ ! -f "${BIN_DIR}/$h" ]; then
        echo "ERROR: ${BIN_DIR}/$h is required but missing" >&2
        exit 1
    fi
    cp "${BIN_DIR}/$h" dist/EasyABC.app/Contents/Helpers/
done

# Optional: NWC import only, not available on Apple Silicon
if [ -f "${BIN_DIR}/nwc2xml" ]; then
    cp "${BIN_DIR}/nwc2xml" dist/EasyABC.app/Contents/Helpers/
    echo "nwc2xml: included (NWC import available)"
else
    echo "nwc2xml: not included (NWC import unavailable on this arch)"
fi

echo "Helpers content:"
ls -lh dist/EasyABC.app/Contents/Helpers

echo "Removing quarantine"
xattr -cr dist/EasyABC.app

echo "Signing included binaries"
find dist/EasyABC.app -type f \( -name "*.dylib" -o -name "*.so" \) -exec \
    codesign --force --sign - {} \;
codesign --force --sign - dist/EasyABC.app/Contents/MacOS/python
for fw in dist/EasyABC.app/Contents/Frameworks/*.framework; do
    [ -d "$fw" ] && codesign --force --sign - "$fw"
done
codesign --force --sign - dist/EasyABC.app/Contents/Helpers/*

echo "Signing App"
codesign --force --sign - dist/EasyABC.app

echo "Verifying signature"
codesign --verify --verbose dist/EasyABC.app
codesign --verify --deep --strict --verbose=2 dist/EasyABC.app

spctl -a -vv dist/EasyABC.app || true # it is expected to return a rejection as only ad-hoc sign

SRC_DIR="dmg"
TEMP_DMG="/tmp/easyabc_temp.dmg"
TEMP_VOL="/Volumes/$VOL_NAME"

#
# Remove temporary DMG if user confirmed
#
if [ -f "$TEMP_DMG" ]; then
    echo "⚠️  Warning: $TEMP_DMG already exists."
    read -p "Delete it and continue? (y/N): " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        rm -f "$TEMP_DMG"
        if [ $? -ne 0 ]; then
            echo "❌ Error: failed to delete $TEMP_DMG"
            exit 1
        fi
        echo "✔ Deleted $TEMP_DMG"
    else
        echo "❌ Aborting."
        exit 1
    fi
fi

#
# Unmount volume if already mounted
#
if [ -d "$TEMP_VOL" ]; then
    echo "⚠️  Warning: Volume $TEMP_VOL is already mounted."
    read -p "Unmount it and continue? (y/N): " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        hdiutil detach "$TEMP_VOL"
        if [ $? -ne 0 ]; then
            echo "❌ Error: failed to detach $TEMP_VOL"
            exit 1
        fi
        echo "✔ Unmounted $TEMP_VOL"
    else
        echo "❌ Aborting."
        exit 1
    fi
fi

# Remove old DMG
rm -f "dist/$DMG_NAME"

# Create temporary HFS+ volume (adjust size if needed)
#hdiutil create -size 200m -fs HFS+ -volname EasyABC_TEMP "$TEMP_DMG"
DMG_SIZE=(`du -m -s "dist" | tail -1`)
DMG_SIZE=$(( $DMG_SIZE + 50 ))

hdiutil create -size ${DMG_SIZE}M -fs HFS+ -volname "$VOL_NAME" "$TEMP_DMG"

# Mount it
#hdiutil attach "$TEMP_DMG"
DEV=$(hdiutil attach "$TEMP_DMG" | grep Apple_HFS | awk '{print $1}')

echo "Temporary DMG file mounted on device: $DEV"

# Copy DMG contents into the HFS+ volume
cp -R "$SRC_DIR/" "$TEMP_VOL/"

#osascript -e 'tell application "Finder" to make alias file to POSIX file "/Applications" at POSIX file "'"$TEMP_VOL"'"'
ln -s /Applications "$TEMP_VOL/Applications"

if [ -d "dist/EasyABC.app" ]; then
    echo "Copy EasyABC.app to Volume $TEMP_VOL." 
    cp -R "dist/EasyABC.app" "$TEMP_VOL/"
fi

if [ ! -f "$TEMP_VOL/Ghostscript.pkg" ]; then
    echo "⚠️  Warning: Ghostscript.pkg not present, downloading it from https://pages.uoregon.edu/koch/"

    curl https://pages.uoregon.edu/koch/Ghostscript-10.07.1.pkg -o "$TEMP_VOL/Ghostscript.pkg"
fi

if [ ! -f "img/Fond-DMG.png" ]; then
    echo "❌ Background image missing: img/Fond-DMG.png"
    exit 1
fi
mkdir "$TEMP_VOL/.background"
cp "img/Fond-DMG.png" "$TEMP_VOL/.background/"

ls -al "$SRC_DIR"
ls -al "$TEMP_VOL"
read -p "Press ENTER when the layout is ready..."

echo ""
echo "Running an AppleScript to set up view properties of the .dmg (from xojo2dmg)"
echo '
   tell application "Finder"
     tell disk "'${VOL_NAME}'"
           open
           delay 2
		   activate
		   delay 1
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set viewOptions to the icon view options of container window
           delay 1
           set the bounds of container window to {'200, 100, 1100, 700'}
           delay 1
           set arrangement of viewOptions to not arranged
           set background picture of viewOptions to file ".background:Fond-DMG.png"
           delay 1
           set position of item "Install_Ghostscript.webloc" of container window to {'170, 450'}
           delay 1
           set position of item "Ghostscript.pkg" of container window to {'420, 450'}
           delay 1
           set position of item "README" of container window to {'670, 250'}
           delay 1
           set position of item "Applications" of container window to {'420, 250'}
           delay 1
           set position of item "EasyABC.app" of container window to {'170, 250'}
           delay 1
           set icon size of viewOptions to '104'
           set text size of viewOptions to '16'
           delay 2
           close
           open
           update without registering applications
           delay 4
     end tell
   end tell
' | osascript

sync
sleep 2

# Build final DMG from the HFS+ volume
hdiutil create "dist/$DMG_NAME" -srcdevice "$DEV"

# Unmount and clean
hdiutil detach "$TEMP_VOL"
rm -f "$TEMP_DMG"

echo "DMG created: dist/$DMG_NAME"