//! Acceptance of one ZBDIFF01 statement (Astra r5 finding 3): beyond "the Groth16 proof verifies", a proof is accepted
//! only if its public bytes carry the EXPECTED identities. The expected identities come from a frozen JSON
//! (`tools/make_expected_identities.py` -> `expected_identities_august.json`), never from whatever ELF, blob or
//! noise file happens to be at hand: a different noise tensor, blob or program produces a valid proof of a
//! DIFFERENT statement, and this module is what refuses it.
//!
//! Layers, each a named check with PASS / FAIL / SKIP and a detail string, in the order they run:
//!
//! 1. circuit identity: `sha256(sp1_verifier::GROTH16_VK_BYTES)` equals the pinned circuit verifier key digest
//!    (the same 492 bytes as `~/.sp1/circuits/groth16/<version>/groth16_vk.bin`);
//! 2. Groth16: `sp1_verifier::Groth16Verifier::verify(proof_bytes, public, expected_vkey, GROTH16_VK_BYTES)` with the
//!    PINNED program vkey string, the verifier's own `VK_ROOT_BYTES` and exit code 0 (standalone, no SP1 prover
//!    setup, no ELF needed);
//! 3. layout: exactly 752 bytes, `PublicOutput::parse` (magic, ABI, protocol, length, zero padding of the session
//!    id, fixed noising constants, `D = R_wrong - R_correct`, denominator 721,554,505,728, sign byte, clip flag /
//!    count consistency, offset rule admissible on its face, `u = r + d`);
//! 4. program identities: denoiser kind 1, constants / network-spec / preprocessing digests;
//! 5. session identities: id, row count 712, tree depth, `S_0`, `S_N`, authority manifest, chain-log BLAKE3,
//!    context digest, ordered-session root;
//! 6. the declared offset rule: `600 <= r <= 711`, `(d, mirror flag, u)` equal `rule::august_assignment(r)` exactly;
//! 7. per-row identities: the frozen normative noise BLAKE3 (G1 `august_inputs/manifest.json` `noise_map`), the
//!    chain log's raw BLAKE3, emission digests and drand rounds of `r` and `u`, the leaves;
//! 8. oracle comparison, when the table carries it: `R_correct` and `R_wrong` equal G1's `expected_residual_sum_int`;
//! 9. outcome class: positive / zero / negative from the signed `D`, published in the receipt (nothing is filtered).
//!
//! Any FAIL is an error: the caller must not print success.

use armc_relation::header::hex;
use armc_relation::noise::{F_CT, F_EPS, NOISE_SHIFT, RESIDUAL_DENOMINATOR, SA_INT, SO_INT, TIMESTEP};
use armc_relation::rule::{august_assignment, AUGUST_RULE_ROW_END_INCLUSIVE, AUGUST_RULE_ROW_START};
use armc_relation::statement::{PublicOutput, OFFSET_RULE_MIRRORED, PUBLIC_BYTES};
use sha2::{Digest, Sha256};

pub const EXPECTED_SCHEMA: &str = "zbdiff-expected-identities/v1";

/// The frozen expected identities (see the module doc for the layout).
pub struct Expected {
    pub json: serde_json::Value,
    pub path: String,
    pub sha256: String,
}

impl Expected {
    pub fn load(path: &std::path::Path) -> Result<Self, String> {
        let bytes = std::fs::read(path).map_err(|e| format!("cannot read expected identities {}: {e}", path.display()))?;
        let json: serde_json::Value = serde_json::from_slice(&bytes).map_err(|e| format!("expected identities {} is not JSON: {e}", path.display()))?;
        if json["schema"].as_str() != Some(EXPECTED_SCHEMA) {
            return Err(format!("expected identities {} carry schema {:?}, want {EXPECTED_SCHEMA}", path.display(), json["schema"]));
        }
        for key in ["sp1_vkey", "groth16_vk_sha256", "sp1_circuit_version", "constants_sha256", "spec_sha256", "preprocess_spec_sha256"] {
            if json[key].as_str().is_none() {
                return Err(format!("expected identities lack {key}"));
            }
        }
        if !json["session"].is_object() || !json["rows"].is_object() {
            return Err("expected identities lack session or rows".into());
        }
        Ok(Self { json, path: path.display().to_string(), sha256: format!("{:x}", Sha256::digest(&bytes)) })
    }

    pub fn str(&self, key: &str) -> &str {
        self.json[key].as_str().unwrap_or("")
    }

    pub fn vkey(&self) -> &str {
        self.str("sp1_vkey")
    }

    pub fn row(&self, r: u32) -> Option<&serde_json::Value> {
        let v = &self.json["rows"][r.to_string()];
        if v.is_object() {
            Some(v)
        } else {
            None
        }
    }
}

#[derive(Clone, Debug)]
pub struct Check {
    pub name: String,
    pub status: &'static str,
    pub detail: String,
}

pub struct Acceptance {
    pub checks: Vec<Check>,
    pub decoded: Option<PublicOutput>,
    pub outcome_class: Option<&'static str>,
    pub public_sha256: String,
    pub proof_sha256: Option<String>,
    pub failed: Option<String>,
}

impl Acceptance {
    pub fn ok(&self) -> bool {
        self.failed.is_none()
    }

    pub fn json(&self) -> serde_json::Value {
        serde_json::json!({
            "accepted": self.ok(),
            "failed_check": self.failed,
            "outcome_class": self.outcome_class,
            "public_values_sha256": self.public_sha256,
            "proof_bytes_sha256": self.proof_sha256,
            "checks": self.checks.iter().map(|c| serde_json::json!({"check": c.name, "status": c.status, "detail": c.detail})).collect::<Vec<_>>(),
        })
    }
}

struct Ledger {
    checks: Vec<Check>,
    failed: Option<String>,
}

impl Ledger {
    fn new() -> Self {
        Self { checks: Vec::new(), failed: None }
    }
    fn pass(&mut self, name: &str, detail: String) {
        self.checks.push(Check { name: name.into(), status: "PASS", detail });
    }
    fn skip(&mut self, name: &str, detail: &str) {
        self.checks.push(Check { name: name.into(), status: "SKIP", detail: detail.into() });
    }
    /// Record a failure; the first failure is the reported one. Returns false so callers can `return`.
    fn fail(&mut self, name: &str, detail: String) -> bool {
        self.checks.push(Check { name: name.into(), status: "FAIL", detail: detail.clone() });
        if self.failed.is_none() {
            self.failed = Some(format!("{name}: {detail}"));
        }
        false
    }
    fn eq_hex(&mut self, name: &str, actual: &[u8], expected: Option<&str>) -> bool {
        match expected {
            None => {
                self.skip(name, "not in the expected-identities table");
                true
            }
            Some(e) => {
                let a = hex(actual);
                if a == e.to_lowercase() {
                    self.pass(name, a);
                    true
                } else {
                    self.fail(name, format!("public {a} != expected {e}"))
                }
            }
        }
    }
    fn eq_u64(&mut self, name: &str, actual: u64, expected: Option<u64>) -> bool {
        match expected {
            None => {
                self.skip(name, "not in the expected-identities table");
                true
            }
            Some(e) if e == actual => {
                self.pass(name, actual.to_string());
                true
            }
            Some(e) => self.fail(name, format!("public {actual} != expected {e}")),
        }
    }
}

/// SHA-256 of the circuit verifier key the pinned `sp1-verifier` embeds (hex).
pub fn embedded_groth16_vk_sha256() -> String {
    format!("{:x}", Sha256::digest(*sp1_verifier::GROTH16_VK_BYTES))
}

pub fn embedded_groth16_vk_bytes() -> usize {
    sp1_verifier::GROTH16_VK_BYTES.len()
}

pub fn vk_root_hex() -> String {
    hex(&*sp1_verifier::VK_ROOT_BYTES)
}

pub fn outcome_class(d: i64) -> &'static str {
    match d.signum() {
        1 => "positive",
        0 => "zero",
        _ => "negative",
    }
}

/// Layers 1 and 2: the standalone Groth16 verification under the PINNED program vkey and circuit key.
pub fn verify_groth16_standalone(proof_bytes: &[u8], public: &[u8], expected_vkey: &str, expected_groth16_vk_sha256: &str) -> Result<(), String> {
    let vk_sha = embedded_groth16_vk_sha256();
    if vk_sha != expected_groth16_vk_sha256.to_lowercase() {
        return Err(format!("embedded circuit verifier key sha256 {vk_sha} != expected {expected_groth16_vk_sha256}"));
    }
    sp1_verifier::Groth16Verifier::verify(proof_bytes, public, expected_vkey, *sp1_verifier::GROTH16_VK_BYTES).map_err(|e| format!("Groth16 verification failed under the pinned keys: {e:?}"))
}

/// Layers 3 to 9 on the public bytes alone (used after the executor, where there is no proof, and inside `accept`).
pub fn accept_public(public: &[u8], exp: &Expected) -> Acceptance {
    let mut l = Ledger::new();
    let public_sha256 = format!("{:x}", Sha256::digest(public));
    let mut out = Acceptance { checks: Vec::new(), decoded: None, outcome_class: None, public_sha256, proof_sha256: None, failed: None };
    if public.len() != PUBLIC_BYTES {
        l.fail("layout.length", format!("{} bytes, want {PUBLIC_BYTES}", public.len()));
        out.checks = l.checks;
        out.failed = l.failed;
        return out;
    }
    let p = match PublicOutput::parse(public) {
        Ok(p) => {
            l.pass("layout.parse", "magic, ABI, protocol, length, session-id padding, fixed noising constants, D, denominator, sign, clip flag, offset rule on its face, u = r + d".into());
            p
        }
        Err(e) => {
            l.fail("layout.parse", e.message().into());
            out.checks = l.checks;
            out.failed = l.failed;
            return out;
        }
    };
    // the fixed constants, spelled out (parse enforced them; the record names them)
    l.pass(
        "layout.fixed_constants",
        format!("timestep {TIMESTEP}, SA {SA_INT}, SO {SO_INT}, shift {NOISE_SHIFT}, F_CT {F_CT}, F_HINT {}, F_EPS {F_EPS}, denominator {RESIDUAL_DENOMINATOR}", armc_relation::hint::F_HINT),
    );
    let d = p.difference();
    if (p.r_wrong as i128 - p.r_correct as i128) as i64 != d || u64::from_le_bytes(public[740..748].try_into().unwrap()) != RESIDUAL_DENOMINATOR || public[748] != u8::from(d > 0) {
        l.fail("layout.difference", "D, denominator or sign byte inconsistent".into());
    } else {
        l.pass("layout.difference", format!("R_correct {} R_wrong {} D {d} sign {} clip_flag {} clip_events {}", p.r_correct, p.r_wrong, public[748], public[749], p.clip_events));
    }
    // program identities
    let kind_expected = exp.json["denoiser_kind"].as_u64().unwrap_or(1);
    if u64::from(p.denoiser_kind) != kind_expected {
        l.fail("program.denoiser_kind", format!("public {} != expected {kind_expected}", p.denoiser_kind));
    } else {
        l.pass("program.denoiser_kind", p.denoiser_kind.to_string());
    }
    l.eq_hex("program.constants_sha256", &p.constants_sha256, Some(exp.str("constants_sha256")));
    l.eq_hex("program.spec_sha256", &p.spec_sha256, Some(exp.str("spec_sha256")));
    l.eq_hex("program.preprocess_spec_sha256", &p.preprocess_spec_sha256, Some(exp.str("preprocess_spec_sha256")));
    // session identities
    let s = &exp.json["session"];
    match s["session_id"].as_str() {
        Some(id) if id.as_bytes() == p.session_id.as_slice() => l.pass("session.id", id.into()),
        Some(id) => {
            l.fail("session.id", format!("public {:?} != expected {id}", String::from_utf8_lossy(&p.session_id)));
        }
        None => l.skip("session.id", "not in the expected-identities table"),
    }
    l.eq_u64("session.row_count", u64::from(p.row_count), s["row_count"].as_u64());
    l.eq_u64("session.tree_depth", u64::from(p.tree_depth), s["tree_depth"].as_u64());
    l.eq_hex("session.s_0", &p.s_0, s["s_0"].as_str());
    l.eq_hex("session.s_n", &p.s_n, s["s_n"].as_str());
    l.eq_hex("session.authority_manifest_sha256", &p.authority_manifest_sha256, s["authority_manifest_sha256"].as_str());
    l.eq_hex("session.chain_log_blake3", &p.chain_log_blake3, s["chain_log_blake3"].as_str());
    l.eq_hex("session.context_digest", &p.context_digest, s["context_digest"].as_str());
    l.eq_hex("session.ordered_session_root", &p.ordered_session_root, s["ordered_session_root"].as_str());
    // the declared offset rule on the public triple
    let rule = &exp.json["rule"];
    let row_start = rule["row_start"].as_u64().unwrap_or(u64::from(AUGUST_RULE_ROW_START)) as u32;
    let row_end = rule["row_end_inclusive"].as_u64().unwrap_or(u64::from(AUGUST_RULE_ROW_END_INCLUSIVE)) as u32;
    if row_start != AUGUST_RULE_ROW_START || row_end != AUGUST_RULE_ROW_END_INCLUSIVE {
        l.fail("rule.range", format!("expected table declares rows {row_start}..={row_end}; this verifier enforces the August rule {AUGUST_RULE_ROW_START}..={AUGUST_RULE_ROW_END_INCLUSIVE}"));
    } else if !(row_start..=row_end).contains(&p.row_r) {
        l.fail("rule.range", format!("row {} is outside {row_start}..={row_end}", p.row_r));
    } else {
        l.pass("rule.range", format!("row {} in {row_start}..={row_end}", p.row_r));
    }
    match august_assignment(p.row_r) {
        Some(a) if a.offset == p.offset && a.mirrored == (p.offset_rule == OFFSET_RULE_MIRRORED) && a.wrong_row == p.row_u => {
            l.pass(
                "rule.assignment",
                format!("row {} base {:+} -> offset {:+} ({}), u = {}", p.row_r, a.base, a.offset, if a.mirrored { "mirrored, byte 11 = 1" } else { "direct, byte 11 = 0" }, a.wrong_row),
            );
        }
        Some(a) => {
            l.fail(
                "rule.assignment",
                format!("public offset {:+} flag {} u {} != rule offset {:+} flag {} u {} for row {}", p.offset, p.offset_rule, p.row_u, a.offset, u8::from(a.mirrored), a.wrong_row, p.row_r),
            );
        }
        None => {
            l.fail("rule.assignment", format!("row {} has no assignment under the August rule", p.row_r));
        }
    }
    // per-row identities from the frozen table
    match exp.row(p.row_r) {
        None => {
            l.fail("row.table", format!("row {} is not in the expected-identities table", p.row_r));
        }
        Some(row) => {
            l.pass("row.table", format!("row {} present", p.row_r));
            if let Some(w) = row["wrong_row"].as_u64() {
                l.eq_u64("row.wrong_row", u64::from(p.row_u), Some(w));
            }
            if let Some(o) = row["offset"].as_i64() {
                if o != i64::from(p.offset) {
                    l.fail("row.offset", format!("public {:+} != table {o:+}", p.offset));
                } else {
                    l.pass("row.offset", format!("{o:+}"));
                }
            }
            if let Some(f) = row["offset_rule"].as_str() {
                let want = if f == "mirrored" { OFFSET_RULE_MIRRORED } else { 0 };
                if want != p.offset_rule {
                    l.fail("row.offset_rule", format!("public byte 11 = {} != table {f}", p.offset_rule));
                } else {
                    l.pass("row.offset_rule", f.into());
                }
            }
            if row["noise_blake3"].as_str().is_none() {
                l.fail("row.noise_blake3", "the table carries no normative noise BLAKE3 for this row".into());
            } else {
                l.eq_hex("row.noise_blake3", &p.noise_blake3, row["noise_blake3"].as_str());
            }
            l.eq_hex("row.raw_blake3", &p.raw_blake3_r, row["raw_blake3"].as_str());
            l.eq_hex("row.emission_blake3_r", &p.emission_blake3_r, row["emission_blake3_r"].as_str());
            l.eq_hex("row.emission_blake3_u", &p.emission_blake3_u, row["emission_blake3_u"].as_str());
            l.eq_u64("row.own_drand_round", p.own_drand_round, row["own_drand_round"].as_u64());
            l.eq_u64("row.prev_drand_round", p.prev_drand_round, row["prev_drand_round"].as_u64());
            l.eq_hex("row.leaf_r", &p.leaf_r, row["leaf_r"].as_str());
            l.eq_hex("row.leaf_u", &p.leaf_u, row["leaf_u"].as_str());
            // oracle comparison (G1's int16 residual sums for this row and offset)
            let er = &row["expected_residual_int16"];
            if er.is_object() {
                l.eq_u64("oracle.r_correct", p.r_correct, er["correct"].as_u64());
                l.eq_u64("oracle.r_wrong", p.r_wrong, er["wrong"].as_u64());
            } else {
                l.skip("oracle.residuals", "no G1 expected residuals in the table for this row");
            }
        }
    }
    let class = outcome_class(d);
    l.pass("outcome.class", format!("{class} (D = {d}); clip_events {}", p.clip_events));
    out.decoded = Some(p);
    out.outcome_class = Some(class);
    out.checks = l.checks;
    out.failed = l.failed;
    out
}

/// The complete acceptance of a Groth16 proof: circuit identity, standalone Groth16 verification under the pinned
/// program vkey, then every identity check on the public bytes.
pub fn accept(proof_bytes: &[u8], public: &[u8], exp: &Expected) -> Acceptance {
    let mut l = Ledger::new();
    let vk_sha = embedded_groth16_vk_sha256();
    if vk_sha == exp.str("groth16_vk_sha256").to_lowercase() {
        l.pass("circuit.groth16_vk_sha256", format!("{vk_sha} ({} bytes, sp1-verifier {})", embedded_groth16_vk_bytes(), exp.str("sp1_circuit_version")));
    } else {
        l.fail("circuit.groth16_vk_sha256", format!("embedded {vk_sha} != expected {}", exp.str("groth16_vk_sha256")));
    }
    match sp1_verifier::Groth16Verifier::verify(proof_bytes, public, exp.vkey(), *sp1_verifier::GROTH16_VK_BYTES) {
        Ok(()) => l.pass("groth16.verify", format!("standalone sp1-verifier, program vkey {}, vk root {}, exit code 0", exp.vkey(), vk_root_hex())),
        Err(e) => {
            l.fail("groth16.verify", format!("{e:?}"));
        }
    }
    let mut acc = accept_public(public, exp);
    let mut checks = l.checks;
    checks.append(&mut acc.checks);
    acc.checks = checks;
    if l.failed.is_some() {
        acc.failed = l.failed;
    }
    acc.proof_sha256 = Some(format!("{:x}", Sha256::digest(proof_bytes)));
    acc
}

// ------------------------------------------------------------------ proof-level negative controls (Astra r5 finding 10)

fn sha256_hex(b: &[u8]) -> String {
    format!("{:x}", Sha256::digest(b))
}

pub struct Control {
    pub name: String,
    pub layer: &'static str,
    pub mutation: String,
    pub expected_stage: String,
    pub actual: String,
    pub behaved: bool,
    pub artefact_sha256: String,
}

impl Control {
    pub fn json(&self) -> serde_json::Value {
        serde_json::json!({
            "control": self.name, "layer": self.layer, "mutation": self.mutation, "expected_failure_stage": self.expected_stage,
            "actual": self.actual, "behaved_as_expected": self.behaved, "mutated_artefact_sha256": self.artefact_sha256,
        })
    }
}

/// Relation-level proof controls: every mutation must be rejected by the Groth16 verifier under the pinned keys.
pub fn groth16_rejection_controls(proof_bytes: &[u8], public: &[u8], vkey: &str, groth16_vk_sha256: &str) -> Vec<Control> {
    let mut out = Vec::new();
    let mut public_mutations: Vec<(&str, &str, Box<dyn Fn(&mut Vec<u8>)>)> = vec![
        ("public.kind_byte_10", "public byte 10 (denoiser kind) ^= 1", Box::new(|b: &mut Vec<u8>| b[10] ^= 1)),
        ("public.offset_rule_byte_11", "public byte 11 (offset-rule flag) ^= 1", Box::new(|b: &mut Vec<u8>| b[11] ^= 1)),
        ("public.row_u_20", "public u (bytes 20..24) + 1", Box::new(|b: &mut Vec<u8>| {
            let u = u32::from_le_bytes(b[20..24].try_into().unwrap()).wrapping_add(1);
            b[20..24].copy_from_slice(&u.to_le_bytes());
        })),
        ("public.offset_24", "public offset d (bytes 24..28) negated", Box::new(|b: &mut Vec<u8>| {
            let d = i32::from_le_bytes(b[24..28].try_into().unwrap()).wrapping_neg();
            b[24..28].copy_from_slice(&d.to_le_bytes());
        })),
        ("public.constants_sha256_564", "public constants_sha256 byte 564 ^= 1", Box::new(|b: &mut Vec<u8>| b[564] ^= 1)),
        ("public.noise_blake3_660", "public noise BLAKE3 byte 660 ^= 1", Box::new(|b: &mut Vec<u8>| b[660] ^= 1)),
        ("public.r_correct_716", "public R_correct byte 716 ^= 1", Box::new(|b: &mut Vec<u8>| b[716] ^= 1)),
        ("public.clip_count_750", "public clip-event count byte 750 ^= 1 (and flag 749 made consistent)", Box::new(|b: &mut Vec<u8>| {
            b[750] ^= 1;
            b[749] = u8::from(b[750] != 0 || b[751] != 0);
        })),
    ];
    if public.len() < 752 {
        public_mutations.truncate(0);
        public_mutations.push(("public.first_byte", "public byte 0 ^= 1 (non-ZBDIFF layout)", Box::new(|b: &mut Vec<u8>| b[0] ^= 1)));
    }
    for (name, mutation, f) in public_mutations {
        let mut m = public.to_vec();
        f(&mut m);
        let r = verify_groth16_standalone(proof_bytes, &m, vkey, groth16_vk_sha256);
        out.push(Control {
            name: name.into(),
            layer: "relation",
            mutation: mutation.into(),
            expected_stage: "groth16.verify (public-input hash differs)".into(),
            actual: match &r {
                Ok(()) => "ACCEPTED".into(),
                Err(e) => e.clone(),
            },
            behaved: r.is_err(),
            artefact_sha256: sha256_hex(&m),
        });
    }
    // the proof bytes: a byte inside the gnark proof (after the 4-byte key prefix and the 96-byte exit/root/nonce header)
    let mut pm = proof_bytes.to_vec();
    if pm.len() > 4 + 96 + 10 {
        pm[4 + 96 + 10] ^= 1;
        let r = verify_groth16_standalone(&pm, public, vkey, groth16_vk_sha256);
        out.push(Control {
            name: "proof.byte_110".into(),
            layer: "relation",
            mutation: "proof byte 110 (inside the Groth16 proof, after the key prefix and exit/root/nonce header) ^= 1".into(),
            expected_stage: "groth16.verify (pairing check fails)".into(),
            actual: r.as_ref().err().cloned().unwrap_or_else(|| "ACCEPTED".into()),
            behaved: r.is_err(),
            artefact_sha256: sha256_hex(&pm),
        });
    }
    let mut prefix = proof_bytes.to_vec();
    prefix[0] ^= 1;
    let r = verify_groth16_standalone(&prefix, public, vkey, groth16_vk_sha256);
    out.push(Control {
        name: "proof.circuit_key_prefix".into(),
        layer: "relation",
        mutation: "proof byte 0 (circuit verifier key prefix) ^= 1".into(),
        expected_stage: "groth16.verify (Groth16VkeyHashMismatch)".into(),
        actual: r.as_ref().err().cloned().unwrap_or_else(|| "ACCEPTED".into()),
        behaved: r.is_err(),
        artefact_sha256: sha256_hex(&prefix),
    });
    let truncated = &proof_bytes[..proof_bytes.len().saturating_sub(1)];
    let r = verify_groth16_standalone(truncated, public, vkey, groth16_vk_sha256);
    out.push(Control {
        name: "proof.truncated".into(),
        layer: "relation",
        mutation: "proof bytes truncated by one byte".into(),
        expected_stage: "groth16.verify (decode fails)".into(),
        actual: r.as_ref().err().cloned().unwrap_or_else(|| "ACCEPTED".into()),
        behaved: r.is_err(),
        artefact_sha256: sha256_hex(truncated),
    });
    // the program vkey: one nibble of the pinned string changed
    let mut chars: Vec<char> = vkey.chars().collect();
    if chars.len() > 10 {
        chars[10] = if chars[10] == '0' { '1' } else { '0' };
    }
    let wrong_vkey: String = chars.into_iter().collect();
    let r = verify_groth16_standalone(proof_bytes, public, &wrong_vkey, groth16_vk_sha256);
    out.push(Control {
        name: "program.vkey".into(),
        layer: "relation",
        mutation: format!("program vkey nibble 10 changed: {wrong_vkey}"),
        expected_stage: "groth16.verify (vkey public input differs)".into(),
        actual: r.as_ref().err().cloned().unwrap_or_else(|| "ACCEPTED".into()),
        behaved: r.is_err(),
        artefact_sha256: sha256_hex(wrong_vkey.as_bytes()),
    });
    out
}

/// Policy-level controls: the proof verifies, the expected identities are mutated, acceptance must fail at the named check.
pub fn policy_rejection_controls(proof_bytes: &[u8], public: &[u8], exp: &Expected) -> Vec<Control> {
    let mut out = Vec::new();
    let row = accept_public(public, exp).decoded.map(|p| p.row_r);
    let mutations: Vec<(&str, &str, &str, Box<dyn Fn(&mut serde_json::Value)>)> = vec![
        ("expected.constants_sha256", "expected constants_sha256 first hex digit changed", "program.constants_sha256", Box::new(|j: &mut serde_json::Value| flip_hex(&mut j["constants_sha256"]))),
        ("expected.spec_sha256", "expected spec_sha256 first hex digit changed", "program.spec_sha256", Box::new(|j: &mut serde_json::Value| flip_hex(&mut j["spec_sha256"]))),
        ("expected.session_root", "expected ordered_session_root first hex digit changed", "session.ordered_session_root", Box::new(|j: &mut serde_json::Value| flip_hex(&mut j["session"]["ordered_session_root"]))),
        ("expected.row_noise_blake3", "expected normative noise BLAKE3 of this row first hex digit changed", "row.noise_blake3", Box::new(move |j: &mut serde_json::Value| {
            if let Some(r) = row {
                flip_hex(&mut j["rows"][r.to_string()]["noise_blake3"]);
            }
        })),
        ("expected.row_removed", "this row removed from the expected table", "row.table", Box::new(move |j: &mut serde_json::Value| {
            if let Some(r) = row {
                if let Some(rows) = j["rows"].as_object_mut() {
                    rows.remove(&r.to_string());
                }
            }
        })),
        ("expected.row_offset", "expected offset of this row negated in the table (the rule check itself is compiled in and still passes; the table check must catch it)", "row.offset", Box::new(move |j: &mut serde_json::Value| {
            if let Some(r) = row {
                let o = j["rows"][r.to_string()]["offset"].as_i64().unwrap_or(0);
                j["rows"][r.to_string()]["offset"] = serde_json::json!(-o);
            }
        })),
    ];
    for (name, mutation, stage, f) in mutations {
        let mut j = exp.json.clone();
        f(&mut j);
        let mutated = Expected { json: j.clone(), path: format!("{} (mutated: {name})", exp.path), sha256: sha256_hex(j.to_string().as_bytes()) };
        let a = accept(proof_bytes, public, &mutated);
        let groth16_ok = a.checks.iter().any(|c| c.name == "groth16.verify" && c.status == "PASS");
        let failed_at = a.checks.iter().find(|c| c.status == "FAIL").map(|c| c.name.clone()).unwrap_or_else(|| "ACCEPTED".into());
        out.push(Control {
            name: name.into(),
            layer: "policy",
            mutation: mutation.into(),
            expected_stage: format!("{stage} (proof still verifies)"),
            actual: format!("groth16 {}, first failed check {failed_at}: {}", if groth16_ok { "PASS" } else { "FAIL" }, a.failed.clone().unwrap_or_default()),
            behaved: groth16_ok && failed_at == stage,
            artefact_sha256: mutated.sha256.clone(),
        });
    }
    out
}

fn flip_hex(v: &mut serde_json::Value) {
    if let Some(s) = v.as_str() {
        let mut c: Vec<char> = s.chars().collect();
        if let Some(first) = c.first_mut() {
            *first = if *first == '0' { '1' } else { '0' };
        }
        *v = serde_json::Value::String(c.into_iter().collect());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn circuit_key_is_the_pinned_v6_1_0_key() {
        // the same 492 bytes as ~/.sp1/circuits/groth16/v6.1.0/groth16_vk.bin (the development machine and the node)
        assert_eq!(embedded_groth16_vk_bytes(), 492);
        assert_eq!(embedded_groth16_vk_sha256(), "4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696");
        assert_eq!(outcome_class(5), "positive");
        assert_eq!(outcome_class(0), "zero");
        assert_eq!(outcome_class(-1), "negative");
    }
}
