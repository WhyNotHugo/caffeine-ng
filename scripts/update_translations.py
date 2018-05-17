#!/usr/bin/env python

import subprocess

print(subprocess.check_output("python scripts/generate_pot.py", shell=True))

print(subprocess.check_output(
    "python scripts/compile_translations.py caffeine translations",
    shell=True,
))
