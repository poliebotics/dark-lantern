#!/bin/bash
# N7-RAW-v1 step 1 (corrected argument order): fetch the held-out frames of d2 and v10 from the public gateway.
set -u
O=.; UA="Mozilla/5.0 (X11; Linux x86_64) BOSUN-p2pv2v/1.0"; BASE=https://data.truthbeam.com/sessions
cd "$O" || exit 1; echo "start $(date -u +%FT%TZ)"
: > urls2.txt
for s in d2 v10; do
  mkdir -p raw/$s/Emissions raw/$s/Recordings_previews
  [ -s raw/$s/manifest.json ] || curl -sS -f -A "$UA" "$BASE/$s/manifest.json" -o raw/$s/manifest.json || { echo "manifest fetch failed for $s"; exit 1; }
  n=$(python3 -c "import json; print(json.load(open('raw/$s/manifest.json'))['N_captures'])"); cut=$(python3 -c "print(int($n*0.9))")
  echo "$s N_captures=$n cut=$cut held-out=$((n-cut))"
  for ((i=cut; i<n; i++)); do
    f=$(printf '%06d' $i)
    [ -s raw/$s/Emissions/tile_$f.png ] || printf '%s\n%s\n' "$BASE/$s/derived/Emissions/tile_$f.png" "raw/$s/Emissions/tile_$f.png" >> urls2.txt
    [ -s raw/$s/Recordings_previews/frame_$f.png ] || printf '%s\n%s\n' "$BASE/$s/derived/Recordings_previews/frame_$f.png" "raw/$s/Recordings_previews/frame_$f.png" >> urls2.txt
  done
done
echo "to fetch: $(( $(wc -l < urls2.txt) / 2 )) files"
export UA
fetch_one() { # url out
  curl -sS -f -A "$UA" --retry 6 --retry-delay 2 -o "$2.part" "$1" && mv "$2.part" "$2" || { rm -f "$2.part"; echo "FAILED $1"; }
}
export -f fetch_one
xargs -a urls2.txt -P 16 -n 2 bash -c 'fetch_one "$1" "$2"' _ 2>&1 | tail -20
xargs -a urls2.txt -P 8 -n 2 bash -c '[ -s "$2" ] || fetch_one "$1" "$2"' _ 2>&1 | tail -5
for s in d2 v10; do echo "$s emissions=$(ls raw/$s/Emissions | wc -l) previews=$(ls raw/$s/Recordings_previews | wc -l) parts=$(ls raw/$s/*/*.part 2>/dev/null | wc -l)"; done
du -sh raw; echo "done $(date -u +%FT%TZ)"
