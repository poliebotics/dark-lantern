//! The ARM-C network program (`int_ref.py: forward_program`, `resblock`, `attn`), parameterised
//! by a [`Constants`] blob: `DiffusionDiagnosticUNet` with hint = cat(E, coord_grid), four
//! levels, two ResBlocks per level, attention at level 3 on the way down, at the first up level
//! and in the middle, hint features bilinear-upsampled x2 and added through 1x1 adapters, average
//! pooling between levels, bilinear x2 and concat on the way up, GroupNorm-SiLU-conv output.
//! Channel counts come from the blob, so a width-12 blob runs through the same code.
//!
//! Scales follow the oracle's *effective* scale map, not the declared `ftab` entry of every name:
//! convolutions, GroupNorms, activations, adds and concats take their output scale from their
//! constants or the `ftab`, while average pooling, bilinear upsampling and the attention core
//! inherit the scale of their input (for the width-16 constants this makes `pool.2`, `pool.3`,
//! `up.0`, `up.1` run at f = 11 where the ftab declares 12, and `down_attns.3.attn`,
//! `mid_attn.attn`, `up_attns.0.attn` at 11 / 12 / 11 where it declares 13 / 13 / 12).
//! Every clipping event is counted (`Net::sat`): clamps in every op and indexed hits on clipped
//! lookup-table entries (the full int16 range is admitted, so integer inputs are in domain by type).
//!
//! Every layer output passes through a [`Hook`], which the parity tests use to compare (and
//! optionally substitute) the oracle's tensor; the guest uses [`NoHook`].

use crate::blob::{Constants, LUT_GELU, LUT_SILU};
use crate::kernels as k;
use crate::tensor::Tensor;
use alloc::format;
use alloc::vec::Vec;

pub trait Hook {
    /// Called with every named layer output; returns the tensor to continue with.
    fn layer(&mut self, name: &str, t: Tensor) -> Tensor;
    /// Called before a kernel of the given kind runs (`conv3x3_s1`, `groupnorm`, ...); a tracing
    /// hook can open a cycle-tracker region here. Default: nothing.
    fn begin(&mut self, _kind: &str) {}
    /// Called after a kernel of the given kind finished. Default: nothing.
    fn end(&mut self, _kind: &str) {}
}

/// Identity hook (the guest).
pub struct NoHook;

impl Hook for NoHook {
    #[inline(always)]
    fn layer(&mut self, _name: &str, t: Tensor) -> Tensor {
        t
    }
}

/// Network state for one forward pass: constants, saturation counter and hook.
pub struct Net<'a, H: Hook> {
    pub k: &'a Constants,
    pub hook: &'a mut H,
    /// Saturation (clamp) events, counted over every op.
    pub sat: u32,
}

impl<'a, H: Hook> Net<'a, H> {
    pub fn new(k: &'a Constants, hook: &'a mut H) -> Self {
        Net { k, hook, sat: 0 }
    }

    fn rec(&mut self, name: &str, t: Tensor) -> Tensor {
        self.hook.layer(name, t)
    }

    /// `hint = cat(E, coord)` at `f_hint`.
    pub fn build_hint(&mut self, e: &Tensor) -> Tensor {
        assert_eq!(e.f, self.k.f_hint, "E fractional bits");
        assert!(e.h == self.k.h && e.w == self.k.w, "E spatial size");
        let mut v = Vec::with_capacity(e.v.len() + self.k.coord.len());
        v.extend_from_slice(&e.v);
        v.extend_from_slice(&self.k.coord);
        let t = Tensor { c: e.c + 2, h: e.h, w: e.w, f: self.k.f_hint, v };
        self.rec("hint", t)
    }

    pub fn conv(&mut self, name: &str, x: &Tensor) -> Tensor {
        let l = self.k.conv(name);
        let kind = if l.kh == 3 && l.stride == 1 {
            "conv3x3_s1"
        } else if l.kh == 3 {
            "conv3x3_s2"
        } else {
            "conv1x1"
        };
        self.hook.begin(kind);
        let t = k::conv2d(x, l, &mut self.sat);
        self.hook.end(kind);
        self.rec(name, t)
    }

    pub fn gn(&mut self, name: &str, x: &Tensor) -> Tensor {
        let l = self.k.gn(name);
        self.hook.begin("groupnorm");
        let t = k::groupnorm(x, l, self.k.gn_t, &mut self.sat);
        self.hook.end("groupnorm");
        self.rec(name, t)
    }

    pub fn act(&mut self, kind: u8, name: &str, x: &Tensor) -> Tensor {
        let f_out = self.k.f_of(name);
        let lut = self.k.lut(kind, x.f, f_out);
        self.hook.begin("lut");
        let t = k::lut_apply(x, &lut.table, &lut.mask, f_out, &mut self.sat);
        self.hook.end("lut");
        self.rec(name, t)
    }

    pub fn add(&mut self, name: &str, a: &Tensor, b: &Tensor) -> Tensor {
        let f_out = self.k.f_of(name);
        self.hook.begin("add");
        let t = k::add(a, b, f_out, &mut self.sat);
        self.hook.end("add");
        self.rec(name, t)
    }

    pub fn cat(&mut self, name: &str, a: &Tensor, b: &Tensor) -> Tensor {
        let f_out = self.k.f_of(name);
        self.hook.begin("cat");
        let t = k::cat(a, b, f_out, &mut self.sat);
        self.hook.end("cat");
        self.rec(name, t)
    }

    pub fn avgpool2(&mut self, name: &str, x: &Tensor) -> Tensor {
        self.hook.begin("avgpool2");
        let t = k::avgpool2(x, &mut self.sat);
        self.hook.end("avgpool2");
        self.rec(name, t)
    }

    pub fn bilinear_up2(&mut self, name: &str, x: &Tensor) -> Tensor {
        self.hook.begin("bilinear_up2");
        let t = k::bilinear_up2(x, &mut self.sat);
        self.hook.end("bilinear_up2");
        self.rec(name, t)
    }

    pub fn attention(&mut self, name: &str, qkv: &Tensor) -> Tensor {
        let l = self.k.attn(name);
        assert_eq!(qkv.f, l.f_qkv, "attention {name}: qkv fractional bits");
        // kernels.attention_scale: head_dim 16 -> (mult 1, shift 2f + 2 - R_EXP); otherwise (rint(2^16/sqrt(d)), 2f + 16 - R_EXP)
        let expect_shift = if l.mult == 1 { 2 * qkv.f + 2 - self.k.r_exp } else { 2 * qkv.f + 16 - self.k.r_exp };
        assert_eq!(l.r_shift, expect_shift, "attention {name}: r_shift");
        self.hook.begin("attention");
        let t = k::attention(qkv, self.k.heads as usize, l.mult, l.r_shift, &self.k.exp_table, &mut self.sat);
        self.hook.end("attention");
        self.rec(name, t)
    }

    /// `ResBlock.forward`: GN-SiLU-conv1 (+ folded t bias), GN-SiLU-conv2, + skip (1x1 conv iff present).
    pub fn resblock(&mut self, name: &str, x: &Tensor) -> Tensor {
        let h = self.gn(&format!("{name}.norm1"), x);
        let h = self.act(LUT_SILU, &format!("{name}.silu1"), &h);
        let h = self.conv(&format!("{name}.conv1"), &h);
        let h = self.gn(&format!("{name}.norm2"), &h);
        let h = self.act(LUT_SILU, &format!("{name}.silu2"), &h);
        let h = self.conv(&format!("{name}.conv2"), &h);
        let skip_name = format!("{name}.skip");
        if self.k.conv_opt(&skip_name).is_some() {
            let sk = self.conv(&skip_name, x);
            self.add(&format!("{name}.res"), &h, &sk)
        } else {
            self.add(&format!("{name}.res"), &h, x)
        }
    }

    /// `Attn.forward`: GN, 1x1 qkv, softmax attention, 1x1 proj, residual.
    pub fn attn_block(&mut self, name: &str, x: &Tensor) -> Tensor {
        let n = self.gn(&format!("{name}.norm"), x);
        let qkv = self.conv(&format!("{name}.qkv"), &n);
        let out = self.attention(&format!("{name}.attn"), &qkv);
        let proj = self.conv(&format!("{name}.proj"), &out);
        self.add(&format!("{name}.res"), x, &proj)
    }

    /// The whole denoiser: `(C_t, E) -> eps` at `f_eps`.
    pub fn forward(&mut self, ct: &Tensor, e: &Tensor) -> Tensor {
        assert_eq!(ct.f, self.k.f_ct, "C_t fractional bits");
        // hint encoder: four strided 3x3 convs, each GN + GELU; the four features are kept
        let hint = self.build_hint(e);
        let mut feats: Vec<Tensor> = Vec::with_capacity(4);
        for s in 0..4 {
            let inp = if s == 0 { &hint } else { &feats[s - 1] };
            let h = self.conv(&format!("hint_encoder.s{s}.0"), inp);
            let h = self.gn(&format!("hint_encoder.s{s}.1"), &h);
            let h = self.act(LUT_GELU, &format!("hint_encoder.s{s}.gelu"), &h);
            feats.push(h);
        }
        // down path
        let mut x = self.conv("in_conv", ct);
        let mut skips: Vec<Tensor> = Vec::with_capacity(4);
        for i in 0..4 {
            for j in 0..2 {
                x = self.resblock(&format!("downs.{i}.{j}"), &x);
            }
            if i == 3 {
                x = self.attn_block("down_attns.3", &x);
            }
            let hi = &feats[i];
            assert!(hi.h * 2 == x.h && hi.w * 2 == x.w, "hint feature {i} size");
            let up = self.bilinear_up2(&format!("hint_up.{i}"), hi);
            let ad = self.conv(&format!("adapters.{i}.conv"), &up);
            let injected = self.add(&format!("inject.{i}"), &x, &ad);
            x = self.avgpool2(&format!("pool.{i}"), &injected);
            skips.push(injected);
        }
        // middle
        x = self.resblock("mid_a", &x);
        x = self.attn_block("mid_attn", &x);
        x = self.resblock("mid_b", &x);
        // up path
        for u in 0..4 {
            let i = 3 - u;
            let skip = &skips[i];
            assert!(skip.h == 2 * x.h && skip.w == 2 * x.w, "skip {i} size");
            let up = self.bilinear_up2(&format!("up.{u}"), &x);
            x = self.cat(&format!("cat.{u}"), &up, skip);
            for j in 0..2 {
                x = self.resblock(&format!("ups.{u}.{j}"), &x);
            }
            if u == 0 {
                x = self.attn_block("up_attns.0", &x);
            }
        }
        let x = self.gn("out_norm", &x);
        let x = self.act(LUT_SILU, "out_silu", &x);
        let eps = self.conv("out_conv", &x);
        assert_eq!(eps.f, self.k.f_eps, "eps fractional bits");
        eps
    }
}

/// Convenience: one evaluation `(C_int, noise_int, E_int) -> (residual sum, saturation count)`
/// with integer forward noising, as the guest runs it.
pub fn evaluate<H: Hook>(k: &Constants, c_int: &[i16], noise_int: &[i16], e_int: &[i16], hook: &mut H) -> (i64, u32) {
    let (h, w) = (k.h, k.w);
    // the C_t clamp is the first counted clipping site (conversion-time input clips are the oracle's)
    let mut sat = 0u32;
    let ct_v = k::noise_ct(c_int, noise_int, k.sa, k.so, k.noise_p, &mut sat);
    let ct = Tensor::new(c_int.len() / (h * w), h, w, k.f_ct, ct_v);
    let e = Tensor::new(e_int.len() / (h * w), h, w, k.f_hint, e_int.to_vec());
    let mut net = Net::new(k, hook);
    let eps = net.forward(&ct, &e);
    let r = k::residual_sum(&eps.v, noise_int);
    (r, sat + net.sat)
}
