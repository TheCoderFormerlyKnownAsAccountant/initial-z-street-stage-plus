"""M3: regenerate Happogahara collision (1LCR in NMZIP) for sections 0-1 (path idx 0..K) as a flat
highway deck + barrier slopes on the stock centre line (same lateral range as the v7 visual deck),
stitched to the remaining stock mesh; adjacency rebuilt; aux-layer triangle refs remapped.
Writes m3/out/s_vh_colli_{0,1}.bin.nz (padded to the stock entry size) + m3/out/*.bin raw + report."""
import sys, os, gzip, math, struct, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, 'lib')
import idcourse as C, xbb, hkcommon as M, width as WD, bend as BD
import numpy as _npc
_NCUM = _npc.concatenate([[0], _npc.cumsum(_npc.linalg.norm(_npc.diff(BD.NEW[:, [0, 2]], axis=0), axis=1))])
def _cf(sv): return float(BD.cross_new(_npc.interp(min(max(sv, 0.0), _NCUM[-1]), _NCUM, _npc.arange(len(_NCUM)))))
F3 = os.path.dirname(HERE); OUT = os.environ.get('COUT', os.path.dirname(HERE) + '/colli_out'); os.makedirs(OUT, exist_ok=True)
U = M.U; PATH = M.PATH
K = int(os.environ.get('M_K', '2079'))   # last path index replaced (end of the converted sections)
ROW, ROAD_ATTR, WALL_ATTR = 10.0, 16, 0x800e
FACE_H, FACE_OUT, SLOPE_H, SLOPE_OUT = 4.0, 0.05, 0.0, 7.0
MINW = 1.5   # M20 v3: minimum flat wall-band width (m)  # vertical 4 m wall face, then a flat top (nothing climbable)
EXT = 30.0   # deck extension beyond both path ends (run-off / start areas)
# path parameter
cum = [0.0]
for a, b in zip(PATH, PATH[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[2] - a[2]))
import numpy as _np
_PA = _np.array([(p[0], p[2]) for p in PATH]); _CUM = None
def proj_all(Q):
    """Vectorised projection of points Q (n,3) onto the whole centre line -> (s, lateral) arrays."""
    A = _PA[:-1]; B = _PA[1:]; D = B - A; L2 = (D ** 2).sum(1); L = _np.sqrt(L2); cm = _np.array(cum[:-1])
    out_s = _np.empty(len(Q)); out_l = _np.empty(len(Q))
    for i, q in enumerate(Q):
        t = ((q[0] - A[:, 0]) * D[:, 0] + (q[2] - A[:, 1]) * D[:, 1]) / L2; tc = _np.clip(t, 0, 1)
        e = A + D * tc[:, None] - _np.array([q[0], q[2]]); d2 = (e ** 2).sum(1); k = int(d2.argmin())
        out_s[i] = cm[k] + t[k] * L[k]; out_l[i] = ((q[0] - A[k, 0]) * -D[k, 1] + (q[2] - A[k, 1]) * D[k, 0]) / L[k]
    return out_s, out_l
def proj(q, lo=0, hi=260):
    best = None
    for k in range(lo, min(hi, len(PATH) - 1)):
        a, b = PATH[k], PATH[k + 1]; dx, dz = b[0] - a[0], b[2] - a[2]; L2 = dx * dx + dz * dz or 1
        t = ((q[0] - a[0]) * dx + (q[2] - a[2]) * dz) / L2; tc = max(0, min(1, t))
        ex, ez = a[0] + dx * tc - q[0], a[2] + dz * tc - q[2]; d2 = ex * ex + ez * ez
        if best is None or d2 < best[0]:
            L = math.sqrt(L2); best = (d2, cum[k] + t * L, ((q[0] - a[0]) * -dz + (q[2] - a[2]) * dx) / L)
    return best[1], best[2]          # s (may be <0 before the start), signed lateral (+ = left normal)
def at(sv):
    # beyond the ends: extrapolate straight along the first/last segment (run-off areas)
    if sv < 0: j = 0
    elif sv > cum[-1]: j = len(cum) - 2
    else: j = next(k for k in range(len(cum) - 1) if cum[k + 1] >= sv)
    a, b = PATH[j], PATH[j + 1]; t = (sv - cum[j]) / ((cum[j + 1] - cum[j]) or 1)
    dx, dz = b[0] - a[0], b[2] - a[2]; L = math.hypot(dx, dz) or 1
    return [a[i] + (b[i] - a[i]) * t for i in range(3)], (-dz / L, dx / L)
def deck_lat():
    tris = M.load_wmp([1813, 1814]); place = M.frame(tris, (0, 86), +1)
    lats = sorted(place.local(q)[1] for P, _, c, tn in tris if tn.startswith(('ROAD', 'LINE')) for q in P)
    near0 = [l for l in lats if abs(l) < 7.6]
    return near0[int(len(near0) * 0.01)], near0[int(len(near0) * 0.99)]

def build(raw, lmin, lmax, label):
    c = C.Colli(raw); nv0, nt0 = c.nv, c.nt
    sK = cum[K]
    S_, L_ = proj_all([v[:3] for v in c.verts]); pv = list(zip(S_, L_))
    def in_region(i): s, l = pv[i]; return 0.0 <= s <= sK and abs(l) < 25
    def in_corr(i): s_, l_ = pv[i]; return 0.0 <= s_ <= sK and abs(l_) < 16
    full = K >= len(PATH) - 1
    removed = [True if full else (all(in_region(i) for i in t[:3]) or any(in_corr(i) for i in t[:3])) for t in c.tris]
    keep_t = [i for i, r in enumerate(removed) if not r]
    used = sorted({i for ti in keep_t for i in c.tris[ti][:3]})
    vmap = {old: new for new, old in enumerate(used)}
    verts = [list(c.verts[i]) for i in used]
    tris = [[vmap[x] for x in c.tris[ti][:3]] + [c.tris[ti][7]] for ti in keep_t]
    oldnew_t = {ti: n for n, ti in enumerate(keep_t)}
    # boundary vertices of the kept mesh next to the removed region (edges whose neighbour was removed)
    bnd = {}
    for ti in keep_t:
        t = c.tris[ti]; adj = {0: t[4], 1: t[5], 2: t[3]}  # edge k=(v_k, v_k+1) -> field (perm 1,2,0)
        for k in range(3):
            a = adj[k]
            if a != 0xffff and removed[a]:
                for x in (t[k], t[(k + 1) % 3]): bnd[vmap[x]] = pv[x]
    # new deck
    base = len(verts)
    # adaptive rows: chord sagitta at the outer wall line (|lat| ~ 14 m) kept under ~0.25 m on tight bends
    def heading(sv):
        _, (nx, nz) = at(sv); return math.atan2(nz, nx)
    s_end = sK + (EXT if full else 0.0)
    svs = [-EXT if full else 0.0]
    while svs[-1] < s_end:
        s0 = svs[-1]; d = abs((heading(min(sK, s0 + 5)) - heading(s0) + math.pi) % (2 * math.pi) - math.pi) / 5.0
        R = 1.0 / max(d, 1e-4); chord = max(2.0, min(ROW, math.sqrt(8 * 0.08 * (R + 7.0))))
        svs.append(min(s_end, s0 + chord))
    nrow = len(svs) - 1; ncol = 3
    cols = [lmin + (lmax - lmin) * j / ncol for j in range(ncol + 1)]
    grid = []; rowcols = []; prev_top = {}
    for r in range(nrow + 1):
        sv = svs[r]; p, (nx, nz) = WD.frame(sv); row = []
        lo, hi = WD.lat_range2(sv); ow = WD.outer_at(min(max(sv, 0.0), cum[-1]))
        rcols = [lo + (hi - lo) * j / ncol for j in range(ncol + 1)]; rowcols.append(rcols)
        cf = _cf(sv)
        for l in rcols:
            verts.append([p[0] + nx * l, p[1] + cf * l, p[2] + nz * l, 0.0, 1.0, 0.0, 0.0, 0.0]); row.append(len(verts) - 1)
        # walls on both edges: steep face (FACE_H up, FACE_OUT out) then embankment (SLOPE_H more up, SLOPE_OUT out)
        kk = WD.curv(min(max(sv, 0.0), cum[-1])); Rr = 1.0 / max(abs(kk), 1e-6)
        for l, sgn in ((lo, -1), (hi, +1)):
            # M20 v3: band width >= MINW (no slivers); on the inside of tight bends, if the outer line would fold back,
            # reuse the previous row's outer vertex (fan) instead of shrinking the band towards zero width.
            tw = max(min(MINW, max(ow, 0.6)), min(SLOPE_OUT, ow))          # >= MINW unless another leg is closer
            if kk * sgn > 0: tw = max(0.6, min(tw, 0.5 * (Rr - abs(l))))   # inner side: outer line keeps >= half the deck-edge length -> band grade <= ~2x road grade
            tx, tz = nz, -nx
            qx, qz = p[0] + nx * (l + sgn * (FACE_OUT + tw)), p[2] + nz * (l + sgn * (FACE_OUT + tw))
            if sgn in prev_top and (qx - prev_top[sgn][0]) * tx + (qz - prev_top[sgn][1]) * tz <= 0.5:
                # would fold back: step 0.6 m forward from the previous outer vertex instead (no slivers, no fans)
                qx, qz = prev_top[sgn][0] + tx * 0.6, prev_top[sgn][1] + tz * 0.6
                lat = ((qx - p[0]) * nx + (qz - p[2]) * nz) * sgn - abs(l)
                if lat < 0.6:
                    qx += nx * sgn * (0.6 - lat); qz += nz * sgn * (0.6 - lat)
            verts.append([qx, p[1] + cf * l, qz, 0.0, 1.0, 0.0, 0.0, 0.0]); row.append(len(verts) - 1)
            prev_top[sgn] = (qx, qz, len(verts) - 1)
        grid.append(row)
    def up_tri(a, b, cc, attr):
        if len({a, b, cc}) < 3: return          # M20 v3: fan rows reuse an outer vertex -> skip the degenerate triangle
        P = [verts[x][:3] for x in (a, b, cc)]
        e1 = [P[1][k] - P[0][k] for k in range(3)]; e2 = [P[2][k] - P[0][k] for k in range(3)]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        tris.append([a, b, cc, attr] if ny > 0 else [a, cc, b, attr])
    nd = 0
    row_t0 = []
    for r in range(nrow):
        A, B = grid[r], grid[r + 1]; row_t0.append(len(tris))
        for j in range(ncol):
            up_tri(A[j], B[j], A[j + 1], ROAD_ATTR); up_tri(A[j + 1], B[j], B[j + 1], ROAD_ATTR); nd += 2
        # row layout (M20): deck 0..ncol, left band outer ncol+1, right band outer ncol+2
        for chain in ((0, ncol + 1), (ncol, ncol + 2)):
            for u, v in zip(chain, chain[1:]):
                up_tri(A[u], B[u], A[v], WALL_ATTR); up_tri(A[v], B[u], B[v], WALL_ATTR)
    # M21 v6: course ends. After the deck's EXT m asphalt run-off (with side bands): a full-width asphalt apron
    # (band outer to band outer, APRON m deep) so every point around the end row is on mesh + cells; small wall
    # triangles on the apron's sides and a wall fan cap at its far end. Every end wall triangle has an EDGE on
    # asphalt (a car pushed into it can always back out; no wall->wall pocket, no off-mesh corner).
    APRON, END_D, SIDE_W = 12.0, 6.0, 3.0; end_strips = []
    if full:
        for r_end, sv, sg in ((0, svs[0], -1.0), (nrow, svs[-1], 1.0)):
            p, (nx, nz) = WD.frame(sv); tx, tz = nz * sg, -nx * sg
            rowA = [grid[r_end][ncol + 1]] + grid[r_end][:ncol + 1] + [grid[r_end][ncol + 2]]
            rowB = []
            for x in rowA:
                q = verts[x]; verts.append([q[0] + tx * APRON, q[1], q[2] + tz * APRON, 0.0, 1.0, 0.0, 0.0, 0.0]); rowB.append(len(verts) - 1)
            t0 = len(tris)
            for j in range(len(rowA) - 1):
                up_tri(rowA[j], rowB[j], rowA[j + 1], ROAD_ATTR); up_tri(rowA[j + 1], rowB[j], rowB[j + 1], ROAD_ATTR)
            t_apron = (t0, len(tris))
            t1 = len(tris)
            for ia, ib, side in ((rowA[0], rowB[0], -1.0), (rowA[-1], rowB[-1], 1.0)):   # side walls: one triangle each
                qa, qb = verts[ia], verts[ib]
                mx, mz = (qa[0] + qb[0]) / 2 + nx * side * SIDE_W, (qa[2] + qb[2]) / 2 + nz * side * SIDE_W
                verts.append([mx, (qa[1] + qb[1]) / 2, mz, 0.0, 1.0, 0.0, 0.0, 0.0]); up_tri(ia, ib, len(verts) - 1, WALL_ATTR)
            cx = sum(verts[x][0] for x in rowB) / len(rowB); cz = sum(verts[x][2] for x in rowB) / len(rowB); cy = sum(verts[x][1] for x in rowB) / len(rowB)
            verts.append([cx + tx * END_D, cy, cz + tz * END_D, 0.0, 1.0, 0.0, 0.0, 0.0]); apex = len(verts) - 1
            for j in range(len(rowB) - 1):
                up_tri(rowB[j], rowB[j + 1], apex, WALL_ATTR)
            end_strips.append((rowA, rowB, t_apron, (t1, len(tris))))
    if False:   # M20: no separate end-wall quads (unconnected; the open deck end edge already acts as a wall)
        # end walls: one tall, wide wall across each end (covers the deck, both wall faces and wall tops; no corner slots)
        for sv, sgn in ((svs[0], -1), (svs[-1], +1)):
            p, (nx, nz) = WD.frame(sv); lo, hi = WD.lat_range2(sv); y0 = p[1] - 1.0
            tx, tz = nz, -nx; ye = p[1] - 0.05      # M20: flat end band (road height), 9 m beyond the run-off end
            q = [(p[0] + nx * l + tx * sgn * f, ye, p[2] + nz * l + tz * sgn * f) for l in (lo - 9.0, hi + 9.0) for f in (0.0, 9.0)]
            b0 = len(verts)
            for v in q: verts.append([v[0], v[1], v[2], 0.0, 1.0, 0.0, 0.0, 0.0])
            up_tri(b0, b0 + 2, b0 + 1, WALL_ATTR); up_tri(b0 + 1, b0 + 2, b0 + 3, WALL_ATTR)
    if False:
        for row, sgn in ((grid[0], -1), (grid[-1], +1)):
            sv = svs[0] if sgn < 0 else svs[-1]; p, (nx, nz) = WD.frame(sv)
            tx, tz = nz * -1, nx      # path tangent (normal rotated)
            tops = []
            for j in range(ncol + 1):
                q = verts[row[j]]
                verts.append([q[0] + tx * sgn * 0.05, q[1] + FACE_H, q[2] + tz * sgn * 0.05, 0.0, 1.0, 0.0, 0.0, 0.0]); tops.append(len(verts) - 1)
            for j in range(ncol):
                up_tri(row[j], row[j + 1], tops[j], WALL_ATTR); up_tri(tops[j], row[j + 1], tops[j + 1], WALL_ATTR)
    # M20 v3: relax band-outer vertex heights so no wall-band triangle is steep (a car pushed onto the band must stay
    # level). Only outer vertices move, within the height range of their neighbours; deck heights are untouched.
    outer = set(); [outer.update((row[ncol + 1], row[ncol + 2])) for row in grid]
    vt = {}
    for ti, t in enumerate(tris):
        for x in t[:3]:
            if x in outer: vt.setdefault(x, []).append(ti)
    def tri_ny(t):
        P = [verts[x][:3] for x in t[:3]]
        e1 = [P[1][k] - P[0][k] for k in range(3)]; e2 = [P[2][k] - P[0][k] for k in range(3)]
        n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
        L = math.sqrt(sum(v * v for v in n)) or 1e-9; return abs(n[1]) / L
    for _it in range(6):
        for x, tl in vt.items():
            if min(tri_ny(tris[ti]) for ti in tl) >= 0.97: continue
            ys = [verts[y][1] for ti in tl for y in tris[ti][:3] if y != x]
            lo_, hi_ = min(ys), max(ys); best = (min(tri_ny(tris[ti]) for ti in tl), verts[x][1])
            for k in range(21):
                verts[x][1] = lo_ + (hi_ - lo_) * k / 20
                q = min(tri_ny(tris[ti]) for ti in tl)
                if q > best[0]: best = (q, verts[x][1])
            verts[x][1] = best[1]
    # stitch: zipper between a deck end row and the stock boundary vertices near that end
    nst = 0
    for end_s, row in ((0.0, grid[0]), (sK, grid[-1])):
        chain = sorted([(l, i) for i, (s, l) in bnd.items() if abs(s - end_s) < 12 and lmin - 4 <= l <= lmax + 4])
        rc = rowcols[0] if row is grid[0] else rowcols[-1]
        drow = sorted([(l, row[j]) for j, l in enumerate(rc)])
        i = j = 0
        while chain and (i < len(drow) - 1 or j < len(chain) - 1):
            if j < len(chain) - 1 and (i == len(drow) - 1 or chain[j + 1][0] <= drow[i + 1][0]):
                up_tri(drow[i][1], chain[j][1], chain[j + 1][1], ROAD_ATTR); j += 1
            else:
                up_tri(drow[i][1], chain[j][1], drow[i + 1][1], ROAD_ATTR); i += 1
            nst += 1
    # adjacency (perm: field3 = edge (v2,v0), field4 = edge (v0,v1), field5 = edge (v1,v2))
    E = {}
    for ti, t in enumerate(tris):
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]; E.setdefault((min(a, b), max(a, b)), []).append(ti)
    def nb(ti, k):
        t = tris[ti]; a, b = t[k], t[(k + 1) % 3]; o = [x for x in E[(min(a, b), max(a, b))] if x != ti]
        return o[0] if o else 0xffff
    # vertex normals for new vertices
    acc = {i: [0, 0, 0] for i in range(base, len(verts))}
    for t in tris:
        P = [verts[x][:3] for x in t[:3]]; e1 = [P[1][k] - P[0][k] for k in range(3)]; e2 = [P[2][k] - P[0][k] for k in range(3)]
        n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
        for x in t[:3]:
            if x in acc: acc[x] = [acc[x][k] + n[k] for k in range(3)]
    for i, n in acc.items():
        L = math.sqrt(sum(v * v for v in n)) or 1; verts[i][3:6] = [v / L for v in n]
    # aux layer: remap triangle refs
    aux = bytearray(c.tail)
    newcent = [[sum(verts[x][k] for x in t[:3]) / 3 for k in (0, 2)] for t in tris]
    road_ids = [i for i in range(len(keep_t), len(tris)) if tris[i][3] == ROAD_ATTR]
    def contains(i, x, z):
        a, b, cc = [verts[k] for k in tris[i][:3]]
        d = (b[2] - cc[2]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[2] - cc[2])
        if abs(d) < 1e-9: return False
        l1 = ((b[2] - cc[2]) * (x - cc[0]) + (cc[0] - b[0]) * (z - cc[2])) / d; l2 = ((cc[2] - a[2]) * (x - cc[0]) + (a[0] - cc[0]) * (z - cc[2])) / d
        return min(l1, l2, 1 - l1 - l2) >= -1e-6
    remap_stats = [0, 0, 0]
    for r in range(len(aux) // 56):
        old = struct.unpack_from('<I', aux, 56 * r + 52)[0]
        q = struct.unpack_from('<9f', aux, 56 * r + 16); cx, cz = (q[0] + q[3] + q[6]) / 3, (q[2] + q[5] + q[8]) / 3
        if old in oldnew_t: new = oldnew_t[old]; remap_stats[0] += 1
        else:
            near = sorted(road_ids, key=lambda i: (newcent[i][0] - cx) ** 2 + (newcent[i][1] - cz) ** 2)[:40]
            hit = [i for i in near if contains(i, cx, cz)]
            new = hit[0] if hit else near[0]; remap_stats[1 if hit else 2] += 1
        struct.pack_into('<I', aux, 56 * r + 52, new)
    if full:
        # regenerate the aux layer (flat y=890 cells, each pointing at the deck triangle under its centre) to cover our corridor
        # M20: one aux cell pair per deck row spanning the FULL collision width (band outer to band outer), so every
        # point of the mesh lies in a cell (the game's ground lookup 0x9a224 loses the car outside all cells -> endless
        # "airborne" tumble). Start triangle = the row's deck triangle under the cell centre (walk 0x99e84 reaches the bands).
        recs = bytearray(); AUXY = 890.0
        for r in range(nrow):
            A0, B0, A1, B1 = (verts[grid[r][ncol + 1]], verts[grid[r][ncol + 2]], verts[grid[r + 1][ncol + 1]], verts[grid[r + 1][ncol + 2]])
            A0, B0, A1, B1 = [(q[0], q[2]) for q in (A0, B0, A1, B1)]
            rt = [row_t0[r] + j for j in range(2 * ncol)]
            for Q in ((A0, A1, B0), (B0, A1, B1)):
                ny = (Q[1][1] - Q[0][1]) * (Q[2][0] - Q[0][0]) - (Q[1][0] - Q[0][0]) * (Q[2][1] - Q[0][1])
                if abs(ny) < 1e-6: continue          # degenerate (shared outer vertex)
                if ny <= 0: Q = (Q[0], Q[2], Q[1])
                cx = sum(q[0] for q in Q) / 3; cz = sum(q[1] for q in Q) / 3
                hit = [i for i in rt if contains(i, cx, cz)]
                start = hit[0] if hit else min(rt, key=lambda i: (newcent[i][0] - cx) ** 2 + (newcent[i][1] - cz) ** 2)
                recs += struct.pack('<4f9fI', 0.0, 1.0, 0.0, -AUXY, *[v for q in Q for v in (q[0], AUXY, q[1])], start)
        for rowA, rowB, (a0, a1), (w0, w1) in end_strips:    # M21 v6: apron cells (row quads) + one cell per end wall tri
            ap_ids = list(range(a0, a1))
            for j in range(len(rowA) - 1):
                A0, B0, A1, B1 = [(verts[x][0], verts[x][2]) for x in (rowA[j], rowA[j + 1], rowB[j], rowB[j + 1])]
                for Q in ((A0, A1, B0), (B0, A1, B1)):
                    ny = (Q[1][1] - Q[0][1]) * (Q[2][0] - Q[0][0]) - (Q[1][0] - Q[0][0]) * (Q[2][1] - Q[0][1])
                    if abs(ny) < 1e-6: continue
                    if ny <= 0: Q = (Q[0], Q[2], Q[1])
                    cx = sum(q[0] for q in Q) / 3; cz = sum(q[1] for q in Q) / 3
                    hit = [i for i in ap_ids if contains(i, cx, cz)]
                    start = hit[0] if hit else min(ap_ids, key=lambda i: (newcent[i][0] - cx) ** 2 + (newcent[i][1] - cz) ** 2)
                    recs += struct.pack('<4f9fI', 0.0, 1.0, 0.0, -AUXY, *[v for q in Q for v in (q[0], AUXY, q[1])], start)
            for ti in range(w0, w1):
                Q = [(verts[x][0], verts[x][2]) for x in tris[ti][:3]]
                ny = (Q[1][1] - Q[0][1]) * (Q[2][0] - Q[0][0]) - (Q[1][0] - Q[0][0]) * (Q[2][1] - Q[0][1])
                if ny <= 0: Q = (Q[0], Q[2], Q[1])
                recs += struct.pack('<4f9fI', 0.0, 1.0, 0.0, -AUXY, *[v for q in Q for v in (q[0], AUXY, q[1])], ti)
        aux = recs
    # write 1LCR
    head = bytearray(c.head); nv, nt = len(verts), len(tris)
    vo = c.vo; to = vo + 32 * nv; ao = to + 16 * nt
    struct.pack_into('<4I', head, 0x10, nv, vo, nt, to); struct.pack_into('<I', head, 0x24, ao); struct.pack_into('<I', head, 0x28, len(aux) // 56); struct.pack_into('<I', head, 0x2c, ao)
    out = bytearray(head)
    for v in verts: out += struct.pack('<8f', *v)
    for ti, t in enumerate(tris):
        out += struct.pack('<8H', t[0], t[1], t[2], nb(ti, 2), nb(ti, 0), nb(ti, 1), 0xffff, t[3])
    out += aux
    rep = dict(label=label, stock_verts=nv0, stock_tris=nt0, removed_tris=sum(removed), kept_tris=len(keep_t),
               deck_tris=nd, wall_tris=8 * nrow, stitch_tris=nst, verts=nv, tris=nt, raw=len(out), stock_raw=len(raw),
               boundary_verts=len(bnd), aux_kept_contained_nearest=remap_stats, open_edges=sum(1 for k, v in E.items() if len(v) == 1))
    return bytes(out), rep, (verts, tris)

if __name__ == '__main__':
    lmin, lmax = -M.HALF, M.HALF; reps = []
    for arch, name in (('happou_night_start_data1.gz', 's_vh_colli_0.bin.nz'), ('happou_night_start_data2.gz', 's_vh_colli_1.bin.nz')):
        d = gzip.decompress(open(U + arch, 'rb').read())
        e = [e for e in xbb.parse(d) if e['name'] == name][0]; nz = d[e['offset']:e['offset'] + e['size']]
        raw = C.nmzip_dec(nz)
        new, rep, _ = build(raw, lmin, lmax, name)
        C.Colli(new)  # parses
        enc = C.nmzip_enc(new); rep['nz'] = len(enc); rep['nz_stock'] = len(nz)
        assert len(enc) <= len(nz), rep
        open(OUT + '/' + name, 'wb').write(enc + b'\0' * (len(nz) - len(enc)))
        open(OUT + '/' + name.replace('.nz', ''), 'wb').write(new)
        reps.append(rep); print(rep)
    json.dump(dict(lmin=lmin, lmax=lmax, K=K, reports=reps), open(OUT + '/report.json', 'w'), indent=1)
