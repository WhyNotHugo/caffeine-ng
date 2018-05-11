#!/usr/bin/env python

import subprocess

print(subprocess.check_output(
    'find . -iname "*.py" -o -iname "*.glade" | '
    'xargs xgettext --from-code utf-8 -o translations/caffeine.pot',
    shell=True
))
