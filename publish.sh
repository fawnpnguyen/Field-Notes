#!/bin/bash
# Usage: ./publish.sh "short description of what you wrote"
set -e

if [ -z "$1" ]; then
  echo "Give it a short note about the entry, like:"
  echo '  ./publish.sh "wrote about the market in Hoi An"'
  exit 1
fi

echo "Building site..."
python3 build_journal.py

echo "Saving to git..."
git add .
git commit -m "$1"
git push

echo "Done — entry built and pushed."
