#!/usr/bin/env python3
"""
fix_misdated_photos.py

One-time fix: moves specific photos (and their markdown image lines)
from today's entry (2026-08-13) to yesterday's entry (2026-08-12),
where they actually belong.

Usage:
    cd ~/Desktop/Journal
    python3 fix_misdated_photos.py
"""

import os
import re
import shutil

WRONG_DATE = "2026-08-13"
RIGHT_DATE = "2026-08-12"
FILES_TO_MOVE = ["IMG_2024.jpeg", "IMG_2025.jpeg", "IMG_2026.jpeg", "IMG_2029.jpeg", "IMG_2030.jpeg"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_WRONG = os.path.join(BASE_DIR, "images", WRONG_DATE)
IMAGES_RIGHT = os.path.join(BASE_DIR, "images", RIGHT_DATE)
ENTRY_WRONG = os.path.join(BASE_DIR, "entries", f"{WRONG_DATE}.md")
ENTRY_RIGHT = os.path.join(BASE_DIR, "entries", f"{RIGHT_DATE}.md")

log = []

# 1. Move the actual image files
os.makedirs(IMAGES_RIGHT, exist_ok=True)
for fname in FILES_TO_MOVE:
    src = os.path.join(IMAGES_WRONG, fname)
    dst = os.path.join(IMAGES_RIGHT, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        log.append(f"Moved file: images/{WRONG_DATE}/{fname} -> images/{RIGHT_DATE}/{fname}")
    else:
        log.append(f"WARNING: file not found, skipped: images/{WRONG_DATE}/{fname}")

# 2. Remove the markdown lines from today's entry, collect them
if not os.path.exists(ENTRY_WRONG):
    log.append(f"WARNING: {ENTRY_WRONG} not found.")
    moved_lines = []
else:
    with open(ENTRY_WRONG, "r") as f:
        content = f.read()

    moved_lines = []
    for fname in FILES_TO_MOVE:
        pattern = re.compile(
            r"!\[[^\]]*\]\(\.\./images/" + re.escape(WRONG_DATE) + r"/" + re.escape(fname) + r"\)\n?"
        )
        match = pattern.search(content)
        if match:
            line = match.group(0).rstrip("\n")
            corrected_line = line.replace(f"../images/{WRONG_DATE}/", f"../images/{RIGHT_DATE}/")
            moved_lines.append(corrected_line)
            content = pattern.sub("", content)
            log.append(f"Removed line from {WRONG_DATE}.md: {fname}")
        else:
            log.append(f"WARNING: markdown line for {fname} not found in {WRONG_DATE}.md")

    with open(ENTRY_WRONG, "w") as f:
        f.write(content)

# 3. Append corrected lines to yesterday's entry
if moved_lines:
    if not os.path.exists(ENTRY_RIGHT):
        with open(ENTRY_RIGHT, "w") as f:
            f.write(f"---\ndate: {RIGHT_DATE}\n---\n")
        log.append(f"Created {RIGHT_DATE}.md (didn't exist yet)")

    with open(ENTRY_RIGHT, "a") as f:
        f.write("\n" + "\n".join(moved_lines) + "\n")
    log.append(f"Appended {len(moved_lines)} image line(s) to {RIGHT_DATE}.md")

# Write full log to a file and open it in TextEdit so nothing gets cut off
log_path = "/tmp/fix_misdated_photos_log.txt"
with open(log_path, "w") as f:
    f.write("\n".join(log))

print("\n".join(log))
print(f"\nFull log also written to {log_path} — opening in TextEdit.")
os.system(f"open -a TextEdit {log_path}")
