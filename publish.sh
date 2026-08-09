#!/bin/bash
# Usage: ./publish.sh "short note about what you wrote"
set -e

if [ -z "$1" ]; then
  echo 'Give it a short note, like: ./publish.sh "wrote about the market in Hoi An"'
  exit 1
fi

DATE=$(date +%Y-%m-%d)
ENTRY="entries/$DATE.md"

# Attach any new photo to today's entry, if today's entry exists.
if [ -f "$ENTRY" ]; then
  shopt -s nullglob
  for img in images/*; do
    fname=$(basename "$img")
    if ! grep -qr "$fname" entries/; then
      printf '\n![](images/%s)\n' "$fname" >> "$ENTRY"
      echo "Attached photo to today's entry: $fname"
    fi
  done
fi

echo "Building site..."
python3 build_journal.py

echo "Saving to git..."
git add .
git commit -m "$1"
git push

echo "Done — entry built and pushed."
