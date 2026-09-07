#!/usr/bin/env python3
"""N7 integer positive: manifest, nonces, witness inputs, commitments (roots record pinned before proving), PLONK setup with the
pinned power-15 ceremony, proofs and verification for the two frozen examples, with timings. Then the controls, each recorded with
the layer at which it fails (witness construction, witness check, proof verification, or source validation)."""
import hashlib, json, os, secrets, subprocess, sys, time
sys.path.insert(0, 'n7_integer_positive_20260906')
from reference import S, N, MAXV, Z_OFFSET, moments, channel_q
O = 'n7_integer_positive_20260906'; B = f'{O}/build'; TC = 'provable_yoga_20260815/toolchain'
SNARK = ['node', f'{TC}/node/node_modules/snarkjs/build/cli.cjs']; PTAU = f'{TC}/powersOfTau28_hez_final_15.ptau'
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(open(p, 'rb').read())
spec = json.load(open(f'{O}/SPEC_FREEZE.json')); EX = json.load(open(f'{O}/EXAMPLES.json'))


def run(cmd, timeout=1800):
    t = time.time(); r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout); return r, round(time.time() - t, 2)


def witness_inputs(cap, em, mis, manifest_hi, manifest_lo, nonces, override=None):
    """Circuit inputs from the grids; override lets a control perturb the hints (q by +-1) after they are computed."""
    def hints(x_all, y_all):
        b, a, q, vin_x, vin_y = [], [], [], [], []
        for c in range(3):
            x = x_all[c::3]; y = y_all[c::3]; C, Vx, Vy = moments(x, y); bb, aa, qq, _ = channel_q(C, Vx, Vy)
            b.append(bb); a.append(str(aa)); q.append(qq); vin_x.append(str(pow(Vx % P, -1, P))); vin_y.append(str(pow(Vy % P, -1, P)))
        return b, a, q, vin_x, vin_y
    b_m, a_m, q_m, vc, ve = hints(cap, em); b_x, a_x, q_x, vc2, vm = hints(cap, mis)
    assert vc == vc2
    inp = dict(manifest_hi=str(manifest_hi), manifest_lo=str(manifest_lo), cap=[str(v) for v in cap], em=[str(v) for v in em], mis=[str(v) for v in mis],
               nonce_cap=str(nonces[0]), nonce_em=str(nonces[1]), nonce_mis=str(nonces[2]), vinv_cap=vc, vinv_em=ve, vinv_mis=vm, b_m=b_m, a_m=a_m, q_m=q_m, b_x=b_x, a_x=a_x, q_x=q_x)
    if override:
        override(inp)
    return inp


def calc_witness(inp, tag):
    ip = f'{B}/{tag}_input.json'; wp = f'{B}/{tag}.wtns'; json.dump(inp, open(ip, 'w'))
    r, dt = run(['node', f'{B}/n7_triplet_js/generate_witness.js', f'{B}/n7_triplet_js/n7_triplet.wasm', ip, wp])
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:], wp, dt


def witness_check(wp):
    r, dt = run(SNARK + ['wtns', 'check', f'{B}/n7_triplet.r1cs', wp]); return 'WITNESS IS CORRECT' in r.stdout, (r.stdout + r.stderr).strip()[-200:], dt


def prove(wp, tag):
    pf, pb = f'{B}/{tag}_proof.json', f'{B}/{tag}_public.json'
    r, dt = run(SNARK + ['plonk', 'prove', f'{B}/n7_triplet.zkey', wp, pf, pb]); return r.returncode == 0, pf, pb, dt, (r.stdout + r.stderr).strip()[-200:]


def verify(pb, pf):
    r, dt = run(SNARK + ['plonk', 'verify', f'{B}/verification_key.json', pb, pf]); return 'OK!' in r.stdout, dt, (r.stdout + r.stderr).strip()[-200:]


def main():
    t0 = time.time(); os.makedirs(B, exist_ok=True)
    # 1. manifest (no commitments inside), then its halves
    manifest = dict(schema='n7-integer-positive-manifest/v1', created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), spec_freeze_sha256=fsha(f'{O}/SPEC_FREEZE.json'), examples_sha256=fsha(f'{O}/EXAMPLES.json'),
                    circuit_source_sha256=fsha(f'{O}/n7_triplet.circom'), r1cs_sha256=fsha(f'{B}/n7_triplet.r1cs'), wasm_sha256=fsha(f'{B}/n7_triplet_js/n7_triplet.wasm'), ptau=dict(path='powersOfTau28_hez_final_15.ptau', sha256=fsha(PTAU)),
                    statistic=spec['statistic'], grid=spec['grid'], S=S, N=N, tau=spec['tau'], guards=spec['guards'], selection_rule=spec['selection_rule'], map_sha256=spec['map_sha256'], pairs_manifest_sha256=spec['pairs_manifest_sha256'],
                    status=spec['status'], sources={s: EX[s]['source'] for s in EX}, grid_digests={s: EX[s]['grid_digests'] for s in EX}, expected_public={s: dict(z_matched=EX[s]['matched']['z'], z_mismatch=EX[s]['mismatch']['z']) for s in EX})
    mb = (json.dumps(manifest, indent=1) + '\n').encode(); open(f'{O}/MANIFEST.json', 'wb').write(mb); mdig = int.from_bytes(hashlib.sha256(mb).digest(), 'big'); m_hi, m_lo = mdig >> 128, mdig & ((1 << 128) - 1)
    print('manifest sha256', sha(mb), flush=True)
    # 2. setup once (the circuit is example-independent)
    if not os.path.exists(f'{B}/n7_triplet.zkey'):
        r, dt = run(SNARK + ['plonk', 'setup', f'{B}/n7_triplet.r1cs', PTAU, f'{B}/n7_triplet.zkey'], timeout=3600); print('setup', r.returncode, dt, 's', (r.stdout + r.stderr).strip()[-300:].replace('\n', ' | '), flush=True)
        if r.returncode != 0:
            raise SystemExit('setup failed (does the circuit exceed the power-15 domain?)')
        r, _ = run(SNARK + ['zkey', 'export', 'verificationkey', f'{B}/n7_triplet.zkey', f'{B}/verification_key.json']); assert r.returncode == 0
        setup_time = dt
    else:
        setup_time = None
    r, _ = run(SNARK + ['r1cs', 'info', f'{B}/n7_triplet.r1cs']); r1cs_info = r.stdout.strip()
    results = dict(schema='n7-integer-positive-results/v1', manifest_sha256=sha(mb), setup_seconds=setup_time, r1cs_info=r1cs_info, examples={}, controls=[])
    # 3. nonces and commitments pinned before proving: the witness calculation yields the commitments (outputs 0..2)
    roots = {}
    for s in EX:
        g = EX[s]['grids']; nonces = [secrets.randbits(128) for _ in range(3)]
        inp = witness_inputs(g['capture'], g['matched_emission'], g['recorded_mismatch'], m_hi, m_lo, nonces)
        ok, msg, wp, dt = calc_witness(inp, f'{s}_main'); assert ok, msg
        # public signals from the witness: export via a quick prove is later; read outputs with snarkjs wtns export json
        r, _ = run(SNARK + ['wtns', 'export', 'json', wp, f'{B}/{s}_main_wtns.json']); w = json.load(open(f'{B}/{s}_main_wtns.json'))
        C_cap, C_em, C_mis, z_m, z_x = w[1], w[2], w[3], int(w[4]), int(w[5])
        roots[s] = dict(nonces=[str(n) for n in nonces], commitments=dict(capture=C_cap, matched_emission=C_em, recorded_mismatch=C_mis), expected_z=dict(matched=z_m, mismatch=z_x), witness_seconds=dt)
    open(f'{O}/ROOTS.json', 'w').write(json.dumps(dict(manifest_sha256=sha(mb), manifest_hi=str(m_hi), manifest_lo=str(m_lo), roots=roots, pinned_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), indent=1) + '\n')
    print('roots pinned', {s: roots[s]['expected_z'] for s in roots}, flush=True)
    # 4. proofs and verification
    for s in EX:
        wp = f'{B}/{s}_main.wtns'; okc, msgc, dtc = witness_check(wp); okp, pf, pb, dtp, msgp = prove(wp, f'{s}_main'); okv, dtv, msgv = verify(pb, pf)
        pub = json.load(open(pb)); exp = EX[s]
        outputs_ok = int(pub[3]) == exp['matched']['z'] and int(pub[4]) == exp['mismatch']['z'] and pub[0] == roots[s]['commitments']['capture'] and pub[1] == roots[s]['commitments']['matched_emission'] and pub[2] == roots[s]['commitments']['recorded_mismatch'] and pub[5] == str(m_hi) and pub[6] == str(m_lo)
        results['examples'][s] = dict(witness_check=okc, prove_ok=okp, verify_ok=okv, public_signals=pub, public_signal_order=['C_capture', 'C_matched', 'C_mismatch', 'z_matched', 'z_mismatch', 'manifest_hi', 'manifest_lo'], outputs_match_expected=outputs_ok,
                                      seconds=dict(witness=roots[s]['witness_seconds'], check=dtc, prove=dtp, verify=dtv), proof_sha256=fsha(pf), public_sha256=fsha(pb), messages=dict(check=msgc, prove=msgp, verify=msgv))
        print(f'{s}: check {okc} prove {okp} ({dtp}s) verify {okv} ({dtv}s) outputs {outputs_ok} z {pub[3]} {pub[4]}', flush=True)
    results['seconds_total'] = round(time.time() - t0, 1)
    json.dump(results, open(f'{O}/RESULTS.json', 'w'), indent=1)
    print('done', results['seconds_total'], 's')


if __name__ == '__main__':
    main()
