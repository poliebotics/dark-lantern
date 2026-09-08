//! The constants blob: everything the integer network needs besides its inputs, in one compact
//! little-endian byte string the guest can parse with core Rust only.
//!
//! Layout (all integers little-endian):
//!
//! ```text
//! magic          b"ARMCINT1"
//! u32            version (1)
//! u32            qmax (32767 for int16 weights, 127 for int8)
//! u32 u32        H, W (input spatial size)
//! u32 x 9        F_CT, F_HINT, F_EPS, NOISE_P, GN_T, GN_GAMMA_BITS, R_EXP, P_EXP, heads
//! i64 i64        SA_INT, SO_INT (forward-noising constants)
//! u32 n          ftab: n x (str name, u32 f)             static per-tensor fractional bits
//! u32 n          convs: n x (str name, u32 out_ch, in_ch, kh, kw, stride, pad, f_in, f_out, shift,
//!                          i16[out*in*kh*kw] Wq, i64[out] M, i64[out] b')
//! u32 n          groupnorms: n x (str name, u32 channels, groups, f_in, f_out, i64 eps_int,
//!                          i64[channels] gamma_q, i64[channels] beta_q)
//! u32 n          attentions: n x (str name, u32 f_qkv, r_shift, tokens, mult)
//! u32 n          luts: n x (u8 kind (0 silu, 1 gelu), u32 f_in, f_out, i16[65536] table, u8[8192] clip mask (bitset, LSB first))
//! u32 n          exp table: n x u32
//! i16[2*H*W]     coordinate planes (channel 0 = x, channel 1 = y) at F_HINT
//! ```
//!
//! `str` is `u16 length` + UTF-8 bytes. The parser copies arrays into owned vectors (so alignment
//! never matters), runs the static bound checks of the oracle on every convolution layer, and
//! validates representability: every fractional-bit field (`F_CT`, `F_HINT`, `F_EPS`, ftab entries,
//! conv / GroupNorm `f_in`, `f_out`, attention `f_qkv`) must lie in the contract's range `0..=15`
//! (`f = clip(..., 0, 15)`, README_FINAL.md section 3), so no left shift in `add`/`cat` exceeds 15
//! bits on int16 operands (Astra r4 item 6). Version 2 adds the clipping mask per lookup table.
//! The full int16 domain is admitted (G1 FINAL), so no table entry or coordinate value is rejected
//! for being `-32768`.

use crate::kernels::{AttnLayer, ConvLayer, GnLayer};
use alloc::string::String;
use alloc::vec::Vec;

pub const MAGIC: &[u8; 8] = b"ARMCINT1";
/// Version 2: clipping mask per lookup table (Astra r4 item 2). Version-1 blobs are rejected.
pub const VERSION: u32 = 2;
/// The contract's range of fractional bits for every tensor scale.
pub const MAX_FRACTIONAL_BITS: u32 = 15;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Lut {
    /// 0 = SiLU, 1 = GELU.
    pub kind: u8,
    pub f_in: u32,
    pub f_out: u32,
    pub table: Vec<i16>,
    /// 65536-bit clipping mask (LSB first): entry `i` was clipped to the admitted domain when the
    /// table was built; indexed hits count as clipping events (`kernels::lut_apply`).
    pub mask: Vec<u8>,
}

pub const LUT_SILU: u8 = 0;
pub const LUT_GELU: u8 = 1;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Constants {
    pub qmax: u32,
    pub h: usize,
    pub w: usize,
    pub f_ct: u32,
    pub f_hint: u32,
    pub f_eps: u32,
    pub noise_p: u32,
    pub gn_t: u32,
    pub gn_gamma_bits: u32,
    pub r_exp: u32,
    pub p_exp: u32,
    pub heads: u32,
    pub sa: i64,
    pub so: i64,
    pub ftab: Vec<(String, u32)>,
    pub convs: Vec<ConvLayer>,
    pub gns: Vec<GnLayer>,
    pub attns: Vec<AttnLayer>,
    pub luts: Vec<Lut>,
    pub exp_table: Vec<u32>,
    /// `(2, H, W)` coordinate planes at `f_hint`.
    pub coord: Vec<i16>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BlobError {
    Truncated,
    BadMagic,
    BadVersion,
    BadString,
    BadSize(&'static str),
    Bound(&'static str),
}

impl core::fmt::Display for BlobError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            BlobError::Truncated => write!(f, "blob truncated"),
            BlobError::BadMagic => write!(f, "blob magic mismatch"),
            BlobError::BadVersion => write!(f, "blob version mismatch"),
            BlobError::BadString => write!(f, "blob string not utf-8"),
            BlobError::BadSize(what) => write!(f, "blob size field out of range: {what}"),
            BlobError::Bound(what) => write!(f, "blob static bound violated: {what}"),
        }
    }
}

struct Reader<'a> {
    b: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    fn take(&mut self, n: usize) -> Result<&'a [u8], BlobError> {
        if self.pos + n > self.b.len() {
            return Err(BlobError::Truncated);
        }
        let s = &self.b[self.pos..self.pos + n];
        self.pos += n;
        Ok(s)
    }
    fn u8(&mut self) -> Result<u8, BlobError> {
        Ok(self.take(1)?[0])
    }
    fn u16(&mut self) -> Result<u16, BlobError> {
        let s = self.take(2)?;
        Ok(u16::from_le_bytes([s[0], s[1]]))
    }
    fn u32(&mut self) -> Result<u32, BlobError> {
        let s = self.take(4)?;
        Ok(u32::from_le_bytes([s[0], s[1], s[2], s[3]]))
    }
    fn i64(&mut self) -> Result<i64, BlobError> {
        let s = self.take(8)?;
        Ok(i64::from_le_bytes([s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]]))
    }
    fn usize_field(&mut self, what: &'static str, max: usize) -> Result<usize, BlobError> {
        let v = self.u32()? as usize;
        if v > max {
            return Err(BlobError::BadSize(what));
        }
        Ok(v)
    }
    fn string(&mut self) -> Result<String, BlobError> {
        let n = self.u16()? as usize;
        let s = self.take(n)?;
        core::str::from_utf8(s).map(String::from).map_err(|_| BlobError::BadString)
    }
    fn i16_vec(&mut self, n: usize) -> Result<Vec<i16>, BlobError> {
        let s = self.take(2 * n)?;
        Ok(s.chunks_exact(2).map(|c| i16::from_le_bytes([c[0], c[1]])).collect())
    }
    fn i64_vec(&mut self, n: usize) -> Result<Vec<i64>, BlobError> {
        let s = self.take(8 * n)?;
        Ok(s.chunks_exact(8).map(|c| i64::from_le_bytes([c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]])).collect())
    }
    fn u32_vec(&mut self, n: usize) -> Result<Vec<u32>, BlobError> {
        let s = self.take(4 * n)?;
        Ok(s.chunks_exact(4).map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect())
    }
}

/// Upper bounds on the size fields, so a corrupt blob fails fast instead of allocating.
const MAX_LAYERS: usize = 4096;
const MAX_CHANNELS: usize = 1 << 16;
const MAX_SPATIAL: usize = 1 << 14;
const MAX_KERNEL: usize = 16;

impl Constants {
    pub fn parse(bytes: &[u8]) -> Result<Constants, BlobError> {
        let mut r = Reader { b: bytes, pos: 0 };
        if r.take(8)? != MAGIC {
            return Err(BlobError::BadMagic);
        }
        if r.u32()? != VERSION {
            return Err(BlobError::BadVersion);
        }
        let qmax = r.u32()?;
        if qmax != 32767 && qmax != 127 {
            return Err(BlobError::BadSize("qmax"));
        }
        let h = r.usize_field("H", MAX_SPATIAL)?;
        let w = r.usize_field("W", MAX_SPATIAL)?;
        let f_ct = r.u32()?;
        let f_hint = r.u32()?;
        let f_eps = r.u32()?;
        let noise_p = r.u32()?;
        let gn_t = r.u32()?;
        let gn_gamma_bits = r.u32()?;
        let r_exp = r.u32()?;
        let p_exp = r.u32()?;
        let heads = r.u32()?;
        for (v, what) in [(f_ct, "F_CT"), (f_hint, "F_HINT"), (f_eps, "F_EPS")] {
            if v > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound(what));
            }
        }
        for (v, what) in [(noise_p, "NOISE_P"), (gn_t, "GN_T"), (gn_gamma_bits, "GN_GAMMA_BITS"), (r_exp, "R_EXP"), (p_exp, "P_EXP")] {
            if v == 0 || v > 62 {
                return Err(BlobError::BadSize(what));
            }
        }
        if heads == 0 || heads > 64 {
            return Err(BlobError::BadSize("heads"));
        }
        let sa = r.i64()?;
        let so = r.i64()?;

        let n = r.usize_field("ftab", MAX_LAYERS)?;
        let mut ftab = Vec::with_capacity(n);
        for _ in 0..n {
            let name = r.string()?;
            let f = r.u32()?;
            if f > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound("ftab f"));
            }
            ftab.push((name, f));
        }

        let n = r.usize_field("convs", MAX_LAYERS)?;
        let mut convs = Vec::with_capacity(n);
        for _ in 0..n {
            let name = r.string()?;
            let out_ch = r.usize_field("out_ch", MAX_CHANNELS)?;
            let in_ch = r.usize_field("in_ch", MAX_CHANNELS)?;
            let kh = r.usize_field("kh", MAX_KERNEL)?;
            let kw = r.usize_field("kw", MAX_KERNEL)?;
            let stride = r.usize_field("stride", MAX_KERNEL)?;
            let pad = r.usize_field("pad", MAX_KERNEL)?;
            let f_in = r.u32()?;
            let f_out = r.u32()?;
            let shift = r.u32()?;
            if stride == 0 || kh == 0 || kw == 0 {
                return Err(BlobError::BadSize("conv geometry"));
            }
            if f_in > MAX_FRACTIONAL_BITS || f_out > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound("conv fractional bits"));
            }
            let wn = out_ch * in_ch * kh * kw;
            let wq = r.i16_vec(wn)?;
            if wq.iter().any(|&v| (v as i64).abs() > qmax as i64) {
                return Err(BlobError::Bound("weight outside qmax"));
            }
            let m = r.i64_vec(out_ch)?;
            let bp = r.i64_vec(out_ch)?;
            let mut layer = ConvLayer { name, out_ch, in_ch, kh, kw, stride, pad, f_in, f_out, shift, w: wq, m, bp, acc_bound: 0 };
            layer.finalize().map_err(BlobError::Bound)?;
            convs.push(layer);
        }

        let n = r.usize_field("gns", MAX_LAYERS)?;
        let mut gns = Vec::with_capacity(n);
        for _ in 0..n {
            let name = r.string()?;
            let channels = r.usize_field("channels", MAX_CHANNELS)?;
            let groups = r.usize_field("groups", MAX_CHANNELS)?;
            let f_in = r.u32()?;
            let f_out = r.u32()?;
            let eps_int = r.i64()?;
            if groups == 0 || channels % groups != 0 || eps_int <= 0 {
                return Err(BlobError::BadSize("groupnorm geometry"));
            }
            if f_in > MAX_FRACTIONAL_BITS || f_out > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound("groupnorm fractional bits"));
            }
            let gamma_q = r.i64_vec(channels)?;
            let beta_q = r.i64_vec(channels)?;
            gns.push(GnLayer { name, channels, groups, eps_int, f_in, f_out, gamma_q, beta_q });
        }

        let n = r.usize_field("attns", MAX_LAYERS)?;
        let mut attns = Vec::with_capacity(n);
        for _ in 0..n {
            let name = r.string()?;
            let f_qkv = r.u32()?;
            let r_shift = r.u32()?;
            let tokens = r.usize_field("tokens", MAX_SPATIAL * MAX_SPATIAL)?;
            let mult = r.u32()? as i64;
            if r_shift > 62 || mult == 0 || mult > (1 << 16) {
                return Err(BlobError::BadSize("attention shifts"));
            }
            if f_qkv > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound("attention fractional bits"));
            }
            attns.push(AttnLayer { name, f_qkv, mult, r_shift, tokens });
        }

        let n = r.usize_field("luts", 64)?;
        let mut luts = Vec::with_capacity(n);
        for _ in 0..n {
            let kind = r.u8()?;
            let f_in = r.u32()?;
            let f_out = r.u32()?;
            if kind > 1 {
                return Err(BlobError::BadSize("lut header"));
            }
            if f_in > MAX_FRACTIONAL_BITS || f_out > MAX_FRACTIONAL_BITS {
                return Err(BlobError::Bound("lut fractional bits"));
            }
            let table = r.i16_vec(65536)?;
            let mask = r.take(crate::kernels::LUT_MASK_BYTES)?.to_vec();
            // a masked entry is one that was clipped, so it must sit at a domain endpoint
            for i in 0..65536 {
                if crate::kernels::lut_mask_bit(&mask, i) && table[i] != i16::MIN && table[i] != i16::MAX {
                    return Err(BlobError::Bound("lut mask marks an entry that is not at a domain endpoint"));
                }
            }
            luts.push(Lut { kind, f_in, f_out, table, mask });
        }

        let n = r.usize_field("exp table", 1 << 20)?;
        let exp_table = r.u32_vec(n)?;

        let coord = r.i16_vec(2 * h * w)?;
        if r.pos != bytes.len() {
            return Err(BlobError::BadSize("trailing bytes"));
        }
        Ok(Constants { qmax, h, w, f_ct, f_hint, f_eps, noise_p, gn_t, gn_gamma_bits, r_exp, p_exp, heads, sa, so, ftab, convs, gns, attns, luts, exp_table, coord })
    }

    /// Serialise (the inverse of [`Constants::parse`]).
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut b: Vec<u8> = Vec::new();
        fn s(b: &mut Vec<u8>, st: &str) {
            let bytes = st.as_bytes();
            assert!(bytes.len() <= u16::MAX as usize);
            b.extend_from_slice(&(bytes.len() as u16).to_le_bytes());
            b.extend_from_slice(bytes);
        }
        fn u32s(b: &mut Vec<u8>, v: u32) {
            b.extend_from_slice(&v.to_le_bytes());
        }
        fn i64s(b: &mut Vec<u8>, v: i64) {
            b.extend_from_slice(&v.to_le_bytes());
        }
        b.extend_from_slice(MAGIC);
        u32s(&mut b, VERSION);
        u32s(&mut b, self.qmax);
        u32s(&mut b, self.h as u32);
        u32s(&mut b, self.w as u32);
        for v in [self.f_ct, self.f_hint, self.f_eps, self.noise_p, self.gn_t, self.gn_gamma_bits, self.r_exp, self.p_exp, self.heads] {
            u32s(&mut b, v);
        }
        i64s(&mut b, self.sa);
        i64s(&mut b, self.so);
        u32s(&mut b, self.ftab.len() as u32);
        for (name, f) in &self.ftab {
            s(&mut b, name);
            u32s(&mut b, *f);
        }
        u32s(&mut b, self.convs.len() as u32);
        for l in &self.convs {
            s(&mut b, &l.name);
            for v in [l.out_ch, l.in_ch, l.kh, l.kw, l.stride, l.pad] {
                u32s(&mut b, v as u32);
            }
            for v in [l.f_in, l.f_out, l.shift] {
                u32s(&mut b, v);
            }
            for &w in &l.w {
                b.extend_from_slice(&w.to_le_bytes());
            }
            for &m in &l.m {
                i64s(&mut b, m);
            }
            for &bp in &l.bp {
                i64s(&mut b, bp);
            }
        }
        u32s(&mut b, self.gns.len() as u32);
        for l in &self.gns {
            s(&mut b, &l.name);
            u32s(&mut b, l.channels as u32);
            u32s(&mut b, l.groups as u32);
            u32s(&mut b, l.f_in);
            u32s(&mut b, l.f_out);
            i64s(&mut b, l.eps_int);
            for &g in &l.gamma_q {
                i64s(&mut b, g);
            }
            for &bq in &l.beta_q {
                i64s(&mut b, bq);
            }
        }
        u32s(&mut b, self.attns.len() as u32);
        for l in &self.attns {
            s(&mut b, &l.name);
            u32s(&mut b, l.f_qkv);
            u32s(&mut b, l.r_shift);
            u32s(&mut b, l.tokens as u32);
            u32s(&mut b, l.mult as u32);
        }
        u32s(&mut b, self.luts.len() as u32);
        for l in &self.luts {
            assert_eq!(l.table.len(), 65536);
            b.push(l.kind);
            u32s(&mut b, l.f_in);
            u32s(&mut b, l.f_out);
            for &t in &l.table {
                b.extend_from_slice(&t.to_le_bytes());
            }
            assert_eq!(l.mask.len(), crate::kernels::LUT_MASK_BYTES);
            b.extend_from_slice(&l.mask);
        }
        u32s(&mut b, self.exp_table.len() as u32);
        for &e in &self.exp_table {
            u32s(&mut b, e);
        }
        assert_eq!(self.coord.len(), 2 * self.h * self.w);
        for &c in &self.coord {
            b.extend_from_slice(&c.to_le_bytes());
        }
        b
    }

    // ---- lookups used by the network program (linear scans over a few hundred names)

    pub fn f_of(&self, name: &str) -> u32 {
        match self.ftab.iter().find(|(n, _)| n == name) {
            Some((_, f)) => *f,
            None => panic!("ftab has no entry for {name}"),
        }
    }

    pub fn conv_opt(&self, name: &str) -> Option<&ConvLayer> {
        self.convs.iter().find(|l| l.name == name)
    }

    pub fn conv(&self, name: &str) -> &ConvLayer {
        match self.conv_opt(name) {
            Some(l) => l,
            None => panic!("no conv layer {name}"),
        }
    }

    pub fn gn(&self, name: &str) -> &GnLayer {
        match self.gns.iter().find(|l| l.name == name) {
            Some(l) => l,
            None => panic!("no groupnorm layer {name}"),
        }
    }

    pub fn attn(&self, name: &str) -> &AttnLayer {
        match self.attns.iter().find(|l| l.name == name) {
            Some(l) => l,
            None => panic!("no attention layer {name}"),
        }
    }

    pub fn lut(&self, kind: u8, f_in: u32, f_out: u32) -> &Lut {
        match self.luts.iter().find(|l| l.kind == kind && l.f_in == f_in && l.f_out == f_out) {
            Some(l) => l,
            None => panic!("no lut kind {kind} {f_in}->{f_out}"),
        }
    }
}
