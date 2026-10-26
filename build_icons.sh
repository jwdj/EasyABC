#!/bin/bash

set -e

# For now use png instead of SVG
# Issue with svg is that there might be some errors because of fonts
# Need to rework the svg to flatten them with Inkscape
# For now the png are generated with GIMP in 1024
APP_SVG="img-src/easyabc_logo.png"
DOC_SVG="img-src/abcfile_logo.png"

mkdir -p build/icons/app
mkdir -p build/icons/doc

SIZES="16 32 48 64 128 256 512 1024"

echo "=== Build PNG ==="

for s in $SIZES; do
    magick "$APP_SVG" -background none -resize ${s}x${s} build/icons/app/easyabc_${s}.png
    magick "$DOC_SVG" -background none -resize ${s}x${s} build/icons/doc/abcfile_${s}.png
done

echo "=== Build ICO for Windows ==="

magick \
    build/icons/app/easyabc_16.png \
    build/icons/app/easyabc_32.png \
    build/icons/app/easyabc_48.png \
    build/icons/app/easyabc_64.png \
    build/icons/app/easyabc_128.png \
    build/icons/app/easyabc_256.png \
    img/EasyABC.ico

magick \
    build/icons/doc/abcfile_16.png \
    build/icons/doc/abcfile_32.png \
    build/icons/doc/abcfile_48.png \
    build/icons/doc/abcfile_64.png \
    build/icons/doc/abcfile_128.png \
    build/icons/doc/abcfile_256.png \
    img/ABCFile.ico

echo "=== Build ICNS for macOS ==="

mkdir -p build/easyabc.iconset

cp build/icons/app/easyabc_16.png    build/easyabc.iconset/icon_16x16.png
cp build/icons/app/easyabc_32.png    build/easyabc.iconset/icon_16x16@2x.png
cp build/icons/app/easyabc_32.png    build/easyabc.iconset/icon_32x32.png
cp build/icons/app/easyabc_64.png    build/easyabc.iconset/icon_32x32@2x.png
cp build/icons/app/easyabc_128.png   build/easyabc.iconset/icon_128x128.png
cp build/icons/app/easyabc_256.png   build/easyabc.iconset/icon_128x128@2x.png
cp build/icons/app/easyabc_256.png   build/easyabc.iconset/icon_256x256.png
cp build/icons/app/easyabc_512.png   build/easyabc.iconset/icon_256x256@2x.png
cp build/icons/app/easyabc_512.png   build/easyabc.iconset/icon_512x512.png
cp build/icons/app/easyabc_1024.png  build/easyabc.iconset/icon_512x512@2x.png

iconutil -c icns build/easyabc.iconset

mkdir -p build/abcfile.iconset

cp build/icons/doc/abcfile_16.png   build/abcfile.iconset/icon_16x16.png
cp build/icons/doc/abcfile_32.png   build/abcfile.iconset/icon_16x16@2x.png
cp build/icons/doc/abcfile_32.png   build/abcfile.iconset/icon_32x32.png
cp build/icons/doc/abcfile_64.png   build/abcfile.iconset/icon_32x32@2x.png
cp build/icons/doc/abcfile_128.png  build/abcfile.iconset/icon_128x128.png
cp build/icons/doc/abcfile_256.png  build/abcfile.iconset/icon_128x128@2x.png
cp build/icons/doc/abcfile_256.png  build/abcfile.iconset/icon_256x256.png
cp build/icons/doc/abcfile_512.png  build/abcfile.iconset/icon_256x256@2x.png
cp build/icons/doc/abcfile_512.png  build/abcfile.iconset/icon_512x512.png
cp build/icons/doc/abcfile_1024.png build/abcfile.iconset/icon_512x512@2x.png

iconutil -c icns build/abcfile.iconset

mv build/easyabc.icns img/EasyABC.icns
mv build/abcfile.icns img/ABCFile.icns
echo "=== Icons built ==="