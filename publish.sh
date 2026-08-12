#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Sorting any loose photos into dated folders..."
python3 sort_images.py

echo "Building journal..."
python3 build_journal.py

echo "Copying build to docs/ for GitHub Pages..."
rm -rf docs
cp -r site docs

echo "Committing..."
git add -A
git commit -m "Update: $(date '+%Y-%m-%d %H:%M')" || echo "Nothing new to commit, skipping."

echo "Pushing..."
git push

echo "Done. Site is updating."
