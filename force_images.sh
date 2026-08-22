#!/bin/bash
set -e
DEST=~/Desktop/Journal/images/2026-08-21
mkdir -p "$DEST"

for f in IMG_7456 IMG_0834 IMG_5577; do
  sips -s format jpeg "/Users/fnguyen/Downloads/${f}.HEIC" --out "$DEST/${f}.jpg"
done

echo "Done. Files in $DEST"
