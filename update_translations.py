#!/usr/bin/env python

import commands
version = open("VERSION").read()
version = version.strip()
print version

print commands.getoutput("python ./generate_pot.py . caffeine "+version+
        " translations/caffeine.pot")

print commands.getoutput("python ./compile_translations.py caffeine translations")
