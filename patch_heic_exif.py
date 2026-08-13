#!/usr/bin/env python3
"""
patch_heic_exif.py

One-time fix for sort_images.py: makes HEIC->JPEG conversion preserve
EXIF (date-taken) data instead of silently dropping it.

Usage:
    cd ~/Desktop/Journal
    python3 patch_heic_exif.py
"""

import re
import sys
import os

PATH = "sort_images.py"

if not os.path.exists(PATH):
    print(f"Could not find {PATH} in this folder.")
    print("Make sure you're running this from inside your Journal folder.")
    sys.exit(1)

with open(PATH, "r") as f:
    content = f.read()

# Match the function regardless of minor docstring/comment differences
pattern = re.compile(
    r"def convert_heic_to_jpeg\(src_path\):.*?return new_path",
    re.DOTALL
)

new_function = '''def convert_heic_to_jpeg(src_path):
    """Converts HEIC/HEIF to JPEG, preserving EXIF. Deletes the original."""
    from PIL import Image
    img = Image.open(src_path)
    exif_bytes = img.info.get("exif")
    if img.mode != "RGB":
        img = img.convert("RGB")
    base, _ = os.path.splitext(src_path)
    new_path = base + ".jpeg"
    if exif_bytes:
        img.save(new_path, "JPEG", quality=92, exif=exif_bytes)
    else:
        img.save(new_path, "JPEG", quality=92)
    os.remove(src_path)
    return new_path'''

match = pattern.search(content)

if not match:
    print("Could not locate convert_heic_to_jpeg() in sort_images.py.")
    print("No changes made. Paste me the function from your file and I'll patch it manually.")
    sys.exit(1)

if "exif_bytes" in match.group(0):
    print("Already patched — no changes needed.")
    sys.exit(0)

new_content = content[:match.start()] + new_function + content[match.end():]

with open(PATH, "w") as f:
    f.write(new_content)

print("Patched successfully! HEIC conversions will now preserve EXIF date-taken data.")
