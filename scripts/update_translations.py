#!/usr/bin/env python

import subprocess
version = open("VERSION").read()
version = version.strip()
print(version)

print(subprocess.getoutput("python ./generate_pot.py . caffeine " + version +
      " translations/caffeine.pot"))

print(subprocess.getoutput("python ./compile_translations.py caffeine" +
      "translations"))
