#!/usr/bin/env python

import os
import sys
import subprocess

if len(sys.argv) < 3:
    print("usage: ./compile_translations <program-name> <po directory>")
    sys.exit(1)

po_dir = sys.argv[-1]
prg_name = sys.argv[-2]


po_files = []
for dirpath, dirnames, filenames in os.walk(po_dir):
    for file in filenames:
        if file.split('.')[-1] == "po":
            po_files.append(os.path.join(dirpath, file))

for po in po_files:
    lang = po.split('/')[-1]
    print("Compiling for Locale: " + "".join(lang.split(".")[:-1]))
    lang = lang.split('-')[-1]
    lang = lang.split('.')[0]
    lang = lang.strip()
    if not lang:
        continue

    lang_dir = os.path.join('share/locale', lang)

    if not os.path.isdir(lang_dir):
        os.mkdir(lang_dir)

    lang_lc_dir = os.path.join(lang_dir, 'LC_MESSAGES')
    if not os.path.isdir(lang_lc_dir):
        os.mkdir(lang_lc_dir)

    cmd = ("msgfmt '"+po+"' -o '" +
           os.path.join(lang_lc_dir, "caffeine" + ".mo'"))

    output = subprocess.getoutput(cmd)
