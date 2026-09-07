#!/usr/bin/env python3
"""N7-RAW-v1 (GPT-6 Astra's registration of 6 September 2026, applied verbatim): retrospective train-free correspondence package.

Step A  reproduction: the byte-exact original coupling_stat.py is executed on the halo-built pairs; every full-precision metric
        must agree with the box record within 1e-6 and every strict-win count exactly. Any discrepancy stops the extraction.
Step B  registered random-mismatch endpoint: five independent within-session derangements (PCG64, seeds 2026090601..2026090605,
        fixed points rejected), persisted before scoring, the same maps for every grid; AUROC (ties one half) and paired ordering
        ((wins + ties/2)/n) per session, grid and seed; PASS only if both metrics >= 0.60 in all 50 combinations.
Step C  separately registered hard-negative endpoint: previous frame, next frame, nearest other emission by mean-RGB distance,
        nearest other emission by normalised 32x32 pattern similarity (emissions only, same session, self excluded, lexicographic
        tie-break); PASS only if both metrics >= 0.60 for every grid/session/family. Its failure cannot be called robustness.
Every target/partner identity, score, difference, win and tie is persisted; contiguous 30- and 60-frame block summaries are
reported with shorter terminal blocks retained. Undefined or non-finite measurements stop the run. Thresholds are the
registration's engineering effect-size floors on inspected data, not significance tests or security thresholds."""
import hashlib, importlib.util, json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image

O = Path('.'); PAIRS = O / 'pairs'; RES = O / 'results'; MAPS = RES / 'maps'; SCORES = RES / 'scores'
ORIG = Path('scripts/coupling_stat.py')
BOX = Path('box_record/coupling_stat.json')
GRIDS = (4, 8, 16, 32, 64); SEEDS = (2026090601, 2026090602, 2026090603, 2026090604, 2026090605); FLOOR = 0.60
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(Path(p).read_bytes())


def load_orig():
    spec = importlib.util.spec_from_file_location('coupling_stat_orig', ORIG); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


CS = load_orig()  # grid() and corr() are the frozen statistic, reused byte-exact


def grids_for(name):
    E = Image.open(PAIRS / 'test_A' / name).convert('RGB'); B = Image.open(PAIRS / 'test_B' / name).convert('RGB')
    e = np.asarray(E, dtype=np.float32); mean_rgb = e.reshape(-1, 3).mean(axis=0)
    return name, {g: CS.grid(E, g) for g in GRIDS}, {g: CS.grid(B, g) for g in GRIDS}, mean_rgb.tolist()


def auroc_ties_half(pos, neg):
    pos = np.asarray(pos, dtype=np.float64); neg = np.asarray(neg, dtype=np.float64)
    gt = (pos[:, None] > neg[None, :]).sum(); eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def derangement(items, seed):
    rng = np.random.Generator(np.random.PCG64(seed)); n = len(items); draws = 0
    while True:
        perm = rng.permutation(n); draws += 1
        if not np.any(perm == np.arange(n)):
            return [items[i] for i in perm], draws


def blocks(idx_sorted, size):
    out = []
    for s in range(0, len(idx_sorted), size):
        out.append(idx_sorted[s:s + size])
    return out


def score_map(name_of, targets, partners, data, g):
    rows = []
    for t, p in zip(targets, partners):
        m = CS.corr(data[t][0][g], data[t][1][g]); q = CS.corr(data[t][0][g], data[p][1][g])
        if not (np.isfinite(m) and np.isfinite(q)):
            raise SystemExit(f'STOP: non-finite statistic for {t} vs {p} at grid {g}')
        rows.append(dict(target=t, partner=p, matched=m, mismatched=q, difference=m - q, win=bool(m > q), tie=bool(m == q)))
    return rows


def summarise(rows):
    pos = [r['matched'] for r in rows]; neg = [r['mismatched'] for r in rows]; n = len(rows)
    wins = sum(r['win'] for r in rows); ties = sum(r['tie'] for r in rows)
    return dict(n=n, auroc=auroc_ties_half(pos, neg), wins=wins, ties=ties, paired_ordering=(wins + 0.5 * ties) / n if n else None,
                matched_mean=float(np.mean(pos)) if n else None, mismatched_mean=float(np.mean(neg)) if n else None)


def main():
    t0 = time.time(); RES.mkdir(exist_ok=True); MAPS.mkdir(exist_ok=True); SCORES.mkdir(exist_ok=True)
    pm = json.loads((O / 'PAIRS_MANIFEST.json').read_bytes())
    names = sorted(os.listdir(PAIRS / 'test_A')); assert names == sorted(os.listdir(PAIRS / 'test_B')) and len(names) == pm['n_pairs'] == 975
    by_session = {}
    for n in names:
        by_session.setdefault(n.split('_')[0], []).append(n)
    assert {s: len(v) for s, v in by_session.items()} == {'d2': 600, 'v10': 375}
    # registration frozen before any score is produced
    reg = dict(schema='n7-raw-v1-registration/v1', frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), statistic_source=str(ORIG), statistic_sha256=fsha(ORIG),
               box_record=str(BOX), box_record_sha256=fsha(BOX), pairs_manifest_sha256=fsha(O / 'PAIRS_MANIFEST.json'), grids=list(GRIDS), seeds=list(SEEDS), rng='numpy PCG64',
               floor=FLOOR, sessions={s: dict(n=len(v), first=v[0], last=v[-1]) for s, v in by_session.items()}, registration_text_source='scratch/astra_negatives_20260906/ASTRA_NEGATIVES.md, section "N7 registration text"',
               environment=dict(python=sys.version.split()[0], numpy=np.__version__))
    (RES / 'REGISTRATION.json').write_bytes((json.dumps(reg, indent=1) + '\n').encode())
    # ---- Step A: byte-exact reproduction of the original computation ----
    repro = RES / 'coupling_stat_repro.json'
    r = subprocess.run([sys.executable, str(ORIG), str(PAIRS), str(repro)], capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise SystemExit(f'STOP: original script failed: {r.stderr[-800:]}')
    box = json.loads(BOX.read_bytes()); rep = json.loads(repro.read_bytes()); repro_ok = True; diffs = []
    for g in map(str, GRIDS):
        for key in ('d2', 'v10', 'pooled'):
            a, b = box['grids'][g][key], rep['grids'][g][key]
            n_key = 'n_pairs' if key == 'pooled' else 'n'
            da = abs(a['auroc'] - b['auroc']); wa = round(a['paired_matched_greater'] * a[n_key]); wb = round(b['paired_matched_greater'] * b[n_key])
            extra = {} if key == 'pooled' else dict(matched_mean_diff=abs(a['matched_mean'] - b['matched_mean']), mismatched_mean_diff=abs(a['mismatched_mean'] - b['mismatched_mean']))
            ok = da <= 1e-6 and wa == wb and all(v <= 1e-6 for v in extra.values()); repro_ok &= ok
            diffs.append(dict(grid=int(g), key=key, auroc_box=a['auroc'], auroc_halo=b['auroc'], auroc_absdiff=da, wins_box=wa, wins_halo=wb, ok=ok, **extra))
    (RES / 'REPRODUCTION.json').write_bytes((json.dumps(dict(ok=repro_ok, tolerance=1e-6, comparisons=diffs, box_sha256=reg['box_record_sha256'], repro_sha256=fsha(repro)), indent=1) + '\n').encode())
    print(f'reproduction {"OK" if repro_ok else "FAILED"}: {sum(d["ok"] for d in diffs)}/{len(diffs)} comparisons within 1e-6 and exact wins', flush=True)
    if not repro_ok:
        raise SystemExit('STOP: the original measurements did not reproduce; nothing further is extracted')
    # ---- grids for all frames (once) ----
    with ProcessPoolExecutor(max_workers=16) as ex:
        loaded = list(ex.map(grids_for, names, chunksize=8))
    data = {n: (e, b) for n, e, b, _ in loaded}; mean_rgb = {n: np.array(m) for n, _, _, m in loaded}
    # ---- Step B: five within-session derangements, persisted before scoring ----
    maps = {}
    for seed in SEEDS:
        m = {}
        for s, ns in by_session.items():
            partners, draws = derangement(ns, seed + (0 if s == 'd2' else 0))  # one generator per (seed, session) in session order: deterministic
            assert all(t != p for t, p in zip(ns, partners)) and sorted(partners) == ns
            m[s] = dict(targets=ns, partners=partners, draws_until_derangement=draws)
        mp = MAPS / f'random_seed{seed}.json'; mp.write_bytes((json.dumps(m, indent=0) + '\n').encode()); maps[f'random_seed{seed}'] = dict(path=str(mp.relative_to(O)), sha256=fsha(mp), kind='within-session derangement', seed=seed)
    # ---- Step C maps: hard-negative families (emissions only) ----
    hard = {}
    for s, ns in by_session.items():
        idx = {n: i for i, n in enumerate(ns)}
        prev_t, prev_p = zip(*[(ns[i], ns[i - 1]) for i in range(1, len(ns))])
        next_t, next_p = zip(*[(ns[i], ns[i + 1]) for i in range(len(ns) - 1)])
        M = np.stack([mean_rgb[n] for n in ns]); dist = np.sqrt(((M[:, None, :] - M[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(dist, np.inf)
        rgb_p = [ns[min((dist[i, j], ns[j]) for j in range(len(ns)) if j != i)[1] and idx[min((dist[i, j], ns[j]) for j in range(len(ns)) if j != i)[1]]] for i in range(len(ns))]
        G32 = np.stack([data[n][0][32].reshape(-1) for n in ns]); G32 = (G32 - G32.mean(1, keepdims=True)) / (G32.std(1, keepdims=True) + 1e-12); sim = G32 @ G32.T / G32.shape[1]; np.fill_diagonal(sim, -np.inf)
        pat_p = [ns[max((sim[i, j], -j) for j in range(len(ns)) if j != i)[1] * -1] for i in range(len(ns))]
        hard.setdefault('hard_prev', {})[s] = dict(targets=list(prev_t), partners=list(prev_p))
        hard.setdefault('hard_next', {})[s] = dict(targets=list(next_t), partners=list(next_p))
        hard.setdefault('hard_nearest_mean_rgb', {})[s] = dict(targets=ns, partners=rgb_p)
        hard.setdefault('hard_nearest_pattern32', {})[s] = dict(targets=ns, partners=pat_p)
    for fam, m in hard.items():
        mp = MAPS / f'{fam}.json'; mp.write_bytes((json.dumps(m, indent=0) + '\n').encode()); maps[fam] = dict(path=str(mp.relative_to(O)), sha256=fsha(mp), kind='hard negative family (emissions only, same session, self excluded, lexicographic tie-break)')
    (RES / 'MAPS_INDEX.json').write_bytes((json.dumps(maps, indent=1) + '\n').encode())
    print('maps persisted:', len(maps), flush=True)
    # ---- scoring ----
    results = dict(schema='n7-raw-v1-results/v1', registration=reg, reproduction_ok=repro_ok, floor=FLOOR, random=dict(), hard=dict(), blocks=dict())
    all_maps = {**{k: json.loads((O / v['path']).read_bytes()) for k, v in maps.items()}}
    for mname, m in all_maps.items():
        fam = 'random' if mname.startswith('random') else 'hard'
        for g in GRIDS:
            pooled_rows = []
            for s in by_session:
                rows = score_map(None, m[s]['targets'], m[s]['partners'], data, g); pooled_rows += rows
                sp = SCORES / f'{mname}_grid{g}_{s}.jsonl'; sp.write_text(''.join(json.dumps(r) + '\n' for r in rows))
                results[fam].setdefault(mname, {}).setdefault(str(g), {})[s] = dict(summarise(rows), scores=str(sp.relative_to(O)), scores_sha256=fsha(sp))
                # contiguous blocks in frame order (targets are in session order)
                for bs in (30, 60):
                    results['blocks'].setdefault(mname, {}).setdefault(str(g), {}).setdefault(s, {})[str(bs)] = [dict(first=b[0]['target'], last=b[-1]['target'], **summarise(b)) for b in blocks(rows, bs)]
            results[fam][mname][str(g)]['pooled'] = summarise(pooled_rows)
        print(f'{mname}: ' + '; '.join(f"g{g} d2 {results[fam][mname][str(g)]['d2']['auroc']:.3f}/{results[fam][mname][str(g)]['d2']['paired_ordering']:.3f} v10 {results[fam][mname][str(g)]['v10']['auroc']:.3f}/{results[fam][mname][str(g)]['v10']['paired_ordering']:.3f}" for g in GRIDS), flush=True)
    # ---- endpoints ----
    def endpoint(fam):
        combos = [(mn, g, s) for mn in results[fam] for g in map(str, GRIDS) for s in by_session]
        fails = [dict(map=mn, grid=int(g), session=s, auroc=results[fam][mn][g][s]['auroc'], paired_ordering=results[fam][mn][g][s]['paired_ordering']) for mn, g, s in combos
                 if not (results[fam][mn][g][s]['auroc'] >= FLOOR and results[fam][mn][g][s]['paired_ordering'] >= FLOOR)]
        return dict(combinations=len(combos), failures=fails, status='PASS' if not fails else 'HELD', criterion=f'AUROC >= {FLOOR} and paired ordering >= {FLOOR} in every session/grid/map combination')
    results['endpoint_random_mismatch'] = endpoint('random'); results['endpoint_hard_negatives'] = endpoint('hard')
    results['seconds'] = round(time.time() - t0, 1)
    (RES / 'N7_RAW_v1_results.json').write_bytes((json.dumps(results, indent=1, default=float) + '\n').encode())
    print('random endpoint:', results['endpoint_random_mismatch']['status'], len(results['endpoint_random_mismatch']['failures']), 'failures of', results['endpoint_random_mismatch']['combinations'])
    print('hard endpoint:', results['endpoint_hard_negatives']['status'], len(results['endpoint_hard_negatives']['failures']), 'failures of', results['endpoint_hard_negatives']['combinations'])
    print(f'done in {results["seconds"]} s; results sha256 {fsha(RES / "N7_RAW_v1_results.json")}')


if __name__ == '__main__':
    main()
