#!/usr/bin/env python3
"""
sort_images.py — Move any loose photos and short video clips sitting
directly in images/ into images/YYYY-MM-DD/ (using the date the file was
actually taken), converting HEIC/HEIF to JPEG along the way (most
browsers can't display HEIC), create that day's entry file if it
doesn't exist yet, and append Markdown image lines (photos) or HTML
<video> tags (clips) to the bottom of it.

Date detection, in order of preference:
  1. EXIF DateTimeOriginal / DateTimeDigitized / DateTime (photos only —
     video files don't carry this, so they skip straight to step 2)
  2. macOS Spotlight metadata (kMDItemContentCreationDate) — often
     survives even when an app (messaging, export, re-save) strips EXIF,
     because Photos/AirDrop can carry the original capture date here
     separately from EXIF. This is the primary method for videos.
  3. File creation date (birthtime)
  4. File modified date — last resort, least reliable

Prints which method was used for each photo so misdates are easy to
spot before they go live.

Run standalone, or let publish.sh call it automatically.
"""

import os
import shutil
import subprocess
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
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".m4v")
VALID_EXT = IMAGE_EXT + VIDEO_EXT
CONVERT_TO_JPEG = (".heic", ".heif")

EXIF_DATE_TAGS = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]


def get_date_from_exif(path):
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
                        return dt.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue
    except Exception:
        pass
    return None


def get_date_from_spotlight(path):
    """Checks macOS Spotlight metadata for a capture date. This often
    survives even when EXIF has been stripped (e.g. photos that came
    through a messaging app before landing on disk), because Photos/
    AirDrop can tag files with this separately from EXIF."""
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemContentCreationDate", "-raw", path],
            capture_output=True, text=True, timeout=5
        )
        raw = result.stdout.strip()
        if raw and raw != "(null)":
            # Typical format: 2026-08-12 14:23:01 +0000
            dt = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


def get_date_taken(path):
    date_str = get_date_from_exif(path)
    if date_str:
        return date_str, "EXIF"

    date_str = get_date_from_spotlight(path)
    if date_str:
        return date_str, "macOS metadata (no EXIF)"

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

        # Check dates BEFORE conversion when possible — Spotlight metadata
        # on the original HEIC can be more reliable than on a freshly
        # written JPEG, and this keeps date detection independent of
        # the conversion step entirely.
        is_video = ext in VIDEO_EXT

        pre_convert_date, pre_convert_method = None, None
        if ext in CONVERT_TO_JPEG:
            pre_convert_date, pre_convert_method = get_date_taken(fpath)

        # Convert HEIC/HEIF to JPEG first, in place, before date-checking/moving
        if ext in CONVERT_TO_JPEG:
            if not HEIF_SUPPORT:
                print(f"  Skipping {fname}: HEIC support not installed "
                      f"(run: pip install pillow-heif --break-system-packages)")
                continue
            fpath = convert_heic_to_jpeg(fpath)
            fname = os.path.basename(fpath)

        if pre_convert_date and "EXIF" in pre_convert_method:
            # Trust the pre-conversion EXIF read; re-check post-conversion
            # only as a fallback if it somehow didn't carry over.
            post_date, post_method = get_date_taken(fpath)
            if "EXIF" in post_method:
                date_str, method = post_date, post_method
            else:
                date_str, method = pre_convert_date, pre_convert_method
        else:
            date_str, method = get_date_taken(fpath)

        dest_dir = os.path.join(IMAGES_DIR, date_str)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, fname)
        if os.path.exists(dest_path):
            base, ext2 = os.path.splitext(fname)
            dest_path = os.path.join(dest_dir, f"{base}_{int(datetime.now().timestamp())}{ext2}")

        shutil.move(fpath, dest_path)
        moved.append((date_str, os.path.basename(dest_path), method, is_video))

    if not moved:
        print("No loose images to sort.")
        return

    print("Sorted images:")
    by_date = defaultdict(list)
    for date_str, final_name, method, is_video in moved:
        if is_video:
            line = (f'<video controls src="../images/{date_str}/{final_name}">'
                    f'</video>')
        else:
            line = f"![](../images/{date_str}/{final_name})"
        by_date[date_str].append(line)
        flag = "  <-- check this one" if "EXIF" not in method and "macOS metadata" not in method else ""
        kind = "video" if is_video else "image"
        print(f"  images/{date_str}/{final_name}   [{kind}, {method}]{flag}")

    for date_str, lines in by_date.items():
        append_to_entry(date_str, lines)
        print(f"  -> Added {len(lines)} image(s) to entries/{date_str}.md")


if __name__ == "__main__":
    main()
