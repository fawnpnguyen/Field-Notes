#!/bin/bash
# Opens today's entry, creating it first if it doesn't exist yet.
DATE=$(date +%Y-%m-%d)
FILE="entries/$DATE.md"

if [ ! -f "$FILE" ]; then
  cat > "$FILE" <<EOF
---
date: $DATE
---

EOF
  echo "Started a fresh page for today ($DATE)."
else
  echo "Opening today's page ($DATE) — pick up where you left off."
fi

open -a TextEdit "$FILE"
