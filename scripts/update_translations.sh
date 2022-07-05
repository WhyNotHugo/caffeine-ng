#!/usr/bin/env sh

set -e

scripts/generate_pot.sh
scripts/compile_translations.py caffeine translations
