#!/usr/bin/env python3
"""
sort_images.py — Move any loose photos sitting directly in images/
into images/YYYY-MM-DD/ (using the date the photo was actually taken),
converting HEIC/HEIF to JPEG along the way (most browsers can't display
HEIC), create that day's entry file if it doesn't exist yet, and append
the photos' Markdown image lines to the bottom of it.

Date detection, in order of preference:
  1. EXIF DateTimeOriginal / DateTimeDigitized / DateTime
  2. File creation date (birthtime)
  3. File modified date — last resort, least reliable

Prints which method was used for each photo so misdates are easy to
spot before they go live.

Run standalone, or let publish.sh call it automatically.
"""

import os
import shutil
from datetime import datetime
from collections import defaultdict

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ENTRIES_DIR = os.path.join(BASE_DIR, "entries")
VALID_EXT = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".webp")
CONVERT_TO_JPEG = (".heic", ".heif")

EXIF_DATE_TAGS = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]


def get_date_taken(path):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(path)
        exif = img._getexif()
        if exif:
            tagged = {TAGS.get(tag_id, tag_id): value for tag_id, value in exif.items()}
            for tag_name in EXIF_DATE_TAGS:
                if tag_name in tagged:
                    try:
                        dt = datetime.strptime(tagged[tag_name], "%Y:%m:%d %H:%M:%S")
                        return dt.strftime("%Y-%m-%d"), "EXIF"
                    except (ValueError, TypeError):
                        continue
    except Exception:
        pass

    try:
        birthtime = os.stat(path).st_birthtime
        return datetime.fromtimestamp(birthtime).strftime("%Y-%m-%d"), "file creation date (no EXIF)"
    except AttributeError:
        pass

    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"), "file modified date (least reliable)"


def ensure_entry_exists(date_str):
    entry_path = os.path.join(ENTRIES_DIR, f"{date_str}.md")
    if not os.path.isfile(entry_path):
        os.makedirs(ENTRIES_DIR, exist_ok=True)
        with open(entry_path, "w") as f:
            f.write(f"---\ndate: {date_str}\n---\n\n")
        print(f"  -> Created new entry: entries/{date_str}.md (no entry existed for this date)")
    return entry_path


def append_to_entry(date_str, markdown_lines):
    entry_path = ensure_entry_exists(date_str)
    with open(entry_path, "r") as f:
        content = f.read()
    new_lines = [line for line in markdown_lines if line not in content]
    if not new_lines:
        return
    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + "\n\n".join(new_lines) + "\n"
    with open(entry_path, "w") as f:
        f.write(content)


def convert_heic_to_jpeg(src_path):
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
    return new_path


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"No images/ folder found at {IMAGES_DIR}, skipping sort.")
        return

    moved = []
    for fname in os.listdir(IMAGES_DIR):
        fpath = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in VALID_EXT:
            continue

        # Convert HEIC/HEIF to JPEG first, in place, before date-checking/moving
        if ext in CONVERT_TO_JPEG:
            if not HEIF_SUPPORT:
                print(f"  Skipping {fname}: HEIC support not installed "
                      f"(run: pip install pillow-heif --break-system-packages)")
                continue
            fpath = convert_heic_to_jpeg(fpath)
            fname = os.path.basename(fpath)

        date_str, method = get_date_taken(fpath)
        dest_dir = os.path.join(IMAGES_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            base, ext2 = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_{int(datetime.now().timestamp())}{ext2}")

        shutil.move(fpath, dest_path)
        moved.append((date_str, os.path.basename(dest_path), method))

    if not moved:
        print("No loose images to sort.")
        return

    print("Sorted images:")
    by_date = defaultdict(list)
    for date_str, final_name, method in moved:
        markdown = f"![](../images/{date_str}/{final_name})"
        by_date[date_str].append(markdown)
        flag = "  <-- check this one" if "EXIF" not in method else ""
        print(f"  images/{date_str}/{final_name}   [{method}]{flag}")

    for date_str, lines in by_date.items():
        append_to_entry(date_str, lines)
        print(f"  -> Added {len(lines)} image(s) to entries/{date_str}.md")


if __name__ == "__main__":
    main()
