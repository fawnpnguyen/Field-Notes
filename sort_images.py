#!/usr/bin/env python3
"""
sort_images.py — Move any loose photos sitting directly in images/
into images/YYYY-MM-DD/, using the date the photo was actually taken.

Date is pulled from EXIF (DateTimeOriginal). If a photo has no EXIF
(screenshots, downloaded images, etc.), falls back to the file's
modified date.

Run standalone, or let publish.sh call it automatically.
"""

import os
import shutil
import sys
from datetime import datetime

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
VALID_EXT = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".webp")


def get_date_taken(path):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(path)
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    # EXIF format: "2026:08:12 14:03:00"
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback: file modified time
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"No images/ folder found at {IMAGES_DIR}, skipping sort.")
        return

    moved = []
    for fname in os.listdir(IMAGES_DIR):
        fpath = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(fpath):
            continue  # skip folders (already-sorted dated subfolders)
        if not fname.lower().endswith(VALID_EXT):
            continue  # skip non-image junk (.DS_Store etc.)

        date_str = get_date_taken(fpath)
        dest_dir = os.path.join(IMAGES_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_{int(datetime.now().timestamp())}{ext}")

        shutil.move(fpath, dest_path)
        moved.append((fname, date_str, os.path.basename(dest_path)))

    if moved:
        print("Sorted images:")
        for original, date_str, final_name in moved:
            print(f"  {original}  ->  images/{date_str}/{final_name}")
            print(f"    Markdown: ![]({'../'}images/{date_str}/{final_name})")
    else:
        print("No loose images to sort.")


if __name__ == "__main__":
    main()
