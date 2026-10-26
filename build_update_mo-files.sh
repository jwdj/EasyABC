#!/bin/bash
set -e

for i in locale/*/LC_MESSAGES/easyabc.po
do
    [ -f "$i" ] || continue

    echo "process : $i"
    
    # generate binary .mo pour wxPython
    msgfmt -o "${i%.po}.mo" "$i"
done

echo "Translation updated!"
