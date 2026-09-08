#!/usr/bin/env python3
"""Lean conditional-diffusion trainer (single GPU or DDP), configurable modes.

Its original mode warm-started the published Phase G verifier (model_final.pt, sha pinned) as an ARM-A fine-tune on
D2 + V10 (train rows outside the eval blocks with 60-row guards, half-open) plus August development rows. The released
ARM-C checkpoint of this package was trained from scratch (`--arch armc --from-scratch --no-base-ckpt`, the checkpoint's
recorded arguments) on the d2/v10 training blocks and August rows 0 to 599 (`--august-train-rows 600`). Phase G locked preprocessing
throughout. bf16 autocast, MSE on eps, AdamW, cosine with warmup, grad accumulation.
Atomic resumable checkpoints (model/optim/step/per-rank RNG) to the ZeeBeam filesystem; periodic
matched-vs-crossed eval at t=150 on held-out D2/V10 rows and an August diagnostic.
Single file, no deps beyond torch/numpy/PIL and the copied phase_g model source.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, sys, time
import torch.distributed as dist
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, "[node home]/verifier/src")
from phase_g.diffusion_diagnostic_model import DiffusionDiagnosticUNet, build_diffusion_constants, q_sample, ResBlock, Attn, coord_grid
from phase_g.zk_unet import ZkUNet, ZkResBlock  # lean, proof-friendly variant (BOSUN 2026-09-07)
from phase_g.lean_denoiser import LeanDenoiser   # arch zk2: Astra's dense conv-only design, optional QAT  # noqa: E402
sys.path.insert(0, "[node home]/tb_public/truthbeam_verify/code/verifier/src")
from data.xof_generation import xof_octaves_from_hex  # noqa: E402
import csv as _csv

# ---- ARM C: conditioning is the four committed XOF octave grids, NOT a rendered tile ----
# Conditioning uses all four committed XOF octave grids and the whole-frame input, without explicit homographies.
# 129,330 conditioning bytes vs 6,220,800 for a rendered RGB tile = 48.1x smaller.
# Octave 3 is 135x240 over 1080x1920: exactly one sample per 8x8 native cell, so the finest
# octave is carried at full fidelity with NO resampling on the emission side.
_STATE = {}

def _load_states(sid, d):
    """row -> S_t_hex. Offset 0, established BIT-EXACTLY by two independent routes (audit
    2026-08-25): (a) blake3(gen_rgb_v2(compute_xof_seeds(S_t_hex[t]))) equals the logged
    emission_live_pixel_blake3_hex[t] for 24/24 sampled rows across d2/v10/august and never at
    offset 1; (b) pixel-exact against tile_%06d.png, 96/96 exact at offset 0 and 0/96 at offset 1,
    offset 1 differing in ~6.19M of 6.22M subpixels.

    ROOT CAUSE of the apparent contradiction, which matters more than the offset: these are v9 B++
    BLOCKING-loop sessions (E_t = gen(xof(S_t))), whereas xof_generation.py:18 documents the v8
    ASYNC loop (tile t from S_next). The v9 schema fingerprint is that all three chain_logs carry
    emission_live_pixel_blake3_hex plus drand columns and NO xof_seed_*_hex. The shipped verifier
    agrees: verify/verify_frames.py:74-76 feeds data[t]["S_t_hex"] straight in.

    An earlier version of this docstring justified offset 0 with "mean |err| ~25 vs ~65" from a
    BILINEAR stand-in. That conclusion was right and that evidence was not good enough to carry it."""
    p = d / "chain_log.csv"
    if not p.is_file():
        raise SystemExit(f"FAIL: no chain_log.csv for {sid} at {p}")
    rows = [l for l in p.read_text().splitlines() if not l.startswith("#")]
    out = {}
    for r in _csv.DictReader(rows):
        t = r.get("t", "")
        if t.isdigit() and r.get("S_t_hex"):
            out[int(t)] = r["S_t_hex"]
    if not out:
        raise SystemExit(f"FAIL: no S_t_hex parsed for {sid}")
    return out


ROOT = Path("[private corpus path]")
CKPT_SHA = "b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055"
# ARM C: no CROP constant. The full sensor frame is the input.
TH, TW = 768, 1024            # DEFAULT ONLY: overridden by --out-size

SESSIONS = {
    "d2": {"dir": ROOT / "truthbeam/sessions/d2", "rows_total": 5992, "raw": "frames/frame_{r:06d}.raw",
           "em": "derived/Emissions/tile_{r:06d}.png",
           "train": [(0, 1238), (1758, 2736), (3256, 4234), (4754, 5992)],
           "eval_blocks": [(1298, 1698), (2796, 3196), (4294, 4694)]},
    "v10": {"dir": ROOT / "truthbeam/sessions/v10", "rows_total": 3743, "raw": "frames/frame_{r:06d}.raw",
            "em": "derived/Emissions/tile_{r:06d}.png",
            "train": [(0, 1050), (1420, 2285), (2655, 3743)],
            "eval_blocks": [(1110, 1360), (2345, 2595)]},
    "august": {"dir": ROOT / "august_dev_712", "rows_total": 712, "raw": "Recordings/frame_{r:06d}.raw",
               "em": "derived/Emissions/tile_{r:06d}.png",
               "train": [(0, 712)], "eval_blocks": []},
}


# test hook (BOSUN 2026-09-07): LEAN_SESSIONS_JSON replaces the session table for smoke tests on synthetic data; never set on a real run
if os.environ.get("LEAN_SESSIONS_JSON"):
    _ov = json.loads(Path(os.environ["LEAN_SESSIONS_JSON"]).read_text())
    SESSIONS = {sid: {"dir": ROOT / v["dir"], "rows_total": v["rows_total"], "raw": v["raw"], "em": v["em"],
                      "train": [tuple(x) for x in v["train"]], "eval_blocks": [tuple(x) for x in v["eval_blocks"]]} for sid, v in _ov.items()}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def resolve_raw_layout():
    """The public sessions may store raw frames under a different subdir; detect once."""
    for sid, s in SESSIONS.items():
        d = s["dir"]
        for cand in (s["raw"], "frames/frame_{r:06d}.raw", "Recordings/frame_{r:06d}.raw", "raw/frame_{r:06d}.raw", "frame_{r:06d}.raw"):
            if (d / cand.format(r=0)).is_file():
                s["raw"] = cand
                break
        else:
            raise SystemExit(f"FAIL: no raw layout found for {sid} under {d}")
        if not (d / s["em"].format(r=0)).is_file():
            raise SystemExit(f"FAIL: no emission layout for {sid}")


CACHE_DIR = None   # set by --cache-dir: <cache>/<TH>x<TW>/<sid>/C_<r>.npy and E_<r>.npy, written by precache.py with these same loaders

def _cache_path(kind, sid, r):
    return None if CACHE_DIR is None else Path(CACHE_DIR) / f"{TH}x{TW}" / sid / f"{kind}_{r:06d}.npy"

def load_C(sid, r):
    cp = _cache_path("C", sid, r)
    if cp is not None and cp.is_file():
        return torch.from_numpy(np.load(cp).astype(np.float32))
    s = SESSIONS[sid]
    raw = np.frombuffer((s["dir"] / s["raw"].format(r=r)).read_bytes(), dtype=np.uint8)
    if raw.size != 5320 * 4600:
        raise ValueError(f"raw size {sid} {r}")
    x = raw.reshape(4600, 5320)
    cfa = np.stack([x[0::2, 0::2], x[0::2, 1::2], x[1::2, 0::2], x[1::2, 1::2]], 0)
    # ARM C: NO CROP. The whole sensor frame is the input; the model must find the
    # projected field itself.
    t = torch.from_numpy(cfa.astype(np.float32) / 255.0)
    return F.interpolate(t.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0)


def load_E(sid, r):
    cp = _cache_path("E", sid, r)
    if cp is not None and cp.is_file():
        return torch.from_numpy(np.load(cp).astype(np.float32))
    return _load_E_uncached(sid, r)

def _load_E_uncached(sid, r):
    """ARM C conditioning: the four XOF octave grids, each area-resized to the frame grid and
    concatenated -> 12 channels. The rendered tile is NEVER formed. Returns (12, TH, TW)."""
    s = SESSIONS[sid]
    if sid not in _STATE:
        _STATE[sid] = _load_states(sid, s["dir"])
    st = _STATE[sid]
    if r not in st:
        r = max(k for k in st if k <= r)
    octs = xof_octaves_from_hex(st[r])          # 4 x (3, h, w) in [0,1]
    ups = [F.interpolate(o.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0) for o in octs]
    return torch.cat(ups, dim=0).contiguous()   # (12, TH, TW)


class ArmCUNet(DiffusionDiagnosticUNet):
    """Identical architecture; the hint stack carries 12 octave channels + 2 coord = 14.
    Conditioning still enters through the ControlNet spatial hint path, NOT FiLM on E --
    FiLM-on-E is the documented 2026-04-29 F-A mini failure and is not repeated here."""

    @staticmethod
    def _build_hint(E: torch.Tensor) -> torch.Tensor:
        B, _, H, W = E.shape
        coord = coord_grid(H, W, E.device, E.dtype).unsqueeze(0).expand(B, 2, -1, -1)
        return torch.cat([E, coord], dim=1)


def train_row_list():
    rows = []
    for sid, s in SESSIONS.items():
        for a, b in s["train"]:
            rows += [(sid, r) for r in range(a, b)]
    return rows


def eval_rows():
    out = []
    for sid in [s for s in ("d2", "v10") if s in SESSIONS]:
        for a, b in SESSIONS[sid]["eval_blocks"]:
            out += [(sid, r) for r in range(a + 30, b - 30, 40)]
    if "august" in SESSIONS:
        out += [("august", r) for r in range(30, 682, 24)]
    return out


@torch.no_grad()
def quick_eval(model, dc, dev, rows, t_val=150, offset=2):
    model.eval()
    res = {}
    for sid in list(SESSIONS):
        cs, ws = [], []
        for s, r in rows:
            if s != sid:
                continue
            C = load_C(s, r).to(dev, torch.bfloat16)
            # Do not perturb the training RNG: a checkpoint immediately before an
            # eval must resume to the same subsequent training stream.
            gen = torch.Generator(device=dev)
            gen.manual_seed(999 + r)
            noise = torch.randn(1, 4, TH, TW, device=dev, generator=gen)
            tt = torch.full((1,), t_val, device=dev, dtype=torch.long)
            Ct = q_sample(C.float().unsqueeze(0), tt, dc, noise).to(torch.bfloat16)
            with torch.autocast(dev.type if hasattr(dev, "type") else "cuda", dtype=torch.bfloat16):
                e_c = model(Ct, load_E(s, r).to(dev, torch.bfloat16).unsqueeze(0), tt)
                e_w = model(Ct, load_E(s, min(r + offset, SESSIONS[s]["rows_total"] - 1)).to(dev, torch.bfloat16).unsqueeze(0), tt)
            cs.append(float((e_c.float() - noise).pow(2).mean()))
            ws.append(float((e_w.float() - noise).pow(2).mean()))
        c, w = np.array(cs), np.array(ws)
        res[sid] = {"n": len(cs), "correct": float(c.mean()), "wrong": float(w.mean()),
                    "delta": float((w - c).mean()), "paired": float((c < w).mean())}
    model.train()
    return res


def capture_rng_state(dev):
    return {
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state(dev) if dev.type == "cuda" else None,
        "numpy": np.random.get_state(),
        "python": random.getstate(),
    }


def save_ckpt(path: Path, model, opt, step, rng_by_rank, args_d):
    tmp = path.with_name(path.name + ".tmp")
    torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(), "step": step,
                "rng_by_rank": rng_by_rank, "rng_world_size": len(rng_by_rank),
                "sampler": "splitmix64_rank_slot_v1", "args": args_d}, tmp)
    os.replace(tmp, path)


def splitmix64(x):
    """Stable integer mixer used to map (seed, rank, sample slot) to a row."""
    mask = (1 << 64) - 1
    x = (x + 0x9E3779B97F4A7C15) & mask
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & mask
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & mask
    return x ^ (x >> 31)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "runs/arm_a_ft_20260823"))
    ap.add_argument("--ckpt", default=str(ROOT / "truthbeam/models/verifier/model_final.pt"))
    ap.add_argument("--max-steps", type=int, default=200000)  # run until stopped
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--warmup", type=int, default=200)
    ap.add_argument("--cosine-horizon", type=int, default=40000)
    ap.add_argument("--accum", type=int, default=8)
    ap.add_argument("--ckpt-every", type=int, default=1000)
    ap.add_argument("--eval-every", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--sessions", default="d2,v10,august")
    ap.add_argument("--from-scratch", action="store_true", help="random init instead of warm start (architecture from the published ckpt args)")
    ap.add_argument("--arch", choices=["armc", "zk", "zk2"], default="armc", help="armc: the published ARM-C U-Net; zk: ZkUNet (conv/ReLU/BN); zk2: LeanDenoiser (conv/ReLU, no norm, dilation at depth)")
    ap.add_argument("--qat", action="store_true", help="zk2 only: quantisation-aware training (int8 weights, int16 activations)")
    ap.add_argument("--base-ch", type=int, default=0, help="override base channels (0 = from the base checkpoint args)")
    ap.add_argument("--mults", default="", help="override channel multipliers, e.g. 1,2,4,4")
    ap.add_argument("--no-base-ckpt", action="store_true", help="lean from-scratch run: do not require or read the published base checkpoint")
    ap.add_argument("--cond-drop", type=float, default=0.2, help="hint dropout probability during training (ARM-C default 0.2; 0 = always conditioned)")
    ap.add_argument("--august-train-rows", type=int, default=712, help="use august rows [0, N) for training; the rest are held out for proof-row selection")
    ap.add_argument("--cache-dir", default="", help="pre-downsampled C/E cache root written by precache.py (same loaders, same tensors)")
    ap.add_argument("--cpu", action="store_true", help="smoke tests only: run on the CPU")
    ap.add_argument("--act-ckpt", action="store_true", help="activation checkpointing (needed on 24GB GPUs)")
    ap.add_argument("--local-root", default="", help="if set, remap session dirs onto this root (same layout: truthbeam/sessions/*, august_dev_712)")
    ap.add_argument("--prefetch", type=int, default=6, help="prefetch worker threads per rank")
    ap.add_argument("--bs", type=int, default=1, help="micro-batch per rank per accum step; effective batch = ranks*accum*bs")
    ap.add_argument("--shuffle-conditions", action="store_true", help="CONTROL: pair each C with a wrong-but-real E via a fixed seeded derangement over training rows; eval stays unshuffled")
    # ARM C takes NO crop. --crop deliberately does not exist here: it was parsed,
    # range-asserted and stamped into every checkpoint via vars(a) while load_C ignored
    # it, which is exactly the provenance defect that caused the 2026-08-25 crop confusion.
    ap.add_argument("--out-size", default="768,896", help="TH,TW after area-resize; emission is NOT cropped, only resized to the same size")
    ap.add_argument("--crop-id", default="UNCROPPED_FULL_FRAME_20260825",
                    help="ARM C is uncropped; this name is fixed and must not be set to a crop name")
    ap.add_argument("--cond-seed", type=int, default=-1, help="REQUIRED with --shuffle-conditions: independent declared seed for the derangement (must not be derived from --seed; the development machine review point 1)")
    a = ap.parse_args()
    global TH, TW, CACHE_DIR
    CACHE_DIR = a.cache_dir or None
    TH, TW = (int(v) for v in a.out_size.split(","))
    # no CROP: ARM C consumes the full sensor frame. See load_C.
    assert a.crop_id.startswith("UNCROPPED"), \
        f"ARM C is uncropped; refusing crop_id {a.crop_id!r} which would misattribute every checkpoint"
    if not a.from_scratch:
        raise SystemExit("FAIL: ARM C cannot warm-start. The published hint_encoder.s0.0.weight is "
                         "(96,11,3,3); ARM C needs hint_in_ch=14 -> (96,14,3,3), so strict load_state_dict "
                         "raises. Pass --from-scratch.")

    ddp = "RANK" in os.environ
    rank = int(os.environ.get("RANK", 0)); world = int(os.environ.get("WORLD_SIZE", 1))
    if ddp:
        dist.init_process_group("nccl")
        torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))
    is_main = rank == 0
    out = Path(a.out)
    if is_main:
        out.mkdir(parents=True, exist_ok=True)
    dev = torch.device("cpu") if a.cpu else torch.device("cuda")
    AC = dev.type   # autocast device type; bf16 autocast on cpu is supported in torch >= 2.x
    for sid in [k for k in list(SESSIONS) if k not in a.sessions.split(",")]:
        del SESSIONS[sid]
    if a.local_root:
        LR = Path(a.local_root)
        remap = {"d2": LR / "sessions/d2", "v10": LR / "sessions/v10", "august": LR / "august_dev_712"}
        for sid in SESSIONS:
            if remap[sid].is_dir():
                SESSIONS[sid]["dir"] = remap[sid]
        if is_main:
            print("data roots:", {k: str(v["dir"]) for k, v in SESSIONS.items()}, flush=True)
    resolve_raw_layout()
    if "august" in SESSIONS and getattr(a, "august_train_rows", 712) < 712:
        SESSIONS["august"]["train"] = [(0, int(a.august_train_rows))]
        if is_main:
            print(f"august train rows limited to [0, {a.august_train_rows}); rows {a.august_train_rows}..711 held out", flush=True)
    rows = train_row_list()
    if not is_main:
        pass
    print(f"[rank {rank}] train rows: {len(rows)} "
          f"(d2 {sum(1 for s,_ in rows if s=='d2')}, v10 {sum(1 for s,_ in rows if s=='v10')}, august {sum(1 for s,_ in rows if s=='august')})", flush=True)
    ev = eval_rows()

    if a.no_base_ckpt:
        if not a.from_scratch:
            raise SystemExit("FAIL: --no-base-ckpt requires --from-scratch")
        margs = {}
    else:
        if sha256(Path(a.ckpt)) != CKPT_SHA:
            raise SystemExit("FAIL: base checkpoint hash")
        ck = torch.load(a.ckpt, map_location="cpu", weights_only=True)
        margs = ck["args"]
    mults = tuple(int(v) for v in a.mults.split(",")) if a.mults else tuple(margs.get("mults", (1, 2, 4, 4)))
    base_ch = a.base_ch if a.base_ch > 0 else margs.get("base_ch", 96)
    # v3 (Astra r2 item 5): seed BEFORE construction so the declared seed also fixes the initial weights
    torch.manual_seed(a.seed + rank); np.random.seed(a.seed + rank); random.seed(a.seed + rank)
    if is_main:
        print("seeded before model construction (trainer v3)", flush=True)
    if a.arch == "zk2":
        model = LeanDenoiser(in_ch=4, base_ch=base_ch, channel_mults=mults, cond_drop_prob=getattr(a, "cond_drop", 0.2), hint_in_ch=14, qat=a.qat)
    elif a.arch == "zk":
        model = ZkUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, cond_drop_prob=getattr(a, "cond_drop", 0.2), hint_in_ch=14)
    else:
        model = ArmCUNet(in_ch=4, base_ch=base_ch, channel_mults=mults,
                                        attn_at=tuple(i == len(mults) - 1 for i in range(len(mults))),
                                        cond_drop_prob=getattr(a, "cond_drop", 0.2), hint_in_ch=14)
    if is_main:
        print(f"model arch={a.arch} base_ch={base_ch} mults={mults} params={sum(p.numel() for p in model.parameters())/1e6:.2f}M out_size={TH}x{TW}", flush=True)
    if not a.from_scratch:
        model.load_state_dict(ck["model"], strict=True)
    model = model.to(dev).train()
    # activation checkpointing: recompute ResBlock/Attn activations in backward (A10 22GB)
    import torch.utils.checkpoint as _ckpt
    def _wrap(mod):
        orig = mod.forward
        def f(*args, **kw):
            if torch.is_grad_enabled():
                return _ckpt.checkpoint(orig, *args, use_reentrant=False, **kw)
            return orig(*args, **kw)
        mod.forward = f
    if a.act_ckpt:
        n_wrapped = 0
        for m in model.modules():
            if isinstance(m, (ResBlock, Attn, ZkResBlock)):
                _wrap(m); n_wrapped += 1
        print(f"activation checkpointing on {n_wrapped} blocks", flush=True)
    raw_model = model
    if ddp:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[int(os.environ["LOCAL_RANK"])])
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    dc = build_diffusion_constants(1000, dev, torch.float32)
    step0 = 0
    resume = out / "latest.pt"
    if resume.is_file():
        rk = torch.load(resume, map_location="cpu", weights_only=False)
        raw_model.load_state_dict(rk["model"]); opt.load_state_dict(rk["optimizer"]); step0 = rk["step"]
        per_rank = rk.get("rng_by_rank")
        if isinstance(per_rank, list) and len(per_rank) == world:
            state = per_rank[rank]
            torch.set_rng_state(state["torch"])
            if dev.type == "cuda" and state.get("cuda") is not None: torch.cuda.set_rng_state(state["cuda"], dev)
            np.random.set_state(state["numpy"])
            random.setstate(state["python"])
            resume_mode = "exact_per_rank_v1"
        else:
            # Backward-compatible recovery from pre-fix rank-0-only checkpoints.
            # Rank 0 can restore its actual stream; the other streams were never
            # recorded, so seed them distinctly and say so in the receipt.
            fallback_seed = int((a.seed + 1_000_003 * rank + 7_919 * step0) % (2**31 - 1))
            torch.manual_seed(fallback_seed)
            if dev.type == "cuda": torch.cuda.manual_seed(fallback_seed)
            np.random.seed(fallback_seed % (2**32))
            random.seed(fallback_seed)
            if rank == 0 and all(k in rk for k in ("rng_torch", "rng_cuda", "rng_np", "rng_py")):
                torch.set_rng_state(rk["rng_torch"])
                old_cuda = rk["rng_cuda"]
                if dev.type == "cuda": torch.cuda.set_rng_state(old_cuda[0] if isinstance(old_cuda, list) else old_cuda, dev)
                np.random.set_state(rk["rng_np"])
                random.setstate(rk["rng_py"])
            resume_mode = "legacy_rank0_plus_distinct_rank_fallback"
        print(f"resumed at step {step0} mode={resume_mode}", flush=True)
    else:
        torch.manual_seed(a.seed + rank); np.random.seed(a.seed + rank); random.seed(a.seed + rank)
        resume_mode = "fresh_rank_seed"

    hist = open(out / "history.jsonl", "a") if is_main else open(os.devnull, "w")
    args_d = {k: getattr(a, k.replace("-", "_")) if hasattr(a, k.replace("-", "_")) else None for k in vars(a)}
    args_d = vars(a)
    t0 = time.time(); losses = []
    from concurrent.futures import ThreadPoolExecutor
    pool = ThreadPoolExecutor(max_workers=a.prefetch)
    cond_map = None
    if a.shuffle_conditions:
        if a.cond_seed < 0:
            raise SystemExit("FAIL: --shuffle-conditions requires an explicit --cond-seed (independent declared derangement seed)")
        # Fixed derangement over the row list under its OWN declared seed: every C
        # trains against a wrong-but-real E. Independent of --seed so the shuffle
        # cannot correlate with weight init or batch order (the development machine review point 1).
        import random as _rnd
        idx = list(range(len(rows)))
        g = _rnd.Random(int(a.cond_seed))
        while True:
            perm = idx[:]
            g.shuffle(perm)
            if all(perm[i] != i for i in idx):
                break
        cond_map = perm
        if is_main:
            print(f"[control] shuffle-conditions ON: derangement over {len(rows)} rows, cond_seed {a.cond_seed} (independent of main seed {a.seed})", flush=True)
    def sample_one(slot):
        # Sampling is a pure function of the completed optimizer step and rank.
        # Prefetched work therefore needs no opaque queue state in a checkpoint.
        key = (int(a.seed) ^ (int(rank) << 32) ^ int(slot)) & ((1 << 64) - 1)
        i = splitmix64(key) % len(rows)
        sid, r = rows[i]
        if cond_map is None:
            return load_C(sid, r), load_E(sid, r)
        es, er = rows[cond_map[i]]
        return load_C(sid, r), load_E(es, er)
    first_slot = step0 * a.accum * a.bs
    pending = [pool.submit(sample_one, first_slot + i) for i in range(a.prefetch)]
    next_slot = first_slot + a.prefetch
    for step in range(step0, a.max_steps):
        lr = a.lr * min(1.0, (step + 1) / a.warmup) * (0.5 * (1 + math.cos(math.pi * min(step, a.cosine_horizon) / a.cosine_horizon)))
        for g in opt.param_groups:
            g["lr"] = lr
        opt.zero_grad(set_to_none=True)
        for _ in range(a.accum):
            Cs, Es = [], []
            for _b in range(a.bs):
                Cb, Eb = pending.pop(0).result()
                pending.append(pool.submit(sample_one, next_slot))
                next_slot += 1
                Cs.append(Cb); Es.append(Eb)
            C = torch.stack(Cs).to(dev, non_blocking=True)
            E = torch.stack(Es).to(dev, non_blocking=True)
            t = torch.randint(0, 1000, (a.bs,), device=dev)
            noise = torch.randn(a.bs, 4, TH, TW, device=dev)
            Ct = q_sample(C, t, dc, noise)
            with torch.autocast(AC, dtype=torch.bfloat16):
                eps = model(Ct.to(torch.bfloat16), E, t)
                loss = F.mse_loss(eps.float(), noise) / a.accum
            loss.backward()
            losses.append(float(loss) * a.accum)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if (step + 1) % 50 == 0 and is_main:
            m = float(np.mean(losses[-50 * a.accum:]))
            if not math.isfinite(m):
                raise SystemExit("FAIL: non-finite loss")
            line = {"step": step + 1, "loss": m, "lr": lr, "elapsed_s": time.time() - t0}
            hist.write(json.dumps(line) + "\n"); hist.flush()
            print(line, flush=True)
        if (step + 1) % a.ckpt_every == 0:
            local_rng = capture_rng_state(dev)
            if ddp:
                rng_by_rank = [None] * world if is_main else None
                dist.gather_object(local_rng, rng_by_rank, dst=0)
            else:
                rng_by_rank = [local_rng]
            if is_main:
                save_ckpt(out / "latest.pt", raw_model, opt, step + 1, rng_by_rank, args_d)
                if (step + 1) % (a.ckpt_every * 5) == 0:
                    save_ckpt(out / f"step_{step+1:08d}.pt", raw_model, opt, step + 1, rng_by_rank, args_d)
            if ddp:
                dist.barrier()
        if (step + 1) % a.eval_every == 0 and is_main:
            r = quick_eval(raw_model, dc, dev, ev)
            line = {"step": step + 1, "eval": r}
            hist.write(json.dumps(line) + "\n"); hist.flush()
            print("EVAL", json.dumps(line), flush=True)


if __name__ == "__main__":
    main()
