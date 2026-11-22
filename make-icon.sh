#!/bin/bash
# Draw the icons of copyparty-hildon with ImageMagick: icons/48.png and 64.png (a folder with a gear on a dark rounded square).
# The PNGs are committed; run this only to change the design.
set -euo pipefail
cd "$(dirname "$0")"
# ImageMagick writes the creation time into the PNG: without these options every run changes the files although the picture is the same.
convert() { command convert +set date:create +set date:modify -define png:exclude-chunk=date,time "$@"; }
mkdir -p icons
teeth=()
for a in 0 45 90 135 180 225 270 315; do
    teeth+=(-draw "translate 172,172 rotate $a rectangle -10,-52 10,-34")
done
convert -size 256x256 xc:none -fill '#26323f' -draw 'roundrectangle 8,8 247,247 44,44' \
  -fill '#f2b84b' -draw 'polygon 30,60 88,60 100,80 190,80 190,170 30,170' \
  -fill '#e0a22f' -draw 'rectangle 30,100 190,170' \
  -fill '#d9dde2' "${teeth[@]}" -draw 'circle 172,172 172,132' \
  -fill '#26323f' -draw 'circle 172,172 172,152' \
  icons/256.png
for s in 64 48; do convert icons/256.png -resize ${s}x${s} icons/$s.png; done
rm -f icons/256.png
