"""Model of the engine's section selection on the new line (BOOT34W): car path index (nearest s_vh_path point) ->
section k = first k with idx < boundary[k] (0x73b30, boundaries table 0x10a37c[course 4]) -> streamer keeps blk k-2..k+2
(0x132410 sets cur+-1, +-2). For every 5 m of both directions check: the section's GMO model bbox contains the car,
road triangles are drawn under the car and >=150 m ahead within the loaded sections, and the grid spawn rows."""
import sys, json, struct, numpy as np
sys.path.insert(0, 'tools'); sys.path.insert(0, 'lib')
import width as WD, gmo, gmo_tree as G
from scipy.spatial import cKDTree
B = json.load(open('engine_sections.json'))['boundaries']; R = json.load(open('m5_ranges.json'))
name = {v[0]: 'vh_a%s.gmo' % k for k, v in R.items()}
P = np.array(WD.P); KD = cKDTree(P[:, [0, 2]]); N = len(P)
road, bbox = {}, {}
for k, nm in name.items():
    g = open('vis/sect/' + nm, 'rb').read(); parts, tex = gmo.load(g)
    pts = [p['verts'][i][0] for p in parts for t, ti in zip(p['tris'], p['tri_tex']) if ti is not None and 'road' in tex[ti] for i in t]
    road[k] = cKDTree(np.array(pts)[:, [0, 2]]) if pts else None
    T = G.GmoTree.load(g); mb = [c for c in T.find(3)[0].children if c.type == 0x8014][0]; bbox[k] = struct.unpack('<6f', mb.payload)
def section(idx):
    for k, b in enumerate(B):
        if idx < b: return k
    return len(B) - 1
def covered(q, ks, r=4.0): return any(road[k] is not None and road[k].query(q)[0] < r for k in ks)
fails = []; trans = 0; prev = None; n = 0
for dr in (1, -1):
    ss = np.arange(0, WD.CUM[-1], 5.0)[::dr]
    for s in ss:
        pos, _ = WD.frame(s); q = (pos[0], pos[2]); idx = int(KD.query(q)[1]); k = section(idx); n += 1
        if k != prev: trans += 1; prev = k
        L = [j for j in range(k - 2, k + 3) if 0 <= j < 32]
        x0, y0, z0, x1, y1, z1 = bbox[k]
        if not (x0 - 2 <= pos[0] <= x1 + 2 and z0 - 2 <= pos[2] <= z1 + 2): fails.append(('car outside bbox of current section', dr, round(s), k))
        if not covered(q, [k]): fails.append(('no road under the car in the current section', dr, round(s), k))
        ahead = s + 150 * dr
        if 0 <= ahead <= WD.CUM[-1]:
            pa, _ = WD.frame(ahead)
            if not covered((pa[0], pa[2]), L, 6.0): fails.append(('no road 150 m ahead in the loaded set', dr, round(s), k, L))
import grid as GR
spawn = [(GR.ROWS[0][0][0], GR.ROWS[0][0][2]), (GR.ROWS[1][0][0], GR.ROWS[1][0][2])]
for nm_, sp, arch in (('outbound', spawn[0], [0, 1, 31]), ('return', spawn[1], [0, 30, 31])):
    idx = int(KD.query(sp)[1]); k = section(idx)
    print(f'{nm_} spawn idx {idx} section {k} in start archive {arch}: {k in arch}, road under spawn: {covered(sp, arch)}')
print('samples', n, 'section changes', trans, 'fails', len(fails), fails[:10])
