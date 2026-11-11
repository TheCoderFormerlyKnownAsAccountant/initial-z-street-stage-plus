#!/usr/bin/env python3
"""M-HW: the new Wangan route = WMP Shuto lane ribbons 3526 + 3528 + 3530 (one carriageway, ~6.1 km:
sweeping N->S run, the JCT corner, the long straight to the SW), placed in Initial D's Happogahara world box.

Outputs (m35/hw/happou/, same formats/counts as the stock Happogahara files so the engine tables keep working):
  s_vh_path.bin  (2080 pts centre line, hdr n=2080,kind=3)   s_vh_path_l/_r.bin (edges at +-5.0 m)
  PATH_vhi_0.bin (outbound AI line, 1000 slots, ~10 m step, zero-terminated)  PATH_vho_0.bin (return)
  line.json      (transform WMP -> course, lengths, height profile)
Transform: course = (wmp_x - CX, wmp_y + DY, wmp_z - CZ) (no rotation: WMP and ID are both metres, y up)."""
import sys, os, json, struct, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, 'work/m17/f3/tools'); sys.path.insert(0, 'lib')
import ribbons as RB, idcourse as C
OUT = HERE + '/happou'; os.makedirs(OUT, exist_ok=True)
RIBBONS = (3526, 3528, 3530)
RUNS = ('2803', '2844', '2884', '2926', '2971')      # WMP runs whose chunk geometry surrounds the line
N, NAI = 2080, 1000
CX, CZ = 6325.0, -6523.0        # bbox centre of the route -> world origin (sky dome centre)
Y_BASE = 950.0                  # lowest road point -> 950 m (Happo runs 900-1020; sky/fog tuned for that)

def chain():
    pts = []
    for i in RIBBONS:
        A, B = RB.ribbon(i); c = (A + B) / 2
        if pts and np.linalg.norm(c[0] - pts[-1]) < 15: c = c[1:]
        pts += list(c)
    return np.array(pts)

def resample(P, n):
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    t = np.linspace(0, d[-1], n)
    return np.stack([np.interp(t, d, P[:, k]) for k in range(P.shape[1])], 1), d[-1]

def smooth_xy(P, win=9, it=3):
    Q = P.copy()
    for _ in range(it):
        R = Q.copy()
        for i in range(1, len(Q) - 1):
            a, b = max(0, i - win // 2), min(len(Q), i + win // 2 + 1); R[i] = Q[a:b].mean(0)
        Q = R
    return Q

def heights(XZ):
    """road height under each line point from the WMP chunk road triangles (median of road vertices within 6 m)."""
    Z = np.load(HERE + '/runs_roadpts.npz'); pts = np.concatenate([Z[k] for k in RUNS])
    from scipy.spatial import cKDTree
    t = cKDTree(pts[:, :2]); y = np.full(len(XZ), np.nan); prev = None
    for i, q in enumerate(XZ):          # follow the carriageway's own level: road vertices within 6 m and +-2.5 m of the previous height
        idx = t.query_ball_point(q, 6.0)
        if not idx: continue
        c = pts[idx, 2]
        if prev is not None:
            c = c[np.abs(c - prev) < 2.5]
            if not len(c): continue
        y[i] = np.median(c); prev = y[i]
    ok = np.isfinite(y); y = np.interp(np.arange(len(y)), np.where(ok)[0], y[ok])
    k = 41; ys = np.convolve(np.pad(y, k // 2, mode='edge'), np.ones(k) / k, mode='valid')   # ~120 m moving average
    # grade limit 4 % (expressway), forward/backward passes
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(XZ, axis=0), axis=1))])
    for _ in range(3):
        for i in range(1, len(ys)): ys[i] = np.clip(ys[i], ys[i-1] - 0.04 * (cum[i]-cum[i-1]), ys[i-1] + 0.04 * (cum[i]-cum[i-1]))
        for i in range(len(ys) - 2, -1, -1): ys[i] = np.clip(ys[i], ys[i+1] - 0.04 * (cum[i+1]-cum[i]), ys[i+1] + 0.04 * (cum[i+1]-cum[i]))
    return y, ys

def main():
    raw = chain()
    P, L = resample(raw, 1200); P = smooth_xy(P); P, L = resample(P, N)
    yr, ys = heights(P)
    ymin = ys.min(); DY = Y_BASE - ymin
    W = np.stack([P[:, 0] - CX, ys + DY, P[:, 1] - CZ], 1)
    def wpath(fn, Q): open(OUT + '/' + fn, 'wb').write(C.write_path([tuple(map(float, q)) for q in Q]))
    wpath('s_vh_path.bin', W)
    t = np.gradient(W[:, [0, 2]], axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    # progress quads (BOOT 0x10ac58): _l is on the RIGHT-hand side of the travel direction (-left normal), _r on the left,
    # exactly like stock Happogahara (_l median -4.8 m, _r +4.4 m). Round 2 had them swapped -> the car was never inside any
    # quad -> progress index stuck at the start -> no block streaming + WRONG WAY. 7.8 m covers the whole 14 m deck.
    for nm, sg in (('s_vh_path_l.bin', -1), ('s_vh_path_r.bin', 1)):
        Q = W.copy(); Q[:, 0] += nrm[:, 0] * 7.8 * sg; Q[:, 2] += nrm[:, 1] * 7.8 * sg; wpath(nm, Q)
    # AI lines: racing line = centre line pulled toward the inside of bends (max 3.5 m), 10 m step, zero-terminated
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(W[:, [0, 2]], axis=0), axis=1))])
    h = np.unwrap(np.arctan2(t[:, 1], t[:, 0])); k = np.gradient(h) / np.gradient(cum)
    ks = np.convolve(np.pad(k, 30, mode='edge'), np.ones(61) / 61, mode='valid')
    off = np.clip(ks * 900.0, -3.5, 3.5)            # + = toward +normal (left) on left bends
    def ai(rev):
        s = np.arange(0, cum[-1], 10.0); s = s[::-1] if rev else s
        Q = np.stack([np.interp(s, cum, W[:, k_]) + (np.interp(s, cum, nrm[:, k_ // 2] * off) if k_ != 1 else 0) for k_ in (0, 1, 2)], 1)
        buf = np.zeros((NAI, 3), np.float32); buf[:len(Q)] = Q; return buf.tobytes(), len(Q)
    (bo, no), (br, nr) = ai(False), ai(True)
    open(OUT + '/PATH_vhi_0.bin', 'wb').write(bo); open(OUT + '/PATH_vho_0.bin', 'wb').write(br)
    info = dict(ribbons=RIBBONS, runs=RUNS, length_m=round(float(cum[-1]), 1), n=N, spacing_m=round(float(cum[-1] / (N - 1)), 3),
                transform=dict(CX=CX, CZ=CZ, DY=round(float(DY), 3)), y_range=[round(float(W[:, 1].min()), 1), round(float(W[:, 1].max()), 1)],
                max_grade=round(float(np.max(np.abs(np.diff(W[:, 1])) / np.diff(cum))), 4), ai_points=[no, nr],
                min_radius_m=round(float(1 / max(np.abs(ks).max(), 1e-6)), 1), extent_r=round(float(np.linalg.norm(W[:, [0, 2]], axis=1).max()), 1))
    json.dump(info, open(HERE + '/line.json', 'w'), indent=1); print(json.dumps(info))

if __name__ == '__main__':
    main()
