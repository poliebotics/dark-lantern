//! Ordered-session membership: context digest, row leaf, node, wrapped root, and the two-leaf opening.
//!
//! The hash functions are copied from the proved membership crate
//! (rust/row_binding_join_membership_sp1_candidate/membership/src/lib.rs, lines 40-43 domains, 140-149
//! `domain_hash`, 267-288 `session_context_digest`, 341-357 `row_leaf_hash`, 359-383 `node_hash` and
//! `wrapped_root_hash`, 385-412 the path walk) and generalised in one way only: the leaf fields are taken from a
//! struct rather than parsed out of the proved base journal, so the same code opens the proved row (with its
//! recomputed `S_{r+1}` and emission digest) and the declared wrong row (whose fields are witnessed). The
//! `ZBOSM001` private encoding (lines 23-28, 169-265) is kept byte for byte so `session_tree.py` output feeds it.
//!
//! Positive control: the frozen August row-96 constants of native/src/lib.rs (context, leaf, internal root,
//! wrapped root) are reproduced in the tests.

use crate::b3xof::blake3p;
use crate::header::PROTOCOL_V9_CODE;
use crate::{RelationError, Result};

pub const PRIVATE_MAGIC: &[u8; 8] = b"ZBOSM001";
pub const PRIVATE_ABI_VERSION: u8 = 1;
pub const PRIVATE_FIXED_BYTES: usize = 184;
pub const SESSION_ID_MAX_BYTES: usize = 128;
pub const MAX_TREE_DEPTH: usize = 20;
pub const MAX_ROW_COUNT: u32 = 1_000_000;

pub const CONTEXT_DOMAIN: &[u8] = b"ZEEBEAM_ORDERED_SESSION_CONTEXT_V1\0";
pub const ROW_DOMAIN: &[u8] = b"ZEEBEAM_ORDERED_SESSION_ROW_V1\0";
pub const NODE_DOMAIN: &[u8] = b"ZEEBEAM_ORDERED_SESSION_NODE_V1\0";
pub const ROOT_DOMAIN: &[u8] = b"ZEEBEAM_ORDERED_SESSION_ROOT_V1\0";

/// The session context and the committed root, with the sibling path of one row (the `ZBOSM001` witness).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MembershipWitness {
    pub protocol_code: u8,
    pub terminal_committed: u8,
    pub tree_depth: u16,
    pub row_count: u32,
    pub session_id: Vec<u8>,
    pub s_0: [u8; 32],
    pub s_n: [u8; 32],
    pub authority_manifest_sha256: [u8; 32],
    pub chain_log_blake3: [u8; 32],
    pub ordered_session_root_blake3: [u8; 32],
    pub siblings_blake3: Vec<[u8; 32]>,
}

/// What one leaf commits (membership lib.rs 341-357, in this field order).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LeafFields {
    pub row_index: u32,
    pub s_t: [u8; 32],
    pub raw_blake3: [u8; 32],
    pub meta: [u8; 28],
    pub drand_round: u64,
    pub drand_value: [u8; 32],
    pub s_next: [u8; 32],
    pub emission_blake3: [u8; 32],
}

fn exact_32(bytes: &[u8]) -> [u8; 32] {
    bytes.try_into().expect("fixed 32-byte slice")
}

fn identifier_byte(value: u8, first: bool) -> bool {
    value.is_ascii_alphanumeric() || (!first && matches!(value, b'.' | b'_' | b':' | b'-'))
}

fn validate_identifier(value: &[u8]) -> Result<()> {
    if value.is_empty() || value.len() > SESSION_ID_MAX_BYTES {
        return Err(RelationError("session identifier length is outside 1..128"));
    }
    if !identifier_byte(value[0], true) || value[1..].iter().copied().any(|b| !identifier_byte(b, false)) {
        return Err(RelationError("session identifier is not canonical ASCII"));
    }
    Ok(())
}

pub fn tree_depth_for_count(row_count: u32) -> Result<u16> {
    if row_count == 0 || row_count > MAX_ROW_COUNT {
        return Err(RelationError("row count is outside 1..1000000"));
    }
    let mut remaining = row_count - 1;
    let mut depth = 0_u16;
    while remaining != 0 {
        depth += 1;
        remaining >>= 1;
    }
    if usize::from(depth) > MAX_TREE_DEPTH {
        return Err(RelationError("minimal tree depth exceeds ABI ceiling"));
    }
    Ok(depth)
}

/// `BLAKE3(domain || for each part: u32be(len) || part)`.
pub fn domain_hash(domain: &[u8], parts: &[&[u8]]) -> [u8; 32] {
    let mut hasher = blake3p::Hasher::new();
    hasher.update(domain);
    for part in parts {
        let length = u32::try_from(part.len()).expect("membership field length exceeds u32");
        hasher.update(&length.to_be_bytes());
        hasher.update(part);
    }
    hasher.finalize()
}

fn validate_witness_shape(w: &MembershipWitness) -> Result<()> {
    if w.protocol_code != PROTOCOL_V9_CODE {
        return Err(RelationError("membership protocol must be TB-v0.9"));
    }
    if w.terminal_committed != 1 {
        return Err(RelationError("terminal committed must be one"));
    }
    validate_identifier(&w.session_id)?;
    if w.tree_depth != tree_depth_for_count(w.row_count)? {
        return Err(RelationError("tree depth is not minimal for row count"));
    }
    if w.siblings_blake3.len() != usize::from(w.tree_depth) {
        return Err(RelationError("sibling count differs from tree depth"));
    }
    Ok(())
}

impl MembershipWitness {
    pub fn parse(bytes: &[u8]) -> Result<Self> {
        if bytes.len() < PRIVATE_FIXED_BYTES {
            return Err(RelationError("membership witness is shorter than fixed header"));
        }
        if &bytes[0..8] != PRIVATE_MAGIC {
            return Err(RelationError("membership witness magic differs"));
        }
        if bytes[8] != PRIVATE_ABI_VERSION {
            return Err(RelationError("membership private ABI version differs"));
        }
        if bytes[11] != 0 {
            return Err(RelationError("membership reserved byte must be zero"));
        }
        let declared_length = u32::from_le_bytes(bytes[12..16].try_into().expect("fixed length")) as usize;
        let session_length = u16::from_le_bytes(bytes[16..18].try_into().expect("fixed session length")) as usize;
        let tree_depth = u16::from_le_bytes(bytes[18..20].try_into().expect("fixed depth"));
        if session_length == 0 || session_length > SESSION_ID_MAX_BYTES {
            return Err(RelationError("session identifier length is outside 1..128"));
        }
        if usize::from(tree_depth) > MAX_TREE_DEPTH {
            return Err(RelationError("tree depth exceeds ABI ceiling"));
        }
        let expected_length = PRIVATE_FIXED_BYTES + session_length + usize::from(tree_depth) * 32;
        if bytes.len() != expected_length || declared_length != expected_length {
            return Err(RelationError("membership witness length differs"));
        }
        let siblings_start = PRIVATE_FIXED_BYTES + session_length;
        let witness = Self {
            protocol_code: bytes[9],
            terminal_committed: bytes[10],
            tree_depth,
            row_count: u32::from_le_bytes(bytes[20..24].try_into().expect("fixed row count")),
            s_0: exact_32(&bytes[24..56]),
            s_n: exact_32(&bytes[56..88]),
            authority_manifest_sha256: exact_32(&bytes[88..120]),
            chain_log_blake3: exact_32(&bytes[120..152]),
            ordered_session_root_blake3: exact_32(&bytes[152..184]),
            session_id: bytes[184..184 + session_length].to_vec(),
            siblings_blake3: bytes[siblings_start..].chunks_exact(32).map(exact_32).collect(),
        };
        validate_witness_shape(&witness)?;
        Ok(witness)
    }

    pub fn encode(&self) -> Result<Vec<u8>> {
        validate_witness_shape(self)?;
        let total = PRIVATE_FIXED_BYTES + self.session_id.len() + self.siblings_blake3.len() * 32;
        let mut b = Vec::with_capacity(total);
        b.extend_from_slice(PRIVATE_MAGIC);
        b.push(PRIVATE_ABI_VERSION);
        b.push(self.protocol_code);
        b.push(self.terminal_committed);
        b.push(0);
        b.extend_from_slice(&(total as u32).to_le_bytes());
        b.extend_from_slice(&(self.session_id.len() as u16).to_le_bytes());
        b.extend_from_slice(&self.tree_depth.to_le_bytes());
        b.extend_from_slice(&self.row_count.to_le_bytes());
        b.extend_from_slice(&self.s_0);
        b.extend_from_slice(&self.s_n);
        b.extend_from_slice(&self.authority_manifest_sha256);
        b.extend_from_slice(&self.chain_log_blake3);
        b.extend_from_slice(&self.ordered_session_root_blake3);
        b.extend_from_slice(&self.session_id);
        for s in &self.siblings_blake3 {
            b.extend_from_slice(s);
        }
        assert_eq!(b.len(), total);
        Ok(b)
    }

    /// `H(CONTEXT, [b"TB-v0.9", session_id, u32be(rows), [terminal], s_0, s_n, manifest_sha256, chain_log_blake3])`.
    pub fn context_digest(&self) -> Result<[u8; 32]> {
        validate_witness_shape(self)?;
        let protocol = match self.protocol_code {
            PROTOCOL_V9_CODE => b"TB-v0.9".as_slice(),
            _ => return Err(RelationError("membership protocol must be TB-v0.9")),
        };
        let row_count = self.row_count.to_be_bytes();
        let terminal = [self.terminal_committed];
        Ok(domain_hash(
            CONTEXT_DOMAIN,
            &[
                protocol,
                &self.session_id,
                &row_count,
                &terminal,
                &self.s_0,
                &self.s_n,
                &self.authority_manifest_sha256,
                &self.chain_log_blake3,
            ],
        ))
    }
}

/// `H(ROW, [context, u32be(row), s_t, raw_blake3, meta, u64be(round), value, s_next, emission_blake3])`.
pub fn row_leaf_hash(context: &[u8; 32], leaf: &LeafFields) -> [u8; 32] {
    let row_index = leaf.row_index.to_be_bytes();
    let round = leaf.drand_round.to_be_bytes();
    domain_hash(
        ROW_DOMAIN,
        &[
            context,
            &row_index,
            &leaf.s_t,
            &leaf.raw_blake3,
            &leaf.meta,
            &round,
            &leaf.drand_value,
            &leaf.s_next,
            &leaf.emission_blake3,
        ],
    )
}

pub fn node_hash(context: &[u8; 32], level: u16, parent_index: u32, left: &[u8; 32], right: &[u8; 32]) -> [u8; 32] {
    let level = level.to_be_bytes();
    let parent_index = parent_index.to_be_bytes();
    domain_hash(NODE_DOMAIN, &[context, &level, &parent_index, left, right])
}

pub fn wrapped_root_hash(context: &[u8; 32], row_count: u32, tree_depth: u16, internal_root: &[u8; 32]) -> [u8; 32] {
    let row_count = row_count.to_be_bytes();
    let tree_depth = tree_depth.to_be_bytes();
    domain_hash(ROOT_DOMAIN, &[context, &row_count, &tree_depth, internal_root])
}

/// Walk a leaf up its sibling path (membership lib.rs 393-404) and wrap: returns the wrapped root the path yields.
pub fn open_to_wrapped_root(
    context: &[u8; 32],
    row_count: u32,
    tree_depth: u16,
    leaf: &[u8; 32],
    row_index: u32,
    siblings: &[[u8; 32]],
) -> Result<[u8; 32]> {
    if siblings.len() != usize::from(tree_depth) {
        return Err(RelationError("sibling count differs from tree depth"));
    }
    if row_index >= row_count {
        return Err(RelationError("row index is outside committed session"));
    }
    let mut current = *leaf;
    let mut position = row_index;
    for (zero_level, sibling) in siblings.iter().enumerate() {
        let parent_index = position / 2;
        let level = u16::try_from(zero_level + 1).expect("tree depth exceeds u16");
        current = if position & 1 == 1 {
            node_hash(context, level, parent_index, sibling, &current)
        } else {
            node_hash(context, level, parent_index, &current, sibling)
        };
        position = parent_index;
    }
    Ok(wrapped_root_hash(context, row_count, tree_depth, &current))
}

/// The two-row opening the diffusion statement needs: both leaves must open to the committed root.
pub fn verify_two_leaves(
    witness: &MembershipWitness,
    leaf_r: &LeafFields,
    leaf_u: &LeafFields,
    siblings_u: &[[u8; 32]],
) -> Result<([u8; 32], [u8; 32], [u8; 32])> {
    let context = witness.context_digest()?;
    let lr = row_leaf_hash(&context, leaf_r);
    let lu = row_leaf_hash(&context, leaf_u);
    let root_r = open_to_wrapped_root(&context, witness.row_count, witness.tree_depth, &lr, leaf_r.row_index, &witness.siblings_blake3)?;
    if root_r != witness.ordered_session_root_blake3 {
        return Err(RelationError("proved row does not open to the committed ordered-session root"));
    }
    let root_u = open_to_wrapped_root(&context, witness.row_count, witness.tree_depth, &lu, leaf_u.row_index, siblings_u)?;
    if root_u != witness.ordered_session_root_blake3 {
        return Err(RelationError("declared wrong row does not open to the committed ordered-session root"));
    }
    Ok((context, lr, lu))
}

// ------------------------------------------------------------------ tree construction (host side)

/// Padding leaves for the incomplete last level, the Python golden's rule
/// (`ordered_session_opening_candidate.py`, restated in the proved `session_tree.py` lines 12-14 and 87-89):
/// `H(PADDING, [context, u32be(row_count), u32be(index)])` for every index in `row_count..2^depth`. The proved
/// Rust only verifies sibling paths; this builder reproduces the frozen August row-96 siblings (tests).
pub const PADDING_DOMAIN: &[u8] = b"ZEEBEAM_ORDERED_SESSION_PADDING_V1\0";

pub fn padding_leaf_hash(context: &[u8; 32], row_count: u32, index: u32) -> [u8; 32] {
    let row_count = row_count.to_be_bytes();
    let index = index.to_be_bytes();
    domain_hash(PADDING_DOMAIN, &[context, &row_count, &index])
}

/// All levels of the ordered-session tree: `layers[0]` are the `2^depth` leaves (padded), `layers[depth]` the
/// single internal root.
pub struct TreeLayers {
    pub depth: u16,
    pub row_count: u32,
    pub layers: Vec<Vec<[u8; 32]>>,
}

impl TreeLayers {
    pub fn build(context: &[u8; 32], leaves: &[[u8; 32]]) -> Result<Self> {
        let row_count = u32::try_from(leaves.len()).map_err(|_| RelationError("too many leaves"))?;
        let depth = tree_depth_for_count(row_count)?;
        let width = 1_usize << depth;
        let mut layer: Vec<[u8; 32]> = leaves.to_vec();
        for index in leaves.len()..width {
            layer.push(padding_leaf_hash(context, row_count, index as u32));
        }
        let mut layers = vec![layer];
        for level in 1..=depth {
            let below = &layers[usize::from(level) - 1];
            let mut next = Vec::with_capacity(below.len() / 2);
            for parent in 0..below.len() / 2 {
                next.push(node_hash(context, level, parent as u32, &below[2 * parent], &below[2 * parent + 1]));
            }
            layers.push(next);
        }
        debug_assert_eq!(layers[usize::from(depth)].len(), 1);
        Ok(Self { depth, row_count, layers })
    }

    pub fn internal_root(&self) -> [u8; 32] {
        self.layers[usize::from(self.depth)][0]
    }

    pub fn wrapped_root(&self, context: &[u8; 32]) -> [u8; 32] {
        wrapped_root_hash(context, self.row_count, self.depth, &self.internal_root())
    }

    /// The sibling path of leaf `index`, leaf level first.
    pub fn siblings(&self, index: u32) -> Vec<[u8; 32]> {
        let mut out = Vec::with_capacity(usize::from(self.depth));
        let mut pos = index as usize;
        for level in 0..usize::from(self.depth) {
            out.push(self.layers[level][pos ^ 1]);
            pos /= 2;
        }
        out
    }
}

/// The witnessed fields of the declared wrong row, `ZBDLFU01` (208 bytes):
/// magic 8 | row u32 LE | S_u 32 | raw_blake3_u 32 | meta_u 28 | round_u u64 LE | value_u 32 | S_{u+1} 32 | emission_blake3_u 32.
pub const LEAF_U_MAGIC: &[u8; 8] = b"ZBDLFU01";
pub const LEAF_U_BYTES: usize = 208;

pub fn parse_leaf_u(bytes: &[u8]) -> Result<LeafFields> {
    if bytes.len() != LEAF_U_BYTES {
        return Err(RelationError("wrong-row leaf witness must be exactly 208 bytes"));
    }
    if &bytes[0..8] != LEAF_U_MAGIC {
        return Err(RelationError("wrong-row leaf witness magic differs"));
    }
    let row_index = u32::from_le_bytes(bytes[8..12].try_into().unwrap());
    let meta: [u8; 28] = bytes[76..104].try_into().unwrap();
    if u32::from_be_bytes(meta[0..4].try_into().unwrap()) != row_index {
        return Err(RelationError("wrong-row metadata row index differs from its leaf row index"));
    }
    Ok(LeafFields {
        row_index,
        s_t: exact_32(&bytes[12..44]),
        raw_blake3: exact_32(&bytes[44..76]),
        meta,
        drand_round: u64::from_le_bytes(bytes[104..112].try_into().unwrap()),
        drand_value: exact_32(&bytes[112..144]),
        s_next: exact_32(&bytes[144..176]),
        emission_blake3: exact_32(&bytes[176..208]),
    })
}

pub fn encode_leaf_u(leaf: &LeafFields) -> Vec<u8> {
    let mut b = Vec::with_capacity(LEAF_U_BYTES);
    b.extend_from_slice(LEAF_U_MAGIC);
    b.extend_from_slice(&leaf.row_index.to_le_bytes());
    b.extend_from_slice(&leaf.s_t);
    b.extend_from_slice(&leaf.raw_blake3);
    b.extend_from_slice(&leaf.meta);
    b.extend_from_slice(&leaf.drand_round.to_le_bytes());
    b.extend_from_slice(&leaf.drand_value);
    b.extend_from_slice(&leaf.s_next);
    b.extend_from_slice(&leaf.emission_blake3);
    b
}

/// A concatenation of 32-byte siblings.
pub fn parse_siblings(bytes: &[u8]) -> Result<Vec<[u8; 32]>> {
    if bytes.len() % 32 != 0 {
        return Err(RelationError("sibling list is not a multiple of 32 bytes"));
    }
    Ok(bytes.chunks_exact(32).map(exact_32).collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::header::{unhex, unhex32};

    // native/src/lib.rs of the proved membership tree: the frozen August row-96 fixture.
    pub const SESSION_ID: &[u8] = b"ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001";
    const S_0: &str = "74e3a131e1aaadd98e18c5f2a5f28ffaf59b8cd738e10216586efa2a893f384c";
    const S_N: &str = "aeea9f4d6a55ebecd900eae187ea70dce05696551f96ae976c9a5243b3a4398e";
    const MANIFEST: &str = "740d752d27b70cb63c9501a470562a52616f4a445a7a9c0fb300844f61c7d783";
    const CHAIN_LOG: &str = "754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b";
    const CONTEXT: &str = "f5eba65f4a3604bee08207b4af571b97813cbd4dd3f919c110f6c5125ab21ee0";
    const LEAF96: &str = "2e4e76aa9bfece295ce728ad12e37d1cc40fddfd190fa6012116cb88969f4f8b";
    const INTERNAL: &str = "1d43309ef9a0e2fc6dba98846134280b98cda01840d2204dc41100d5038d3b37";
    const ROOT: &str = "38a484b8793f3afadaf8fc5ba1c04d47e08cdbb4c07a39da09fb4149499a6572";
    const SIBLINGS: [&str; 10] = [
        "5044e45b95bb454f818d7c6053cd017c88eb63167e00553ffca90fc4db105ea7",
        "dbf38b9f009639960bb19bb34a49723b86f8dab1124e9957838c53ded27e5f14",
        "e8b97d9ae3e24d60685b5c48137e35173b22951e8338cc785470555bc110025f",
        "25d45e7302f4b9c1785ca604a4ac9d819a920eb76de51e947d2431dd8ee65913",
        "62be39eb75e5d08eb05003a92da6c99949ada732bee04fc1d23963562320747c",
        "881655aed30915bf6e5779e36c284b96ab57e679c935b067d441b6080a4b9cf8",
        "9cf816f0e5cec6347a00959af7a661b7ed783fea126aa75479d5168826683f86",
        "22e5c272ed13d3b3dede9638ea3f8519fbd9a3e90c22014c9fe0c2089e64d5d0",
        "583b3de49e15a665d6aeeaccc7af17165a58fc75a42dea3f6da873f321dadf59",
        "626eacc9816d13823066712b6b8953580e0383460da0ffa0b4a5775501872240",
    ];
    // row_binding_join_sp1_candidate/native/src/lib.rs: row 96's fields
    const S_T: &str = "9ebaec46e2e4924c1a628ce67c482f49ff48b4972c0619f972443888c881584e";
    const S_NEXT: &str = "fd45348cc15fd1badd65d03b65d8db92bc0a236010c7c7a800b89f34a6567f7e";
    const META: &str = "000000600000074d1edaba52000050cb876e1d4d0000fa0052473038";
    const RAW_BLAKE3: &str = "c6535a541172deb06d2f8f208a63c760e8c9340e5ec9dea8d70679d4ec12badd";
    const EMISSION_BLAKE3: &str = "5e4a0bc9f4790b843d91185736b916042f5cac794a5d8c31662a2cd601a4bfa8";
    const DRAND_VALUE: &str = "65775d2f4063482fe05f1889939b7822407b395deb6a94dfc4236ef80f10f313";

    pub fn august_witness() -> MembershipWitness {
        MembershipWitness {
            protocol_code: PROTOCOL_V9_CODE,
            terminal_committed: 1,
            tree_depth: 10,
            row_count: 712,
            session_id: SESSION_ID.to_vec(),
            s_0: unhex32(S_0),
            s_n: unhex32(S_N),
            authority_manifest_sha256: unhex32(MANIFEST),
            chain_log_blake3: unhex32(CHAIN_LOG),
            ordered_session_root_blake3: unhex32(ROOT),
            siblings_blake3: SIBLINGS.iter().map(|s| unhex32(s)).collect(),
        }
    }

    pub fn row96() -> LeafFields {
        LeafFields {
            row_index: 96,
            s_t: unhex32(S_T),
            raw_blake3: unhex32(RAW_BLAKE3),
            meta: unhex(META).try_into().unwrap(),
            drand_round: 31_521_620,
            drand_value: unhex32(DRAND_VALUE),
            s_next: unhex32(S_NEXT),
            emission_blake3: unhex32(EMISSION_BLAKE3),
        }
    }

    #[test]
    fn frozen_row96_constants_reproduce() {
        let w = august_witness();
        let ctx = w.context_digest().unwrap();
        assert_eq!(ctx, unhex32(CONTEXT));
        let leaf = row_leaf_hash(&ctx, &row96());
        assert_eq!(leaf, unhex32(LEAF96));
        // internal root: walk without the wrap
        let mut current = leaf;
        let mut position = 96_u32;
        for (zero_level, sibling) in w.siblings_blake3.iter().enumerate() {
            let parent = position / 2;
            current = if position & 1 == 1 {
                node_hash(&ctx, (zero_level + 1) as u16, parent, sibling, &current)
            } else {
                node_hash(&ctx, (zero_level + 1) as u16, parent, &current, sibling)
            };
            position = parent;
        }
        assert_eq!(current, unhex32(INTERNAL));
        assert_eq!(wrapped_root_hash(&ctx, 712, 10, &current), unhex32(ROOT));
        assert_eq!(open_to_wrapped_root(&ctx, 712, 10, &leaf, 96, &w.siblings_blake3).unwrap(), unhex32(ROOT));
    }

    #[test]
    fn witness_round_trips_and_mutations_fail_closed() {
        let w = august_witness();
        let enc = w.encode().unwrap();
        assert_eq!(enc.len(), 184 + SESSION_ID.len() + 320);
        assert_eq!(MembershipWitness::parse(&enc).unwrap(), w);
        for i in [0_usize, 8, 9, 10, 11, 12, 16, 18] {
            let mut c = enc.clone();
            c[i] ^= 1;
            assert!(MembershipWitness::parse(&c).is_err(), "byte {i}");
        }
        let ctx = w.context_digest().unwrap();
        let leaf = row_leaf_hash(&ctx, &row96());
        let mut wrong = w.clone();
        wrong.siblings_blake3[3][0] ^= 1;
        assert_ne!(open_to_wrapped_root(&ctx, 712, 10, &leaf, 96, &wrong.siblings_blake3).unwrap(), unhex32(ROOT));
        assert_ne!(open_to_wrapped_root(&ctx, 712, 10, &leaf, 97, &w.siblings_blake3).unwrap(), unhex32(ROOT));
        let mut other = row96();
        other.emission_blake3[0] ^= 1;
        assert_ne!(row_leaf_hash(&ctx, &other), leaf);
        assert!(open_to_wrapped_root(&ctx, 712, 10, &leaf, 712, &w.siblings_blake3).is_err());
    }

    #[test]
    fn leaf_u_encoding_round_trips() {
        let l = row96();
        let enc = encode_leaf_u(&l);
        assert_eq!(enc.len(), LEAF_U_BYTES);
        assert_eq!(parse_leaf_u(&enc).unwrap(), l);
        let mut bad = enc.clone();
        bad[8] ^= 1; // row index no longer matches meta
        assert!(parse_leaf_u(&bad).is_err());
    }
}
