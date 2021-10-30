#!/usr/bin/env sh

set -e

find . -iname "*.py" -o -iname "*.glade" | \
    xargs xgettext --from-code utf-8 -o translations/caffeine.pot
