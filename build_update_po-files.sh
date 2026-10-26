#!/bin/bash
set -e

mkdir -p locale

find . -type d \( -name ".venv" -o -name "env" \) -prune -o -name "*.py" -print | xgettext --from-code=UTF-8 -k_ -o locale/easyabc.pot -f -

for i in locale/*/LC_MESSAGES/easyabc.po
do
    [ -f "$i" ] || continue

    echo "process : $i"
    
    msgmerge -U "$i" locale/easyabc.pot
    
    # generate binary .mo pour wxPython
    msgfmt -o "${i%.po}.mo" "$i"
done

echo "Translation updated!"
