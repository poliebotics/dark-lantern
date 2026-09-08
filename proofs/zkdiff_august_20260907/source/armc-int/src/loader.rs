//! Host-side (std) loader for the G1 oracle export written by `g2_guest/tools/export_oracle.py`:
//! `<dir>/index.json` (the G1 manifest verbatim under `manifest`, plus an `arrays` table) and one
//! raw little-endian `.bin` per array. Builds a [`Constants`] blob and an [`OracleSet`] (inputs,
//! all layer outputs, residual sum) from it. Reads both the superseded step-12000 manifests (`ftab`,
//! int16-only arrays) and the FINAL manifests (`scale_map`, native int8 weights, float32 noise
//! records, attention entries without `f_in`); the per-table clipping masks are the exporter's
//! `MASK:<kind>:<f_in>:<f_out>` bitsets (8192 bytes, LSB first), computed with the oracle's
//! `make_act_lut_with_mask` and hash-listed in `arrays`.

use crate::blob::{Constants, Lut, LUT_GELU, LUT_SILU};
use crate::kernels::{AttnLayer, ConvLayer, GnLayer};
use crate::tensor::Tensor;
use serde::Deserialize;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

#[derive(Deserialize, Debug, Clone)]
pub struct ArrayEntry {
    pub dtype: String,
    pub shape: Vec<usize>,
    pub file: String,
    pub sha256: String,
    /// For native int8 weight arrays: the hash of the int16-widened bytes, the form the manifest records.
    #[serde(default)]
    pub sha256_int16_le: Option<String>,
    #[serde(default)]
    pub popcount: Option<u64>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct LayerEntry {
    pub shape: Vec<usize>,
    pub f: u32,
    pub sha256_int16_le: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct InputEntry {
    #[serde(default)]
    pub f: Option<u32>,
    pub shape: Vec<usize>,
    /// Absent for the FINAL manifests' float32 noise record (`sha256_f32_le` instead).
    #[serde(default)]
    pub sha256_int16_le: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct ConstEntry {
    pub kind: String,
    /// Absent on the FINAL manifests' attention entries (they carry `f_qkv`).
    #[serde(default)]
    pub f_in: Option<u32>,
    #[serde(default)]
    pub f_out: Option<u32>,
    #[serde(rename = "S", default)]
    pub shift: Option<u32>,
    #[serde(default)]
    pub stride: Option<usize>,
    #[serde(default)]
    pub pad: Option<usize>,
    #[serde(default)]
    pub wq_shape: Option<Vec<usize>>,
    #[serde(default)]
    pub groups: Option<usize>,
    #[serde(default)]
    pub eps_int: Option<i64>,
    #[serde(rename = "T", default)]
    pub t: Option<u32>,
    #[serde(default)]
    pub gamma_bits: Option<u32>,
    #[serde(default)]
    pub r_shift: Option<u32>,
    #[serde(default)]
    pub f_qkv: Option<u32>,
    #[serde(default)]
    pub tokens: Option<usize>,
    #[serde(default)]
    pub heads: Option<u32>,
    #[serde(default)]
    pub mult: Option<i64>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct LutEntry {
    pub entries: usize,
    pub sha256_int16_le: String,
    /// FINAL manifests: number of table entries clipped to the domain, and the artifact's mask array/hash.
    #[serde(default)]
    pub clipped_entries: Option<usize>,
    #[serde(default)]
    pub mask_array: Option<String>,
    #[serde(default)]
    pub mask_sha256_uint8: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct ExpEntry {
    pub entries: usize,
    pub sha256_int64_le: String,
}

#[derive(Deserialize, Debug, Clone)]
pub struct FixedPoint {
    #[serde(rename = "F_CT")]
    pub f_ct: u32,
    #[serde(rename = "F_HINT")]
    pub f_hint: u32,
    #[serde(rename = "F_EPS")]
    pub f_eps: u32,
    #[serde(rename = "GN_T")]
    pub gn_t: u32,
    #[serde(rename = "GN_GAMMA_BITS")]
    pub gn_gamma_bits: u32,
    #[serde(rename = "R_EXP")]
    pub r_exp: u32,
    #[serde(rename = "EXP_SIZE")]
    pub exp_size: usize,
    #[serde(rename = "P_EXP")]
    pub p_exp: u32,
    #[serde(rename = "NOISE_P")]
    pub noise_p: u32,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Noising {
    #[serde(rename = "SA_INT")]
    pub sa_int: i64,
    #[serde(rename = "SO_INT")]
    pub so_int: i64,
    #[serde(rename = "P")]
    pub p: u32,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Manifest {
    pub scheme: String,
    pub sid: String,
    pub row: u64,
    pub conditioning_row: u64,
    pub checkpoint_sha256: String,
    pub fixed_point: FixedPoint,
    pub noising: Noising,
    /// The per-tensor scale table: `scale_map` (FINAL, the one effective map) or `ftab` (the
    /// superseded artifact's declared table). Insertion order is not relied on.
    #[serde(alias = "scale_map")]
    pub ftab: BTreeMap<String, u32>,
    pub inputs: BTreeMap<String, InputEntry>,
    pub layers: BTreeMap<String, LayerEntry>,
    pub constants: BTreeMap<String, ConstEntry>,
    pub luts: BTreeMap<String, LutEntry>,
    pub exp_table: ExpEntry,
    pub residual_sum_int: i64,
    /// FINAL manifests: how each tensor's scale was fixed (`fixed`, `calibration`, `inherited`).
    #[serde(default)]
    pub scale_source: BTreeMap<String, String>,
    /// Clip events the oracle counted for this evaluation, by site name (empty for every FINAL set).
    #[serde(default)]
    pub clip_events: BTreeMap<String, u64>,
    /// FINAL manifests: the static bounds table (`global`, `conv`, `groupnorm`, `attention`).
    #[serde(default)]
    pub static_bounds: BTreeMap<String, serde_json::Value>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct Index {
    pub manifest: Manifest,
    pub arrays: BTreeMap<String, ArrayEntry>,
}

/// The oracle's byte-exact record of one (row, conditioning) evaluation.
pub struct OracleSet {
    pub dir: PathBuf,
    pub index: Index,
    pub c_int: Vec<i16>,
    pub noise_int: Vec<i16>,
    pub ct_int: Vec<i16>,
    pub e_int: Vec<i16>,
    /// Every layer output by name, with its fractional bits.
    pub layers: BTreeMap<String, Tensor>,
    pub residual_sum_int: i64,
}

fn read_i16(path: &Path) -> Vec<i16> {
    let b = std::fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    assert!(b.len() % 2 == 0, "{}: odd length", path.display());
    b.chunks_exact(2).map(|c| i16::from_le_bytes([c[0], c[1]])).collect()
}

fn read_i8_as_i16(path: &Path) -> Vec<i16> {
    let b = std::fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    b.iter().map(|&x| (x as i8) as i16).collect()
}

fn read_u8(path: &Path) -> Vec<u8> {
    std::fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()))
}

fn read_i64(path: &Path) -> Vec<i64> {
    let b = std::fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    assert!(b.len() % 8 == 0, "{}: length not a multiple of 8", path.display());
    b.chunks_exact(8).map(|c| i64::from_le_bytes([c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]])).collect()
}

impl Index {
    pub fn load(dir: &Path) -> Index {
        let p = dir.join("index.json");
        let s = std::fs::read_to_string(&p).unwrap_or_else(|e| panic!("read {}: {e}", p.display()));
        serde_json::from_str(&s).unwrap_or_else(|e| panic!("parse {}: {e}", p.display()))
    }

    fn entry(&self, name: &str) -> &ArrayEntry {
        self.arrays.get(name).unwrap_or_else(|| panic!("oracle export has no array {name}"))
    }

    /// An int16 array, or a native int8 array widened to int16 (values unchanged).
    pub fn i16(&self, dir: &Path, name: &str) -> (Vec<i16>, Vec<usize>) {
        let e = self.entry(name);
        let v = match e.dtype.as_str() {
            "i16" => read_i16(&dir.join(&e.file)),
            "i8" => read_i8_as_i16(&dir.join(&e.file)),
            other => panic!("{name}: dtype {other} is not an integer activation/weight array"),
        };
        assert_eq!(v.len(), e.shape.iter().product::<usize>(), "{name}: size");
        (v, e.shape.clone())
    }

    /// A byte array (the lookup-table clipping masks).
    pub fn u8(&self, dir: &Path, name: &str) -> Vec<u8> {
        let e = self.entry(name);
        assert_eq!(e.dtype, "u8", "{name}: dtype");
        let v = read_u8(&dir.join(&e.file));
        assert_eq!(v.len(), e.shape.iter().product::<usize>(), "{name}: size");
        v
    }

    pub fn i64(&self, dir: &Path, name: &str) -> (Vec<i64>, Vec<usize>) {
        let e = self.entry(name);
        assert_eq!(e.dtype, "i64", "{name}: dtype");
        let v = read_i64(&dir.join(&e.file));
        assert_eq!(v.len(), e.shape.iter().product::<usize>(), "{name}: size");
        (v, e.shape.clone())
    }
}

/// Build the constants blob from one oracle export directory (constants are identical between
/// the `correct` and `wrong_p2` sets of a scheme; the caller picks one).
pub fn load_constants(dir: &Path) -> Constants {
    let idx = Index::load(dir);
    let m = &idx.manifest;
    let qmax = match m.scheme.as_str() {
        "int16" => 32767,
        "int8" => 127,
        other => panic!("unknown scheme {other}"),
    };
    let c_shape = &m.inputs["C_int"].shape;
    assert_eq!(c_shape.len(), 3);
    let (h, w) = (c_shape[1], c_shape[2]);
    let fp = &m.fixed_point;
    assert_eq!(m.noising.p, fp.noise_p);

    // ftab in the manifest's order is lost through BTreeMap; order does not matter for lookups
    let ftab: Vec<(String, u32)> = m.ftab.iter().map(|(k, v)| (k.clone(), *v)).collect();

    let mut convs = Vec::new();
    let mut gns = Vec::new();
    let mut attns = Vec::new();
    let mut heads: Option<u32> = None;
    for (name, ce) in &m.constants {
        match ce.kind.as_str() {
            "conv" => {
                let shape = ce.wq_shape.clone().expect("wq_shape");
                assert_eq!(shape.len(), 4);
                let (wq, ws) = idx.i16(dir, &format!("W:{name}"));
                assert_eq!(ws, shape);
                let (mm, _) = idx.i64(dir, &format!("M:{name}"));
                let (bp, _) = idx.i64(dir, &format!("BP:{name}"));
                let mut l = ConvLayer {
                    name: name.clone(),
                    out_ch: shape[0],
                    in_ch: shape[1],
                    kh: shape[2],
                    kw: shape[3],
                    stride: ce.stride.expect("stride"),
                    pad: ce.pad.expect("pad"),
                    f_in: ce.f_in.expect("conv f_in"),
                    f_out: ce.f_out.expect("f_out"),
                    shift: ce.shift.expect("S"),
                    w: wq,
                    m: mm,
                    bp,
                    acc_bound: 0,
                };
                l.finalize().unwrap_or_else(|e| panic!("conv {name}: {e}"));
                convs.push(l);
            }
            "groupnorm" => {
                let (gq, gs) = idx.i64(dir, &format!("GQ:{name}"));
                let (bq, _) = idx.i64(dir, &format!("BQ:{name}"));
                assert_eq!(ce.t, Some(fp.gn_t), "{name}: T");
                assert_eq!(ce.gamma_bits, Some(fp.gn_gamma_bits), "{name}: gamma bits");
                gns.push(GnLayer {
                    name: name.clone(),
                    channels: gs[0],
                    groups: ce.groups.expect("groups"),
                    eps_int: ce.eps_int.expect("eps_int"),
                    f_in: ce.f_in.expect("groupnorm f_in"),
                    f_out: ce.f_out.expect("f_out"),
                    gamma_q: gq,
                    beta_q: bq,
                });
            }
            "attention" => {
                if let Some(h) = ce.heads {
                    assert!(heads.is_none() || heads == Some(h), "attention head counts differ between layers");
                    heads = Some(h);
                }
                attns.push(AttnLayer {
                    name: name.clone(),
                    f_qkv: ce.f_qkv.expect("f_qkv"),
                    mult: ce.mult.unwrap_or(1),
                    r_shift: ce.r_shift.expect("r_shift"),
                    tokens: ce.tokens.expect("tokens"),
                });
            }
            other => panic!("{name}: unknown constant kind {other}"),
        }
    }

    let mut luts = Vec::new();
    for key in m.luts.keys() {
        // "silu:11->12"
        let (kind_s, rest) = key.split_once(':').expect("lut key");
        let (fi, fo) = rest.split_once("->").expect("lut key arrow");
        let kind = match kind_s {
            "silu" => LUT_SILU,
            "gelu" => LUT_GELU,
            other => panic!("lut kind {other}"),
        };
        let (f_in, f_out): (u32, u32) = (fi.parse().unwrap(), fo.parse().unwrap());
        let (table, _) = idx.i16(dir, &format!("LUT:{kind_s}:{f_in}:{f_out}"));
        assert_eq!(table.len(), 65536);
        let mask = idx.u8(dir, &format!("MASK:{kind_s}:{f_in}:{f_out}"));
        assert_eq!(mask.len(), crate::kernels::LUT_MASK_BYTES, "lut mask bytes");
        luts.push(Lut { kind, f_in, f_out, table, mask });
    }

    let (exp64, _) = idx.i64(dir, "EXP_TABLE");
    assert_eq!(exp64.len(), fp.exp_size);
    let exp_table: Vec<u32> = exp64.iter().map(|&v| u32::try_from(v).expect("exp table entry fits u32")).collect();

    let (coord, cs) = idx.i16(dir, "IN:coord_int");
    assert_eq!(cs, vec![2, h, w]);

    Constants {
        qmax,
        h,
        w,
        f_ct: fp.f_ct,
        f_hint: fp.f_hint,
        f_eps: fp.f_eps,
        noise_p: fp.noise_p,
        gn_t: fp.gn_t,
        gn_gamma_bits: fp.gn_gamma_bits,
        r_exp: fp.r_exp,
        p_exp: fp.p_exp,
        heads: heads.unwrap_or(4),
        sa: m.noising.sa_int,
        so: m.noising.so_int,
        ftab,
        convs,
        gns,
        attns,
        luts,
        exp_table,
        coord,
    }
}

/// Load inputs and every layer output of one export directory.
pub fn load_oracle(dir: &Path) -> OracleSet {
    let idx = Index::load(dir);
    let (c_int, _) = idx.i16(dir, "IN:C_int");
    let (noise_int, _) = idx.i16(dir, "IN:noise_int");
    let (ct_int, _) = idx.i16(dir, "IN:Ct_int");
    let (e_int, _) = idx.i16(dir, "IN:E_int");
    let mut layers = BTreeMap::new();
    for (name, le) in &idx.manifest.layers {
        let (v, shape) = idx.i16(dir, &format!("T:{name}"));
        assert_eq!(shape, le.shape, "{name}: shape");
        assert_eq!(shape.len(), 3);
        layers.insert(name.clone(), Tensor { c: shape[0], h: shape[1], w: shape[2], f: le.f, v });
    }
    let residual_sum_int = idx.manifest.residual_sum_int;
    OracleSet { dir: dir.to_path_buf(), index: idx, c_int, noise_int, ct_int, e_int, layers, residual_sum_int }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let d = Sha256::digest(bytes);
    let mut s = String::with_capacity(64);
    for b in d {
        s.push_str(&format!("{b:02x}"));
    }
    s
}

pub fn i16_le_bytes(v: &[i16]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len() * 2);
    for &x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
    out
}

pub fn i64_le_bytes(v: &[i64]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len() * 8);
    for &x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
    out
}
