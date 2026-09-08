//! Host-side session handling for the batch driver: the chain log, the session profile (the August constants of
//! the proved native oracle by default, or a JSON profile), the ordered-session tree, and the assembly of the
//! nine-item witness for any row and declared offset.

use std::path::Path;

use armc_relation::b3xof::{self, blake3p};
use armc_relation::header::{unhex, unhex32, RowWitnessHeader};
use armc_relation::membership::{encode_leaf_u, row_leaf_hash, LeafFields, MembershipWitness, TreeLayers};
use armc_relation::statement::{PreviousRecord, Witness, OFFSET_RULE_DIRECT, OFFSET_RULE_MIRRORED};

/// A row of `chain_log.csv` (columns as recorded by the v9 recorder; `drand_signature_hex` exists for the August
/// session and is absent for d2/v10).
#[derive(Clone, Debug)]
pub struct ChainRow {
    pub t: u32,
    pub s_t: [u8; 32],
    pub bayer_blake3: [u8; 32],
    pub meta: [u8; 28],
    pub drand_round: u64,
    pub drand_value: [u8; 32],
    pub drand_signature: Option<[u8; 48]>,
    pub emission_blake3: [u8; 32],
}

pub struct ChainLog {
    pub bytes_blake3: [u8; 32],
    pub rows: Vec<ChainRow>,
}

impl ChainLog {
    pub fn parse(bytes: &[u8]) -> Result<Self, String> {
        let bytes_blake3 = blake3p::hash(bytes);
        let text = std::str::from_utf8(bytes).map_err(|e| format!("chain log is not UTF-8: {e}"))?;
        let mut lines = text.lines().filter(|l| !l.starts_with('#'));
        let header: Vec<&str> = lines.next().ok_or("empty chain log")?.split(',').collect();
        let col = |name: &str| header.iter().position(|h| *h == name).ok_or_else(|| format!("chain log lacks column {name}"));
        let (c_t, c_s, c_b, c_m, c_r, c_v, c_e) = (
            col("t")?,
            col("S_t_hex")?,
            col("bayer_blake3_hex")?,
            col("meta_hex")?,
            col("drand_round_number")?,
            col("drand_round_value_hex")?,
            col("emission_live_pixel_blake3_hex")?,
        );
        let c_sig = header.iter().position(|h| *h == "drand_signature_hex");
        let mut rows = Vec::new();
        for (i, line) in lines.enumerate() {
            let f: Vec<&str> = line.split(',').collect();
            let t: u32 = f[c_t].parse().map_err(|_| format!("row {i}: t is not an integer"))?;
            if t as usize != i {
                return Err(format!("chain log row {i} carries t = {t}"));
            }
            rows.push(ChainRow {
                t,
                s_t: unhex32(f[c_s]),
                bayer_blake3: unhex32(f[c_b]),
                meta: unhex(f[c_m]).try_into().map_err(|_| format!("row {i}: meta is not 28 bytes"))?,
                drand_round: f[c_r].parse().map_err(|_| format!("row {i}: round is not an integer"))?,
                drand_value: unhex32(f[c_v]),
                drand_signature: c_sig.map(|c| unhex(f[c]).try_into().expect("48-byte signature")),
                emission_blake3: unhex32(f[c_e]),
            });
        }
        Ok(Self { bytes_blake3, rows })
    }
}

/// The session context fields the tree is built under.
#[derive(Clone, Debug)]
pub struct SessionProfile {
    pub name: String,
    pub session_id: Vec<u8>,
    pub row_count: u32,
    pub s_0: [u8; 32],
    pub s_n: [u8; 32],
    pub authority_manifest_sha256: [u8; 32],
    pub chain_log_blake3: [u8; 32],
    /// The committed root, when known independently (the frozen August root); the builder must reproduce it.
    pub expected_root: Option<[u8; 32]>,
}

impl SessionProfile {
    /// The August session, constants from the proved native oracle (row_binding_join_membership native/src/lib.rs).
    pub fn august() -> Self {
        Self {
            name: "august_dev_712".into(),
            session_id: b"ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001".to_vec(),
            row_count: 712,
            s_0: unhex32("74e3a131e1aaadd98e18c5f2a5f28ffaf59b8cd738e10216586efa2a893f384c"),
            s_n: unhex32("aeea9f4d6a55ebecd900eae187ea70dce05696551f96ae976c9a5243b3a4398e"),
            authority_manifest_sha256: unhex32("740d752d27b70cb63c9501a470562a52616f4a445a7a9c0fb300844f61c7d783"),
            chain_log_blake3: unhex32("754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b"),
            expected_root: Some(unhex32("38a484b8793f3afadaf8fc5ba1c04d47e08cdbb4c07a39da09fb4149499a6572")),
        }
    }

    /// `{"name","session_id","row_count","s_0","s_n","authority_manifest_sha256","chain_log_blake3","expected_root"?}`.
    pub fn from_json(path: &Path) -> Result<Self, String> {
        let j: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;
        let s = |k: &str| j[k].as_str().ok_or_else(|| format!("session profile lacks {k}")).map(|v| v.to_string());
        Ok(Self {
            name: s("name")?,
            session_id: s("session_id")?.into_bytes(),
            row_count: j["row_count"].as_u64().ok_or("session profile lacks row_count")? as u32,
            s_0: unhex32(&s("s_0")?),
            s_n: unhex32(&s("s_n")?),
            authority_manifest_sha256: unhex32(&s("authority_manifest_sha256")?),
            chain_log_blake3: unhex32(&s("chain_log_blake3")?),
            expected_root: j["expected_root"].as_str().map(unhex32),
        })
    }
}

/// The session as the host holds it: parsed log, context, all leaves, the tree.
pub struct Session {
    pub profile: SessionProfile,
    pub log: ChainLog,
    pub context: [u8; 32],
    pub leaves: Vec<[u8; 32]>,
    pub tree: TreeLayers,
    pub root: [u8; 32],
}

impl Session {
    pub fn load(profile: SessionProfile, chain_log_bytes: &[u8]) -> Result<Self, String> {
        let log = ChainLog::parse(chain_log_bytes)?;
        if log.bytes_blake3 != profile.chain_log_blake3 {
            return Err("chain log BLAKE3 differs from the session profile".into());
        }
        if log.rows.len() != profile.row_count as usize {
            return Err(format!("chain log has {} rows, profile says {}", log.rows.len(), profile.row_count));
        }
        if log.rows[0].s_t != profile.s_0 {
            return Err("chain log row 0 state differs from the profile's S_0".into());
        }
        let membership = MembershipWitness {
            protocol_code: 9,
            terminal_committed: 1,
            tree_depth: armc_relation::membership::tree_depth_for_count(profile.row_count).map_err(|e| e.to_string())?,
            row_count: profile.row_count,
            session_id: profile.session_id.clone(),
            s_0: profile.s_0,
            s_n: profile.s_n,
            authority_manifest_sha256: profile.authority_manifest_sha256,
            chain_log_blake3: profile.chain_log_blake3,
            ordered_session_root_blake3: [0; 32],
            siblings_blake3: Vec::new(),
        };
        // context_digest validates the shape but not the root; build with an empty sibling list of the right length
        let mut shaped = membership.clone();
        shaped.siblings_blake3 = vec![[0; 32]; usize::from(membership.tree_depth)];
        let context = shaped.context_digest().map_err(|e| e.to_string())?;
        let leaves: Vec<[u8; 32]> = log.rows.iter().map(|r| row_leaf_hash(&context, &Self::leaf_fields_of(&log, &profile, r.t))).collect();
        let tree = TreeLayers::build(&context, &leaves).map_err(|e| e.to_string())?;
        let root = tree.wrapped_root(&context);
        if let Some(expected) = profile.expected_root {
            if root != expected {
                return Err("rebuilt ordered-session root differs from the profile's committed root".into());
            }
        }
        Ok(Self { profile, log, context, leaves, tree, root })
    }

    fn leaf_fields_of(log: &ChainLog, profile: &SessionProfile, t: u32) -> LeafFields {
        let r = &log.rows[t as usize];
        let s_next = if (t as usize) + 1 < log.rows.len() { log.rows[t as usize + 1].s_t } else { profile.s_n };
        LeafFields {
            row_index: t,
            s_t: r.s_t,
            raw_blake3: r.bayer_blake3,
            meta: r.meta,
            drand_round: r.drand_round,
            drand_value: r.drand_value,
            s_next,
            emission_blake3: r.emission_blake3,
        }
    }

    pub fn leaf_fields(&self, t: u32) -> LeafFields {
        Self::leaf_fields_of(&self.log, &self.profile, t)
    }

    pub fn membership_witness(&self, t: u32) -> MembershipWitness {
        MembershipWitness {
            protocol_code: 9,
            terminal_committed: 1,
            tree_depth: self.tree.depth,
            row_count: self.profile.row_count,
            session_id: self.profile.session_id.clone(),
            s_0: self.profile.s_0,
            s_n: self.profile.s_n,
            authority_manifest_sha256: self.profile.authority_manifest_sha256,
            chain_log_blake3: self.profile.chain_log_blake3,
            ordered_session_root_blake3: self.root,
            siblings_blake3: self.tree.siblings(t),
        }
    }

    /// The ten witness items for proved row `r`, declared offset `d` (`u = r + d`) and offset-rule flag. `raw` and
    /// `noise` may be empty when only the frame-independent items are wanted (prepare mode).
    pub fn assemble(&self, r: u32, d: i32, mirrored: bool, raw: Vec<u8>, noise: Vec<u8>) -> Result<Witness, String> {
        let n = self.profile.row_count as i64;
        if r == 0 || r as i64 >= n {
            return Err(format!("row {r} is outside 1..{n}"));
        }
        let u = r as i64 + d as i64;
        if u < 0 || u >= n {
            return Err(format!("row {r} offset {d}: wrong row {u} is outside the session"));
        }
        if mirrored {
            let direct = r as i64 - d as i64;
            if direct >= 0 && direct < n {
                return Err(format!("row {r} offset {d}: mirrored flag set although the direct wrong row {direct} is inside the session"));
            }
        }
        let row = &self.log.rows[r as usize];
        let prev = &self.log.rows[r as usize - 1];
        let sig_r = row.drand_signature.ok_or("chain log has no drand signature for the proved row")?;
        let sig_prev = prev.drand_signature.ok_or("chain log has no drand signature for the previous row")?;
        let header = RowWitnessHeader { row_index: r, s_t: row.s_t, meta: row.meta, drand_round: row.drand_round, drand_value: row.drand_value }
            .encode()
            .map_err(|e| e.to_string())?;
        let previous = PreviousRecord {
            s_t: prev.s_t,
            raw_blake3: prev.bayer_blake3,
            meta: prev.meta,
            drand_round: prev.drand_round,
            drand_value: prev.drand_value,
            signature: sig_prev,
        };
        let leaf_u = self.leaf_fields(u as u32);
        let siblings_u: Vec<u8> = self.tree.siblings(u as u32).iter().flat_map(|s| s.iter().copied()).collect();
        Ok(Witness {
            header: header.to_vec(),
            membership: self.membership_witness(r).encode().map_err(|e| e.to_string())?,
            raw,
            signature: sig_r.to_vec(),
            previous: previous.encode(),
            leaf_u: encode_leaf_u(&leaf_u),
            siblings_u,
            noise,
            offset: d.to_le_bytes().to_vec(),
            offset_rule: vec![if mirrored { OFFSET_RULE_MIRRORED } else { OFFSET_RULE_DIRECT }],
        })
    }

    /// Write the frame-independent items of a witness into `dir` in the layout `witness::build` reads.
    pub fn write_witness_files(dir: &Path, w: &Witness) -> Result<(), String> {
        std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
        for (name, bytes) in [
            ("header_r.bin", &w.header),
            ("membership_r_zbosm001.bin", &w.membership),
            ("sig_r.bin", &w.signature),
            ("prev_zbdprv01.bin", &w.previous),
            ("leaf_u_zbdlfu01.bin", &w.leaf_u),
            ("siblings_u.bin", &w.siblings_u),
            ("offset.bin", &w.offset),
            ("offset_rule.bin", &w.offset_rule),
        ] {
            std::fs::write(dir.join(name), bytes).map_err(|e| format!("{name}: {e}"))?;
        }
        if !w.noise.is_empty() {
            std::fs::write(dir.join("noise_q12.bin"), &w.noise).map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    /// Frame-independent checks of one row's witness: beacons r and r-1 verify and bind, both patterns render to
    /// the chain log's digests, both leaves (with the chain log's raw digest for r) open to the root, and the
    /// previous advance yields S_r. Returns notes.
    pub fn prepare_checks(&self, r: u32, d: i32) -> Result<Vec<String>, String> {
        let n = self.profile.row_count as i64;
        if r == 0 || r as i64 >= n {
            return Err(format!("row {r} is outside 1..{n}"));
        }
        let u64_ = r as i64 + d as i64;
        if u64_ < 0 || u64_ >= n {
            return Err(format!("wrong row {u64_} is outside the session (protocol boundary rule: absent, never imputed)"));
        }
        let u = u64_ as u32;
        let row = &self.log.rows[r as usize];
        let prev = &self.log.rows[r as usize - 1];
        let mut notes = Vec::new();
        armc_relation::beacon::verify_and_bind(row.drand_round, &row.drand_signature.ok_or("no signature")?, &row.drand_value).map_err(|e| format!("beacon r: {e}"))?;
        armc_relation::beacon::verify_and_bind(prev.drand_round, &prev.drand_signature.ok_or("no signature")?, &prev.drand_value).map_err(|e| format!("beacon r-1: {e}"))?;
        notes.push(format!("beacons {} and {} verify and bind", prev.drand_round, row.drand_round));
        let recomputed = b3xof::advance_chain(&prev.s_t, &prev.bayer_blake3, &prev.meta, prev.drand_round, &prev.drand_value);
        if recomputed != row.s_t {
            return Err("previous advance does not yield S_r".into());
        }
        let (_, em_r) = armc_relation::emission::expand_and_digest(&row.s_t);
        if em_r != row.emission_blake3 {
            return Err("render of S_r differs from the chain log's emission digest".into());
        }
        let (_, em_u) = armc_relation::emission::expand_and_digest(&self.log.rows[u as usize].s_t);
        if em_u != self.log.rows[u as usize].emission_blake3 {
            return Err("render of S_u differs from the chain log's emission digest".into());
        }
        notes.push("both patterns render to the chain log's digests".into());
        let (_, lr, lu) = armc_relation::membership::verify_two_leaves(&self.membership_witness(r), &self.leaf_fields(r), &self.leaf_fields(u), &self.tree.siblings(u))
            .map_err(|e| e.to_string())?;
        notes.push(format!("leaf_r {} and leaf_u {} open to the committed root", armc_relation::header::hex(&lr), armc_relation::header::hex(&lu)));
        Ok(notes)
    }
}
