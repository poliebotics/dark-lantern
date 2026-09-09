#!/usr/bin/env python3
"""2023 track: aligned pix2pixHD pairs from the April 2023 NumPy sessions (old_truth_beams x7 + the PoliePals trailer 1682718815).

A (input)  = the emission array, 1024x1024x3 float32 (one float64 file per session), value range recorded from the data
             (--thumbs prints it), scaled to uint8 and resized (bicubic) to SIZE. The 2023 recorder stretched the square emission
             to the projector's 1920x1200 fullscreen, so the resize to a 16:10 SIZE reproduces that stretch.
B (target) = the camera report, 1536x2048x3 uint8 (2048 wide), cropped to CROP (x0, y0, x1, y1), the region holding the projected
             scene (chosen by eye from --thumbs), -> SIZE (Lanczos).
Pairs are matched on the 6-digit index prefix (emission 000123_<hash>.npy <-> report 000123_<hash>.npy); indices missing on one side are dropped.
Holdouts: the whole session HELD (1682718815, the last by timestamp) -> heldsession_A/B; the contiguous last 10 percent of every other
          session by index -> test_A/B; the rest -> train_A/B.  Names: <session>_<index:06d>.png
Usage: python3 prep_2023.py --thumbs ;  python3 prep_2023.py --crop x0,y0,x1,y1 --size 2048x1280
"""
import argparse, json, os, re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default=os.path.join(os.environ.get("OL_LOCAL", "oldlight_local"), "raw2023")); ap.add_argument("--out", default=os.path.join(os.environ.get("OL_LOCAL", "oldlight_local"), "pairs2023"))
ap.add_argument("--fs", default=os.environ.get("OL_FS", "oldlight_fs")); ap.add_argument("--held", default="1682718815")
ap.add_argument("--thumbs", action="store_true"); ap.add_argument("--crop", default=None); ap.add_argument("--size", default="1792x1120")
ap.add_argument("--rot180", action="store_true", help="rotate the report crop by 180 degrees (the 2023 camera was mounted inverted relative to the projector; orientation check 01:37Z)")
ap.add_argument("--tail", type=float, default=0.10); ap.add_argument("--emax", type=float, default=None, help="emission value that maps to 255 (default: per-file max if <=1 -> 1.0 else 255)")
a = ap.parse_args()
RAW, OUT = Path(a.raw), Path(a.out)
SIZE = tuple(int(x) for x in a.size.split("x"))
IDX = re.compile(r"^(\d{6})_")


def index_pairs(s):
    em = {IDX.match(p.name).group(1): p for p in (RAW / s / "emissions").glob("*.npy") if IDX.match(p.name)}
    rp = {IDX.match(p.name).group(1): p for p in (RAW / s / "reports").glob("*.npy") if IDX.match(p.name)}
    common = sorted(set(em) & set(rp))
    return [(int(i), em[i], rp[i]) for i in common], sorted(set(em) ^ set(rp))


def em_to_uint8(x):
    x = np.asarray(x, dtype=np.float64)
    mx = a.emax if a.emax else (1.0 if x.max() <= 1.0 + 1e-6 else 255.0)
    return np.clip(x / mx * 255.0, 0, 255).astype(np.uint8), float(x.min()), float(x.max())


def thumbs():
    T = Path(a.fs) / "thumbs" / "2023"; T.mkdir(parents=True, exist_ok=True)
    for s in sorted(p.name for p in RAW.iterdir() if p.is_dir()):
        pairs, odd = index_pairs(s)
        picks = [pairs[0], pairs[len(pairs) // 2], pairs[-1]] if len(pairs) >= 3 else pairs
        for i, e, r in picks:
            em = np.load(e); rep = np.load(r)
            u8, mn, mx = em_to_uint8(em)
            print(s, "pairs", len(pairs), "unmatched", len(odd), "idx", i, "emission", em.shape, em.dtype, f"range {mn:.4f}..{mx:.4f}", "report", rep.shape, rep.dtype, flush=True)
            Image.fromarray(u8).resize((512, 512), Image.BOX).save(T / f"{s}_{i:06d}_emission.png")
            Image.fromarray(rep).resize((1024, 768), Image.BOX).save(T / f"{s}_{i:06d}_report.png")
    print("thumbs in", T)


def job(args):
    s, i, e, r, split = args
    name = f"{s}_{i:06d}.png"; a_dst = OUT / f"{split}_A" / name; b_dst = OUT / f"{split}_B" / name
    if a_dst.exists() and b_dst.exists(): return 0
    u8, _, _ = em_to_uint8(np.load(e))
    Image.fromarray(u8).resize(SIZE, Image.BICUBIC).save(a_dst, compress_level=1)
    b = Image.fromarray(np.load(r)).crop(CROP)
    if a.rot180: b = b.transpose(Image.ROTATE_180)
    b.resize(SIZE, Image.LANCZOS).save(b_dst, compress_level=1)
    return 1


def main():
    global CROP
    if a.thumbs: return thumbs()
    CROP = tuple(int(x) for x in a.crop.split(","))
    for d in ("train_A", "train_B", "test_A", "test_B", "heldsession_A", "heldsession_B"): (OUT / d).mkdir(parents=True, exist_ok=True)
    jobs, rec_all = [], {"schema": "oldlight-split/1", "track": "2023", "size": list(SIZE), "crop_x0y0x1y1": list(CROP), "held_session": a.held, "tail_fraction": a.tail, "sessions": {},
                         "emission_geometry": "1024x1024 float -> uint8 -> SIZE bicubic (reproduces the recorder's fullscreen stretch to 16:10)", "report_geometry": f"2048x1536 uint8 crop {CROP}" + (" -> rotate 180" if a.rot180 else "") + " -> SIZE lanczos", "rot180": a.rot180}
    for s in sorted(p.name for p in RAW.iterdir() if p.is_dir()):
        pairs, odd = index_pairs(s); n = len(pairs); cut = int(n * (1 - a.tail))
        if s == a.held:
            rec = {"pairs": n, "unmatched_indices": odd, "role": "heldsession"}; jobs += [(s, i, e, r, "heldsession") for (i, e, r) in pairs]
        else:
            rec = {"pairs": n, "unmatched_indices": odd, "role": "train+tail", "train_positions": [0, cut - 1], "test_tail_positions": [cut, n - 1],
                   "train_index_range": [pairs[0][0], pairs[cut - 1][0]], "test_index_range": [pairs[cut][0], pairs[-1][0]] if cut < n else None}
            jobs += [(s, i, e, r, "train" if k < cut else "test") for k, (i, e, r) in enumerate(pairs)]
        rec_all["sessions"][s] = rec
    with ProcessPoolExecutor(max_workers=min(28, os.cpu_count() or 8)) as ex:
        made = sum(1 for r in ex.map(job, jobs, chunksize=4) if r == 1)
    counts = {d: len(list((OUT / d).glob("*.png"))) for d in ("train_A", "train_B", "test_A", "test_B", "heldsession_A", "heldsession_B")}
    rec_all["counts"] = counts; rec_all["made_now"] = made
    json.dump(rec_all, open(Path(a.fs) / "SPLIT_2023.json", "w"), indent=1); json.dump(rec_all, open(OUT / "SPLIT.json", "w"), indent=1)
    print(json.dumps(counts), "made", made)


if __name__ == "__main__":
    main()
