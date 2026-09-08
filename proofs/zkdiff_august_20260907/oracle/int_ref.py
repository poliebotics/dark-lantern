#!/usr/bin/env python3
"""G1 integer (fixed-point) reference inference of the ARM-C lean denoiser.

The network program is written once (`forward_program`) against a small backend
interface and executed by two backends:

  F64Backend : float64 numpy mirror of the torch model (t-embedding folded into the
               conv1 biases).  Used (a) to check the program against torch fp32 and
               (b) to calibrate the per-tensor fixed-point scales.
  IntBackend : int64 numpy, kernels from kernels.py.  Every stored tensor is an int16
               value set with a static per-tensor scale 2^-f; every op is exact integer
               arithmetic with documented rounding.  Weights are per-output-channel
               int16 (first baseline) or int8 ("scheme").

Execution contract (restated in README_FINAL.md; kernels.py holds the rounding rules):
  scale map    ONE effective map, `scale_map`, recorded from an executed trace and then locked:
               every tensor's f at execution is asserted equal to the published value.  Sources:
               fixed (hint 14, C_t 12, out_conv 12), calibration (conv, GroupNorm, activation,
               add, concat outputs: f = clip(floor(log2(32768 / (2 * maxabs))), 0, 15)), inherited
               (avg-pool, bilinear and attention outputs carry their input's f).
  domain       full int16 [-32768, 32767]; every clamp counted, including input quantisation
               clips, the C_t clamp and runtime hits on clipped LUT entries.
  noising      C_int = rint(C_bf16 * 2^12), noise_int = rint(noise * 2^12) (also the target),
               C_t_int = clamp16((SA*C_int + SO*noise_int + 2^15) >> 16), SA/SO = rint(sqrt(a_150),
               sqrt(1-a_150) * 2^16) from the trainer's float32 diffusion constants
  conv         acc = sum Wq*x (exact int64); y = clamp16((acc*M_c + b'_c + 2^(S-1)) >> S)
               Wq = rint(W/s_c), s_c = max|W[c]|/qmax (qmax 32767 or 127)
               M_c = rint(s_c * 2^(f_out - f_in + S)), b'_c = rint(bias_c * 2^(f_out + S))
               S chosen per layer so max M_c < 2^min(24, 62 - bits(32768*max_c sum|Wq[c]|))
  groupnorm    exact integer sums, N = n*S2 - S1^2 + n^2*eps_int, mean with 6 extra bits,
               Q = isqrt((n*2^(f_out+T-6))^2 // N), T = 30, gamma at 12 fractional bits
  silu/gelu    65536-entry int16 lookup tables per (f_in, f_out), clipped entries known
  softmax      exp table 2^15 entries, argument resolution 2^-10, values at 2^20,
               logit scale 1/sqrt(head_dim) as (mult, shift) from kernels.attention_scale,
               out = round_div(sum w*v, sum w)
  avgpool2     (a+b+c+d+2) >> 2 ; bilinear x2: exact k/16 weights, (sum+8) >> 4
  add / cat    align both operands to max(f) by exact left shift, add, one rounding to f_out
  bounds       static bounds over the admitted domain are computed from the frozen constants and
               traced shapes (`static_bounds`) with Python ints and exported with the artifact
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
import kernels as K
from common import (CKPT, OUT, T_VAL, TH, TW, august_rows, build_model, env_summary, eval_rows, import_trainer,
                    load_C_bf16, load_E_bf16, make_Ct, protocol_noise, protocol_row_index, row_available)

HERE = Path(__file__).resolve().parent
HEADROOM = 2.0
F_CT, F_HINT, F_EPS = 12, 14, 12
GN_T, GN_GAMMA_BITS = 30, 12
R_EXP, EXP_SIZE, P_EXP = 10, 1 << 15, 20
NOISE_P = 16
ROUNDING = {
    "conversion": "float -> integer once at freeze time (inputs C/noise/E, coordinates, weights, biases, multipliers, gamma/beta, LUT and exp-table entries): ties to even (numpy rint)",
    "runtime_shift": "rshift_round(v, s) = (v + 2^(s-1)) >> s with arithmetic (floor) shift: ties toward +inf; exact left shift v << -s when s <= 0",
    "runtime_division": "round_div(a, b) = floor((2a + b) / (2b)), b > 0: ties toward +inf",
    "port_rule": "a Rust port imports the frozen integer constants and tables from the artifact; it must not regenerate them from transcendental functions",
}
DOMAIN = {"admitted": [K.I16_MIN, K.I16_MAX], "policy": "saturate to the admitted domain and count every clamp; static bounds use 32768",
          "counted": ["input:C", "input:noise", "input:E", "input:coord", "C_t", "every op output", "lut_clipped_hit:<layer> (runtime lookups of clipped table entries)"]}


# ---------------------------------------------------------------- parameters from the torch model

def extract_params(model):
    """float64 copies of every weight, with the t=150 time-embedding folded into conv1 biases."""
    sd = {k: v.detach().double().numpy() for k, v in model.state_dict().items()}
    P = {"conv": {}, "gn": {}}
    half = model.t_emb.dim // 2                                      # TimeEmb.forward, diffusion_diagnostic_model.py:72-81
    freqs = np.exp(-math.log(10000) * np.arange(half, dtype=np.float64) / half)
    ang = float(T_VAL) * freqs
    emb = np.concatenate([np.sin(ang), np.cos(ang)])
    h1 = sd["t_emb.mlp.0.weight"] @ emb + sd["t_emb.mlp.0.bias"]
    h1 = F.gelu(torch.from_numpy(h1)).numpy()                       # exact erf GELU as torch
    t_emb = sd["t_emb.mlp.2.weight"] @ h1 + sd["t_emb.mlp.2.bias"]
    silu_t = t_emb / (1.0 + np.exp(-t_emb))                         # F.silu(t_emb), ResBlock.forward line 101
    P["t_emb"] = t_emb; P["silu_t_emb"] = silu_t
    for name, m in model.named_modules():
        if isinstance(m, torch.nn.Conv2d):
            P["conv"][name] = {"w": sd[name + ".weight"], "b": sd[name + ".bias"].copy(), "stride": m.stride[0], "pad": m.padding[0]}
        elif isinstance(m, torch.nn.GroupNorm):
            P["gn"][name] = {"g": m.num_groups, "gamma": sd[name + ".weight"], "beta": sd[name + ".bias"], "eps": m.eps}
    for name, m in model.named_modules():                            # fold t_proj(silu(t_emb)) into conv1 bias
        if hasattr(m, "t_proj") and isinstance(m.t_proj, torch.nn.Linear):
            tp = sd[name + ".t_proj.weight"] @ silu_t + sd[name + ".t_proj.bias"]
            P["conv"][name + ".conv1"]["b"] = P["conv"][name + ".conv1"]["b"] + tp
            P["conv"][name + ".conv1"]["t_fold"] = tp
    P["has_skip"] = {name for name, m in model.named_modules() if hasattr(m, "skip") and isinstance(m.skip, torch.nn.Conv2d)}
    P["n_heads"] = {name: m.n_heads for name, m in model.named_modules() if hasattr(m, "n_heads")}
    return P


def coord_grid_f64(h, w):
    """coord_grid (diffusion_diagnostic_model.py:53-58): channel 0 = x (width), channel 1 = y (height)."""
    y = np.linspace(-1.0, 1.0, h); x = np.linspace(-1.0, 1.0, w)
    yy, xx = np.meshgrid(y, x, indexing="ij")
    return np.stack([xx, yy], 0)


# ---------------------------------------------------------------- the network program

def forward_program(B, Ct, E):
    """DiffusionDiagnosticUNet.forward (diffusion_diagnostic_model.py:262-312) with ArmCUNet._build_hint
    (train_lean.py:161-165), base_ch 16, mults (1,2,4,4), attention only at level 3."""
    hint = B.build_hint(E)                                            # (14,H,W)
    feats = []
    h = hint
    for s in range(4):                                                # HintEncoder, lines 139-157
        h = B.conv(f"hint_encoder.s{s}.0", h)
        h = B.gn(f"hint_encoder.s{s}.1", h)
        h = B.act("gelu", f"hint_encoder.s{s}.gelu", h)
        feats.append(h)
    x = B.conv("in_conv", Ct)                                         # line 286
    skips = []
    for i in range(4):                                                # lines 288-299
        for j in range(2):
            x = resblock(B, f"downs.{i}.{j}", x)
        if i == 3:
            x = attn(B, "down_attns.3", x)
        hi = feats[i]
        assert hi.shape[-2] * 2 == x.shape[-2] and hi.shape[-1] * 2 == x.shape[-1], (hi.shape, x.shape)
        hi = B.bilinear_up2(f"hint_up.{i}", hi)                       # F.interpolate bilinear, align_corners=False
        x = B.add(f"inject.{i}", x, B.conv(f"adapters.{i}.conv", hi))
        skips.append(x)
        x = B.avgpool2(f"pool.{i}", x)
    x = resblock(B, "mid_a", x); x = attn(B, "mid_attn", x); x = resblock(B, "mid_b", x)   # lines 301-303
    for u in range(4):                                                # lines 305-310
        i = 3 - u
        skip = skips[i]
        assert skip.shape[-2] == 2 * x.shape[-2] and skip.shape[-1] == 2 * x.shape[-1]
        x = B.bilinear_up2(f"up.{u}", x)
        x = B.cat(f"cat.{u}", x, skip)
        for j in range(2):
            x = resblock(B, f"ups.{u}.{j}", x)
        if u == 0:
            x = attn(B, "up_attns.0", x)
    x = B.gn("out_norm", x); x = B.act("silu", "out_silu", x)
    return B.conv("out_conv", x)                                      # line 312


def resblock(B, name, x):
    """ResBlock.forward (lines 99-103); t_proj(silu(t_emb)) is folded into conv1's bias."""
    h = B.act("silu", f"{name}.silu1", B.gn(f"{name}.norm1", x))
    h = B.conv(f"{name}.conv1", h)
    h = B.act("silu", f"{name}.silu2", B.gn(f"{name}.norm2", h))
    h = B.conv(f"{name}.conv2", h)
    sk = B.conv(f"{name}.skip", x) if name in B.P["has_skip"] else x
    return B.add(f"{name}.res", h, sk)


def attn(B, name, x):
    """Attn.forward (lines 114-125): n_heads heads, scores / sqrt(head_dim)."""
    qkv = B.conv(f"{name}.qkv", B.gn(f"{name}.norm", x))
    out = B.attention(f"{name}.attn", qkv, n_heads=B.P["n_heads"][name])
    return B.add(f"{name}.res", x, B.conv(f"{name}.proj", out))


# ---------------------------------------------------------------- float64 backend

class F64Backend:
    def __init__(self, P, record=None):
        self.P = P; self.rec = record; self.tensors = {}

    def _r(self, name, v):
        if self.rec is not None:
            self.rec[name] = max(self.rec.get(name, 0.0), float(np.abs(v).max()))
        self.tensors[name] = v
        return v

    def build_hint(self, E):
        return self._r("hint", np.concatenate([E, coord_grid_f64(E.shape[1], E.shape[2])], 0))

    def conv(self, name, x):
        p = self.P["conv"][name]
        w, b, s, pad = p["w"], p["b"], p["stride"], p["pad"]
        O, C, kh, kw = w.shape
        xp = np.pad(x, ((0, 0), (pad, pad), (pad, pad)))
        Ho = (x.shape[1] + 2 * pad - kh) // s + 1; Wo = (x.shape[2] + 2 * pad - kw) // s + 1
        cols = np.empty((C, kh, kw, Ho, Wo))
        for i in range(kh):
            for j in range(kw):
                cols[:, i, j] = xp[:, i:i + s * Ho:s, j:j + s * Wo:s]
        y = w.reshape(O, -1) @ cols.reshape(-1, Ho * Wo) + b[:, None]
        return self._r(name, y.reshape(O, Ho, Wo))

    def gn(self, name, x):
        p = self.P["gn"][name]
        xg = x.reshape(p["g"], -1)
        mu = xg.mean(1, keepdims=True); var = xg.var(1, keepdims=True)      # biased variance, as torch GroupNorm
        y = ((xg - mu) / np.sqrt(var + p["eps"])).reshape(x.shape)
        return self._r(name, y * p["gamma"][:, None, None] + p["beta"][:, None, None])

    def act(self, kind, name, x):
        y = x / (1.0 + np.exp(-x)) if kind == "silu" else F.gelu(torch.from_numpy(x)).numpy()
        return self._r(name, y)

    def add(self, name, a, b):
        return self._r(name, a + b)

    def cat(self, name, a, b):
        return self._r(name, np.concatenate([a, b], 0))

    def avgpool2(self, name, x):
        return self._r(name, 0.25 * (x[:, 0::2, 0::2] + x[:, 0::2, 1::2] + x[:, 1::2, 0::2] + x[:, 1::2, 1::2]))

    def bilinear_up2(self, name, x):
        def up(v, axis):
            v = np.moveaxis(v, axis, 0); n = v.shape[0]
            ip = np.maximum(np.arange(n) - 1, 0); inx = np.minimum(np.arange(n) + 1, n - 1)
            out = np.empty((2 * n,) + v.shape[1:]); out[0::2] = 0.25 * v[ip] + 0.75 * v; out[1::2] = 0.75 * v + 0.25 * v[inx]
            return np.moveaxis(out, 0, axis)
        return self._r(name, up(up(x, 1), 2))

    def attention(self, name, qkv, n_heads):
        C3, H, W = qkv.shape; c = C3 // 3; d = c // n_heads
        q, k, v = (t.reshape(n_heads, d, H * W) for t in np.split(qkv, 3, 0))
        a = np.einsum("hci,hcj->hij", q, k) / math.sqrt(d)
        a = a - a.max(-1, keepdims=True); a = np.exp(a); a /= a.sum(-1, keepdims=True)
        return self._r(name, np.einsum("hij,hcj->hci", a, v).reshape(c, H, W))


# ---------------------------------------------------------------- integer backend

class ITensor:
    __slots__ = ("v", "f")
    def __init__(self, v, f):
        self.v = v; self.f = f
    @property
    def shape(self):
        return self.v.shape
    def real(self):
        return self.v.astype(np.float64) * (2.0 ** -self.f)


class IntBackend:
    def __init__(self, P, ftab, scheme, record_tensors=False):
        assert scheme in ("int8", "int16")
        self.P = P; self.ftab = ftab; self.scheme = scheme
        self.qmax = 127 if scheme == "int8" else 32767
        self.Q = {}                       # quantised constants, keyed by (layer name, f_in)
        self.luts = {}                    # (kind, f_in, f_out) -> (table, clipped_mask)
        self.exp_table = K.make_exp_table(R_EXP, EXP_SIZE, P_EXP)
        self.sat = {}                     # every clamp / clip event, per name
        self.bounds_obs = {}              # observed accumulator bit-lengths per conv layer
        self.eff_f = {}                   # executed f per tensor (filled during the trace)
        self.scale_map = None             # locked map; execution is asserted against it once set
        self.scale_source = {}
        self.shapes = {}
        self.tensors = {} if record_tensors else None
        coord = coord_grid_f64(TH, TW) * 2.0 ** F_HINT
        self.hint_coord = self._quant_input(coord, "input:coord")
        self.SA_INT = self.SO_INT = None

    def _r(self, name, t, source):
        if self.scale_map is None:
            self.eff_f[name] = t.f; self.scale_source[name] = source
        else:
            assert self.scale_map[name] == t.f, (name, self.scale_map[name], t.f)
        self.shapes[name] = tuple(int(s) for s in t.shape)
        if self.tensors is not None:
            self.tensors[name] = t
        return t

    def f_out(self, name):
        return self.ftab[name]

    def _quant_input(self, real_scaled, name):
        """rint (ties to even) then clamp to the admitted domain, counting clipped elements."""
        v = np.rint(real_scaled)
        n = int(np.count_nonzero((v < K.I16_MIN) | (v > K.I16_MAX)))
        if n:
            self.sat[name] = self.sat.get(name, 0) + n
        return np.clip(v, K.I16_MIN, K.I16_MAX).astype(np.int64)

    # -- inputs and integer forward noising (q_sample, diffusion_diagnostic_model.py:335-339)
    def set_noising_constants(self, dc):
        sa = float(dc["sqrt_alphas_cum"][T_VAL]); so = float(dc["sqrt_one_minus_alphas_cum"][T_VAL])
        self.SA_INT = int(np.rint(sa * 2.0 ** NOISE_P)); self.SO_INT = int(np.rint(so * 2.0 ** NOISE_P))
        self.noising = {"sqrt_alphas_cum_t_f32": sa, "sqrt_one_minus_alphas_cum_t_f32": so, "P": NOISE_P, "SA_INT": self.SA_INT, "SO_INT": self.SO_INT}

    def quant_C(self, C_bf16):
        return self._quant_input(C_bf16.float().numpy().reshape(4, TH, TW).astype(np.float64) * 2.0 ** F_CT, "input:C")

    def quant_noise(self, noise_f32):
        return self._quant_input(noise_f32.numpy().reshape(4, TH, TW).astype(np.float64) * 2.0 ** F_EPS, "input:noise")

    def quant_E(self, E_bf16):
        return self._quant_input(E_bf16.float().numpy().reshape(12, TH, TW).astype(np.float64) * 2.0 ** F_HINT, "input:E")

    def noise_Ct(self, C_int, noise_int):
        """Integer q_sample: C_t = sqrt(a_t) C + sqrt(1-a_t) noise, both at f=12, one rounding."""
        assert F_CT == F_EPS and self.SA_INT is not None
        assert (self.SA_INT + self.SO_INT) * K.I16_ABS < (1 << 62)
        acc = self.SA_INT * C_int + self.SO_INT * noise_int
        return ITensor(K.clamp16(K.rshift_round(acc, NOISE_P), self.sat, "C_t"), F_CT)

    def int_inputs(self, C_bf16, noise_f32, E_bf16):
        C_int = self.quant_C(C_bf16); noise_int = self.quant_noise(noise_f32); E_int = self.quant_E(E_bf16)
        return {"C_int": C_int, "noise_int": noise_int, "E_int": E_int, "Ct": self.noise_Ct(C_int, noise_int), "E": ITensor(E_int, F_HINT)}

    def build_hint(self, E):
        assert E.f == F_HINT
        return self._r("hint", ITensor(np.concatenate([E.v, self.hint_coord], 0), F_HINT), "fixed")

    # -- conv
    def _quant_conv(self, name, f_in):
        key = (name, f_in)
        if key in self.Q:
            return self.Q[key]
        p = self.P["conv"][name]
        w, b = p["w"], p["b"]
        O = w.shape[0]
        amax = np.abs(w.reshape(O, -1)).max(1)
        s = np.where(amax > 0, amax / self.qmax, 1.0)
        wq = np.clip(np.rint(w / s[:, None, None, None]), -self.qmax, self.qmax).astype(np.int64)
        f_out = self.f_out(name)
        accbound = K.conv_acc_bound(wq)                       # 32768 * max L1 row: bounds EVERY partial sum
        mbits = min(24, 62 - accbound.bit_length())
        scale = s * 2.0 ** (f_out - f_in)
        S = mbits - 1 - int(math.floor(math.log2(scale.max())))
        M = np.rint(scale * 2.0 ** S).astype(np.int64)
        assert M.max() < (1 << mbits) and M.min() >= 0
        bp = np.rint(b * 2.0 ** (f_out + S)).astype(np.int64)
        expr = accbound * int(M.max()) + int(np.abs(bp).max()) + (1 << (S - 1))
        assert expr < (1 << 63), name
        q = {"wq": wq, "M": M, "bp": bp, "S": S, "f_in": f_in, "f_out": f_out, "stride": p["stride"], "pad": p["pad"],
             "mbits": mbits, "accbound": accbound, "requant_expr_bound": expr, "qmax": self.qmax}
        self.Q[key] = q
        return q

    def conv(self, name, x):
        q = self._quant_conv(name, x.f)
        assert K.in_domain(x.v), name
        acc = K.conv2d_acc(x.v, q["wq"], q["stride"], q["pad"])
        amax = int(np.abs(acc).max())
        assert amax <= q["accbound"]
        self.bounds_obs[name] = max(self.bounds_obs.get(name, 0), amax.bit_length())
        y = K.requant(acc, q["M"], q["bp"], q["S"], self.sat, name)
        return self._r(name, ITensor(y, q["f_out"]), "calibration" if name != "out_conv" else "fixed")

    # -- groupnorm
    def _quant_gn(self, name, f_in):
        key = (name, f_in)
        if key in self.Q:
            return self.Q[key]
        p = self.P["gn"][name]; f_out = self.f_out(name)
        q = {"g": p["g"], "gamma_q": np.rint(p["gamma"] * 2.0 ** GN_GAMMA_BITS).astype(np.int64),
             "beta_q": np.rint(p["beta"] * 2.0 ** f_out).astype(np.int64),
             "eps_int": max(1, int(np.rint(p["eps"] * 2.0 ** (2 * f_in)))), "f_in": f_in, "f_out": f_out}
        assert int(np.abs(q["gamma_q"]).max()) < (1 << 15)
        self.Q[key] = q
        return q

    def gn(self, name, x):
        q = self._quant_gn(name, x.f)
        y = K.groupnorm_int(x.v, q["g"], q["gamma_q"], q["beta_q"], q["eps_int"], GN_T, q["f_out"], self.sat, name)
        return self._r(name, ITensor(y, q["f_out"]), "calibration")

    # -- activations
    def act(self, kind, name, x):
        f_out = self.f_out(name)
        key = (kind, x.f, f_out)
        if key not in self.luts:
            fn = (lambda z: z / (1.0 + np.exp(-z))) if kind == "silu" else (lambda z: F.gelu(torch.from_numpy(np.ascontiguousarray(z))).numpy())
            self.luts[key] = K.make_act_lut_with_mask(fn, x.f, f_out)
        table, mask = self.luts[key]
        hits = int(np.count_nonzero(mask[x.v + 32768]))
        if hits:
            self.sat[f"lut_clipped_hit:{name}"] = self.sat.get(f"lut_clipped_hit:{name}", 0) + hits
        return self._r(name, ITensor(K.lut_apply(x.v, table), f_out), "calibration")

    # -- structural
    def add(self, name, a, b):
        f_out = self.f_out(name); fm = max(a.f, b.f)
        s = K.rescale(a.v, a.f, fm) + K.rescale(b.v, b.f, fm)       # |.| <= 2 * 32768 * 2^15 = 2^31
        return self._r(name, ITensor(K.clamp16(K.rescale(s, fm, f_out), self.sat, name), f_out), "calibration")

    def cat(self, name, a, b):
        f_out = self.f_out(name)
        v = np.concatenate([K.clamp16(K.rescale(a.v, a.f, f_out), self.sat, name), K.clamp16(K.rescale(b.v, b.f, f_out), self.sat, name)], 0)
        return self._r(name, ITensor(v, f_out), "calibration")

    def avgpool2(self, name, x):
        return self._r(name, ITensor(K.avgpool2_int(x.v, self.sat, name), x.f), "inherited")

    def bilinear_up2(self, name, x):
        return self._r(name, ITensor(K.bilinear_up2_int(x.v, self.sat, name), x.f), "inherited")

    def attention(self, name, qkv, n_heads):
        C3, H, W = qkv.shape; c = C3 // 3; d = c // n_heads
        q, k, v = (t.reshape(n_heads, d, H * W) for t in np.split(qkv.v, 3, 0))
        mult, r_shift = K.attention_scale(d, qkv.f, R_EXP)
        assert r_shift >= 0, r_shift
        self.Q[(name, qkv.f)] = {"kind": "attention", "head_dim": d, "heads": n_heads, "tokens": H * W, "f_qkv": qkv.f, "mult": mult, "r_shift": r_shift,
                                 "R_EXP": R_EXP, "EXP_SIZE": EXP_SIZE, "P_EXP": P_EXP}
        out = K.attention_int(q, k, v, r_shift, self.exp_table, mult).reshape(c, H, W)
        return self._r(name, ITensor(out, qkv.f), "inherited")

    # -- score
    @staticmethod
    def score_int(eps: ITensor, noise_int: np.ndarray) -> int:
        assert eps.f == F_EPS
        d = eps.v - noise_int                                        # |d| <= 65535; d^2 <= 65535^2; sum over 43008 < 2^48
        return int((d * d).sum())

    @staticmethod
    def score_scale() -> float:
        """real MSE = score_int / score_scale()."""
        return float(4 * TH * TW) * 2.0 ** (2 * F_EPS)

    # -- bounds and summaries
    def static_bounds(self):
        """Data-independent bounds over the admitted domain, from the frozen constants and traced shapes (Python ints)."""
        conv, gn, att = {}, {}, {}
        for (name, f_in), q in self.Q.items():
            if "wq" in q:
                conv[name] = {"acc_bound": q["accbound"], "acc_bits": q["accbound"].bit_length(), "requant_expr_bound": q["requant_expr_bound"],
                              "requant_bits": q["requant_expr_bound"].bit_length(), "S": q["S"], "M_max": int(q["M"].max()), "bp_absmax": int(np.abs(q["bp"]).max())}
            elif "gamma_q" in q:
                shp = self.shapes[name]; n = (shp[0] // q["g"]) * shp[1] * shp[2]
                gn[name] = K.groupnorm_static_bounds(n, q["f_out"], GN_T, q["eps_int"], int(np.abs(q["gamma_q"]).max()))
                gn[name]["eps_int"] = q["eps_int"]; gn[name]["f_in"] = f_in; gn[name]["f_out"] = q["f_out"]
            elif q.get("kind") == "attention":
                d, P_, mult = q["head_dim"], q["tokens"], q["mult"]
                s_b = d * K.I16_ABS ** 2; z_b = 2 * s_b * mult; den_b = P_ * (1 << P_EXP); num_b = den_b * K.I16_ABS
                att[name] = {"score_bound": s_b, "score_bits": s_b.bit_length(), "scaled_diff_bound": z_b, "scaled_diff_bits": z_b.bit_length(),
                             "den_bound": den_b, "num_bound": num_b, "div_expr_bound": 2 * num_b + den_b, "div_expr_bits": (2 * num_b + den_b).bit_length()}
        sse = 4 * TH * TW * (K.I16_MAX - K.I16_MIN) ** 2
        g = {"conv_acc_bound_max": max(v["acc_bound"] for v in conv.values()), "conv_requant_expr_max": max(v["requant_expr_bound"] for v in conv.values()),
             "gn_n_max": max(v["n"] for v in gn.values()), "gn_N_bits_max": max(v["N_bits"] for v in gn.values()), "gn_X2_bits_max": max(v["X2_bits"] for v in gn.values()),
             "gn_affine_bits_max": max(v["affine_bits"] for v in gn.values()), "gn_S2_bits_max": max(v["S2_bits"] for v in gn.values()),
             "attention_div_expr_bits_max": max(v["div_expr_bits"] for v in att.values()),
             "noising_acc_bound": (self.SA_INT + self.SO_INT) * K.I16_ABS, "add_cat_sum_bound": 2 * K.I16_ABS * (1 << 15),
             "avgpool_sum_bound": 4 * K.I16_ABS, "bilinear_sum_bound": 16 * K.I16_ABS, "sse_bound": sse, "paired_sum_bound": 5 * sse}
        g["all_i64_except_gn_X2"] = all(v < (1 << 63) for kk, v in g.items() if isinstance(v, int) and not kk.endswith("_bits_max") and kk != "gn_X2_bits_max") \
            and g["gn_N_bits_max"] <= 63 and g["gn_affine_bits_max"] <= 63 and g["attention_div_expr_bits_max"] <= 63
        return {"factor": K.I16_ABS, "conv": conv, "groupnorm": gn, "attention": att, "global": g,
                "note": "i64 accumulation suffices everywhere with operands widened before multiplication; u128 is required only for GroupNorm's X^2 // N and its isqrt"}

    def constants_summary(self):
        out = {}
        for key, q in self.Q.items():
            name, f_in = key
            if "wq" in q:
                out[name] = {"kind": "conv", "f_in": f_in, "f_out": q["f_out"], "shift": q["S"], "mult_bits": q["mbits"], "acc_bound_bits": q["accbound"].bit_length(),
                             "M_min": int(q["M"].min()), "M_max": int(q["M"].max()), "qmax": q["qmax"], "weights": int(q["wq"].size), "t_fold": name.endswith(".conv1")}
            elif "gamma_q" in q:
                out[name] = {"kind": "groupnorm", "f_in": f_in, "f_out": q["f_out"], "groups": int(q["g"]), "eps_int": q["eps_int"], "T": GN_T, "gamma_bits": GN_GAMMA_BITS}
            else:
                out[name] = dict(q)
        for (kind, fi, fo), (lut, mask) in self.luts.items():
            out[f"lut:{kind}:{fi}->{fo}"] = {"kind": "lut", "entries": int(lut.size), "clipped_entries": int(mask.sum()),
                                             "table_sha256_int16_le": hashlib.sha256(np.ascontiguousarray(lut.astype("<i2")).tobytes()).hexdigest(),
                                             "mask_sha256_uint8": hashlib.sha256(np.ascontiguousarray(mask.astype(np.uint8)).tobytes()).hexdigest()}
        return out


# ---------------------------------------------------------------- calibration and setup

def default_calib_rows(include_august=True):
    """Every fifth protocol row (indices 0,5,...,30: 7 rows) plus, when present, every 16th held-out August row (7 rows)."""
    rows = eval_rows()[::5]
    if include_august and row_available("august", 600):
        rows += [("august", r) for r in range(600, 712, 16)]
    return rows


def calibrate(P, calib_rows):
    """Run the float64 mirror over the calibration rows (own E and E of row+15 when available) and record max|v| per tensor."""
    rec = {}
    M = import_trainer(); dc = M.build_diffusion_constants(1000, torch.device("cpu"), torch.float32)
    for sid, r in calib_rows:
        noise = protocol_noise(sid, r); Ct = make_Ct(load_C_bf16(sid, r), noise, dc, M)
        Ctn = Ct.float().numpy().reshape(4, TH, TW).astype(np.float64)
        for rr in (r, r + 15):
            if not row_available(sid, rr):
                continue
            E = load_E_bf16(sid, rr).float().numpy().astype(np.float64)
            forward_program(F64Backend(P, rec), Ctn, E)
    return rec


def f_from_maxabs(m):
    if m <= 0:
        return 15
    return int(min(15, max(0, math.floor(math.log2(K.I16_ABS / (HEADROOM * m))))))


def build_ftab(rec):
    ftab = {name: f_from_maxabs(m) for name, m in rec.items()}
    ftab["hint"] = F_HINT
    ftab["out_conv"] = F_EPS
    return ftab


class QuantModel:
    """Quantise once (calibrate, trace, lock the scale map), then run rows."""
    def __init__(self, scheme, calib_rows=None, record_tensors=False, verbose=True):
        t0 = time.time()
        self.model, self.dc, self.M, self.ck = build_model(CKPT)
        self.P = extract_params(self.model)
        self.calib_rows = calib_rows or default_calib_rows()
        self.calib_maxabs = calibrate(self.P, self.calib_rows)
        self.ftab = build_ftab(self.calib_maxabs)
        self.scheme = scheme
        self.B = IntBackend(self.P, self.ftab, scheme, record_tensors=record_tensors)
        self.B.set_noising_constants(self.dc)
        # trace once to record the EXECUTED scale of every tensor, then lock the map
        sid, r = self.calib_rows[0]
        inp = self.B.int_inputs(load_C_bf16(sid, r), protocol_noise(sid, r), load_E_bf16(sid, r))
        forward_program(self.B, inp["Ct"], inp["E"])
        self.scale_map = dict(self.B.eff_f); self.scale_source = dict(self.B.scale_source)
        self.B.scale_map = self.scale_map
        self.B.sat = {k: v for k, v in self.B.sat.items() if k == "input:coord"}   # drop the trace's data-dependent counts
        self.B.bounds_obs = {}
        self.static_bounds = self.B.static_bounds()
        if verbose:
            n_inh = sum(1 for s in self.scale_source.values() if s == "inherited")
            print(f"[{scheme}] calibrated on {len(self.calib_rows)} rows ({sum(1 for s,_ in self.calib_rows if s=='august')} august) in {time.time()-t0:.1f}s; "
                  f"scale map {len(self.scale_map)} tensors ({n_inh} inherited); bounds i64-safe: {self.static_bounds['global']['all_i64_except_gn_X2']}", flush=True)

    def run_int(self, C_bf16, noise_f32, E_bf16):
        inp = self.B.int_inputs(C_bf16, noise_f32, E_bf16)
        return forward_program(self.B, inp["Ct"], inp["E"]), inp

    def run_f64(self, Ct_bf16, E_bf16, record_tensors=False):
        Bf = F64Backend(self.P)
        out = forward_program(Bf, Ct_bf16.float().numpy().reshape(4, TH, TW).astype(np.float64), E_bf16.float().numpy().astype(np.float64))
        return (out, Bf.tensors) if record_tensors else out

    def run_f64_real(self, Ct_real, E_real):
        return forward_program(F64Backend(self.P), Ct_real, E_real)

    def score_int(self, eps, noise_int):
        return self.B.score_int(eps, noise_int)

    def scale_histogram(self):
        from collections import Counter
        return dict(sorted(Counter(self.scale_map.values()).items()))

    def export_vectors(self, outdir, sid, r, rr, noise, tag):
        """Byte-exact test vectors for one (row, conditioning): inputs (incl. the normative integer noise and
        the float32 stream it was rounded from), every layer's int16 output, the residual sum, the full
        constant set, the effective scale map, the rounding rules and the static bounds."""
        outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
        def h16(a):
            return hashlib.sha256(np.ascontiguousarray(a.astype("<i2")).tobytes()).hexdigest()
        def h64(a):
            return hashlib.sha256(np.ascontiguousarray(a.astype("<i8")).tobytes()).hexdigest()
        def hf32(a):
            return hashlib.sha256(np.ascontiguousarray(a.astype("<f4")).tobytes()).hexdigest()
        C = load_C_bf16(sid, r); E = load_E_bf16(sid, rr)
        B = IntBackend(self.P, self.ftab, self.scheme, record_tensors=True); B.set_noising_constants(self.dc)
        B.Q = self.B.Q; B.luts = self.B.luts; B.scale_map = self.scale_map
        inp = B.int_inputs(C, noise, E)
        eps = forward_program(B, inp["Ct"], inp["E"])
        score = B.score_int(eps, inp["noise_int"])
        layers, arrays = {}, {}
        for name, t in B.tensors.items():
            assert K.in_domain(t.v) and t.f == self.scale_map[name]
            layers[name] = {"shape": list(t.shape), "f": t.f, "scale_source": self.scale_source[name], "sha256_int16_le": h16(t.v)}
            arrays["T:" + name] = t.v.astype(np.int16)
        noise_f32 = noise.numpy().reshape(4, TH, TW).astype(np.float32)
        for k in ("C_int", "noise_int", "E_int"):
            arrays["IN:" + k] = inp[k].astype(np.int16)
        arrays["IN:Ct_int"] = inp["Ct"].v.astype(np.int16)
        arrays["IN:coord_int"] = B.hint_coord.astype(np.int16)
        arrays["IN:noise_f32"] = noise_f32
        inputs = {"C_int": {"f": F_CT, "shape": [4, TH, TW], "sha256_int16_le": h16(inp["C_int"])},
                  "noise_int": {"f": F_EPS, "shape": [4, TH, TW], "sha256_int16_le": h16(inp["noise_int"]), "normative": True},
                  "noise_f32": {"shape": [4, TH, TW], "sha256_f32_le": hf32(noise_f32),
                                "note": "emulated CUDA-Philox stream (Philox words exact, float transform approximate); noise_int = rint(noise_f32 * 2^12) is the normative target"},
                  "Ct_int": {"f": F_CT, "shape": [4, TH, TW], "sha256_int16_le": h16(inp["Ct"].v)},
                  "E_int": {"f": F_HINT, "shape": [12, TH, TW], "sha256_int16_le": h16(inp["E_int"])},
                  "coord_int": {"f": F_HINT, "shape": [2, TH, TW], "sha256_int16_le": h16(B.hint_coord)}}
        consts = {}
        for (name, f_in), q in B.Q.items():
            if "wq" in q:
                arrays[f"W:{name}"] = q["wq"].astype(np.int16 if self.qmax_dtype() == np.int16 else np.int8); arrays[f"M:{name}"] = q["M"]; arrays[f"BP:{name}"] = q["bp"]
                consts[name] = {"kind": "conv", "f_in": f_in, "f_out": q["f_out"], "S": q["S"], "stride": q["stride"], "pad": q["pad"], "qmax": q["qmax"],
                                "wq_shape": list(q["wq"].shape), "wq_sha256_int16_le": h16(q["wq"]), "M_sha256_int64_le": h64(q["M"]), "bp_sha256_int64_le": h64(q["bp"])}
            elif "gamma_q" in q:
                arrays[f"GQ:{name}"] = q["gamma_q"]; arrays[f"BQ:{name}"] = q["beta_q"]
                consts[name] = {"kind": "groupnorm", "f_in": f_in, "f_out": q["f_out"], "groups": int(q["g"]), "eps_int": q["eps_int"], "T": GN_T,
                                "gamma_bits": GN_GAMMA_BITS, "gamma_q_sha256_int64_le": h64(q["gamma_q"]), "beta_q_sha256_int64_le": h64(q["beta_q"])}
            else:
                consts[name] = dict(q)
        luts = {}
        def h8(a):
            return hashlib.sha256(np.ascontiguousarray(a.astype(np.uint8)).tobytes()).hexdigest()
        for (kind, fi, fo), (lut, mask) in B.luts.items():
            arrays[f"LUT:{kind}:{fi}:{fo}"] = lut.astype(np.int16)
            arrays[f"LUTMASK:{kind}:{fi}:{fo}"] = mask.astype(np.uint8)          # 1 = entry was clipped to the admitted domain
            luts[f"{kind}:{fi}->{fo}"] = {"entries": 65536, "index": "x_int16 + 32768", "clipped_entries": int(mask.sum()), "sha256_int16_le": h16(lut),
                                          "mask_array": f"LUTMASK:{kind}:{fi}:{fo}", "mask_sha256_uint8": h8(mask),
                                          "hit_rule": "each lookup whose index has mask 1 is one clip event (counter lut_clipped_hit:<layer>)"}
        arrays["EXP_TABLE"] = B.exp_table
        exp_mask = np.zeros(EXP_SIZE, dtype=np.uint8)                          # int64 table, values in [0, 2^P_EXP]: never clamped
        arrays["EXP_TABLE_CLIP_MASK"] = exp_mask
        manifest = {"artifact": "G1 integer execution contract", "scheme": self.scheme, "sid": sid, "row": r, "conditioning_row": rr,
                    "protocol_noise_index": protocol_row_index(sid, r), "noise_convention": "frozen protocol stream" if sid != "august" else "G1 convention: block (600,712), seed 20260823, index r-600",
                    "checkpoint": str(CKPT), "checkpoint_sha256": hashlib.sha256(open(CKPT, "rb").read()).hexdigest(), "env": env_summary(),
                    "fixed_point": {"F_CT": F_CT, "F_HINT": F_HINT, "F_EPS": F_EPS, "GN_T": GN_T, "GN_GAMMA_BITS": GN_GAMMA_BITS, "R_EXP": R_EXP,
                                    "EXP_SIZE": EXP_SIZE, "P_EXP": P_EXP, "NOISE_P": NOISE_P, "HEADROOM": HEADROOM},
                    "rounding": ROUNDING, "domain": DOMAIN, "noising": B.noising,
                    "scale_map": self.scale_map, "scale_source": self.scale_source, "scale_histogram": self.scale_histogram(),
                    "inputs": inputs, "layers": layers, "constants": consts, "luts": luts,
                    "exp_table": {"entries": EXP_SIZE, "value": "rint(exp(-u/2^R_EXP) * 2^P_EXP)", "sha256_int64_le": h64(B.exp_table),
                                  "clipped_entries": 0, "mask_array": "EXP_TABLE_CLIP_MASK", "mask_sha256_uint8": h8(exp_mask),
                                  "note": "int64 table in [0, 2^20]; not an int16 tensor, no clamp applies; index clamp to 32767 is not a clip event"},
                    "residual_sum_int": score, "residual_scale": B.score_scale(), "residual_mse": score / B.score_scale(),
                    "clip_events": dict(B.sat), "static_bounds": self.static_bounds}
        np.savez_compressed(outdir / f"vectors_{self.scheme}_{sid}_{r}_{tag}.npz", **arrays)
        json.dump(manifest, open(outdir / f"vectors_{self.scheme}_{sid}_{r}_{tag}.json", "w"), indent=1)
        return manifest

    def qmax_dtype(self):
        return np.int16 if self.scheme == "int16" else np.int8


# ---------------------------------------------------------------- op count (MACs), attention products included

class CountBackend(F64Backend):
    def __init__(self, P):
        super().__init__(P); self.macs = {}
    def conv(self, name, x):
        y = super().conv(name, x); w = self.P["conv"][name]["w"]
        self.macs[name] = int(np.prod(w.shape) * y.shape[1] * y.shape[2]); return y
    def attention(self, name, qkv, n_heads):
        C3, H, W = qkv.shape; c = C3 // 3; d = c // n_heads; Pn = H * W
        self.macs[name + ".QKt"] = n_heads * d * Pn * Pn; self.macs[name + ".AV"] = n_heads * d * Pn * Pn
        return super().attention(name, qkv, n_heads)


def op_count(P):
    Bc = CountBackend(P)
    forward_program(Bc, np.zeros((4, TH, TW)), np.zeros((12, TH, TW)))
    gn_elems = sum(int(np.prod(t.shape)) for n, t in Bc.tensors.items() if n in P["gn"])
    act_elems = sum(int(np.prod(t.shape)) for n, t in Bc.tensors.items() if n.endswith((".silu1", ".silu2", ".gelu", "out_silu")))
    attn_tokens = {n.replace(".attn", ""): int(np.prod(t.shape[1:])) for n, t in Bc.tensors.items() if n.endswith(".attn")}
    return {"macs": Bc.macs, "total_macs": sum(Bc.macs.values()), "attention_macs": sum(v for k, v in Bc.macs.items() if ".QKt" in k or ".AV" in k),
            "groupnorm_elements": gn_elems, "activation_elements": act_elems, "attention_tokens": attn_tokens}


# ---------------------------------------------------------------- CLI: self checks and artifact export

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", default="int16", choices=["int16", "int8"])
    ap.add_argument("--no-august-calib", action="store_true")
    ap.add_argument("--layer-report", action="store_true", help="per-layer int vs float64 deviation on the first protocol row")
    ap.add_argument("--dump-constants", default="", help="write the constants summary, scale map and bounds to this JSON")
    ap.add_argument("--vectors", default="", help="directory for byte-exact test vectors")
    ap.add_argument("--vector-rows", default="d2:1328", help="comma-separated sid:row list for --vectors (correct and wrong +2 each)")
    a = ap.parse_args()
    torch.set_num_threads(16)
    assert K.selftest(verbose=False), "kernel selftest failed"
    print("kernels selftest PASS")
    qm = QuantModel(a.scheme, calib_rows=default_calib_rows(include_august=not a.no_august_calib), record_tensors=a.layer_report)
    sid, r = eval_rows()[0]
    noise = protocol_noise(sid, r)
    C = load_C_bf16(sid, r); E = load_E_bf16(sid, r)
    Ct = make_Ct(C, noise, qm.dc, qm.M)
    tt = torch.full((1,), T_VAL, dtype=torch.long)
    with torch.no_grad():
        e_torch = qm.model(Ct.float(), E.float().unsqueeze(0), tt)[0].double().numpy()
    e64, tens64 = qm.run_f64(Ct, E, record_tensors=True)
    print(f"float64 mirror vs torch fp32 on {sid} {r}: max|diff| {np.abs(e64 - e_torch).max():.3e} (rel to max|eps| {np.abs(e64 - e_torch).max()/np.abs(e_torch).max():.2e})")
    t0 = time.time(); e_int, inp = qm.run_int(C, noise, E); dti = time.time() - t0
    s_f = float(((torch.from_numpy(e64).float() - noise[0]) ** 2).mean()); s_i = qm.score_int(e_int, inp["noise_int"]) / qm.B.score_scale()
    print(f"[{a.scheme}] integer forward {dti:.1f}s; eps int vs float64 RMS diff {np.sqrt(((e_int.real() - e64)**2).mean()):.3e}; score f64 {s_f:.6f} int {s_i:.6f} rel {s_i/s_f-1:+.3e}; clip events {dict(qm.B.sat)}")
    print(f"  scale histogram {qm.scale_histogram()}; sources {dict(sorted(__import__('collections').Counter(qm.scale_source.values()).items()))}")
    g = qm.static_bounds["global"]
    print(f"  bounds: conv acc max {g['conv_acc_bound_max']} ({g['conv_acc_bound_max'].bit_length()} bits), requant max {g['conv_requant_expr_max']} ({g['conv_requant_expr_max'].bit_length()} bits), "
          f"GN n max {g['gn_n_max']}, N bits {g['gn_N_bits_max']}, X^2 bits {g['gn_X2_bits_max']}, affine bits {g['gn_affine_bits_max']}, attention div bits {g['attention_div_expr_bits_max']}, SSE {g['sse_bound']}")
    oc = op_count(qm.P)
    print(f"  op count: total {oc['total_macs']/1e9:.5f} GMAC (attention QK^T+AV {oc['attention_macs']/1e6:.3f} MMAC, tokens {oc['attention_tokens']}); GN elements {oc['groupnorm_elements']/1e6:.3f}M, act elements {oc['activation_elements']/1e6:.3f}M")
    if a.layer_report:
        print(f"{'tensor':32s} {'f':>2s} {'src':>11s} {'rel RMS dev':>12s} {'maxabs f64':>10s}")
        for name, t in qm.B.tensors.items():
            ref = tens64[name]
            print(f"{name:32s} {t.f:2d} {qm.scale_source[name]:>11s} {np.sqrt(((t.real() - ref) ** 2).mean()) / (np.sqrt((ref ** 2).mean()) + 1e-30):12.3e} {np.abs(ref).max():10.3f}")
    if a.vectors:
        for item in a.vector_rows.split(","):
            vs, vr = item.split(":"); vr = int(vr)
            vnoise = protocol_noise(vs, vr)
            for rr, tag in ((vr, "correct"), (vr + 2, "wrong_p2")):
                if not row_available(vs, rr):
                    continue
                man = qm.export_vectors(a.vectors, vs, vr, rr, vnoise, tag)
                print(f"  vectors {vs} {vr} {tag}: residual_sum_int {man['residual_sum_int']} ({man['residual_mse']:.6f}), clip events {man['clip_events']}")
    if a.dump_constants:
        json.dump({"scheme": a.scheme, "checkpoint": str(CKPT), "checkpoint_sha256": hashlib.sha256(open(CKPT, "rb").read()).hexdigest(), "env": env_summary(),
                   "scale_map": qm.scale_map, "scale_source": qm.scale_source, "scale_histogram": qm.scale_histogram(),
                   "calibration_candidates_ftab": qm.ftab, "calib_maxabs": qm.calib_maxabs, "calib_rows": qm.calib_rows,
                   "rounding": ROUNDING, "domain": DOMAIN, "noising": qm.B.noising, "layers": qm.B.constants_summary(),
                   "static_bounds": qm.static_bounds, "op_count": oc}, open(a.dump_constants, "w"), indent=1)
        print("wrote", a.dump_constants)


if __name__ == "__main__":
    main()
