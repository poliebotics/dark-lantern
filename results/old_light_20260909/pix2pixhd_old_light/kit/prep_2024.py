#!/usr/bin/env python3
"""2024 track: aligned pix2pixHD pairs from the seven 19 December 2024 HDF5 sessions.

A (input)  = the emission the projector threw, 1920x1080 uint8 -> SIZE (bicubic, mild upscale, as the 6 September kit did).
B (target) = the camera recording, 5320x4600 uint8, cropped to CROP (x0, y0, x1, y1), the band that holds the projected scene,
             -> SIZE (Lanczos). The crop is chosen by eye from --thumbs renders and recorded in SPLIT.json.
Holdouts: the whole session HELD (20241219_050046, the session the January 2025 run held out) -> heldsession_A/B;
          the contiguous last 10 percent of every other session by frame index (frames 57..63 of 64) -> test_A/B;
          the rest -> train_A/B.  Names: s<HHMMSS>_<index:06d>.png (the eval scripts parse session_index.png with a 6-digit index).
Usage: python3 prep_2024.py --thumbs        (downsized full frames for the crop decision)
       python3 prep_2024.py --crop x0,y0,x1,y1 [--size 2048x1152]
"""
import argparse, json, os, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import h5py, numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default=os.path.join(os.environ.get("OL_LOCAL", "oldlight_local"), "raw2024")); ap.add_argument("--out", default=os.path.join(os.environ.get("OL_LOCAL", "oldlight_local"), "pairs2024"))
ap.add_argument("--fs", default=os.environ.get("OL_FS", "oldlight_fs")); ap.add_argument("--held", default="20241219_050046")
ap.add_argument("--thumbs", action="store_true"); ap.add_argument("--crop", default=None); ap.add_argument("--size", default="2048x1152")
ap.add_argument("--tail", type=float, default=0.10)
a = ap.parse_args()
RAW, OUT = Path(a.raw), Path(a.out)
SIZE = tuple(int(x) for x in a.size.split("x"))
SESSIONS = sorted(p.stem for p in RAW.glob("*.h5"))
short = lambda s: "s" + s.split("_")[1]      # 20241219_044052 -> s044052


def thumbs():
    T = Path(a.fs) / "thumbs" / "2024"; T.mkdir(parents=True, exist_ok=True)
    for s in SESSIONS:
        with h5py.File(RAW / f"{s}.h5", "r") as f:
            print(s, {k: (f[k].shape, str(f[k].dtype)) for k in f}, dict(f.attrs), flush=True)
            for i in (0, 32, 63):
                em = f["emissions"][i]; rec = f["recordings"][i]
                Image.fromarray(em).resize((480, 270), Image.BOX).save(T / f"{short(s)}_{i:03d}_emission.png")
                Image.fromarray(rec).resize((1330, 1150), Image.BOX).save(T / f"{short(s)}_{i:03d}_recording.png")   # quarter size
                # a full-resolution 800x800 centre patch of the recording, for focus and sensor detail
                Image.fromarray(rec[1900:2700, 2260:3060]).save(T / f"{short(s)}_{i:03d}_recording_centre800.png")
    print("thumbs in", T)


def job(args):
    s, i, split = args
    name = f"{short(s)}_{i:06d}.png"
    a_dst = OUT / f"{split}_A" / name; b_dst = OUT / f"{split}_B" / name
    if a_dst.exists() and b_dst.exists(): return 0
    with h5py.File(RAW / f"{s}.h5", "r") as f:
        em = f["emissions"][i]; rec = f["recordings"][i]
    Image.fromarray(em).resize(SIZE, Image.BICUBIC).save(a_dst, compress_level=1)
    Image.fromarray(rec).crop(CROP).resize(SIZE, Image.LANCZOS).save(b_dst, compress_level=1)
    return 1


def main():
    global CROP
    if a.thumbs: return thumbs()
    CROP = tuple(int(x) for x in a.crop.split(","))
    for d in ("train_A", "train_B", "test_A", "test_B", "heldsession_A", "heldsession_B"): (OUT / d).mkdir(parents=True, exist_ok=True)
    jobs, split_rec = [], {"schema": "oldlight-split/1", "track": "2024", "size": list(SIZE), "crop_x0y0x1y1": list(CROP), "held_session": a.held,
                            "tail_fraction": a.tail, "sessions": {}, "emission_geometry": "1920x1080 uint8 -> SIZE bicubic", "recording_geometry": f"5320x4600 uint8 crop {CROP} -> SIZE lanczos"}
    for s in SESSIONS:
        with h5py.File(RAW / f"{s}.h5", "r") as f: n = f["emissions"].shape[0]; attrs = {k: (v.item() if hasattr(v, "item") else str(v)) for k, v in f.attrs.items()}
        cut = int(n * (1 - a.tail))
        if s == a.held:
            rec = {"short": short(s), "frames": n, "role": "heldsession", "heldsession": list(range(n))}
            jobs += [(s, i, "heldsession") for i in range(n)]
        else:
            rec = {"short": short(s), "frames": n, "role": "train+tail", "train": [0, cut - 1], "test_tail": [cut, n - 1]}
            jobs += [(s, i, "train" if i < cut else "test") for i in range(n)]
        rec["attrs"] = attrs; split_rec["sessions"][s] = rec
    with ProcessPoolExecutor(max_workers=min(28, os.cpu_count() or 8)) as ex:
        made = sum(1 for r in ex.map(job, jobs, chunksize=2) if r == 1)
    counts = {d: len(list((OUT / d).glob("*.png"))) for d in ("train_A", "train_B", "test_A", "test_B", "heldsession_A", "heldsession_B")}
    split_rec["counts"] = counts; split_rec["made_now"] = made
    Path(a.fs).mkdir(parents=True, exist_ok=True)
    json.dump(split_rec, open(Path(a.fs) / "SPLIT_2024.json", "w"), indent=1); json.dump(split_rec, open(OUT / "SPLIT.json", "w"), indent=1)
    print(json.dumps(counts), "made", made)


if __name__ == "__main__":
    main()
