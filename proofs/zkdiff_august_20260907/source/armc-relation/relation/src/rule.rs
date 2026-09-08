//! The declared two-part wrong-row offset rule of 7 September 2026, as a pure function,
//! so that the batch driver that assigns offsets, the acceptance verifier that checks them and the regression tests
//! that enumerate them all read one definition:
//!
//! ```text
//!   base   = OFFSETS[(r - row_start) mod 5],   OFFSETS = [-2, +2, -15, +15, +30]
//!   offset = base    and flag = direct     if 0 <= r + base < row_count
//!   offset = -base   and flag = mirrored   otherwise (and only then)
//! ```
//!
//! For the August proof set (`row_start = 600`, `row_count = 712`, rows 600..=711) the mirrored rows are exactly
//! 684, 689, 694, 699, 704, 709 (base +30, offset -30), 698, 703, 708 (base +15, offset -15) and 711 (base +2,
//! offset -2).
//!
//! Division of labour (Astra r5, findings 1 and 3): the guest checks the *generic* admissibility of a statement
//! (`statement::check_offset_rule`: a direct offset lies in the protocol set, a mirrored offset is the mirror of a
//! protocol-set value whose direct wrong row lies outside the session, and `u = r + d` lies inside), because the
//! guest does not know which batch it is part of. The *exact modulo assignment* anchored at row 600 is policy, and
//! the acceptance verifier enforces it on the public fields (`r`, `u`, `d`, byte 11) with [`august_assignment`].
//! A coherent alternative offset (row 698 declared direct -15, say) can satisfy the generic relation and must fail
//! the declared-rule check; that is by design, and the negative controls record it.

use crate::statement::OFFSETS;

/// First row of the August proof set.
pub const AUGUST_RULE_ROW_START: u32 = 600;
/// Last row of the August proof set (inclusive).
pub const AUGUST_RULE_ROW_END_INCLUSIVE: u32 = 711;
/// Rows in the August session.
pub const AUGUST_ROW_COUNT: u32 = 712;
/// Number of rows in the August proof set.
pub const AUGUST_RULE_ROWS: u32 = AUGUST_RULE_ROW_END_INCLUSIVE - AUGUST_RULE_ROW_START + 1; // 112
/// The ten mirrored rows of the August proof set, ascending.
pub const AUGUST_MIRRORED_ROWS: [u32; 10] = [684, 689, 694, 698, 699, 703, 704, 708, 709, 711];

pub const RULE_TEXT: &str = "one proof per held-out August row r in 600..=711; base = OFFSETS[(r - 600) mod 5], OFFSETS = [-2, +2, -15, +15, +30]; offset = base when 0 <= r + base < 712 (offset_rule = direct, public byte 11 = 0), else offset = -base (offset_rule = mirrored, byte 11 = 1; rows 684, 689, 694, 699, 704, 709 at +30 mirror to -30, 698, 703, 708 at +15 to -15, 711 at +2 to -2); u = r + offset; every outcome published, negative and zero differences included";

/// One assignment of the rule: the declared offset `d`, whether it is the mirror of the base, and `u = r + d`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Assignment {
    pub row: u32,
    pub base: i32,
    pub offset: i32,
    pub mirrored: bool,
    pub wrong_row: u32,
}

/// `OFFSETS[(r - row_start) mod 5]`; `r >= row_start` required.
pub fn base_offset(r: u32, row_start: u32) -> Option<i32> {
    if r < row_start {
        return None;
    }
    Some(OFFSETS[((r - row_start) % OFFSETS.len() as u32) as usize])
}

/// The rule for any session: `None` when `r < row_start`, when `r` is not a provable row (`1 <= r < row_count`), or
/// when neither the direct nor the mirrored wrong row lies inside the session (impossible for August).
pub fn assignment(r: u32, row_start: u32, row_count: u32) -> Option<Assignment> {
    if r == 0 || r >= row_count {
        return None;
    }
    let base = base_offset(r, row_start)?;
    let inside = |d: i32| {
        let u = r as i64 + d as i64;
        u >= 0 && u < row_count as i64
    };
    if inside(base) {
        Some(Assignment { row: r, base, offset: base, mirrored: false, wrong_row: (r as i64 + base as i64) as u32 })
    } else if inside(-base) {
        Some(Assignment { row: r, base, offset: -base, mirrored: true, wrong_row: (r as i64 - base as i64) as u32 })
    } else {
        None
    }
}

/// The August proof-set assignment of row `r`, or `None` outside 600..=711.
pub fn august_assignment(r: u32) -> Option<Assignment> {
    if !(AUGUST_RULE_ROW_START..=AUGUST_RULE_ROW_END_INCLUSIVE).contains(&r) {
        return None;
    }
    assignment(r, AUGUST_RULE_ROW_START, AUGUST_ROW_COUNT)
}

/// All 112 August assignments, ascending by row.
pub fn august_table() -> Vec<Assignment> {
    (AUGUST_RULE_ROW_START..=AUGUST_RULE_ROW_END_INCLUSIVE).map(|r| august_assignment(r).expect("every August row has an assignment")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::statement::{check_offset_rule, OFFSET_RULE_DIRECT, OFFSET_RULE_MIRRORED};

    /// The declared rule written out by hand for the boundary rows, independent of the arithmetic above.
    const EXPECTED_MIRRORED: [(u32, i32, i32, u32); 10] = [
        (684, 30, -30, 654),
        (689, 30, -30, 659),
        (694, 30, -30, 664),
        (698, 15, -15, 683),
        (699, 30, -30, 669),
        (703, 15, -15, 688),
        (704, 30, -30, 674),
        (708, 15, -15, 693),
        (709, 30, -30, 679),
        (711, 2, -2, 709),
    ];

    #[test]
    fn all_112_august_assignments_follow_the_owner_rule() {
        let table = august_table();
        assert_eq!(table.len(), AUGUST_RULE_ROWS as usize);
        assert_eq!(table.len(), 112);
        let mut mirrored_rows = Vec::new();
        for (i, a) in table.iter().enumerate() {
            let r = 600 + i as u32;
            assert_eq!(a.row, r);
            // the modulo rule, spelled out
            let expected_base = [-2, 2, -15, 15, 30][((r - 600) % 5) as usize];
            assert_eq!(a.base, expected_base, "row {r} base");
            let direct_u = r as i64 + expected_base as i64;
            if (0..712).contains(&direct_u) {
                assert!(!a.mirrored, "row {r} must be direct");
                assert_eq!(a.offset, expected_base);
                assert_eq!(a.wrong_row as i64, direct_u);
            } else {
                assert!(a.mirrored, "row {r} must be mirrored");
                assert_eq!(a.offset, -expected_base);
                assert_eq!(a.wrong_row as i64, r as i64 - expected_base as i64);
                mirrored_rows.push(r);
            }
            assert_eq!(a.wrong_row as i64, r as i64 + a.offset as i64);
            assert!(a.wrong_row < 712);
            // the guest's generic check admits exactly this assignment with exactly this flag ...
            let flag = if a.mirrored { OFFSET_RULE_MIRRORED } else { OFFSET_RULE_DIRECT };
            assert_eq!(check_offset_rule(r, 712, a.offset, flag).unwrap(), a.wrong_row, "row {r} admitted");
            // ... and the same offset under the opposite flag is admitted generically exactly when first principles
            // say so: a direct claim needs d in the set; a mirrored claim needs -d in the set and r - d outside.
            // Those "policy-only" rows are refused by the declared-rule check alone (recorded as negative controls):
            //   flipped to direct  : 698, 703, 708 (-15) and 711 (-2), whose offsets are protocol values in their own right
            //   flipped to mirrored: 697, 702, 707 (-15 with r + 15 >= 712) and 710 (-2 with r + 2 = 712)
            let flipped = check_offset_rule(r, 712, a.offset, flag ^ 1);
            let generic_ok = if a.mirrored {
                OFFSETS.contains(&a.offset)
            } else {
                let direct_of_mirror = r as i64 - a.offset as i64;
                OFFSETS.contains(&-a.offset) && !(0..712).contains(&direct_of_mirror)
            };
            assert_eq!(flipped.is_ok(), generic_ok, "row {r}: flipped flag generic admissibility");
            let policy_only = [697, 698, 702, 703, 707, 708, 710, 711].contains(&r);
            assert_eq!(generic_ok, policy_only, "row {r}: the policy-only rows are exactly those eight");
            // the declared-rule check refuses every flag flip and every other offset
            for other in [-30, -15, -2, 2, 15, 30] {
                for other_flag in [false, true] {
                    let same = other == a.offset && other_flag == a.mirrored;
                    let ok = august_assignment(r).map(|x| x.offset == other && x.mirrored == other_flag).unwrap_or(false);
                    assert_eq!(ok, same, "row {r} offset {other} mirrored {other_flag}");
                }
            }
        }
        assert_eq!(mirrored_rows, AUGUST_MIRRORED_ROWS.to_vec());
        for (r, base, offset, u) in EXPECTED_MIRRORED {
            let a = august_assignment(r).unwrap();
            assert_eq!((a.base, a.offset, a.mirrored, a.wrong_row), (base, offset, true, u), "row {r}");
        }
        // the six -30 rows are exactly the +30 rows whose direct wrong row would be 714..=739
        let minus30: Vec<u32> = table.iter().filter(|a| a.offset == -30).map(|a| a.row).collect();
        assert_eq!(minus30, vec![684, 689, 694, 699, 704, 709]);
        // outside the set there is no assignment
        assert!(august_assignment(599).is_none());
        assert!(august_assignment(712).is_none());
        assert!(assignment(0, 0, 712).is_none());
        assert_eq!(base_offset(599, 600), None);
    }

    #[test]
    fn generic_rule_fails_closed_on_other_sessions() {
        // a 40-row session anchored at 0: row 39 has base OFFSETS[39 mod 5 = 4] = +30 -> 69 outside -> mirrored -30 -> u = 9
        let a = assignment(39, 0, 40).unwrap();
        assert_eq!((a.base, a.offset, a.mirrored, a.wrong_row), (30, -30, true, 9));
        // row 34: base +30 -> 64 outside -> -30 -> 4; row 35: base -2 -> 33 inside, direct
        let a = assignment(34, 0, 40).unwrap();
        assert_eq!((a.offset, a.mirrored, a.wrong_row), (-30, true, 4));
        let a = assignment(35, 0, 40).unwrap();
        assert_eq!((a.base, a.offset, a.mirrored, a.wrong_row), (-2, -2, false, 33));
        // a 20-row session: row 19 has base +30 -> 49 outside, -30 -> -11 outside: no assignment
        assert!(assignment(19, 0, 20).is_none());
        // row 1 with base -2 -> -1 outside -> mirrored +2 -> 3
        let a = assignment(1, 1, 16).unwrap();
        assert_eq!((a.base, a.offset, a.mirrored, a.wrong_row), (-2, 2, true, 3));
    }
}
