#!/bin/bash

set -e

DMG_NAME="EasyABC_1.4.0.dmg"
VOL_NAME="EasyABC 1.4.0"
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
hdiutil create -size 200m -fs HFS+ -volname "$VOL_NAME" "$TEMP_DMG"

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

if [ ! -f "img/abclogo.png" ]; then
    echo "❌ Background image missing: img/abclogo.png"
    exit 1
fi
mkdir "$TEMP_VOL/.background"
cp "img/abclogo.png" "$TEMP_VOL/.background/"

echo ""
echo "=============================================================="
echo " $TEMP_VOL will be opened in Finder to prepare the dmg layout"
echo " The $TEMP_VOL/.background folder will also be opened to ease the background selection"
echo " You then need to:"
echo "  - Set background image from .background/background.png"
echo "  - Position icons"
echo "  - Close the Finder window to save .DS_Store"
echo "  - Come back to this Terminal to confirm everything is ready"
echo "=============================================================="
echo ""
read -p "Press ENTER to open $TEMP_VOL in Finder and set appropriate layout..."
open "$TEMP_VOL"
open "$TEMP_VOL/.background"
read -p "Press ENTER when the layout is ready..."

# Build final DMG from the HFS+ volume
hdiutil create "dist/$DMG_NAME" -srcdevice "$DEV"

# Unmount and clean
hdiutil detach "$TEMP_VOL"
rm -f "$TEMP_DMG"

echo "DMG created: dist/$DMG_NAME"
