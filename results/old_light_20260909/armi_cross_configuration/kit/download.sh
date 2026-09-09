#!/bin/bash
# download.sh (BOSUN, 2026-09-09): fetch the public 2024 HDF5 and 2023 NumPy archives from the public gateway onto the
# box's LOCAL disk (not the persistent filesystem), in parallel, then verify every byte against the archive manifests' SHA-256.
# Idempotent: a file already at its manifest size is skipped; verification decides. Usage: download.sh <dest_root> <downloads.tsv>
set -u
DEST=${1:?dest}; TSV=${2:?tsv}; LOG=${3:-$DEST/download.log}
[ -f "$TSV" ] || { echo "no such download list: $TSV" >&2; exit 1; }
# the list and the log are made absolute before the change of directory (they may be given relative to the caller's directory)
mkdir -p "$DEST"; DEST=$(cd "$DEST" && pwd); TSV=$(cd "$(dirname "$TSV")" && pwd)/$(basename "$TSV"); case "$LOG" in /*) ;; *) LOG=$PWD/$LOG ;; esac
cd "$DEST"
echo "$(date -u +%FT%TZ) download start: $(wc -l < "$TSV") files -> $DEST" | tee -a "$LOG"
cut -f3 "$TSV" | xargs -n1 dirname | sort -u | xargs mkdir -p
fetch_one() {  # url path bytes
  local url=$1 path=$2 bytes=$3 tries=0
  while [ $tries -lt 4 ]; do
    if [ -f "$path" ] && [ "$(stat -c %s "$path")" = "$bytes" ]; then return 0; fi
    rm -f "$path"
    curl -sS -f -L --retry 3 --retry-delay 2 -o "$path" "$url" && [ "$(stat -c %s "$path")" = "$bytes" ] && return 0
    tries=$((tries+1)); sleep 3
  done
  echo "FAILED $path" >&2; return 1
}
export -f fetch_one
awk -F'\t' '$4 > 1000000000 {print $1, $3, $4}' "$TSV" | xargs -P 7 -L 1 bash -c 'fetch_one "$0" "$1" "$2"' 2>>"$LOG" &
BIG=$!
awk -F'\t' '$4 <= 1000000000 {print $1, $3, $4}' "$TSV" | xargs -P 32 -L 1 bash -c 'fetch_one "$0" "$1" "$2"' 2>>"$LOG"
wait $BIG
echo "$(date -u +%FT%TZ) downloads finished; verifying sha256" | tee -a "$LOG"
awk -F'\t' '{print $2"  "$3}' "$TSV" > SHA256SUMS.expected
rm -f sha_part_*
split -n l/24 -d SHA256SUMS.expected sha_part_
for f in sha_part_??; do (sha256sum -c --quiet "$f" > "$f.result" 2>&1; echo "exit $?" >> "$f.result") & done; wait
cat sha_part_??.result | grep -v "^exit 0" | grep -v "^$" > SHA256_FAILURES.txt || true
nfail=$(grep -c -v "^exit" SHA256_FAILURES.txt || true)
echo "$(date -u +%FT%TZ) verification done: $(wc -l < SHA256SUMS.expected) expected, failures: $nfail" | tee -a "$LOG"
rm -f sha_part_*
if [ "$nfail" != "0" ]; then echo "VERIFY FAILED" | tee -a "$LOG"; head SHA256_FAILURES.txt; exit 1; fi
echo "$(date -u +%FT%TZ) ALL VERIFIED" | tee -a "$LOG"; touch "$DEST/.verified"
