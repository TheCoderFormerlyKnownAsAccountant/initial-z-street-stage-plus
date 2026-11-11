"""End-to-end check from the BUILT night data: progress index by the engine's quad test (progress_sim model of 0x10ac58,
using s_vh_path/_l/_r extracted from vis/files/hakone_night_data.gz) -> section (0x73b30 boundaries) -> streamer window
k-2..k+2 -> road drawn under the car and 150 m ahead (built section GMOs); plus the WRONG WAY test (0x89b30: car heading
dot path tangent at the progress index < 0) for a car driving forward, both directions."""
import sys, os, gzip, json, numpy as np
sys.path.insert(0, 'lib'); sys.path.insert(0, 'tools'); import xbb
import progress_sim as PS, streamer_sim as SS
d = gzip.decompress(open('vis/files/hakone_night_data.gz', 'rb').read()); tmp = '/tmp/built_paths/'; os.makedirs(tmp, exist_ok=True)
for e in xbb.parse(d):
    if e['name'] in ('s_vh_path.bin', 's_vh_path_l.bin', 's_vh_path_r.bin'): open(tmp + e['name'], 'wb').write(d[e['offset']:e['offset'] + e['size']])
P, L, R = PS.load(tmp); N = len(P)
t = np.gradient(P[:, [0, 2]], axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; nl = np.stack([-t[:, 1], t[:, 0]], 1)
cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P[:, [0, 2]], axis=0), axis=1))])
res = {}
for dr, start in ((1, 64), (-1, 2022)):
    for lat in (0.0, -6.0, 6.0):
        idx = start if dr > 0 else start - 1; ww = stuck = nodraw = 0; secs = set()
        ss = np.arange(cum[start] + 3, cum[-1] - 5, 3.0) if dr > 0 else np.arange(cum[start] - 3, 5, -3.0)
        for s in ss:
            k = int(np.searchsorted(cum, s)) - 1; f = (s - cum[k]) / (cum[k + 1] - cum[k]); p = P[k] + (P[k + 1] - P[k]) * f; p = p.copy(); p[[0, 2]] += nl[k] * lat
            if not PS.inside(L, R, idx, p):
                c = next((c for dk in range(1, 40) for c in (idx + dk, idx - dk) if 0 <= c < N - 1 and PS.inside(L, R, c, p)), None)
                if c is None: stuck += 1
                else: idx = c
            sec = SS.section(idx); secs.add(sec); Lw = [j for j in range(sec - 2, sec + 3) if 0 <= j < 32]
            if not SS.covered((p[0], p[2]), [sec]): nodraw += 1
            heading = t[k] * dr; tang = t[idx] * dr   # the path object reverses its tangent for the return direction (obj+0x1c)
            if heading @ tang < 0: ww += 1
        res[f'dir {dr:+d} lat {lat:+.0f}'] = dict(samples=len(ss), final_idx=idx, sections_visited=len(secs), stuck=stuck, no_road_in_current_section=nodraw, wrong_way=ww)
for k, v in res.items(): print(k, v)
json.dump(res, open('game_sim.json', 'w'), indent=1)
