#!/usr/bin/env python3
"""Shared pieces for G1: model construction, protocol inputs, and an emulation of the
CUDA Philox `torch.randn` stream the reference evaluator drew its noise from.

Paths are configurable through the environment so the same code serves the superseded
step-12000 artifact (defaults) and the FINAL artifact (final/run_final.sh):
  G1_CKPT      checkpoint .pt
  G1_REF_JSON  the evaluator's pubproto_eval.json for that checkpoint
  G1_RAW_DIR   directory holding pubproto_raw.npz_{d2,v10}.npz for that checkpoint
  G1_TRAINLOG  optional train.log (quick_eval control, superseded artifact only)
  G1_OUT       output directory for every json/md produced by the scripts

Everything here is CPU-only.  Architectural facts are cited to the source files in
../src (see README_FINAL.md for the full citation table).
"""
from __future__ import annotations
import importlib.util, json, math, os, sys
from pathlib import Path
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
SRC = HERE / "trainer" if (HERE / "trainer" / "train_lean.py").is_file() else HERE.parent / "src"   # the publication ships the trainer under oracle/trainer/ (Astra r6 finding 8)
CKPT = Path(os.environ.get("G1_CKPT", HERE / "ckpt" / "armc_b16_96x112_s20260907_step12000.pt"))
REF_JSON = Path(os.environ.get("G1_REF_JSON", HERE.parent / "node_results" / "armc_b16_96x112_s20260907" / "pubproto_eval.json"))
RAW_DIR = Path(os.environ.get("G1_RAW_DIR", HERE / "ckpt"))
REF_TRAINLOG = Path(os.environ.get("G1_TRAINLOG", HERE.parent / "node_results" / "armc_b16_96x112_s20260907" / "train.log"))
OUT = Path(os.environ.get("G1_OUT", HERE))
OUT.mkdir(parents=True, exist_ok=True)

ROWS_ROOT = HERE / "rows"            # published layout: oracle/rows/{d2,v10}/ (the private cache prefix is not published, REDACTION.md)
ROWS_ROOT_AUG = HERE / "rows_august"  # published layout: oracle/rows_august/august/

TH, TW = 96, 112
T_VAL = 150                       # lean_pubproto_eval.py:17
EVAL_SEED = 20260823              # lean_pubproto_eval.py:17
OFFSETS = [-2, 2, -15, 15, 30]    # lean_pubproto_eval.py:16
# train_lean.py:72-84 (SESSIONS table), eval_rows() train_lean.py:176-183.
# "august": the held-out rows 600-711 of the 712 August development rows (train_lean.py:81-83; the
# final checkpoint trained on august rows [0, 600) via --august-train-rows 600).  There is NO frozen
# evaluator for August; the G1 convention for its noise is the protocol rule applied to the block
# (600, 712): one emulated CUDA-Philox generator seeded EVAL_SEED, row r at stream position r-600.
SESSIONS = {
    "d2": {"rows_total": 5992, "eval_blocks": [(1298, 1698), (2796, 3196), (4294, 4694)], "root": ROWS_ROOT / "d2", "protocol": True},
    "v10": {"rows_total": 3743, "eval_blocks": [(1110, 1360), (2345, 2595)], "root": ROWS_ROOT / "v10", "protocol": True},
    "august": {"rows_total": 712, "eval_blocks": [(600, 712)], "root": ROWS_ROOT_AUG / "august", "protocol": False},
}


def eval_rows():
    """The 37 rows train_lean.eval_rows() produces for sessions d2,v10 (train_lean.py:176-183)."""
    out = []
    for sid in ("d2", "v10"):
        for a, b in SESSIONS[sid]["eval_blocks"]:
            out += [(sid, r) for r in range(a + 30, b - 30, 40)]
    return out


def august_rows():
    """The 112 held-out August rows available on this box (600..711)."""
    return [("august", r) for r in range(600, 712)]


def rule_pair(r):
    """August proof-set rule (coordinator, 2026-09-07): nominal wrong offset OFFSETS[(r-600) mod 5], one proof per
    row 600..711.  Boundary clause: when r + offset >= 712 the mirrored offset -offset is used (rows 684, 689, 694,
    699, 704, 709 at +30 -> -30; 698, 703, 708 at +15 -> -15; 711 at +2 -> -2).
    Returns (effective_offset, wrong_row, "direct"|"mirrored", nominal_offset)."""
    o = OFFSETS[(r - 600) % 5]
    if r + o >= 712:
        return -o, r - o, "mirrored", o
    return o, r + o, "direct", o


def august_offsets(r):
    """The five protocol offsets plus the rule-pair offset when it is not one of them (the mirrored -30)."""
    ro = rule_pair(r)[0]
    return OFFSETS + ([ro] if ro not in OFFSETS else [])


def row_available(sid, r):
    return 0 <= r < SESSIONS[sid]["rows_total"] and (SESSIONS[sid]["root"] / f"E_{r:06d}.npy").is_file()


def protocol_row_index(sid, r):
    """Position of row r in lean_pubproto_eval.py's per-session row order (lines 115-117,
    stride 1).  The session noise generator is drawn once per position, in this order."""
    i = 0
    for lo, hi in SESSIONS[sid]["eval_blocks"]:
        if lo <= r < hi:
            return i + (r - lo)
        i += hi - lo
    raise ValueError(f"row {sid} {r} is not inside an eval block")


# ---------------------------------------------------------------- model

def import_trainer():
    """Import ../src/train_lean.py as a module without writing bytecode under src/."""
    sys.dont_write_bytecode = True
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    spec = importlib.util.spec_from_file_location("train_lean", str(SRC / "train_lean.py"))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def build_model(ckpt_path=None):
    """Construct exactly as train_lean.py:341-343 and load strictly (train_lean.py:347)."""
    ckpt_path = Path(ckpt_path or CKPT)
    M = import_trainer()
    ck = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    args = ck["args"]
    base_ch = int(args["base_ch"]) if int(args.get("base_ch", 0)) > 0 else 96
    mults = tuple(int(v) for v in args["mults"].split(",")) if args.get("mults") else (1, 2, 4, 4)
    # cond_drop only acts in training mode (diffusion_diagnostic_model.py:274); inference is unaffected.
    cond_drop = float(args.get("cond_drop", 0.2))
    model = M.ArmCUNet(in_ch=4, base_ch=base_ch, channel_mults=mults,
                       attn_at=tuple(i == len(mults) - 1 for i in range(len(mults))),
                       cond_drop_prob=cond_drop, hint_in_ch=14)
    model.load_state_dict(ck["model"], strict=True)
    model.eval()
    dc = M.build_diffusion_constants(1000, torch.device("cpu"), torch.float32)   # train_lean.py:368
    return model, dc, M, ck


# ---------------------------------------------------------------- data

def load_C_bf16(sid, r):
    """train_lean.load_C (line 120-123) then the evaluator's .to(bfloat16) (lean_pubproto_eval.py:125)."""
    x = np.load(SESSIONS[sid]["root"] / f"C_{r:06d}.npy").astype(np.float32)
    return torch.from_numpy(x).to(torch.bfloat16)


def load_E_bf16(sid, r):
    """train_lean.load_E (line 136-139) then .to(bfloat16) (lean_pubproto_eval.py:130,136)."""
    x = np.load(SESSIONS[sid]["root"] / f"E_{r:06d}.npy").astype(np.float32)
    return torch.from_numpy(x).to(torch.bfloat16)


def make_Ct(C_bf16, noise_f32, dc, M):
    """lean_pubproto_eval.py:128: Ct = q_sample(C.float().unsqueeze(0), tt, dc, noise).to(bfloat16)."""
    tt = torch.full((1,), T_VAL, dtype=torch.long)
    return M.q_sample(C_bf16.float().unsqueeze(0), tt, dc, noise_f32).to(torch.bfloat16)


def score(e, noise):
    """lean_pubproto_eval.py:131: float((e.float() - noise).pow(2).mean())."""
    return float((e.float() - noise).pow(2).mean())


# ---------------------------------------------------------------- CUDA Philox randn emulation
# torch.randn on a CUDA tensor with a torch.Generator(device="cuda") draws from cuRAND's
# Philox4x32-10 through ATen's distribution_nullary_kernel.  For numel = 43008 on an
# A100 (108 SMs, 2048 threads/SM) the launch is 168 blocks x 256 threads = exactly one
# thread per element, so element idx takes the .x lane of curand_normal4() of the thread
# whose curand_init was (seed, subsequence=idx, offset=4*call).  The per-call philox
# offset increment is 4 (calc_execution_policy counter_offset), so the k-th randn call
# on a freshly seeded generator uses counter (k, 0, idx, 0) and key (seed_lo, seed_hi).
# Box-Muller: u from lane x, v from lane y; result .x = sqrt(-2 ln u) * sin(v).
# The Philox WORDS are exact (known-answer tests).  The float32 transform here uses libm
# log/sin, cuRAND uses logf and the fast __sincosf: the correspondence to the GPU's float
# samples is APPROXIMATE (about 1e-6 absolute per sample; Astra r3 measured that a 4.77e-7
# perturbation flips two Q12 target integers on d2/1328).  The NORMATIVE noise of the G1
# artifact is therefore the exported integer target (IN:noise_int, Q12) together with the
# exported float32 stream bytes (IN:noise_f32), not a re-derivation from CUDA.

_M0, _M1 = np.uint64(0xD2511F53), np.uint64(0xCD9E8D57)
_W0, _W1 = np.uint32(0x9E3779B9), np.uint32(0xBB67AE85)
_MASK32 = np.uint64(0xFFFFFFFF)


def philox4x32_10(c0, c1, c2, c3, k0, k1):
    """Random123 / cuRAND Philox4x32-10.  All inputs numpy uint32 arrays of one shape (or scalars)."""
    c0 = np.asarray(c0, dtype=np.uint32); c1 = np.asarray(c1, dtype=np.uint32)
    c2 = np.asarray(c2, dtype=np.uint32); c3 = np.asarray(c3, dtype=np.uint32)
    k0 = np.uint32(k0); k1 = np.uint32(k1)
    with np.errstate(over="ignore"):
        for rnd in range(10):
            if rnd > 0:
                k0 = np.uint32((int(k0) + int(_W0)) & 0xFFFFFFFF)
                k1 = np.uint32((int(k1) + int(_W1)) & 0xFFFFFFFF)
            p0 = _M0 * c0.astype(np.uint64)
            p1 = _M1 * c2.astype(np.uint64)
            hi0 = (p0 >> np.uint64(32)).astype(np.uint32); lo0 = (p0 & _MASK32).astype(np.uint32)
            hi1 = (p1 >> np.uint64(32)).astype(np.uint32); lo1 = (p1 & _MASK32).astype(np.uint32)
            c0, c1, c2, c3 = (hi1 ^ c1 ^ k0), lo1, (hi0 ^ c3 ^ k1), lo0
    return c0, c1, c2, c3


def philox_self_test():
    """Random123 known-answer vectors for philox4x32-10 (kat_vectors)."""
    kats = [
        ((0, 0, 0, 0), (0, 0), (0x6627e8d5, 0xe169c58d, 0xbc57ac4c, 0x9b00dbd8)),
        ((0xffffffff,) * 4, (0xffffffff,) * 2, (0x408f276d, 0x41c83b0e, 0xa20bc7c6, 0x6d5451fd)),
        ((0x243f6a88, 0x85a308d3, 0x13198a2e, 0x03707344), (0xa4093822, 0x299f31d0),
         (0xd16cfe09, 0x94fdcceb, 0x5001e420, 0x24126ea1)),
    ]
    ok = True
    for ctr, key, want in kats:
        got = tuple(int(v) for v in philox4x32_10(*ctr, *key))
        ok &= (got == want)
    return ok


_INV = np.float32(2.3283064e-10)                     # CURAND_2POW32_INV
_INV_2PI = np.float32(2.3283064e-10) * np.float32(6.2831855)   # CURAND_2POW32_INV_2PI (float product)


def box_muller_x(x_u32, y_u32):
    """cuRAND _curand_box_muller(x, y).x in float32 arithmetic (libm log/sin; approximate vs the GPU)."""
    u = x_u32.astype(np.float32) * _INV + _INV / np.float32(2)
    v = y_u32.astype(np.float32) * _INV_2PI + _INV_2PI / np.float32(2)
    s = np.sqrt(np.float32(-2) * np.log(u)).astype(np.float32)
    return (np.sin(v).astype(np.float32) * s).astype(np.float32)


def _box_muller_y(x_u32, y_u32):
    u = x_u32.astype(np.float32) * _INV + _INV / np.float32(2)
    v = y_u32.astype(np.float32) * _INV_2PI + _INV_2PI / np.float32(2)
    s = np.sqrt(np.float32(-2) * np.log(u)).astype(np.float32)
    return (np.cos(v).astype(np.float32) * s).astype(np.float32)


def randn_cuda_emul(seed: int, call_index: int, numel: int = 4 * TH * TW,
                    sms: int = 108, max_threads_per_sm: int = 2048):
    """Emulate torch.randn(numel, device='cuda', generator=g) where g was seeded with `seed`
    and `call_index` randn calls of this exact size preceded it (each advancing the philox
    offset by 4).  Returns float32 (numel,)."""
    block = 256
    grid = (numel + block - 1) // block
    grid = min(grid, sms * (max_threads_per_sm // block))
    stride = grid * block
    unroll = 4
    counter_offset = ((numel - 1) // (stride * unroll) + 1) * unroll
    base_ctr = (call_index * counter_offset) // 4          # curand_init offset / 4 -> ctr.x
    assert (call_index * counter_offset) % 4 == 0
    k0, k1 = seed & 0xFFFFFFFF, (seed >> 32) & 0xFFFFFFFF
    out = np.empty(numel, dtype=np.float32)
    idx = np.arange(stride, dtype=np.uint32)
    rounded = ((numel - 1) // (stride * unroll) + 1) * stride * unroll
    it = 0
    for lin0 in range(0, rounded, stride * unroll):
        c0 = np.full(stride, (base_ctr + it) & 0xFFFFFFFF, dtype=np.uint32)
        c1 = np.full(stride, ((base_ctr + it) >> 32) & 0xFFFFFFFF, dtype=np.uint32)
        x0, x1, x2, x3 = philox4x32_10(c0, c1, idx, np.zeros(stride, np.uint32), k0, k1)
        lanes = [box_muller_x(x0, x1), None, box_muller_x(x2, x3), None]
        if numel > lin0 + stride:
            lanes[1], lanes[3] = _box_muller_y(x0, x1), _box_muller_y(x2, x3)
        for ii in range(unroll):
            li = lin0 + idx.astype(np.int64) + stride * ii
            m = li < numel
            if not m.any():
                continue
            out[li[m]] = lanes[ii][m]
        it += 1
    return out


def protocol_noise(sid, r):
    """The frozen-protocol noise for row r: session generator seeded EVAL_SEED, one draw per
    row in row order (lean_pubproto_eval.py:122-126).  For 'august' this is the G1 convention
    over the held-out block (600, 712); no evaluator ran on August."""
    i = protocol_row_index(sid, r)
    return torch.from_numpy(randn_cuda_emul(EVAL_SEED, i).reshape(1, 4, TH, TW))


def quick_eval_noise(r):
    """train_lean.quick_eval noise: fresh generator manual_seed(999 + r), one draw (train_lean.py:198-200).
    Used only for the superseded artifact's control against train.log."""
    return torch.from_numpy(randn_cuda_emul(999 + r, 0).reshape(1, 4, TH, TW))


def read_trainlog_eval(step=12000):
    """The quick_eval line the trainer logged at `step` (train.log / history.jsonl), if the log exists."""
    if not Path(REF_TRAINLOG).exists():
        return None
    for line in Path(REF_TRAINLOG).read_text().splitlines():
        if line.startswith("EVAL "):
            d = json.loads(line[5:])
            if d.get("step") == step:
                return d["eval"]
    return None


def env_summary():
    return {"G1_CKPT": str(CKPT), "G1_REF_JSON": str(REF_JSON), "G1_RAW_DIR": str(RAW_DIR), "G1_OUT": str(OUT),
            "torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0]}


if __name__ == "__main__":
    print("philox KAT:", philox_self_test())
    n = randn_cuda_emul(20260823, 0)
    print("emulated randn(seed 20260823, call 0): mean %.5f std %.5f min %.3f max %.3f" % (n.mean(), n.std(), n.min(), n.max()))
    print(env_summary())
