//! The two-row statement: private witness layout, leg order, public output layout, and `evaluate`, which both the
//! SP1 guest and the host oracle call so that a native/zkVM divergence is detectable (the b3xof `evaluate` pattern).
//!
//! Private witness (ten `read_vec` items, in this order):
//! ```text
//!  1 header_r     ZBROWW01, 120 B   row r, S_r, meta_r, round_r, value_r
//!  2 membership   ZBOSM001          session context, committed root, siblings of row r
//!  3 raw_r        24,472,000 B      the complete raw Bayer frame of row r
//!  4 sig_r        48 B              quicknet signature of round_r
//!  5 previous     ZBDPRV01, 188 B   S_{r-1}, raw_blake3_{r-1}, meta_{r-1}, round_{r-1} LE, value_{r-1}, sig_{r-1}
//!  6 leaf_u       ZBDLFU01, 208 B   the declared wrong row's leaf fields (S_u, ..., S_{u+1}, emission_blake3_u)
//!  7 siblings_u   depth x 32 B
//!  8 noise        86,016 B          int16 LE Q12, 4 x 96 x 112
//!  9 offset       4 B               i32 LE, the declared offset d (u = r + d)
//! 10 offset_rule  1 B               0 direct (d in {-2,2,-15,15,30}), 1 mirrored (-d in that set and r - d outside
//!                                   the session; so -30 only under the flag and only when r + 30 leaves the session)
//! ```
//! Direct and mirrored offsets are validated together by `check_offset_rule` (Astra r5 finding 1); the exact modulo
//! assignment anchored at row 600 is `rule::august_assignment`, enforced by the acceptance verifier, not the guest.
//! Public output `ZBDIFF01`, 752 bytes, little-endian unless stated (offsets in RELATION.md s.4):
//! magic, abi, protocol, denoiser kind, offset_rule flag (byte 11), public length; r, u, d, row count, tree depth, session id (128, zero
//! padded); S_0, S_N, manifest SHA-256, chain-log BLAKE3; context digest, ordered-session root; leaf_r, leaf_u;
//! raw_blake3_r, emission_blake3_r, emission_blake3_u; previous and own drand rounds (u64 BE), drand leg digest;
//! constants, spec and preprocessing digests; noise BLAKE3, timestep, SA, SO, shift, F_CT, F_HINT, F_EPS;
//! R_correct, R_wrong, D, denominator, sign (748), clip flag (749), clip-event count u16 LE saturating (750..752):
//! every clamp outside the admitted int16 domain in the noising leg and in both network passes, plus every indexed
//! hit on a clipped lookup-table entry (the G1 FINAL contract), published rather than hidden or refused.

use crate::b3xof::{self, blake3p, META_BYTES};
use crate::beacon::{drand_leg_digest, verify_and_bind, SIGNATURE_BYTES};
use crate::emission::expand_and_digest;
use crate::frame::frame_c_int;
use crate::header::RowWitnessHeader;
use crate::hint::{e_int_torchpath, hint14, F_HINT};
use crate::membership::{parse_leaf_u, parse_siblings, verify_two_leaves, LeafFields, MembershipWitness};
use crate::net::Denoiser;
use crate::noise::{forward_noise, i16_from_le, residual_sum, F_CT, F_EPS, NOISE_BYTES, NOISE_SHIFT, RESIDUAL_DENOMINATOR, SA_INT, SO_INT, TIMESTEP};
use crate::spec::preprocess_spec_sha256;
use crate::{RelationError, Result, RAW_BYTES};

/// The protocol's wrong-row offsets (lean_pubproto_eval.py:16).
pub const OFFSETS: [i32; 5] = [-2, 2, -15, 15, 30];

pub const PUBLIC_MAGIC: &[u8; 8] = b"ZBDIFF01";
pub const PUBLIC_ABI_VERSION: u8 = 1;
pub const PROTOCOL_V9_CODE: u8 = 9;
pub const PUBLIC_BYTES: usize = 752;
pub const SESSION_ID_FIELD_BYTES: usize = 128;

pub const PREV_MAGIC: &[u8; 8] = b"ZBDPRV01";
pub const PREV_BYTES: usize = 8 + 32 + 32 + META_BYTES + 8 + 32 + SIGNATURE_BYTES; // 188

macro_rules! track {
    ($($arg:tt)*) => {
        #[cfg(target_os = "zkvm")]
        println!($($arg)*);
    };
}

/// Row r-1's record with its beacon signature: the previous-row advance leg (august.rs `verify_previous_advance`
/// took these fields out of the anchored August CSV prefix; here they are explicit witnesses so the leg works for
/// any session whose signatures are known).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PreviousRecord {
    pub s_t: [u8; 32],
    pub raw_blake3: [u8; 32],
    pub meta: [u8; META_BYTES],
    pub drand_round: u64,
    pub drand_value: [u8; 32],
    pub signature: [u8; SIGNATURE_BYTES],
}

impl PreviousRecord {
    pub fn parse(bytes: &[u8]) -> Result<Self> {
        if bytes.len() != PREV_BYTES {
            return Err(RelationError("previous-row record must be exactly 188 bytes"));
        }
        if &bytes[0..8] != PREV_MAGIC {
            return Err(RelationError("previous-row record magic differs"));
        }
        Ok(Self {
            s_t: bytes[8..40].try_into().unwrap(),
            raw_blake3: bytes[40..72].try_into().unwrap(),
            meta: bytes[72..100].try_into().unwrap(),
            drand_round: u64::from_le_bytes(bytes[100..108].try_into().unwrap()),
            drand_value: bytes[108..140].try_into().unwrap(),
            signature: bytes[140..188].try_into().unwrap(),
        })
    }

    pub fn encode(&self) -> Vec<u8> {
        let mut b = Vec::with_capacity(PREV_BYTES);
        b.extend_from_slice(PREV_MAGIC);
        b.extend_from_slice(&self.s_t);
        b.extend_from_slice(&self.raw_blake3);
        b.extend_from_slice(&self.meta);
        b.extend_from_slice(&self.drand_round.to_le_bytes());
        b.extend_from_slice(&self.drand_value);
        b.extend_from_slice(&self.signature);
        b
    }
}

/// The ten private items, as byte strings, exactly as the guest reads them.
#[derive(Clone, Debug, Default)]
pub struct Witness {
    pub header: Vec<u8>,
    pub membership: Vec<u8>,
    pub raw: Vec<u8>,
    pub signature: Vec<u8>,
    pub previous: Vec<u8>,
    pub leaf_u: Vec<u8>,
    pub siblings_u: Vec<u8>,
    pub noise: Vec<u8>,
    pub offset: Vec<u8>,
    /// One byte: `OFFSET_RULE_DIRECT` or `OFFSET_RULE_MIRRORED`. An empty vector is read as direct (older witness sets).
    pub offset_rule: Vec<u8>,
}

/// Public byte 11: the declared offset is the batch rule's direct value.
pub const OFFSET_RULE_DIRECT: u8 = 0;
/// Public byte 11: the declared offset is the mirror (-base) of the rule's value because `r + base` lies outside the
/// session; the guest checks that `r - d` is indeed outside `[0, row_count)`.
pub const OFFSET_RULE_MIRRORED: u8 = 1;

/// Every field of the public statement.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PublicOutput {
    pub denoiser_kind: u8,
    /// `OFFSET_RULE_DIRECT` or `OFFSET_RULE_MIRRORED` (public byte 11).
    pub offset_rule: u8,
    pub row_r: u32,
    pub row_u: u32,
    pub offset: i32,
    pub row_count: u32,
    pub tree_depth: u16,
    pub session_id: Vec<u8>,
    pub s_0: [u8; 32],
    pub s_n: [u8; 32],
    pub authority_manifest_sha256: [u8; 32],
    pub chain_log_blake3: [u8; 32],
    pub context_digest: [u8; 32],
    pub ordered_session_root: [u8; 32],
    pub leaf_r: [u8; 32],
    pub leaf_u: [u8; 32],
    pub raw_blake3_r: [u8; 32],
    pub emission_blake3_r: [u8; 32],
    pub emission_blake3_u: [u8; 32],
    pub prev_drand_round: u64,
    pub own_drand_round: u64,
    pub drand_leg_digest: [u8; 32],
    pub constants_sha256: [u8; 32],
    pub spec_sha256: [u8; 32],
    pub preprocess_spec_sha256: [u8; 32],
    pub noise_blake3: [u8; 32],
    pub r_correct: u64,
    pub r_wrong: u64,
    /// Clipping events over the noising leg and both network passes, saturating at 65535 (public bytes 750..752;
    /// byte 749 is 1 iff nonzero).
    pub clip_events: u16,
}

impl PublicOutput {
    pub fn difference(&self) -> i64 {
        (self.r_wrong as i128 - self.r_correct as i128) as i64
    }

    pub fn encode(&self) -> Vec<u8> {
        let mut b = Vec::with_capacity(PUBLIC_BYTES);
        b.extend_from_slice(PUBLIC_MAGIC);
        b.push(PUBLIC_ABI_VERSION);
        b.push(PROTOCOL_V9_CODE);
        b.push(self.denoiser_kind);
        b.push(self.offset_rule);
        b.extend_from_slice(&(PUBLIC_BYTES as u32).to_le_bytes());
        b.extend_from_slice(&self.row_r.to_le_bytes());
        b.extend_from_slice(&self.row_u.to_le_bytes());
        b.extend_from_slice(&self.offset.to_le_bytes());
        b.extend_from_slice(&self.row_count.to_le_bytes());
        b.extend_from_slice(&self.tree_depth.to_le_bytes());
        b.extend_from_slice(&(self.session_id.len() as u16).to_le_bytes());
        b.extend_from_slice(&self.session_id);
        b.resize(36 + SESSION_ID_FIELD_BYTES, 0);
        for field in [
            &self.s_0,
            &self.s_n,
            &self.authority_manifest_sha256,
            &self.chain_log_blake3,
            &self.context_digest,
            &self.ordered_session_root,
            &self.leaf_r,
            &self.leaf_u,
            &self.raw_blake3_r,
            &self.emission_blake3_r,
            &self.emission_blake3_u,
        ] {
            b.extend_from_slice(field);
        }
        b.extend_from_slice(&self.prev_drand_round.to_be_bytes());
        b.extend_from_slice(&self.own_drand_round.to_be_bytes());
        b.extend_from_slice(&self.drand_leg_digest);
        b.extend_from_slice(&self.constants_sha256);
        b.extend_from_slice(&self.spec_sha256);
        b.extend_from_slice(&self.preprocess_spec_sha256);
        b.extend_from_slice(&self.noise_blake3);
        b.extend_from_slice(&TIMESTEP.to_le_bytes());
        b.extend_from_slice(&SA_INT.to_le_bytes());
        b.extend_from_slice(&SO_INT.to_le_bytes());
        b.push(NOISE_SHIFT as u8);
        b.push(F_CT as u8);
        b.push(F_HINT as u8);
        b.push(F_EPS as u8);
        b.extend_from_slice(&self.r_correct.to_le_bytes());
        b.extend_from_slice(&self.r_wrong.to_le_bytes());
        let d = self.difference();
        b.extend_from_slice(&d.to_le_bytes());
        b.extend_from_slice(&RESIDUAL_DENOMINATOR.to_le_bytes());
        b.push(if d > 0 { 1 } else { 0 });
        b.push(u8::from(self.clip_events != 0));
        b.extend_from_slice(&self.clip_events.to_le_bytes());
        assert_eq!(b.len(), PUBLIC_BYTES);
        b
    }

    pub fn parse(b: &[u8]) -> Result<Self> {
        if b.len() != PUBLIC_BYTES {
            return Err(RelationError("public statement must be exactly 752 bytes"));
        }
        if &b[0..8] != PUBLIC_MAGIC || b[8] != PUBLIC_ABI_VERSION || b[9] != PROTOCOL_V9_CODE || b[11] > OFFSET_RULE_MIRRORED {
            return Err(RelationError("public statement framing differs"));
        }
        if u32::from_le_bytes(b[12..16].try_into().unwrap()) != PUBLIC_BYTES as u32 {
            return Err(RelationError("public statement length field differs"));
        }
        let f32b = |o: usize| -> [u8; 32] { b[o..o + 32].try_into().unwrap() };
        let sid_len = u16::from_le_bytes(b[34..36].try_into().unwrap()) as usize;
        if sid_len == 0 || sid_len > SESSION_ID_FIELD_BYTES || b[36 + sid_len..164].iter().any(|&x| x != 0) {
            return Err(RelationError("session identifier field is not zero padded"));
        }
        let out = Self {
            denoiser_kind: b[10],
            offset_rule: b[11],
            row_r: u32::from_le_bytes(b[16..20].try_into().unwrap()),
            row_u: u32::from_le_bytes(b[20..24].try_into().unwrap()),
            offset: i32::from_le_bytes(b[24..28].try_into().unwrap()),
            row_count: u32::from_le_bytes(b[28..32].try_into().unwrap()),
            tree_depth: u16::from_le_bytes(b[32..34].try_into().unwrap()),
            session_id: b[36..36 + sid_len].to_vec(),
            s_0: f32b(164),
            s_n: f32b(196),
            authority_manifest_sha256: f32b(228),
            chain_log_blake3: f32b(260),
            context_digest: f32b(292),
            ordered_session_root: f32b(324),
            leaf_r: f32b(356),
            leaf_u: f32b(388),
            raw_blake3_r: f32b(420),
            emission_blake3_r: f32b(452),
            emission_blake3_u: f32b(484),
            prev_drand_round: u64::from_be_bytes(b[516..524].try_into().unwrap()),
            own_drand_round: u64::from_be_bytes(b[524..532].try_into().unwrap()),
            drand_leg_digest: f32b(532),
            constants_sha256: f32b(564),
            spec_sha256: f32b(596),
            preprocess_spec_sha256: f32b(628),
            noise_blake3: f32b(660),
            r_correct: u64::from_le_bytes(b[716..724].try_into().unwrap()),
            r_wrong: u64::from_le_bytes(b[724..732].try_into().unwrap()),
            clip_events: u16::from_le_bytes(b[750..752].try_into().unwrap()),
        };
        // the row triple and the rule flag must be admissible on their face (the guest never emits anything else,
        // so this only hardens every parser of the public bytes, the acceptance verifier included)
        let u = check_offset_rule(out.row_r, out.row_count, out.offset, out.offset_rule)?;
        if u != out.row_u || out.row_r == 0 || out.row_r >= out.row_count {
            return Err(RelationError("public statement row fields are inconsistent with the offset rule"));
        }
        // the derived tail must be consistent
        if u32::from_le_bytes(b[692..696].try_into().unwrap()) != TIMESTEP
            || i64::from_le_bytes(b[696..704].try_into().unwrap()) != SA_INT
            || i64::from_le_bytes(b[704..712].try_into().unwrap()) != SO_INT
            || b[712..716] != [NOISE_SHIFT as u8, F_CT as u8, F_HINT as u8, F_EPS as u8]
            || i64::from_le_bytes(b[732..740].try_into().unwrap()) != out.difference()
            || u64::from_le_bytes(b[740..748].try_into().unwrap()) != RESIDUAL_DENOMINATOR
            || b[748] != u8::from(out.difference() > 0)
            || b[749] != u8::from(out.clip_events != 0)
        {
            return Err(RelationError("public statement constant or derived fields differ"));
        }
        Ok(out)
    }
}

/// The declared offset as bytes (i32 LE). Admissibility is `check_offset_rule`, which needs `r` and the row count.
fn parse_offset_bytes(bytes: &[u8]) -> Result<i32> {
    if bytes.len() != 4 {
        return Err(RelationError("declared offset must be 4 bytes"));
    }
    Ok(i32::from_le_bytes(bytes.try_into().unwrap()))
}

/// The two-part offset rule as far as a statement can check it without knowing which batch it belongs to
/// (Astra r5 finding 1): direct and mirrored offsets are validated together.
///
/// * `OFFSET_RULE_DIRECT`: `d` is a nonzero protocol offset (`OFFSETS`) and `u = r + d` lies inside the session.
/// * `OFFSET_RULE_MIRRORED`: `-d` is a protocol offset (so `d` is one of `+2, -2, +15, -15, -30`), `u = r + d` lies
///   inside the session, and the rule's direct wrong row `r - d` lies OUTSIDE `[0, row_count)`. So `-30` is admitted
///   only under the mirror flag and only when `r + 30` would leave the session, and a mirror flag on a row whose
///   direct wrong row exists is refused.
///
/// Returns `u`. The exact modulo assignment anchored at row 600 (`rule::august_assignment`) is policy and is
/// enforced by the acceptance verifier on the public fields, not here.
pub fn check_offset_rule(r: u32, row_count: u32, d: i32, offset_rule: u8) -> Result<u32> {
    match offset_rule {
        OFFSET_RULE_DIRECT => {
            if d == 0 || !OFFSETS.contains(&d) {
                return Err(RelationError("declared offset must be a nonzero protocol offset"));
            }
        }
        OFFSET_RULE_MIRRORED => {
            let base = d.checked_neg().ok_or(RelationError("declared offset overflows"))?;
            if base == 0 || !OFFSETS.contains(&base) {
                return Err(RelationError("mirrored offset must be the mirror of a protocol offset"));
            }
        }
        _ => return Err(RelationError("offset rule flag must be one byte, 0 (direct) or 1 (mirrored)")),
    }
    let u = r as i64 + d as i64;
    if u < 0 || u >= row_count as i64 {
        return Err(RelationError("declared wrong row is outside the committed session"));
    }
    if offset_rule == OFFSET_RULE_MIRRORED {
        // the mirror is admissible only when the rule's direct wrong row r + base = r - d lies outside the session
        let direct = r as i64 - d as i64;
        if direct >= 0 && direct < row_count as i64 {
            return Err(RelationError("mirrored offset claimed although the direct wrong row lies inside the session"));
        }
    }
    Ok(u as u32)
}

fn parse_offset_rule(bytes: &[u8]) -> Result<u8> {
    match bytes {
        [] => Ok(OFFSET_RULE_DIRECT),
        [f] if *f == OFFSET_RULE_DIRECT || *f == OFFSET_RULE_MIRRORED => Ok(*f),
        _ => Err(RelationError("offset rule flag must be one byte, 0 (direct) or 1 (mirrored)")),
    }
}

/// Run the whole relation on a witness with the given network. Returns the 752 public bytes, or the first leg that
/// fails.
pub fn evaluate(w: &Witness, net: &dyn Denoiser) -> Result<Vec<u8>> {
    track!("cycle-tracker-report-start: parse_witness");
    let header = RowWitnessHeader::parse(&w.header)?;
    let membership = MembershipWitness::parse(&w.membership)?;
    let offset = parse_offset_bytes(&w.offset)?;
    let offset_rule = parse_offset_rule(&w.offset_rule)?;
    let leaf_u = parse_leaf_u(&w.leaf_u)?;
    let siblings_u = parse_siblings(&w.siblings_u)?;
    let previous = PreviousRecord::parse(&w.previous)?;
    if w.raw.len() != RAW_BYTES {
        return Err(RelationError("raw Bayer input must be exactly 24,472,000 bytes"));
    }
    if w.noise.len() != NOISE_BYTES {
        return Err(RelationError("noise witness must be exactly 86,016 bytes (4x96x112 int16)"));
    }
    let r = header.row_index;
    if r == 0 {
        return Err(RelationError("row 0 has no previous row; its emission derives from the session seed"));
    }
    if r >= membership.row_count {
        return Err(RelationError("proved row index is outside the committed session"));
    }
    // direct and mirrored offsets validated together: the protocol set under the direct flag, its mirror image under
    // the mirror flag with the direct wrong row required to lie outside the session, u = r + d inside in both cases
    let u = check_offset_rule(r, membership.row_count, offset, offset_rule)?;
    if leaf_u.row_index != u {
        return Err(RelationError("wrong-row leaf witness does not carry row r + offset"));
    }
    if u32::from_be_bytes(previous.meta[0..4].try_into().unwrap()) != r - 1 {
        return Err(RelationError("previous-row record metadata does not name row r - 1"));
    }
    track!("cycle-tracker-report-end: parse_witness");

    track!("cycle-tracker-report-start: constants");
    let preprocess_digest = preprocess_spec_sha256();
    let constants_digest = net.constants_sha256();
    let spec_digest = net.spec_sha256();
    track!("cycle-tracker-report-end: constants");

    // DRAND leg, the row's own beacon: verified, then bound to the value the advance consumes.
    track!("cycle-tracker-report-start: drand_verify");
    verify_and_bind(header.drand_round, &w.signature, &header.drand_value)?;
    track!("cycle-tracker-report-end: drand_verify");

    track!("cycle-tracker-report-start: raw_blake3_24MB");
    let raw_blake3 = blake3p::hash(&w.raw);
    track!("cycle-tracker-report-end: raw_blake3_24MB");
    let s_next = b3xof::advance_chain(&header.s_t, &raw_blake3, &header.meta, header.drand_round, &header.drand_value);

    // PREVIOUS-ROW ADVANCE leg: the beacon that bounds THIS frame's emission from below.
    track!("cycle-tracker-report-start: previous_advance_leg");
    verify_and_bind(previous.drand_round, &previous.signature, &previous.drand_value)?;
    let recomputed = b3xof::advance_chain(&previous.s_t, &previous.raw_blake3, &previous.meta, previous.drand_round, &previous.drand_value);
    if recomputed != header.s_t {
        return Err(RelationError("previous row's advance does not produce the proved row's S_t"));
    }
    track!("cycle-tracker-report-end: previous_advance_leg");

    track!("cycle-tracker-report-start: emission_render_r");
    let (cond_r, emission_r) = expand_and_digest(&header.s_t);
    track!("cycle-tracker-report-end: emission_render_r");
    track!("cycle-tracker-report-start: emission_render_u");
    let (cond_u, emission_u) = expand_and_digest(&leaf_u.s_t);
    if emission_u != leaf_u.emission_blake3 {
        return Err(RelationError("declared wrong row's pattern does not render to its leaf's emission digest"));
    }
    track!("cycle-tracker-report-end: emission_render_u");

    track!("cycle-tracker-report-start: ordered_session_membership");
    let leaf_r = LeafFields {
        row_index: r,
        s_t: header.s_t,
        raw_blake3,
        meta: header.meta,
        drand_round: header.drand_round,
        drand_value: header.drand_value,
        s_next,
        emission_blake3: emission_r,
    };
    let (context, leaf_r_hash, leaf_u_hash) = verify_two_leaves(&membership, &leaf_r, &leaf_u, &siblings_u)?;
    track!("cycle-tracker-report-end: ordered_session_membership");

    track!("cycle-tracker-report-start: frame_reduce");
    let c_int = frame_c_int(&w.raw);
    track!("cycle-tracker-report-end: frame_reduce");

    track!("cycle-tracker-report-start: hints");
    let hint_r = hint14(&e_int_torchpath(&cond_r));
    let hint_u = hint14(&e_int_torchpath(&cond_u));
    drop(cond_r);
    drop(cond_u);
    track!("cycle-tracker-report-end: hints");

    track!("cycle-tracker-report-start: noise");
    let noise_blake3 = blake3p::hash(&w.noise);
    let noise_int = i16_from_le(&w.noise)?;
    // the C_t clamp is the first counted clipping site (G1 FINAL: one event per element outside the int16 domain);
    // the count is published, never hidden and never a refusal
    let (ct, noise_clips) = forward_noise(&c_int, &noise_int)?;
    track!("cycle-tracker-report-end: noise");

    track!("cycle-tracker-report-start: denoiser_correct");
    let (eps_r, clips_r) = net.predict(&ct, &hint_r)?;
    let r_correct = residual_sum(&eps_r, &noise_int)?;
    drop(eps_r);
    track!("cycle-tracker-report-end: denoiser_correct");
    track!("cycle-tracker-report-start: denoiser_wrong");
    let (eps_u, clips_u) = net.predict(&ct, &hint_u)?;
    let r_wrong = residual_sum(&eps_u, &noise_int)?;
    drop(eps_u);
    track!("cycle-tracker-report-end: denoiser_wrong");
    let clip_events = (noise_clips as u64 + clips_r as u64 + clips_u as u64).min(u16::MAX as u64) as u16;

    let public = PublicOutput {
        denoiser_kind: net.kind(),
        offset_rule,
        row_r: r,
        row_u: u,
        offset,
        row_count: membership.row_count,
        tree_depth: membership.tree_depth,
        session_id: membership.session_id.clone(),
        s_0: membership.s_0,
        s_n: membership.s_n,
        authority_manifest_sha256: membership.authority_manifest_sha256,
        chain_log_blake3: membership.chain_log_blake3,
        context_digest: context,
        ordered_session_root: membership.ordered_session_root_blake3,
        leaf_r: leaf_r_hash,
        leaf_u: leaf_u_hash,
        raw_blake3_r: raw_blake3,
        emission_blake3_r: emission_r,
        emission_blake3_u: emission_u,
        prev_drand_round: previous.drand_round,
        own_drand_round: header.drand_round,
        drand_leg_digest: drand_leg_digest(previous.drand_round, &previous.drand_value, header.drand_round, &header.drand_value),
        constants_sha256: constants_digest,
        spec_sha256: spec_digest,
        preprocess_spec_sha256: preprocess_digest,
        noise_blake3,
        r_correct,
        r_wrong,
        clip_events,
    };
    Ok(public.encode())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample() -> PublicOutput {
        PublicOutput {
            denoiser_kind: 0,
            offset_rule: OFFSET_RULE_DIRECT,
            row_r: 600,
            row_u: 602,
            offset: 2,
            row_count: 712,
            tree_depth: 10,
            session_id: b"ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001".to_vec(),
            s_0: [1; 32],
            s_n: [2; 32],
            authority_manifest_sha256: [3; 32],
            chain_log_blake3: [4; 32],
            context_digest: [5; 32],
            ordered_session_root: [6; 32],
            leaf_r: [7; 32],
            leaf_u: [8; 32],
            raw_blake3_r: [9; 32],
            emission_blake3_r: [10; 32],
            emission_blake3_u: [11; 32],
            prev_drand_round: 31_521_689,
            own_drand_round: 31_521_690,
            drand_leg_digest: [12; 32],
            constants_sha256: [13; 32],
            spec_sha256: [14; 32],
            preprocess_spec_sha256: [15; 32],
            noise_blake3: [16; 32],
            r_correct: 12_775_807_457,
            r_wrong: 15_569_339_266,
            clip_events: 0,
        }
    }

    #[test]
    fn public_layout_round_trips_and_offsets_are_fixed() {
        let p = sample();
        let b = p.encode();
        assert_eq!(b.len(), PUBLIC_BYTES);
        assert_eq!(&b[0..8], PUBLIC_MAGIC);
        assert_eq!(u32::from_le_bytes(b[16..20].try_into().unwrap()), 600);
        assert_eq!(u32::from_le_bytes(b[20..24].try_into().unwrap()), 602);
        assert_eq!(i32::from_le_bytes(b[24..28].try_into().unwrap()), 2);
        assert_eq!(&b[36..36 + 51], p.session_id.as_slice());
        assert!(b[87..164].iter().all(|&x| x == 0));
        assert_eq!(&b[164..196], &[1; 32]);
        assert_eq!(&b[484..516], &[11; 32]);
        assert_eq!(u64::from_be_bytes(b[516..524].try_into().unwrap()), 31_521_689);
        assert_eq!(u64::from_le_bytes(b[716..724].try_into().unwrap()), 12_775_807_457);
        assert_eq!(i64::from_le_bytes(b[732..740].try_into().unwrap()), 2_793_531_809);
        assert_eq!(u64::from_le_bytes(b[740..748].try_into().unwrap()), 721_554_505_728);
        assert_eq!(b[748], 1);
        assert_eq!(PublicOutput::parse(&b).unwrap(), p);
        let mut neg = p.clone();
        neg.r_wrong = neg.r_correct - 5;
        let nb = neg.encode();
        assert_eq!(nb[748], 0);
        assert_eq!(i64::from_le_bytes(nb[732..740].try_into().unwrap()), -5);
        let mut bad = b.clone();
        bad[748] ^= 1;
        assert!(PublicOutput::parse(&bad).is_err());
        // byte 11 carries the offset-rule flag: 0 and 1 parse, anything else is refused (a mirrored statement must
        // also be admissible on its face: row 711, base +2 -> 713 outside, mirrored -2 -> u = 709)
        let mut mirrored = p.clone();
        mirrored.offset_rule = OFFSET_RULE_MIRRORED;
        mirrored.row_r = 711;
        mirrored.row_u = 709;
        mirrored.offset = -2;
        let mb = mirrored.encode();
        assert_eq!(mb[11], 1);
        assert_eq!(PublicOutput::parse(&mb).unwrap(), mirrored);
        let mut bad11 = b.clone();
        bad11[11] = 2;
        assert!(PublicOutput::parse(&bad11).is_err());
        // clip events: flag byte 749 and the u16 count at 750..752 must agree
        assert_eq!(&b[749..752], &[0, 0, 0]);
        let mut clipped = p.clone();
        clipped.clip_events = 3;
        let cb = clipped.encode();
        assert_eq!(&cb[749..752], &[1, 3, 0]);
        assert_eq!(PublicOutput::parse(&cb).unwrap(), clipped);
        let mut bad_flag = cb.clone();
        bad_flag[749] = 0;
        assert!(PublicOutput::parse(&bad_flag).is_err());
        let mut bad_flag = b.clone();
        bad_flag[749] = 1;
        assert!(PublicOutput::parse(&bad_flag).is_err());
        let mut many = p.clone();
        many.clip_events = u16::MAX;
        assert_eq!(&many.encode()[749..752], &[1, 0xff, 0xff]);
    }

    #[test]
    fn offset_rule_flag_parses() {
        assert_eq!(parse_offset_rule(&[]).unwrap(), OFFSET_RULE_DIRECT);
        assert_eq!(parse_offset_rule(&[0]).unwrap(), OFFSET_RULE_DIRECT);
        assert_eq!(parse_offset_rule(&[1]).unwrap(), OFFSET_RULE_MIRRORED);
        assert!(parse_offset_rule(&[2]).is_err());
        assert!(parse_offset_rule(&[0, 0]).is_err());
    }

    #[test]
    fn offsets_fail_closed() {
        assert!(parse_offset_bytes(&[1, 2, 3]).is_err());
        assert_eq!(parse_offset_bytes(&(-30_i32).to_le_bytes()).unwrap(), -30);
        let n = 712;
        // direct: the protocol set, u inside
        for d in OFFSETS {
            assert_eq!(check_offset_rule(600, n, d, OFFSET_RULE_DIRECT).unwrap() as i64, 600 + d as i64);
        }
        assert_eq!(check_offset_rule(600, n, 0, OFFSET_RULE_DIRECT).unwrap_err().message(), "declared offset must be a nonzero protocol offset");
        assert_eq!(check_offset_rule(600, n, 1, OFFSET_RULE_DIRECT).unwrap_err().message(), "declared offset must be a nonzero protocol offset");
        assert_eq!(check_offset_rule(600, n, -30, OFFSET_RULE_DIRECT).unwrap_err().message(), "declared offset must be a nonzero protocol offset");
        assert_eq!(check_offset_rule(684, n, 30, OFFSET_RULE_DIRECT).unwrap_err().message(), "declared wrong row is outside the committed session");
        assert_eq!(check_offset_rule(1, n, -2, OFFSET_RULE_DIRECT).unwrap_err().message(), "declared wrong row is outside the committed session");
        // mirrored: -30 admitted exactly when r + 30 would leave the session (rows 682..=711 of a 712-row session)
        assert_eq!(check_offset_rule(684, n, -30, OFFSET_RULE_MIRRORED).unwrap(), 654);
        assert_eq!(check_offset_rule(682, n, -30, OFFSET_RULE_MIRRORED).unwrap(), 652);
        assert_eq!(check_offset_rule(711, n, -30, OFFSET_RULE_MIRRORED).unwrap(), 681);
        assert_eq!(check_offset_rule(681, n, -30, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset claimed although the direct wrong row lies inside the session");
        assert_eq!(check_offset_rule(600, n, -30, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset claimed although the direct wrong row lies inside the session");
        // mirrored -15 and -2 likewise, and +2 at row 1
        assert_eq!(check_offset_rule(698, n, -15, OFFSET_RULE_MIRRORED).unwrap(), 683);
        assert_eq!(check_offset_rule(696, n, -15, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset claimed although the direct wrong row lies inside the session");
        assert_eq!(check_offset_rule(711, n, -2, OFFSET_RULE_MIRRORED).unwrap(), 709);
        assert_eq!(check_offset_rule(1, n, 2, OFFSET_RULE_MIRRORED).unwrap(), 3);
        assert_eq!(check_offset_rule(2, n, 2, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset claimed although the direct wrong row lies inside the session");
        // a mirror flag never admits a value whose mirror is not in the set (+30 mirrored would be base -30)
        assert_eq!(check_offset_rule(600, n, 30, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset must be the mirror of a protocol offset");
        assert_eq!(check_offset_rule(600, n, 0, OFFSET_RULE_MIRRORED).unwrap_err().message(), "mirrored offset must be the mirror of a protocol offset");
        assert_eq!(check_offset_rule(600, n, i32::MIN, OFFSET_RULE_MIRRORED).unwrap_err().message(), "declared offset overflows");
        // the mirrored wrong row itself must lie inside
        assert_eq!(check_offset_rule(20, 40, -30, OFFSET_RULE_MIRRORED).unwrap_err().message(), "declared wrong row is outside the committed session");
        // a flag byte other than 0/1
        assert!(check_offset_rule(600, n, 2, 2).is_err());
    }

    #[test]
    fn public_parse_enforces_the_offset_rule_on_the_public_fields() {
        // a mirrored -30 statement for row 684 parses; the same bytes with the flag cleared, or with the flag set on a
        // direct row, or with u != r + d, are refused by every parser of the public bytes
        let mut m = sample();
        m.row_r = 684;
        m.row_u = 654;
        m.offset = -30;
        m.offset_rule = OFFSET_RULE_MIRRORED;
        let mb = m.encode();
        assert_eq!(PublicOutput::parse(&mb).unwrap(), m);
        let mut direct_minus30 = mb.clone();
        direct_minus30[11] = OFFSET_RULE_DIRECT;
        assert_eq!(PublicOutput::parse(&direct_minus30).unwrap_err().message(), "declared offset must be a nonzero protocol offset");
        let mut flag_on_direct = sample().encode();
        flag_on_direct[11] = OFFSET_RULE_MIRRORED;
        assert_eq!(PublicOutput::parse(&flag_on_direct).unwrap_err().message(), "mirrored offset claimed although the direct wrong row lies inside the session");
        let mut bad_u = sample().encode();
        bad_u[20..24].copy_from_slice(&603_u32.to_le_bytes());
        assert_eq!(PublicOutput::parse(&bad_u).unwrap_err().message(), "public statement row fields are inconsistent with the offset rule");
        let mut bad_d = sample().encode();
        bad_d[24..28].copy_from_slice(&3_i32.to_le_bytes());
        assert!(PublicOutput::parse(&bad_d).is_err());
    }

    #[test]
    fn previous_record_round_trips() {
        let p = PreviousRecord { s_t: [1; 32], raw_blake3: [2; 32], meta: [3; 28], drand_round: 77, drand_value: [4; 32], signature: [5; 48] };
        let e = p.encode();
        assert_eq!(e.len(), PREV_BYTES);
        assert_eq!(PreviousRecord::parse(&e).unwrap(), p);
        assert!(PreviousRecord::parse(&e[..187]).is_err());
    }
}
