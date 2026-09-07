#!/usr/bin/env python3
"""N7-RAW-v1 step 2: build the held-out pairs from the fetched public frames exactly as prep_pairs.py did on the box
(A: emission 1920x1080 -> 2048x1152 bicubic; B: preview 5320x4600 cropped to rows 350..3342 -> 2048x1152 Lanczos; PNG
compress_level=1; names <session>_<index>.png), for the contiguous final 10 percent of each session (cut = int(N*0.9)).
Records SHA-256 of every raw file, every pair file, and of the decoded RGB pixel arrays (encoder-independent), plus the
library versions, into PAIRS_MANIFEST.json. Nothing is trained; nothing sealed is touched."""
import hashlib, json, os, platform, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, PIL
from PIL import Image

O = Path('.'); RAW = O / 'raw'; PAIRS = O / 'pairs'
SIZE = (2048, 1152); CROP = (0, 350, 5320, 3342)
sha = lambda b: hashlib.sha256(b).hexdigest()
fsha = lambda p: sha(Path(p).read_bytes())


def job(args):
    s, i = args
    name = f'{s}_{i:06d}.png'
    a_src = RAW / s / 'Emissions' / f'tile_{i:06d}.png'; b_src = RAW / s / 'Recordings_previews' / f'frame_{i:06d}.png'
    a_dst = PAIRS / 'test_A' / name; b_dst = PAIRS / 'test_B' / name
    rec = dict(name=name, session=s, index=i, raw_emission=str(a_src.relative_to(O)), raw_preview=str(b_src.relative_to(O)),
               raw_emission_sha256=fsha(a_src), raw_preview_sha256=fsha(b_src))
    a_img = Image.open(a_src); rec['raw_emission_size_mode'] = [a_img.size, a_img.mode]
    b_img = Image.open(b_src); rec['raw_preview_size_mode'] = [b_img.size, b_img.mode]
    a = a_img.convert('RGB').resize(SIZE, Image.BICUBIC)
    b = b_img.convert('RGB').crop(CROP).resize(SIZE, Image.LANCZOS)
    if not a_dst.exists():
        a.save(a_dst, compress_level=1)
    if not b_dst.exists():
        b.save(b_dst, compress_level=1)
    # pixel digests from the files as written (what every later script reads)
    ra = np.asarray(Image.open(a_dst).convert('RGB')); rb = np.asarray(Image.open(b_dst).convert('RGB'))
    rec.update(pair_A_sha256=fsha(a_dst), pair_B_sha256=fsha(b_dst), pair_A_pixels_sha256=sha(ra.tobytes()), pair_B_pixels_sha256=sha(rb.tobytes()),
               pair_shape=list(ra.shape), pixels_equal_to_in_memory=bool((ra == np.asarray(a)).all() and (rb == np.asarray(b)).all()))
    return rec


def main():
    for side in ('A', 'B'):
        (PAIRS / f'test_{side}').mkdir(parents=True, exist_ok=True)
    jobs = []; sessions = {}
    for s in ('d2', 'v10'):
        m = json.loads((RAW / s / 'manifest.json').read_bytes()); n = int(m['N_captures']); cut = int(n * 0.9)
        sessions[s] = dict(N_captures=n, cut=cut, held_out=n - cut, first_index=cut, last_index=n - 1, manifest_sha256=fsha(RAW / s / 'manifest.json'),
                           capture_log_hash=m.get('capture_log_hash'), bundle_hash=m.get('bundle_hash'), S_N_hex=m.get('S_N_hex'))
        for i in range(cut, n):
            for p in (RAW / s / 'Emissions' / f'tile_{i:06d}.png', RAW / s / 'Recordings_previews' / f'frame_{i:06d}.png'):
                if not p.exists() or p.stat().st_size == 0:
                    raise SystemExit(f'REFUSED: missing or empty raw file {p}')
            jobs.append((s, i))
    t0 = time.time(); recs = []
    with ProcessPoolExecutor(max_workers=16) as ex:
        for r in ex.map(job, jobs, chunksize=4):
            recs.append(r)
    recs.sort(key=lambda r: r['name'])
    bad = [r['name'] for r in recs if not r['pixels_equal_to_in_memory']]
    out = dict(schema='n7-raw-pairs-manifest/v1', created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), source='https://data.truthbeam.com/sessions/<s>/derived/{Emissions,Recordings_previews}',
               prep_rule='prep_pairs.py of 2026-09-06 (box): A bicubic 1920x1080->2048x1152; B crop (0,350,5320,3342) then Lanczos ->2048x1152; PNG compress_level=1',
               environment=dict(python=platform.python_version(), pillow=PIL.__version__, numpy=np.__version__), sessions=sessions, n_pairs=len(recs),
               pixel_roundtrip_mismatches=bad, pairs=recs, seconds=round(time.time() - t0, 1))
    (O / 'PAIRS_MANIFEST.json').write_bytes((json.dumps(out, indent=1) + '\n').encode())
    print(f'{len(recs)} pairs built in {out["seconds"]} s; roundtrip mismatches: {len(bad)}; manifest sha256 {fsha(O / "PAIRS_MANIFEST.json")}')


if __name__ == '__main__':
    main()
