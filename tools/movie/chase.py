"""M49: straights flat out (side-by-side / slipstream), short sharp drifts only in the tight bends
(feint -> snap entry -> hold -> quick counter-steer exit); time gaps close up on straights, single file in bends.
M46 drift chase on the Hakone course (downhill): drift kinematics, tyre smoke, sub-shot cameras.
Cars follow one racing line with time delays (Devil Z lead, Bunta +DB s, Takumi +DT s), so they slide through each
bend in sequence. Drift: nose rotated toward the inside of the bend by alpha = 46 deg * tanh(110 * |kappa|) (look-ahead
12 m), front wheels counter-steered toward the travel direction; speed 24..42 m/s from curvature."""
import math
import numpy as np, cv2
import hrender as HR

DIR = -1                       # downhill = decreasing s
DB, DT = 0.36, 0.72            # Bunta / Takumi time delay behind the Devil Z (s)
OFF = (0.0, 0.85, -0.85)       # lane offsets so the three don't hide each other head-on
L_ = 6000
_S = np.arange(0.0, L_ + 1.0, 1.0)
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def _tables():
    P = np.array([HR.path(s) for s in _S]); P1 = np.array([HR.path(s, 1.0) for s in _S])
    d = np.gradient(P, axis=0); th = np.unwrap(np.arctan2(d[:, 0], d[:, 2]))
    k = np.gradient(th)                                   # rad / m (signed, increasing s)
    g = cv2.getGaussianKernel(41, 9).ravel(); ks = np.convolve(np.pad(k, 20, mode='edge'), g, 'valid')
    g2 = cv2.getGaussianKernel(121, 28).ravel(); kl = np.convolve(np.pad(k, 60, mode='edge'), g2, 'valid')
    nl = P1 - P; nl[:, 1] = 0; nl /= np.linalg.norm(nl, axis=1, keepdims=True)
    T = d.copy(); T[:, 1] = 0; T /= np.linalg.norm(T, axis=1, keepdims=True)
    dT = np.gradient(T, axis=0)
    ins = np.sign(np.einsum('ij,ij->i', nl, dT) + 1e-12)  # +1: inside of the bend is +lat
    return dict(P=P, ks=ks, kl=kl, nl=nl, T=T, ins=ins)
_TB = None
def TB():
    global _TB
    if _TB is None: _TB = _tables()
    return _TB
def _i(s, key):
    t = TB()[key]; s = min(max(s, 0.0), L_ - 1.001); i = int(s); f = s - i
    return t[i] * (1 - f) + t[i + 1] * f

# tight bends [lo, hi] in s (downhill: entry at hi, exit at lo), R < 160 m
def _bends():
    ks = TB()['ks']; R = 1 / np.maximum(np.abs(ks), 1e-5); tight = R < 160; sg = np.sign(ks); out = []; i = 0
    while i < len(ks):
        if tight[i]:
            j = i
            while j < len(ks) and tight[j] and sg[j] == sg[i]: j += 1
            if j - i > 30: out.append((float(i), float(j), int(i + (j - i) // 2)))
            i = j
        else: i += 1
    return out
_BD = None
def BD():
    global _BD
    if _BD is None: _BD = _bends()
    return _BD
V_STR, V_BEND = 50.0, 27.0
def _bend_at(s, pre=70.0, post=130.0):
    """nearest bend whose influence covers s: (d_in = metres past the entry, length, mid index) or None"""
    best = None
    for lo, hi, mid in BD():
        d_in = hi - s if DIR < 0 else s - lo; Lb = hi - lo
        if -pre <= d_in <= Lb + post:
            if best is None or abs(d_in - Lb / 2) < abs(best[0] - best[1] / 2): best = (d_in, Lb, mid)
    return best
def speed(s):
    b = _bend_at(s)
    if b is None: return V_STR
    d, Lb, _ = b
    if d < 0: x = smooth(-d / 60.0); return V_BEND + (V_STR - V_BEND) * x          # braking zone 60 m
    if d <= Lb: return V_BEND
    return V_BEND + (V_STR - V_BEND) * smooth((d - Lb) / 110.0)                   # drive out
def drift_alpha(s):
    """signed slip angle (deg, + = nose to the inside of the coming bend) and the bend's mid index"""
    b = _bend_at(s, 30.0, 20.0)
    if b is None: return 0.0, None
    d, Lb, mid = b; H = min(Lb - 14.0, 46.0)
    if d < -26: return 0.0, mid
    if d < -6: return -9.0 * math.sin(math.pi * (d + 26) / 20.0), mid                # feint toward the outside
    if d < 6: return 40.0 * smooth((d + 6) / 12.0), mid                               # snap in
    if d < H: a = 40.0 - 8.0 * (d - 6) / max(H - 6, 1)                                # hold 40 -> 32
    else: a = 32.0 - 20.0 * smooth((d - H) / 18.0)                                    # long bend: settle to 12
    if d < Lb - 12: return a, mid
    aL = (40.0 - 8.0 * (Lb - 18) / max(H - 6, 1)) if Lb - 12 < H else 12.0 if Lb - 12 > H + 18 else 32.0 - 20.0 * smooth((Lb - 12 - H) / 18.0)
    if d < Lb + 3: return aL + (-7.0 - aL) * smooth((d - (Lb - 12)) / 15.0), mid      # quick counter-steer
    if d < Lb + 14: return -7.0 * (1 - smooth((d - Lb - 3) / 11.0)), mid
    return 0.0, mid
def straightness(s):
    b = _bend_at(s, 45.0, 35.0)
    if b is None: return 1.0
    d, Lb, _ = b
    if d < 0: return smooth(-d / 45.0)
    if d <= Lb: return 0.0
    return smooth((d - Lb) / 35.0)

class Run:
    """lead trajectory s(t) for t in [-3, D]: integrated at 240 Hz from s(0) = s0."""
    def __init__(self, s0, D, vmul=1.0):
        self.dt = 1 / 240.0; self.t0 = -3.0; n = int((D - self.t0) / self.dt) + 2
        s = np.empty(n); k0 = int(-self.t0 / self.dt); s[k0] = s0
        for k in range(k0, n - 1): s[k + 1] = s[k] + DIR * speed(s[k]) * vmul * self.dt
        for k in range(k0, 0, -1): s[k - 1] = s[k] - DIR * speed(s[k]) * vmul * self.dt
        self.s = s
    def at(self, t):
        x = (t - self.t0) / self.dt; i = int(min(max(x, 0), len(self.s) - 2)); f = x - i
        return self.s[i] * (1 - f) + self.s[i + 1] * f

def lat_line(s, amp=2.2, off=0.0):
    k = _i(s, 'kl'); return float(np.clip(_i(s, 'ins') * amp * math.tanh(abs(k) * 140) + off, -3.4, 3.4))

def car_state(s, t, phase=0.0, amp=2.2, off=0.0):
    """M49: slip from the bend envelope (drift_alpha), not from curvature"""
    w = straightness(s); lat = float(np.clip(lat_line(s, amp, 0.0) * (1 - 0.6 * w) + off, -3.9, 3.9)); pos = HR.path(s, lat, 0.0)
    T = _i(s, 'T'); T = T / np.linalg.norm(T); Tt = DIR * T
    a, mid = drift_alpha(s)
    a += (1.6 * math.sin(t * 3.1 + phase) * min(1.0, abs(a) / 20.0)) + 0.6 * math.sin(t * 7.3 + phase) * w
    if mid is None: mid = int(min(max(s, 0), L_ - 1))
    nin = TB()['ins'][mid] * _i(s, 'nl'); nin = nin / np.linalg.norm(nin)
    ar = math.radians(a); fwd = math.cos(ar) * Tt + math.sin(ar) * nin; fwd = fwd / np.linalg.norm(fwd)
    up = np.array([0, 1.0, 0]); fx = np.cross(up, fwd)
    steer = math.atan2(Tt @ fx, Tt @ fwd) * 0.85; steer = max(-0.6, min(0.6, steer))
    return dict(pos=pos, fwd=fwd, fx=fx, steer=steer, alpha=a, s=s, lat=lat, w=w)

def car_state_m46(s, t, phase=0.0, amp=2.2, off=0.0):
    """world pose of a drifting car at path position s: pos (ground), fwd (heading), steer (rad, body frame), alpha (deg)."""
    lat = lat_line(s, amp, off); pos = HR.path(s, lat, 0.0)
    T = _i(s, 'T'); T = T / np.linalg.norm(T); Tt = DIR * T
    ka = _i(s + DIR * 12, 'ks'); a = 46.0 * math.tanh(abs(ka) * 110) + 3.0 * math.sin(t * 3.1 + phase) * min(1, abs(ka) * 300)
    nin = _i(s + DIR * 12, 'ins') * _i(s, 'nl'); nin = nin / np.linalg.norm(nin)
    ar = math.radians(max(a, 0.0)); fwd = math.cos(ar) * Tt + math.sin(ar) * nin; fwd = fwd / np.linalg.norm(fwd)
    up = np.array([0, 1.0, 0]); fx = np.cross(up, fwd)
    steer = math.atan2(Tt @ fx, Tt @ fwd) * 0.85; steer = max(-0.6, min(0.6, steer))
    return dict(pos=pos, fwd=fwd, fx=fx, steer=steer, alpha=a, s=s, lat=lat)

# straights: Bunta side by side with the Devil Z, Takumi in the Devil Z's slipstream; bends: single file
GAP_B = (0.30, 0.055); GAP_T = (0.60, 0.17)      # (bend, straight) time gaps
LAT_S = (-1.25, 1.35, -1.15)                      # lateral lanes on the straights (dz, bunta, takumi)
def delays(run, t):
    """time gaps of Bunta / Takumi; driven by the straightness the lead had ~0.5 s ago, smoothed over 1.2 s"""
    ws = [straightness(run.at(t - 0.5 + k * 0.1)) for k in range(-6, 7)]; w = sum(ws) / len(ws)
    return GAP_B[0] + (GAP_B[1] - GAP_B[0]) * w, GAP_T[0] + (GAP_T[1] - GAP_T[0]) * w
def offs(s, idx):
    return LAT_S[idx] * straightness(s)
PH3 = (0.0, 1.7, 3.1)
def car_at(run, t, idx, amp=2.2):
    d = (0.0,) + delays(run, t); dl = d[idx]; s = run.at(t - dl)
    return car_state(s, t - dl, PH3[idx], amp, offs(s, idx)), dl
def train(run, t, amp=2.2):
    """[(key, state)] lead first."""
    return [(k, car_at(run, t, i, amp)[0]) for i, k in enumerate(('dz', 'bunta', 'takumi'))]

def smoke_particles(run, t, idx, fps, amp=2.2):
    """world-space smoke puffs for car idx (0 dz, 1 bunta, 2 takumi): list of (pos, radius_m, alpha)."""
    dl = (0.0, DB, DT)[idx]; ph = (0.0, 1.7, 3.1)[idx]; out = []
    rng = np.random.default_rng(1234 + idx)
    jit = rng.normal(size=(80, 3))
    dt = 1.0 / fps
    k0 = int(math.floor(t * fps))
    for j in range(0, 44):
        kk = k0 - j; tp = kk * dt; age = t - tp
        if age < 0 or age > 1.45: continue
        st = car_at(run, tp, idx, amp)[0]
        inten = min(1.0, max(0.0, (abs(st['alpha']) - 11.0) / 18.0))
        if inten <= 0.02: continue
        fz = st['fwd']; fx = st['fx']
        for side in (-1, 1):
            r = jit[(kk * 2 + (side > 0)) % 80]
            p = st['pos'] + fx * side * 0.72 - fz * 1.25
            p = p + np.array([r[0] * 0.55 * age * 1.6, 0.22 + 0.55 * age + 0.1 * abs(r[1]), r[2] * 0.55 * age * 1.6])
            rad = 0.30 + 1.0 * age + 0.08 * r[1]
            al = 0.17 * inten * (1 - age / 1.45) ** 1.6
            out.append((p, rad, al))
    return out

def draw_smoke(img, parts, eye, R, f, tint=None):
    """alpha-composite puffs (world) into img (BGR float)."""
    if not parts: return
    H, W = img.shape[:2]; A = np.zeros((H, W), np.float32)
    for p, rad, al in parts:
        q = R @ (np.asarray(p) - eye)
        if q[2] < 1.2: continue
        al = al * min(1.0, (q[2] - 1.2) / 6.0)
        x = W / 2 + f * q[0] / q[2]; y = H / 2 - f * q[1] / q[2]; r = f * rad / q[2]
        if r < 0.6 or x < -r or x > W + r or y < -r or y > H + r: continue
        r = min(r, 220.0)
        x0, y0 = max(0, int(x - r - 2)), max(0, int(y - r - 2)); x1, y1 = min(W, int(x + r + 3)), min(H, int(y + r + 3))
        if x1 <= x0 or y1 <= y0: continue
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        cv2.circle(m, (int(round((x - x0) * 4)), int(round((y - y0) * 4))), int(round(r * 4)), 1.0, -1, cv2.LINE_AA, shift=2)
        sub = A[y0:y1, x0:x1]; sub += (1 - sub) * m * al
    A = cv2.GaussianBlur(A, (0, 0), 2.2)
    col = np.array([168, 164, 158], np.float32) if tint is None else (np.array([168, 164, 158], np.float32) * 0.8 + np.array(tint[::-1], np.float32) * 0.2)
    img[:] = img * (1 - A[..., None]) + col * A[..., None]


def solve_s0(target_s, at_t, D, vmul=1.0):
    """s0 so that the lead reaches target_s at time at_t."""
    s0 = target_s - DIR * 30.0 * at_t
    for _ in range(8):
        r = Run(s0, max(D, at_t + 0.1), vmul); err = r.at(at_t) - target_s; s0 -= err
    return s0
