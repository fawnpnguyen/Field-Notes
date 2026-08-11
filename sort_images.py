#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ENTRIES_DIR = os.path.join(BASE_DIR, "entries")
VALID_EXT = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".webp")
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
        date_str, method = get_date_taken(fpath)
        dest_dir = os.path.join(IMAGES_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_{int(datetime.now().timestamp())}{ext}")
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
