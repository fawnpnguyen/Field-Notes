#!/usr/bin/env python3
"""
sort_images.py — Move any loose photos sitting directly in images/
into images/YYYY-MM-DD/ (using the date the photo was actually taken),
and automatically append their Markdown image lines to the bottom of
that day's entry file (entries/YYYY-MM-DD.md).

Date is pulled from EXIF (DateTimeOriginal). If a photo has no EXIF
(screenshots, downloaded images, etc.), falls back to the file's
modified date.

Run standalone, or let publish.sh call it automatically.
"""

import os
import shutil
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ENTRIES_DIR = os.path.join(BASE_DIR, "entries")
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
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def append_to_entry(date_str, markdown_lines):
    """Append image markdown lines to that date's entry file, if it exists."""
    entry_path = os.path.join(ENTRIES_DIR, f"{date_str}.md")
    if not os.path.isfile(entry_path):
        print(f"  (No entry file for {date_str} yet -- skipping auto-insert, "
              f"markdown printed above for manual paste.)")
        return False

    with open(entry_path, "r") as f:
        content = f.read()

    new_lines = [line for line in markdown_lines if line not in content]
    if not new_lines:
        return True

    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + "\n\n".join(new_lines) + "\n"

    with open(entry_path, "w") as f:
        f.write(content)
    return True


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"No images/ folder found at {IMAGES_DIR}, skipping sort.")
        return

    moved = []
    for fname in os.listdir(IMAGES_DIR):
        fpath = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        if not fname.lower().endswith(VALID_EXT):
            continue

        date_str = get_date_taken(fpath)
        dest_dir = os.path.join(IMAGES_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_{int(datetime.now().timestamp())}{ext}")

        shutil.move(fpath, dest_path)
        moved.append((date_str, os.path.basename(dest_path)))

    if not moved:
        print("No loose images to sort.")
        return

    print("Sorted images:")
    by_date = defaultdict(list)
    for date_str, final_name in moved:
        markdown = f"![](../images/{date_str}/{final_name})"
        by_date[date_str].append(markdown)
        print(f"  images/{date_str}/{final_name}")

    for date_str, lines in by_date.items():
        inserted = append_to_entry(date_str, lines)
        if inserted:
            print(f"  -> Added {len(lines)} image(s) to entries/{date_str}.md")


if __name__ == "__main__":
    main()
