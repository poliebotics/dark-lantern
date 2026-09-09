#!/usr/bin/env python3
"""Held-out evaluation for the two pix2pixHD runs: full-resolution generation on test_A, PSNR and SSIM against
test_B, per session and overall, plus a side-by-side strip (emission | generated | real) for a video.

Baseline:  python3 eval_p2p.py --name tb_p2p_baseline --which_epoch latest
Temporal:  P2P_TEMPORAL=1 python3 eval_p2p.py --name tb_p2p_temporal --which_epoch latest --input_nc 9
Run inside pix2pixHD/ on the box. The temporal run is autoregressive: frames are generated in order and each
generated frame is the B_{t-1} input of the next (the first frame of a session and any gap uses zeros).
Writes results/<name>/<epoch>/{metrics.json, strips/, fake/}.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
import torch
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

# the generator architecture comes from the run's own training record (checkpoints/<name>/opt.txt), so every variant
# (ngf 32 or 64, crop sizes, temporal input) is rebuilt exactly as trained; explicit CLI values are kept if given
_CKPT = os.environ.get("P2P_CKPT", "[the 6 September kit's directory on the persistent filesystem]/checkpoints")
_name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else None
_train = {}
if _name and os.path.exists(os.path.join(_CKPT, _name, "opt.txt")):
    for _line in open(os.path.join(_CKPT, _name, "opt.txt")):
        if ": " in _line and not _line.startswith("-"):
            _k, _v = _line.rstrip("\n").split(": ", 1); _train[_k.strip()] = _v.strip()
else:
    print(f"WARNING: no training opt.txt for {_name}; falling back to the ngf-32 defaults", file=sys.stderr)
def _arch(flag, key, default):
    return [] if flag in sys.argv else [flag, _train.get(key, default)]
sys.argv += ["--dataroot", os.environ.get("P2P_DATAROOT", "[the 6 September kit's directory on the persistent filesystem]/pairs"),
             "--checkpoints_dir", _CKPT,
             "--results_dir", os.environ.get("P2P_RESULTS", "[the 6 September kit's directory on the persistent filesystem]/results"),
             "--label_nc", "0", "--no_instance", "--no_flip", *([] if "--resize_or_crop" in sys.argv else ["--resize_or_crop", "none"]), "--phase", "test",
             *_arch("--netG", "netG", "local"), *_arch("--ngf", "ngf", "32"), *_arch("--n_downsample_global", "n_downsample_global", "4"),
             *_arch("--n_blocks_global", "n_blocks_global", "9"), *_arch("--n_local_enhancers", "n_local_enhancers", "1"),
             *_arch("--input_nc", "input_nc", "3"),
             "--batchSize", "1", "--nThreads", "0", "--serial_batches", "--how_many", "100000", "--gpu_ids", os.environ.get("P2P_GPU", "0")]

from concurrent.futures import ProcessPoolExecutor  # noqa: E402
import multiprocessing as _mp  # noqa: E402


def _metrics(fake_path, real_path):
    """PSNR and SSIM of one saved generated frame against the real capture (worker process; CPU only)"""
    fake = np.array(Image.open(fake_path).convert("RGB")); real = np.array(Image.open(real_path).convert("RGB"))
    if real.shape != fake.shape:
        real = np.array(Image.fromarray(real).resize((fake.shape[1], fake.shape[0]), Image.LANCZOS))
    return float(peak_signal_noise_ratio(real, fake, data_range=255)), float(structural_similarity(real, fake, channel_axis=2, data_range=255))


# the pool is created here, before the model touches CUDA, so forked workers never inherit a CUDA context
POOL = ProcessPoolExecutor(max_workers=int(os.environ.get("P2P_METRIC_PROCS", "12")), mp_context=_mp.get_context("fork"))

from options.test_options import TestOptions  # noqa: E402
from data.data_loader import CreateDataLoader  # noqa: E402
from models.models import create_model  # noqa: E402
import util.util as util  # noqa: E402

opt = TestOptions().parse(save=False)
opt.nThreads = 0
out_root = os.path.join(opt.results_dir, opt.name, opt.which_epoch + os.environ.get("P2P_OUT_SUFFIX", ""))
fake_dir = os.path.join(out_root, "fake"); strip_dir = os.path.join(out_root, "strips")
os.makedirs(fake_dir, exist_ok=True); os.makedirs(strip_dir, exist_ok=True)
# the temporal dataset reads B_{t-1} from prev_b_dir at test time: the run's own previous output (free-running, default) or,
# with P2P_PREV_B_DIR set to the held-out captures, the real previous capture (teacher-forced one-step prediction)
TEACHER_FORCED = bool(os.environ.get("P2P_PREV_B_DIR"))
opt.prev_b_dir = os.environ.get("P2P_PREV_B_DIR") or fake_dir
import re as _re  # noqa: E402
_NAME = _re.compile(r"^(?P<s>[a-z0-9]+)_(?P<i>\d{6})\.png$")
_files = lambda d: {f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))}   # regular files only, as the loader sees them
_test_a = _files(os.path.join(opt.dataroot, "test_A")); _test_b = _files(os.path.join(opt.dataroot, "test_B"))
if _test_a != _test_b: raise SystemExit(f"REFUSED: test_A and test_B name sets differ ({len(_test_a ^ _test_b)} names)")
if TEACHER_FORCED:
    # the previous-capture directory must be exactly the held-out capture set: eligibility below is derived from what the
    # dataset will actually read (predecessor by name in test_A, file present in prev_b_dir), never from an assumed layout
    _prev_set = _files(opt.prev_b_dir)
    if _prev_set != _test_b: raise SystemExit(f"REFUSED: P2P_PREV_B_DIR names differ from test_B ({len(_prev_set ^ _test_b)} names)")
def _effective_prev(name):
    """the predecessor the temporal dataset will use: the previous index if it is in the held-out set, else the frame itself"""
    m = _NAME.match(name)
    if not m or int(m.group("i")) == 0: return name
    c = f"{m.group('s')}_{int(m.group('i')) - 1:06d}.png"
    return c if c in _test_a else name
def _has_prev(name):
    """teacher-forced eligibility: a real predecessor (not the frame itself) whose capture exists where the dataset reads it"""
    p = _effective_prev(name)
    return p != name and os.path.isfile(os.path.join(opt.prev_b_dir, p))

data_loader = CreateDataLoader(opt)
dataset = data_loader.load_data()
model = create_model(opt)
model.eval()

per = defaultdict(list); skipped = []; pending = []
B_root = os.path.join(opt.dataroot, "test_B")
with torch.no_grad():
    for i, data in enumerate(dataset):
        name = os.path.basename(data["path"][0])
        generated = model.inference(data["label"], data["inst"], data.get("image"))
        fake = util.tensor2im(generated.data[0])  # HxWx3 uint8
        fake_path = os.path.join(fake_dir, name); real_path = os.path.join(B_root, name)
        Image.fromarray(fake).save(fake_path)
        session = name.split("_")[0]
        if TEACHER_FORCED and not _has_prev(name):
            skipped.append(name)  # no eligible predecessor: its "previous capture" would be itself or zero; excluded from the metric
        else:
            if TEACHER_FORCED:
                _p = _effective_prev(name)
                if _p == name or not os.path.isfile(os.path.join(opt.prev_b_dir, _p)):
                    raise SystemExit(f"REFUSED: teacher-forced row {name} would have used a self or zero previous capture")
            pending.append((session, name, POOL.submit(_metrics, fake_path, real_path)))
        if i % 25 == 0 and not (TEACHER_FORCED and not _has_prev(name)):   # no teacher-forced strip for a frame without an eligible predecessor
            real = np.array(Image.open(real_path).convert("RGB"))
            if real.shape != fake.shape:
                real = np.array(Image.fromarray(real).resize((fake.shape[1], fake.shape[0]), Image.LANCZOS))
            emission = np.array(Image.open(data["path"][0]).convert("RGB"))
            if emission.shape != fake.shape:
                emission = np.array(Image.fromarray(emission).resize((fake.shape[1], fake.shape[0]), Image.BICUBIC))
            strip = np.concatenate([emission, fake, real], axis=1)
            Image.fromarray(strip).resize((strip.shape[1] // 2, strip.shape[0] // 2), Image.LANCZOS).save(os.path.join(strip_dir, name))
        if i % 100 == 0:
            print(f"{i} {name} generated", flush=True)
for session, name, fut in pending:
    psnr, ssim = fut.result()
    per[session].append((name, psnr, ssim))
POOL.shutdown()

summary = {}
for session, rows in per.items():
    ps = np.array([r[1] for r in rows]); ss = np.array([r[2] for r in rows])
    summary[session] = {"frames": len(rows), "psnr_mean": float(ps.mean()), "psnr_median": float(np.median(ps)),
                        "ssim_mean": float(ss.mean()), "ssim_median": float(np.median(ss))}
allp = np.array([r[1] for rows in per.values() for r in rows]); alls = np.array([r[2] for rows in per.values() for r in rows])
summary["all"] = {"frames": int(len(allp)), "psnr_mean": float(allp.mean()), "ssim_mean": float(alls.mean())}
summary["run"] = {"name": opt.name, "epoch": opt.which_epoch, "input_nc": opt.input_nc, "ngf": opt.ngf, "netG": opt.netG, "train_fineSize": _train.get("fineSize"), "train_batchSize": _train.get("batchSize"), "temporal": bool(os.environ.get("P2P_TEMPORAL")), "teacher_forced": TEACHER_FORCED, "prev_b_dir": opt.prev_b_dir, "skipped_no_predecessor": skipped}
json.dump({"summary": summary, "per_frame": {s: rows for s, rows in per.items()}}, open(os.path.join(out_root, "metrics.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
