#!/usr/bin/env python3
"""Controls for the N7 integer positive, each recorded with the layer at which it fails: 'witness' (witness construction, a
circuit assertion), 'check' (R1CS witness check), 'verify' (PLONK verification), or 'source' (pre-circuit validation). A Python
exception is never called a cryptographic rejection. Also the two synthetic endpoint exercises (identical and complementary grids)."""
import json, secrets, sys, time
sys.path.insert(0, 'n7_integer_positive_20260906')
from pipeline import witness_inputs, calc_witness, witness_check, prove, verify, run, SNARK, B, O, P, fsha
from reference import MAXV, moments, channel_q, S
EX = json.load(open(f'{O}/EXAMPLES.json')); ROOTS = json.load(open(f'{O}/ROOTS.json')); m_hi, m_lo = int(ROOTS['manifest_hi']), int(ROOTS['manifest_lo'])
g = EX['d2']['grids']; cap, em, mis = g['capture'], g['matched_emission'], g['recorded_mismatch']; nonces = [int(x) for x in ROOTS['roots']['d2']['nonces']]
out = []


def record(name, expectation, layer, ok, detail):
    out.append(dict(control=name, expectation=expectation, failure_layer=layer, behaved_as_required=bool(ok), detail=str(detail)[-300:])); print(('ok  ' if ok else 'BAD '), name, '->', layer, str(detail)[-120:].replace('\n', ' | '), flush=True)


def try_triplet(name, c, e, x, expectation, expect_layer, override=None, nonce_set=None, fresh_nonces=True):
    """Attempt the full path on a grid triplet; report at which layer it stops (or that it verified)."""
    nn = [secrets.randbits(128) for _ in range(3)] if fresh_nonces else nonces
    try:
        inp = witness_inputs(c, e, x, m_hi, m_lo, nn, override=override)
    except Exception as ex:  # a pre-circuit condition (zero variance has no inverse): the circuit must also refuse when fed vinv = 0, which we test explicitly
        record(name, expectation, 'source', expect_layer == 'source', f'{type(ex).__name__}: {ex}'); return None
    ok, msg, wp, _ = calc_witness(inp, name)
    if not ok:
        record(name, expectation, 'witness', expect_layer == 'witness', msg); return None
    okc, msgc, _ = witness_check(wp)
    if not okc:
        record(name, expectation, 'check', expect_layer == 'check', msgc); return None
    okp, pf, pb, _, msgp = prove(wp, name)
    if not okp:
        record(name, expectation, 'prove', expect_layer == 'prove', msgp); return None
    okv, _, msgv = verify(pb, pf)
    record(name, expectation, 'verified' if okv else 'verify', (expect_layer == 'verified') == okv, msgv); return pb, pf


# 1. recorded donor substituted into the matched role (recomputed commitments): the positive predicate must fail
try_triplet('donor_in_matched_role', cap, mis, mis, 'matched guard fails (z_matched below 221187)', 'witness')
# 2. positive and negative emissions exchanged
try_triplet('emissions_exchanged', cap, mis, em, 'cannot satisfy both guards', 'witness')
# 3. constant-zero grids: undefined correlation; vinv cannot exist. Python has no inverse of 0 (source layer); feed vinv = 0 to the circuit explicitly too
try_triplet('constant_zero_grids_source', [0] * 48, [0] * 48, [0] * 48, 'no modular inverse of a zero variance', 'source')
def zero_override(inp):
    for k in ('vinv_cap', 'vinv_em', 'vinv_mis'):
        inp[k] = ['0', '0', '0']
    inp['b_m'] = [0, 0, 0]; inp['a_m'] = ['0'] * 3; inp['q_m'] = [0, 0, 0]; inp['b_x'] = [0, 0, 0]; inp['a_x'] = ['0'] * 3; inp['q_x'] = [0, 0, 0]
zeros = [0] * 48
try:
    inp = dict(manifest_hi=str(m_hi), manifest_lo=str(m_lo), cap=['0'] * 48, em=['0'] * 48, mis=['0'] * 48, nonce_cap='1', nonce_em='2', nonce_mis='3'); zero_override(inp)
    ok, msg, wp, _ = calc_witness(inp, 'constant_zero_grids_circuit')
    record('constant_zero_grids_circuit', 'nonzero-variance constraint v*vinv=1 fails in circuit', 'witness', not ok, msg)
except Exception as ex:
    record('constant_zero_grids_circuit', 'nonzero-variance constraint fails', 'source', False, ex)
# 4. complemented matched emission cells: correlation signs flip, positive acceptance fails
try_triplet('complement_matched_emission', cap, [MAXV - v for v in em], mis, 'matched guard fails (sign flipped)', 'witness')
# 5. a grid value changed under the frozen commitment: a new proof does not verify against the pinned public signals
cap2 = list(cap); cap2[7] += 1
res = try_triplet('grid_value_changed_own_commitment', cap2, em, mis, 'valid proof under its own (different) commitments', 'verified', fresh_nonces=False)
if res:
    pb_new, pf_new = res; okv, _, msgv = verify(f'{B}/d2_main_public.json', pf_new)
    record('grid_value_changed_vs_pinned_public', 'the new proof rejects against the pinned original public signals', 'verify', not okv, msgv)
# 6. every public signal of the original proof mutated by +1 mod p: verify rejects
pub = json.load(open(f'{B}/d2_main_public.json')); rej = 0
for i in range(len(pub)):
    mut = list(pub); mut[i] = str((int(mut[i]) + 1) % P); mp = f'{B}/d2_pubmut_{i}.json'; json.dump(mut, open(mp, 'w'))
    okv, _, msgv = verify(mp, f'{B}/d2_main_proof.json'); rej += (not okv)
record('public_signal_mutations', f'all {len(pub)} single-signal mutations reject', 'verify', rej == len(pub), f'{rej}/{len(pub)} rejected')
# 7. quotient witness changed by +-1: a quotient inequality fails
for delta in (+1, -1):
    def qo(inp, d=delta):
        inp['q_m'] = [inp['q_m'][0] + d, inp['q_m'][1], inp['q_m'][2]]
    try_triplet(f'quotient_witness_{"plus" if delta > 0 else "minus"}_one', cap, em, mis, 'quotient slack decomposition fails', 'witness', override=qo)
# 8. synthetic endpoints: identical nonconstant grids (rho = +1 per channel) and the complement (rho = -1): a valid triplet exercising the signed arithmetic at both ends
synth_cap = cap; synth_em = list(cap); synth_mis = [MAXV - v for v in cap]
res = try_triplet('synthetic_identical_and_complement_endpoints', synth_cap, synth_em, synth_mis, 'verifies with z_matched = 393216 (Q = 3S) and z_mismatch = 0 (Q = -3S)', 'verified')
if res:
    pb, _ = res; p = json.load(open(pb)); record('synthetic_endpoint_values', 'z_matched 393216, z_mismatch 0', 'verified', p[3] == '393216' and p[4] == '0', f'z {p[3]} {p[4]}')
# 9. the v10 example's proof does not verify against the d2 public signals (proof and statement are bound)
okv, _, msgv = verify(f'{B}/d2_main_public.json', f'{B}/v10_main_proof.json'); record('cross_example_proof_public', 'v10 proof rejects against d2 publics', 'verify', not okv, msgv)
json.dump(dict(schema='n7-integer-positive-controls/v1', run_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), controls=out, all_behaved=all(c['behaved_as_required'] for c in out)), open(f'{O}/CONTROLS.json', 'w'), indent=1)
print(f"{sum(c['behaved_as_required'] for c in out)}/{len(out)} controls behaved as required")
