#!/usr/bin/env bash
# Regenerate all interior pages from build/data.py + build/shell.py
set -e
cd "$(dirname "$0")"
python3 build/build.py
echo "Done. Open index.html or run ./serve.py to preview."
