#!/usr/bin/env bash
# build_deb.sh — Build of debian package
set -e

cd "$(dirname "$0")"

# IM7 (macOS/brew) command is "magick",
# IM6 (Debian/Xubuntu) command is "convert"
if command -v magick >/dev/null 2>&1; then
    IM="magick"
elif command -v convert >/dev/null 2>&1; then
    IM="convert"
else
    echo "ImageMagick not found (magick or convert)"; exit 1
fi

# Todo switch to flat svg
APP_SRC="img-src/easyabc_logo.png"     # high res (1024)
DOC_SRC="img-src/abcfile_logo.png"
SIZES="16 32 48 64 128 256"

echo "=== Page man ==="
pandoc easyabc.1.md -s -t man > easyabc.1

echo "=== Hicolor icons ==="
HICOLOR=build/icons/debian/hicolor
rm -rf "$HICOLOR"
for s in $SIZES; do
    mkdir -p "$HICOLOR/${s}x${s}/apps" "$HICOLOR/${s}x${s}/mimetypes"
    "$IM" "$APP_SRC" -background none -filter Lanczos -resize ${s}x${s} "$HICOLOR/${s}x${s}/apps/easyabc.png"
    "$IM" "$DOC_SRC" -background none -filter Lanczos -resize ${s}x${s} "$HICOLOR/${s}x${s}/mimetypes/text-vnd-abc.png"
done

echo "=== Update debian/install ==="
generate_install() {
    # The following populate according to what is needed
    # Files related to running from sources, translation, windows script, build scripts are excluded
    # creating_an_executable.txt, easy_abc.txt, requirements.txt, translating_EasyABC.txt,
    # using_EasyABC_in_Linux.txt, using_EasyABC_in_Windows.txt, update_i18n.bat, setup.py
    # Specific files
    echo "easyabc.1 usr/share/man/man1/"
    echo ""
    echo "easyabc usr/bin"
    echo ""
    echo "easyabc.desktop usr/share/applications"
    echo "easyabc.xml usr/share/mime/packages"
    echo ""
    echo "CHANGES usr/share/easyabc"
    echo "gpl-license.txt usr/share/easyabc"
    echo "LICENSE usr/share/easyabc"
    echo "README.md usr/share/easyabc"
    echo "readme.txt usr/share/easyabc"
    echo "reference.txt usr/share/easyabc"
    echo ""

    find build/icons/debian/hicolor -type f | sort | while read -r f; do
        echo "$f usr/share/icons${f#build/icons/debian}"
    done
    echo ""

    find locale -name '*.mo' -type f | sort | awk '
        { n=split($0,p,"/"); print $0 " usr/share/locale/" p[2] "/LC_MESSAGES" }'
    echo ""

    # All other files to /usr/share/easyabc
    find . -type f -name '*.py' -maxdepth 1 | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
    echo ""

    find docs -type f  \
        -not -path '*/__pycache__/*' \
        -not -name '*.pyc' -not -name '*.py' \
        -not -name '.DS_Store' \
        | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
    echo ""

    find midi -type f  \
        -not -path '*/__pycache__/*' \
        -not -name '*.pyc' \
        -not -name '.DS_Store' \
        | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
    echo ""

    find mplay -type f  \
        -not -path '*/__pycache__/*' \
        -not -name '*.pyc' \
        -not -name '.DS_Store' \
        | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
    echo ""

    find img -type f  \
        -not -name '.DS_Store' \
        | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
    echo ""

    find sound -type f  \
        -not -name '.DS_Store' \
        | sed -e 's|^\./||' | sort | \
        while IFS= read -r f; do
            d=$(dirname "$f")
            [ "$d" = "." ] && echo "$f usr/share/easyabc" || echo "$f usr/share/easyabc/$d"
        done
}

generate_install > debian/install
if git diff --quiet debian/install; then
    echo "    debian/install unchanged ($(wc -l < debian/install) lines)"
else
    echo "    debian/install updated, to review and commit:"
    git diff --stat debian/install
fi

echo "=== debuild ==="
debuild --no-tgz-check -uc -us

echo "=== deb package generated ==="
echo "Verify if anything to commit"