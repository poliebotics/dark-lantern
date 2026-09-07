#!/usr/bin/env python3
"""Assemble the public package (v1.1) for the N7 integer positive: records, circuit, build artefacts, the six source PNGs and the
recorded map and pairs manifest as fixtures (public data), the self-contained checker, build and timing logs, the control detail
record, and a receipt completed with toolchain hashes, rerun peak-memory measurements and the fresh source-to-build comparison.
Workspace absolute paths are reduced in every shipped text file; the as-run hashes are recorded. SHA256SUMS covers every other file."""
import hashlib, json, os, shutil, subprocess, time
O = 'n7_integer_positive_20260906'; B = f'{O}/build'; BF = f'{O}/build_fresh'; P = f'{O}/package'
TC = 'provable_yoga_20260815/toolchain'; PAIRS = 'n7_raw_20260906/pairs'; N7 = 'n7_raw_20260906/package'
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(open(p, 'rb').read())
SCR = [(f'{TC}/', 'toolchain/'), (f'{O}/', ''), ('n7_raw_20260906/', 'n7_raw_20260906/'), ('', ''), ('', '')]
def scrub(t):
    for a, b in SCR:
        t = t.replace(a, b)
    return t
spec = json.load(open(f'{O}/SPEC_FREEZE.json')); ex = json.load(open(f'{O}/EXAMPLES.json')); res = json.load(open(f'{O}/RESULTS.json')); ctr = json.load(open(f'{O}/CONTROLS.json')); det = json.load(open(f'{O}/CONTROLS_DETAIL.json')); roots = json.load(open(f'{O}/ROOTS.json'))
shutil.rmtree(P, ignore_errors=True)
for d in ('build', 'scripts', 'fixtures/test_A', 'fixtures/test_B', 'logs'):
    os.makedirs(f'{P}/{d}')
for f in ('SPEC_FREEZE.json', 'EXAMPLES.json', 'MANIFEST.json', 'ROOTS.json', 'RESULTS.json', 'CONTROLS.json', 'CONTROLS_DETAIL.json', 'n7_triplet.circom'):
    open(f'{P}/{f}', 'w').write(scrub(open(f'{O}/{f}').read()))
as_run = {}
for f in ('reference.py', 'pipeline.py', 'controls.py', 'controls_detail.py', 'independent_check.py', 'package.py'):
    as_run[f] = fsha(f'{O}/{f}'); open(f'{P}/scripts/{f}', 'w').write(scrub(open(f'{O}/{f}').read()))
for f in ('n7_triplet.r1cs', 'n7_triplet.sym', 'verification_key.json', 'n7_triplet.zkey', 'd2_main_proof.json', 'd2_main_public.json', 'v10_main_proof.json', 'v10_main_public.json', 'd2_main_input.json', 'v10_main_input.json'):
    shutil.copy2(f'{B}/{f}', f'{P}/build/{f}')
shutil.copytree(f'{B}/n7_triplet_js', f'{P}/build/n7_triplet_js')
for f in ('compile.log', 'compile_time.log', 'reprove.log', 'reprove_time.log'):
    open(f'{P}/logs/{f}', 'w').write(scrub(open(f'{BF}/{f}', errors='replace').read()))
# fixtures: the six source PNGs (public data), the recorded map, the pairs manifest
for s, e in spec['examples'].items():
    shutil.copy2(f"{PAIRS}/test_B/{e['target']}", f"{P}/fixtures/test_B/{e['target']}"); shutil.copy2(f"{PAIRS}/test_A/{e['target']}", f"{P}/fixtures/test_A/{e['target']}"); shutil.copy2(f"{PAIRS}/test_A/{e['mismatch_emission']}", f"{P}/fixtures/test_A/{e['mismatch_emission']}")
shutil.copy2(f'{N7}/results/maps/random_seed2026090601.json', f'{P}/fixtures/random_seed2026090601.json'); shutil.copy2(f'{N7}/PAIRS_MANIFEST.json', f'{P}/fixtures/PAIRS_MANIFEST.json')
assert fsha(f'{P}/fixtures/random_seed2026090601.json') == spec['map_sha256'] and fsha(f'{P}/fixtures/PAIRS_MANIFEST.json') == spec['pairs_manifest_sha256']
# receipt
r1cs_info = subprocess.run(['node', f'{TC}/node/node_modules/snarkjs/build/cli.cjs', 'r1cs', 'info', f'{B}/n7_triplet.r1cs'], capture_output=True, text=True).stdout
cpu = [l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')][0]
def timelog(p):
    d = {}
    for l in open(p):
        if 'Maximum resident set size' in l: d['peak_rss_kbytes'] = int(l.split(':')[1])
        if 'Elapsed (wall clock)' in l: d['elapsed'] = l.split('):')[1].strip()
    return d
orig = {}
for s in ('d2', 'v10'):
    rows = [json.loads(l) for l in open(f'{N7}/results/scores/random_seed2026090601_grid4_{s}.jsonl')]; t = ex[s]['example']['target']; d = ex[s]['example']['mismatch_emission']
    orig[s] = dict(float32_program_matched=next(r['matched'] for r in rows if r['target'] == t), float32_program_recorded_edge_E_donor_B_target=next(r['mismatched'] for r in rows if r['target'] == d and r['partner'] == t), exact_matched=ex[s]['matched']['mean_rho_exact'], exact_mismatch=ex[s]['mismatch']['mean_rho_exact'])
receipt = dict(schema='n7-integer-positive-receipt/v1.1', created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), status='retrospective engineering demonstration on public data; tau = 1/8 chosen after inspecting the two examples; not a calibration, generalisation, authenticity or liveness result',
    protocol=dict(statistic=spec['statistic'], grid=spec['grid'], S=spec['S'], tau=spec['tau'], guards=spec['guards'], error_bound=spec['error_bound'], selection_rule=spec['selection_rule'], directed_map_interpretation=ex['d2']['example']['directed_edge'], map_sha256=spec['map_sha256'], pairs_manifest_sha256=spec['pairs_manifest_sha256']),
    examples={s: dict(target=ex[s]['example']['target'], mismatch_emission=ex[s]['example']['mismatch_emission'], sources=ex[s]['source'], grid_digests_uint32_le=ex[s]['grid_digests'],
                     expected=dict(signed_q_matched=[c['signed_q'] for c in ex[s]['matched']['channels']], signed_q_mismatch=[c['signed_q'] for c in ex[s]['mismatch']['channels']], q_matched=[c['q'] for c in ex[s]['matched']['channels']], q_mismatch=[c['q'] for c in ex[s]['mismatch']['channels']], z_matched=ex[s]['matched']['z'], z_mismatch=ex[s]['mismatch']['z']),
                     actual=dict(witness_q_matched=json.load(open(f'{B}/{s}_main_input.json'))['q_m'], witness_q_mismatch=json.load(open(f'{B}/{s}_main_input.json'))['q_x'], public_z_matched=int(res['examples'][s]['public_signals'][3]), public_z_mismatch=int(res['examples'][s]['public_signals'][4])),
                     commitments=roots['roots'][s]['commitments'], nonces_disclosed=roots['roots'][s]['nonces'], public_signals=res['examples'][s]['public_signals'], public_signal_order=res['examples'][s]['public_signal_order'],
                     verified=res['examples'][s]['verify_ok'], outputs_match=res['examples'][s]['outputs_match_expected'], seconds_original_run=res['examples'][s]['seconds'], proof_sha256=res['examples'][s]['proof_sha256'], public_sha256=res['examples'][s]['public_sha256'], scores=orig[s]) for s in ex},
    commitment=spec['commitment'], manifest_sha256=res['manifest_sha256'], manifest_halves=dict(hi=roots['manifest_hi'], lo=roots['manifest_lo']),
    circuit=dict(source='n7_triplet.circom', source_sha256=fsha(f'{O}/n7_triplet.circom'), compiler='circom 2.2.3', compiler_sha256=fsha(f'{TC}/circom-2.2.3-linux-amd64'), flags='--r1cs --wasm --sym -l <node_modules root holding circomlib>',
                 circomlib=dict(version=json.load(open(f'{TC}/node/node_modules/circomlib/package.json'))['version'], package_json_sha256=fsha(f'{TC}/node/node_modules/circomlib/package.json'), files={f: fsha(f'{TC}/node/node_modules/circomlib/circuits/{f}') for f in ('poseidon.circom', 'poseidon_constants.circom', 'bitify.circom', 'comparators.circom')}),
                 snarkjs=dict(version='0.7.6', cli_sha256=fsha(f'{TC}/node/node_modules/snarkjs/build/cli.cjs')), node=subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip(),
                 r1cs_sha256=fsha(f'{B}/n7_triplet.r1cs'), r1cs_info=r1cs_info.strip(), r1cs_constraints=11811, nonlinear_constraints=8635, linear_constraints=3176, plonk_constraints=23212, domain_power=15, wasm_sha256=fsha(f'{B}/n7_triplet_js/n7_triplet.wasm'), sym_sha256=fsha(f'{B}/n7_triplet.sym'),
                 zkey_sha256=fsha(f'{B}/n7_triplet.zkey'), zkey_bytes=os.path.getsize(f'{B}/n7_triplet.zkey'), verification_key_sha256=fsha(f'{B}/verification_key.json'), ptau=dict(file='powersOfTau28_hez_final_15.ptau', sha256=fsha(f'{TC}/powersOfTau28_hez_final_15.ptau'), power=15, shipped=False),
                 fresh_recompile=dict(when_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(os.path.getmtime(f'{BF}/n7_triplet.r1cs'))), r1cs_sha256=fsha(f'{BF}/n7_triplet.r1cs'), wasm_sha256=fsha(f'{BF}/n7_triplet_js/n7_triplet.wasm'), byte_identical_to_shipped=(fsha(f'{BF}/n7_triplet.r1cs') == fsha(f'{B}/n7_triplet.r1cs') and fsha(f'{BF}/n7_triplet_js/n7_triplet.wasm') == fsha(f'{B}/n7_triplet_js/n7_triplet.wasm')), log='logs/compile.log')),
    timings=dict(original_run=dict(setup_seconds=res['setup_seconds'], d2=res['examples']['d2']['seconds'], v10=res['examples']['v10']['seconds'], peak_memory='not measured on the original run'),
                 reruns=dict(compile=timelog(f'{BF}/compile_time.log'), prove_d2=dict(timelog(f'{BF}/reprove_time.log'), verified=True, note='re-proof of the d2 witness with the shipped proving key; measured with /usr/bin/time -v; labelled as a rerun')), cpu=cpu, host='laptop CPU; the RTX 5090 was not connected'),
    controls=ctr['controls'], controls_all_behaved=ctr['all_behaved'], controls_detail=det['controls'], controls_detail_all_failed_at_witness=det['all_failed_at_witness'],
    scripts_as_run=as_run, path_reduction='workspace absolute paths reduced to package-relative form in every shipped text file; scripts_as_run holds the SHA-256 of the scripts as run',
    replay='from the package root: SNARKJS="/path/to/node_modules/.bin/snarkjs" python3 scripts/independent_check.py   (needs python3 with numpy and Pillow, node, and snarkjs 0.7.6); it checks the six fixture PNGs, the grids against the frozen openings, the quotients and z, the commitments reconstructed from the disclosed openings through the shipped witness generator, and both proofs',
    boundaries=['the proof starts at the committed integer grids; decoding the PNGs and summing the cells is host-side replay evidence (scripts/reference.py, scripts/independent_check.py), not in-circuit computation',
                'the commitments were made on 6 September 2026, not at recording time; nothing here is a recorder-time commitment',
                'the error theorem concerns exact mathematical Pearson correlation; the float32 program of the train-free package differs from exact-sum Pearson by up to about 2.7e-5 on these examples (all four threshold decisions agree)',
                'public data with disclosed nonces: this demonstrates the proof system, not confidentiality', 'two examples chosen by a fixed rule; tau chosen after inspection; no claim about the other 973 pairs',
                'the sealed 288-row take supplies no part of this work', 'a host check that compared only aggregate scores could not distinguish grids shifted by a constant per value; the shipped checker therefore compares the grids and digests themselves against the frozen openings'])
open(f'{P}/RECEIPT.json', 'w').write(scrub(json.dumps(receipt, indent=1)) + '\n')
readme = open(f'{O}/README_template.md').read() if os.path.exists(f'{O}/README_template.md') else None
open(f'{P}/README.md', 'w').write(scrub(open(f'{O}/README_v1_1.md').read()))
sums = []
for root, _, files in os.walk(P):
    for f in sorted(files):
        p = os.path.join(root, f)
        if f != 'SHA256SUMS':
            sums.append(f'{fsha(p)}  {os.path.relpath(p, P)}')
open(f'{P}/SHA256SUMS', 'w').write('\n'.join(sorted(sums, key=lambda l: l.split('  ', 1)[1])) + '\n')
leak = [l.split('  ', 1)[1] for l in sums if l.split('  ', 1)[1].endswith(('.json', '.md', '.py', '.circom', '.sym', '.log')) and ('/home' + '/') in open(os.path.join(P, l.split('  ', 1)[1]), errors='replace').read()]
print('package files', len(sums) + 1, 'bytes', sum(os.path.getsize(os.path.join(P, l.split('  ', 1)[1])) for l in sums), 'leaks', leak)
