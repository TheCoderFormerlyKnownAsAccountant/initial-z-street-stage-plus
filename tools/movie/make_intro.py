#!/usr/bin/env python3
"""M46 opening: rival cards 2 bars each, longer downhill drift chase on Hakone (chase.py), Devil Z with bumpers.
M45 opening = M44 (unchanged through Akio's hero shot, bar 58) + HAKONE card, Bunta and Takumi (carbon-hood AE86)
vignettes, aura chase (Devil Z rainbow <- Bunta red <- Takumi blue) and the title over the receding chase.
M44 art-only opening for Initial Z Street Stage+ (480x272, 29.97 fps, ~104 s, cut to ss_16's beat grid).
All 3D from game data: Wangan night course (wrender) + car select models (carrender) + effect_data aura texture;
2D: rivaldemo / WMP busts, start-card-style English names, m21 logo.
usage: make_intro.py frames [--step N] [--ss S] [--jobs J]   -> frames/%05d.png
       make_intro.py sheet                                      -> contact.png"""
import sys, os, math, json, glob
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
FPS = 30000 / 1001
P_BEAT, PH = 0.3831292517006803, 0.345            # ss_16: 156.6 bpm, downbeat phase (flux autocorrelation)
def beat(k): return PH + k * P_BEAT
def bar(k): return beat(4 * k)
T_END = 108.3; NF = int(round(T_END * FPS))   # EOF + 1.5 s hold stays inside ss_16 (110.0 s) so the BGM never loops
CARS = HERE + '/cars/'
FONT_SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf'
FONT_BI = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
AURA = 'work/m14/inv/effect__effect_data.bin.gz__aura_spa.gim.png'

# key, display name, car file, paint RGB, lower two-tone, car label, camera type, portrait pose file
V = [
 ('itu', 'Itsuki Takeuchi', 'toyota_ae85l', (178, 24, 30), (20, 20, 22), 'COROLLA LEVIN AE85', 'chase', 2),
 ('iketani', 'Koichiro Iketani', 'nissan_s13k', (150, 156, 168), None, 'SILVIA K\'s S13', 'side', 0),
 ('nakazato', 'Takeshi Nakazato', 'nissan_bnr32', (22, 22, 26), None, 'SKYLINE GT-R BNR32', 'front', 0),
 ('kyoko', 'Kyoko Iwase', 'mazda_fd3sa', (16, 16, 20), None, 'RX-7 FD3S', 'orbit', 0),
 ('sudo', 'Kyoichi Sudo', 'mitsu_ce9a', (232, 232, 236), None, 'LANCER EVOLUTION III', 'chase', 0),
 ('keisuke', 'Keisuke Takahashi', 'mazda_fd3s', (236, 196, 20), None, 'RX-7 TYPE R FD3S', 'side', 0),
 ('ryosuke', 'Ryosuke Takahashi', 'mazda_fc3s', (238, 238, 240), None, 'SAVANNA RX-7 FC3S', 'front', 4),
 ('takumi', 'Takumi Fujiwara', 'toyota_ae86t', (240, 240, 242), (18, 18, 20), 'SPRINTER TRUENO AE86', 'orbit', 3),
 ('hiramoto', 'Koichi Hiramoto', 'nissan_bnr32', (92, 98, 110), None, 'SKYLINE GT-R BNR32', 'chase', 'w'),
 ('masaki', 'Masaki', 'mazda_fd3s', (206, 96, 24), None, 'RX-7 FD3S', 'side', 'w'),
 ('reina', 'Reina Akikawa', 'nissan_bnr32', (205, 206, 214), None, 'SKYLINE GT-R BNR32', 'front', 'w'),
 ('eiji', 'Eiji Kamiya', 'mitsu_cp9at', (186, 18, 28), None, 'LANCER EVOLUTION VI T.M.E.', 'orbit', 'w'),
 ('kuroki', 'Kuroki', 'nissan_bcnr33', (24, 34, 78), None, 'SKYLINE GT-R BCNR33', 'chase', 'w'),   # M52: in-game R33 (id 36), WMP dark blue
 ('ota', 'Ota', 'mazda_fd3s', (168, 176, 190), None, 'RX-7 FD3S', 'side', 'w'),
 ('shima', 'Tatsuya Shima', 'porsche_964', (14, 14, 16), None, 'PORSCHE 911 TURBO 964  \u2014  BLACKBIRD', 'front', 'w'),   # M52: in-game 964 (id 40)
]
DZ = ('nissan_s30', (30, 52, 130))
import hrender as HR
# Hakone segment (hrender world: Hakone fork world.json if present, else Usui night stand-in)
HV2 = [
 ('bunta', 'Bunta Fujiwara', 'subaru_gc8s5', (18, 40, 104), None, 'IMPREZA WRX STi Ver.V GC8', 'side', 6, None, 600.0),
 ('takumi2', 'Takumi Fujiwara', 'toyota_ae86t', (240, 240, 242), (18, 18, 20), 'SPRINTER TRUENO AE86  \u2014  CARBON HOOD', 'front_hi', 7, 'd036eb', 1750.0),
]
BUNTA_CAR = (HV2[0][2], HV2[0][3], None, None); TAKUMI_CAR = (HV2[1][2], HV2[1][3], HV2[1][4], 'd036eb')
RED = (255, 52, 40); BLUE = (40, 120, 255)            # aura tints (RGB)
HSPEED = 42.0                                         # m/s on the mountain (151 km/h)
CH_S0 = 2150.0; CH_V = 45.0; HK_S0 = 1480.0; HL_ = 1.6
if HR.SPEC['name'].startswith('hakone'):              # real Hakone course (Hakone fork): wider two-lane road
    HV2[0] = HV2[0][:9] + (1200.0,); HV2[1] = HV2[1][:9] + (600.0,); CH_S0 = 1700.0; HK_S0 = 2905.0; HL_ = 1.9
VSPEED = 50.0                                        # m/s (180 km/h)

VB = 3                 # M51: back to the M44 card length (12 beats = 4.6 s)
VB_REF = 3.0           # orbit-camera sweep keeps the M46 rate (frames before u = 3.06 s are reused from M46)
def VBAR(i): return 6 + VB * i
AK0 = VBAR(15); AK1 = AK0 + 6; HK0 = AK1          # Akio 6 bars, then HAKONE card 2 bars, Bunta/Takumi 3 bars each
AK_SPLIT = 5.2; AK_TIN = 2.6
HV0 = HK0 + 2
CH0 = HV0 + 6
# drift chase sub-shots (bars from CH0): low chase-cam, side tracking (S-bends), hairpin overhead (U-bend),
# near-miss at the apex, reverse front, crane at the exit; then the title over the train running away
# M49 chase (10.5 bars = 42 beats = 16.1 s): straight side by side, chase-cam into a short bend, overhead of the next
# bend, reverse camera on the straight, near miss at the last bend's entry
CHASE = [('c_run', 2), ('c_entry', 2.5), ('c_over', 2), ('c_front', 2), ('c_near', 2)]
# M51 ending (bar 57 -> end, 20.6 s, one continuous camera): Bunta (red) and Takumi (blue) side by side on the
# Wangan straight, the Devil Z (rainbow) comes past and shrinks away down the expressway; the title appears at WE_TITLE
WE_S0 = 4900.0; WE_V = 38.0; WE_TITLE = beat(266) - bar(57)
def we_rel(u):                       # Devil Z position relative to the pair (m), C1-smooth
    return -60.0 + 9.0 * u + 0.5 * max(u - 4.0, 0.0) ** 2
def we_relv(u): return 9.0 + 1.0 * max(u - 4.0, 0.0)
def shots():
    S = [dict(kind='open', t0=0.0, t1=bar(4)), dict(kind='logo', t0=bar(4), t1=bar(6))]
    for i, v in enumerate(V):
        S.append(dict(kind='vig', i=i, t0=bar(VBAR(i)), t1=bar(VBAR(i) + VB), s0=260.0 + i * 368.0))
    S.append(dict(kind='akio', t0=bar(AK0), t1=bar(AK1), s0=2900.0))
    S.append(dict(kind='wend', t0=bar(AK1), t1=T_END, s0=WE_S0))
    return S
FIRST_NEW = bar(6)      # open + logo frames are byte-identical to M44's (copied, not re-rendered)
SHOTS = shots()

def ease(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

import wrender as WR
def cam_R(eye, target, roll=0.0):
    fw = np.asarray(target, float) - eye; fw /= np.linalg.norm(fw)
    rt = np.cross([0, 1.0, 0], fw); rt /= np.linalg.norm(rt); up = np.cross(fw, rt)
    if roll:
        cr, sr = math.cos(roll), math.sin(roll); rt, up = rt * cr + up * sr, -rt * sr + up * cr
    return np.stack([rt, up, fw])
def tangent(s, M=WR):
    a, b = M.path(s - 3), M.path(s + 3); d = b - a; d[1] = 0; return d / np.linalg.norm(d)
HL = HL_                 # mountain lane offset
LANE = 1.9

# ---------------------------------------------------------------- per-shot 3D state
def state(sh, u):
    """returns dict(eye, target, fov, roll, cars=[(file, s, lat, paint, lower)], dz=None|(s, lat), speed=0..1 lines)"""
    k = sh['kind']
    if k in ('open', 'logo'):
        t = sh['t0'] + u; T = bar(6)
        s = 120 + 9.0 * t; h = 1.3 + 34 * smooth(t / bar(4)) + (6 * (t - bar(4)) / (T - bar(4)) if t > bar(4) else 0)
        eye = WR.path(s, -1.0, h); tgt = WR.path(s + 60, 0, h * 0.55 + 6)
        cars = []
        if k == 'open':      # a single car runs under the crane
            cars.append(('toyota_ae86t', 130 + 38 * t, LANE, (240, 240, 242), (18, 18, 20)))
        return dict(eye=eye, target=tgt, fov=1.0, roll=0.0, cars=cars, dz=None, lines=0.0)
    if k == 'vig':
        v = V[sh['i']]; s0 = sh['s0']; typ = v[6]; D = sh['t1'] - sh['t0']
        base = s0 + VSPEED * u; ent = 1 - ease(u / 1.1)
        if typ == 'chase':
            cs, cl = base + 7 - 11 * ent, LANE + 4.2 * ent
            eye = WR.path(base, LANE * 0.6, 2.1); tgt = WR.path(base + 26, LANE * 0.8, 0.5); fov = 1.0; roll = 0.0
        elif typ == 'side':
            cs, cl = base - 16 * ent, LANE
            eye = WR.path(base - 1.0 + 1.2 * u, LANE - 6.2, 1.15); tgt = WR.path(base + 0.6 * u, LANE, 0.75)
            fov = 1.05; roll = 0.03 * math.sin(u * 2)
        elif typ == 'front':
            cs, cl = base - 30 * ent, LANE
            eye = WR.path(base + 9.5, LANE - 1.2, 0.9); tgt = WR.path(base - 2, LANE, 0.75); fov = 1.15; roll = -0.04
        else:  # orbit
            cs, cl = base - 12 * ent, LANE
            a = math.radians(70 - 95 * u / (bar(VB_REF) - bar(0))); c = WR.path(cs, cl, 0.7)
            fwd = tangent(cs); nrm = np.array([-fwd[2], 0, fwd[0]])
            eye = c + 7.2 * (math.cos(a) * fwd + math.sin(a) * nrm) + np.array([0, 1.0 + 0.6 * u / D, 0])
            tgt = c + np.array([0, -0.1, 0]); fov = 1.05; roll = 0.0
        cars = [(v[2], cs, cl, v[3], v[4])]
        dz = None; tz = beat(4 * VBAR(sh['i']) + 6) - sh['t0']        # DZ passes the camera on beat 6 of the vignette
        if u > tz - 0.7:
            rel = 80.0
            if typ == 'front':
                dz = (base + 9.5 + rel * (tz - u), LANE - 3.6)          # comes from far ahead toward camera? no: from behind car
                dz = (base - 40 + rel * (u - tz) + 49.5, LANE - 3.4)
            else:
                cam_s = base if typ == 'chase' else (base - 1 if typ == 'side' else cs)
                dz = (cam_s + rel * (u - tz), LANE - 3.6 if typ != 'side' else LANE - 3.4)
        lines = 0.6 * ent + (0.8 if dz and abs(u - tz) < 0.5 else 0.0) + 0.25
        return dict(eye=eye, target=tgt, fov=fov, roll=roll, cars=cars, dz=dz, lines=lines, tz=tz)
    if k == 'akio':
        s0 = sh['s0']; D = sh['t1'] - sh['t0']; base = s0 + 62 * u
        cs = base; cl = LANE * 0.5
        if u < AK_SPLIT:     # slow orbit from the front-left
            a = math.radians(-20 + 115 * smooth(u / AK_SPLIT)); c = WR.path(cs, cl, 0.6)
            fwd = tangent(cs); nrm = np.array([-fwd[2], 0, fwd[0]])
            eye = c + (6.5 - 1.2 * smooth(u / AK_SPLIT)) * (math.cos(a) * fwd + math.sin(a) * nrm) + np.array([0, 0.75, 0])
            tgt = c + np.array([0, 0.05, 0]) - 1.2 * nrm * smooth(u / AK_SPLIT); fov = 1.0
        else:                # it pulls away from a chase camera with the trail
            w = u - AK_SPLIT; cs = base + 18 * w * w
            eye = WR.path(base - 7, cl, 1.9); tgt = WR.path(base + 30, cl, 0.6); fov = 1.0
        return dict(eye=eye, target=tgt, fov=fov, roll=0.0, cars=[], dz=(cs, cl), lines=0.3 + (0.7 if u > AK_SPLIT else 0), hero=True)
    if k == 'hakone':          # crane up over the night touge; the carbon-hood AE86 runs under it
        s0 = sh['s0']; D = sh['t1'] - sh['t0']; x = smooth(u / D)
        base = s0 + 9.0 * u; h = 1.0 + 26 * x
        eye = HR.path(base, -1.2 - 2.0 * x, h); tgt = HR.path(base + 55 + 20 * x, 0, h * 0.45 + 1.0)
        cars = [dict(car=TAKUMI_CAR, s=s0 + 4 + 34 * u, lat=HL)]
        return dict(eye=eye, target=tgt, fov=1.0, roll=0.0, cars=cars, dz=None, lines=0.0, world='h')
    if k == 'hvig':
        v = HV2[sh['i']]; s0 = sh['s0']; typ = v[6]; D = sh['t1'] - sh['t0']
        base = s0 + HSPEED * u; ent = 1 - ease(u / 1.1)
        car = BUNTA_CAR if v[0] == 'bunta' else TAKUMI_CAR
        if typ == 'side':
            cs, cl = base - 16 * ent, HL
            eye = HR.path(base - 1.0 + 0.8 * u, HL - 7.2, 1.25); tgt = HR.path(base - 0.8 + 0.3 * u, HL, 0.7)
            fov = 1.05; roll = 0.03 * math.sin(u * 2)
        else:  # front_hi: ahead of the car, high enough to read the carbon bonnet
            cs, cl = base - 26 * ent, HL
            eye = HR.path(base + 5.2, HL - 0.9, 1.85 - 0.2 * u / D); tgt = HR.path(base - 0.6, HL, 0.45); fov = 1.1; roll = -0.03
        return dict(eye=eye, target=tgt, fov=fov, roll=roll, cars=[dict(car=car, s=cs, lat=cl)], dz=None,
                    lines=0.6 * ent + 0.25, world='h')
    if k == 'wend':                 # one continuous chase camera behind the pair: rear-right quarter -> centre, then
        ps = sh['s0'] + WE_V * u       # tilts up so the vanishing point (and the shrinking Devil Z) sits below the title
        x = smooth(u / 7.5)
        off = -7.5 - 4.5 * x; lat = 5.2 * (1 - x); h = 1.05 + 0.95 * x
        eye = WR.path(ps + off, lat, h)
        rel = we_rel(u); pitch = math.radians(-2.5 + 12.5 * smooth((u - (WE_TITLE - 3.0)) / 3.5))
        tA = WR.path(ps + 1.0, 0.0, 0.7)
        D = 60.0; tB = WR.path(ps + off + D, 0.0, h + math.tan(pitch) * D)
        y = smooth((u - 1.0) / 6.0); tgt = tA * (1 - y) + tB * y
        dzl = 4.6 * (1 - smooth((rel - 15.0) / 50.0))
        wob = 0.5 * math.sin(0.55 * u)
        cars = [dict(car=BUNTA_CAR, s=ps + 0.3 * math.sin(0.4 * u + 1.0), lat=LANE, aura=RED, vel=WE_V),
                dict(car=TAKUMI_CAR, s=ps + wob, lat=-LANE, aura=BLUE, vel=WE_V)]
        return dict(eye=eye, target=tgt, fov=1.0, roll=0.0, cars=cars, dz=(ps + rel, dzl), lines=0.2 + 0.3 * (1 - x),
                    vel=WE_V + we_relv(u) - 30.0)
    if k.startswith('c_') or k == 'htitle':
        return chase_state(sh, u)
    if k == 'title':
        s0 = sh['s0']; base = s0 + 14 * u
        eye = WR.path(base, -3, 22 + 4 * u / 15); tgt = WR.path(base + 120, 0, 12)
        dz = (s0 - 40 + 70 * (u - 1.0), LANE) if 0.5 < u < 6 else None
        return dict(eye=eye, target=tgt, fov=0.95, roll=0.0, cars=[], dz=dz, lines=0.0)

import chase as CH
_RUNS = {}
CH_CAR = {'dz': (DZ[0], DZ[1], None, None), 'bunta': BUNTA_CAR, 'takumi': TAKUMI_CAR}
CH_AURA = {'dz': 'rainbow', 'bunta': RED, 'takumi': BLUE}
CH_IDX = {'dz': 0, 'bunta': 1, 'takumi': 2}
# (lead target s, time it is reached, lane amplitude) per sub-shot; all downhill (decreasing s)
CH_PLAN = {'c_run': (2300.0, 0.0, 2.2), 'c_entry': (2041.0, 0.55, 2.2), 'c_over': (1729.0, 0.5, 2.3),
           'c_front': (1585.0, 0.0, 2.2), 'c_near': (1275.0, 1.15, 2.0), 'htitle': (2300.0, 1.0, 1.6)}
def run_for(k, D):
    if k not in _RUNS:
        ts, tt, amp = CH_PLAN[k]; _RUNS[k] = (CH.Run(CH.solve_s0(ts, tt, D + 0.5), D + 0.5), amp)
    return _RUNS[k]
def _pos(st, h=0.0): return st['pos'] + np.array([0, h, 0])
def chase_state(sh, u):
    k = sh['kind']; D = sh['t1'] - sh['t0']; run, amp = run_for(k, D)
    tr = dict(CH.train(run, u, amp)); up = np.array([0, 1.0, 0])
    lead, bu, ta = tr['dz'], tr['bunta'], tr['takumi']
    fov, roll, fog0, lines, passes = 1.0, 0.0, 60.0, 0.0, []
    x = smooth(u / D)
    if k == 'c_run':           # straight, flat out: low tracking camera beside Bunta, the pair draws past it
        sb = lead['s']; eye = HR.path(sb + CH.DIR * (9.5 - 3.5 * x), -3.9, 1.7 - 0.4 * x)
        tgt = _pos(lead, 0.4) * 0.35 + _pos(bu, 0.4) * 0.4 + _pos(ta, 0.4) * 0.25
        fov = 1.0; lines = 0.75; roll = 0.03
    elif k == 'c_entry':       # low chase-cam behind Takumi: feint, snap, counter-steer out, in sequence
        sk = ta['s'] - CH.DIR * 11.0; ins = CH.TB()['ins'][2004]; lat = CH.lat_line(sk, amp, 0.0) * 0.6 - ins * 1.6
        eye = HR.path(sk, lat, 2.6); tgt = _pos(ta, 0.4) * 0.4 + _pos(bu, 0.5) * 0.35 + _pos(lead, 0.5) * 0.25
        roll = 0.08 * math.tanh(CH._i(sk, 'ks') * 120) * -CH.DIR; fov = 1.0; lines = 0.35
    elif k == 'c_over':        # high above the outside of the next bend: the three flick in one after another
        mid = 1669; ins = CH.TB()['ins'][mid]
        eye = HR.path(1742.0 - 52.0 * x, -ins * 6.5, 10.5 - 1.5 * x)
        tgt = _pos(bu) * 0.5 + _pos(lead) * 0.3 + _pos(ta) * 0.2; fov = 0.9; fog0 = 100.0
    elif k == 'c_front':       # reverse camera ahead of the Devil Z on the straight: Bunta pulls alongside, Takumi tucks in
        sl = lead['s'] + CH.DIR * (10.0 - 2.5 * x); eye = HR.path(sl, 1.1, 2.1)
        tgt = _pos(lead, 0.5) * 0.4 + _pos(bu, 0.5) * 0.35 + _pos(ta, 0.5) * 0.25; fov = 0.95; lines = 0.3
    elif k == 'c_near':        # camera low on the inside kerb just past the entry: they snap in right at the lens
        sc = 1275.0; ins = CH.TB()['ins'][1219]; eye = HR.path(sc, ins * 3.4, 1.0)
        def raw_dir(uu):                 # look direction toward the weighted cars at time uu
            W_ = []; Pp = []
            for ix in range(3):
                c = CH.car_at(run, uu, ix, amp)[0]; ds = (c['s'] - sc) * -CH.DIR
                W_.append(math.exp(-ds / 14.0) if ds >= 0 else math.exp(ds / 4.0)); Pp.append(_pos(c, 0.45))   # M50: continuous
            W_ = np.array(W_) + 1e-6; p = (np.array(Pp) * W_[:, None]).sum(0) / W_.sum(); d = p - eye; return d / np.linalg.norm(d)
        # M50: the look direction is low-passed over +-0.3 s (gaussian), so the near-miss whip pan has no snap
        ks = np.arange(-6, 7); gw = np.exp(-0.5 * (ks / 3.0) ** 2); dd = sum(g * raw_dir(u + k * 0.05) for k, g in zip(ks, gw))
        tgt = eye + 10.0 * dd / np.linalg.norm(dd); fov = 0.88
        for kk in ('dz', 'bunta', 'takumi'):     # pass times: first frame each car is level with the camera
            for j in range(int(D * FPS)):
                tj = j / FPS; c = CH.car_at(run, tj, CH_IDX[kk], amp)[0]
                if (c['s'] - sc) * -CH.DIR <= 0: passes.append(tj); break
    else:                      # htitle (frames reused from M46; kept for completeness)
        cs = CH.car_state(run.at(u - 0.6 - 0.85), u, 3.1, amp, 0.0)
        eye = _pos(cs, 3.0 + 4.0 * smooth(u / 2.2)); tgt = _pos(lead, 1.0); fov = 1.0; fog0 = 90.0
    cars = []
    for kk in ('dz', 'bunta', 'takumi'):
        c = tr[kk]; ix = CH_IDX[kk]
        tp = [_pos(CH.car_at(run, u - j / FPS, ix, amp)[0], 0.55) for j in range(0, {'dz': 6, 'bunta': 4, 'takumi': 6}[kk])]
        cars.append(dict(car=CH_CAR[kk], pose=c, aura=CH_AURA[kk], trail=tp, key=kk))
    smoke = []
    for kk in ('dz', 'bunta', 'takumi'):
        for p_, r_, a_ in CH.smoke_particles(run, u, CH_IDX[kk], FPS, amp):
            smoke.append((p_, r_, a_, None if kk == 'dz' else CH_AURA[kk]))
    return dict(eye=eye, target=tgt, fov=fov, roll=roll, cars=cars, dz=None, lines=lines, world='h', fog0=fog0,
                smoke=smoke, passes=passes)

# ---------------------------------------------------------------- assets
_A = {}
def aura_tex(color=None):
    k = ('aura', color)
    if k not in _A:
        a = cv2.cvtColor(np.asarray(Image.open(AURA).convert('RGB')), cv2.COLOR_RGB2BGR).astype(np.float32)
        if color is not None:            # same flicker pattern, one hue (RGB tint)
            lum = a.mean(2, keepdims=True) / max(a.mean(), 1e-3)
            a = np.clip(lum * np.array(color[::-1], np.float32) * 0.9, 0, 255)
        _A[k] = a
    return _A[k]

def portrait(v):
    key = v[0]
    if key in _A: return _A[key]
    if key == 'takumi2': key = 'takumi2'
    if v[7] == 'w':
        sys.path.insert(0, 'work/m42/wmpart/tools'); import art42 as A
        C = {c['low']: c for c in A.CH}; im = A.portrait_pose(C[key], 256, 256, 1)
    else:
        im = Image.open('work/m40/video/cards/t_%s_%d.png' % (key.rstrip('2'), v[7])).convert('RGBA')
    bb = im.getchannel('A').point(lambda a: 255 if a > 24 else 0).getbbox(); im = im.crop(bb)
    H = 236; im = im.resize((max(1, int(im.width * H / im.height)), H), Image.LANCZOS)
    if im.width > 250: im = im.resize((250, int(im.height * 250 / im.width)), Image.LANCZOS)
    _A[key] = im; return im

def name_card(name, car):
    k = ('card', name, car)
    if k in _A: return _A[k]
    SSx = 3; W, H = 330 * SSx, 64 * SSx
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # band: dark navy, fading out to the right, red rule on top (game label style)
    band = np.zeros((H, W, 4), np.uint8); xs = np.linspace(1, 0, W) ** 0.6
    band[22 * SSx:, :, :3] = (12, 14, 34); band[22 * SSx:, :, 3] = (215 * xs).astype(np.uint8)
    band[22 * SSx:24 * SSx, :, :3] = (210, 20, 30); band[22 * SSx:24 * SSx, :, 3] = (255 * xs).astype(np.uint8)
    im.alpha_composite(Image.fromarray(band))
    f = ImageFont.truetype(FONT_SERIF, 27 * SSx)
    while f.getlength(name) > W - 30 * SSx: f = ImageFont.truetype(FONT_SERIF, int(f.size * 0.94))
    tm = Image.new('L', (W, H), 0); ImageDraw.Draw(tm).text((10 * SSx, 27 * SSx), name, font=f, fill=255)
    out = tm.filter(ImageFilter.MaxFilter(7))
    sh = out.filter(ImageFilter.GaussianBlur(4))
    navy = Image.new('RGBA', (W, H), (14, 14, 40, 255))
    im.paste(Image.new('RGBA', (W, H), (0, 0, 0, 170)), (3 * SSx, 3 * SSx), sh)
    im.paste(navy, (0, 0), out)
    g = np.zeros((H, W, 4), np.uint8); yy = np.linspace(0, 1, H)[:, None]
    g[..., 0] = (255 - 40 * yy).astype(np.uint8); g[..., 1] = (255 - 46 * yy).astype(np.uint8); g[..., 2] = 255; g[..., 3] = 255
    im.paste(Image.fromarray(g), (0, 0), tm)
    fc = ImageFont.truetype(FONT_BI, 11 * SSx)
    cm = Image.new('L', (W, H), 0); ImageDraw.Draw(cm).text((12 * SSx, 5 * SSx), car, font=fc, fill=255)
    im.paste(Image.new('RGBA', (W, H), (10, 10, 20, 255)), (0, 0), cm.filter(ImageFilter.MaxFilter(5)))
    im.paste(Image.new('RGBA', (W, H), (255, 214, 60, 255)), (0, 0), cm)
    im = im.resize((330, 64), Image.LANCZOS); _A[k] = im; return im

def hakone_card(u):
    """HAKONE title card: tall condensed serif (start-card style), red rule wiping in, small caps subtitle."""
    k = ('hk',)
    if k not in _A:
        SSx = 3; W, H = 480 * SSx, 272 * SSx; tm = Image.new('L', (W, H), 0); d = ImageDraw.Draw(tm)
        f = ImageFont.truetype(FONT_SERIF, 64 * SSx); txt = 'HAKONE'; sp = 10 * SSx
        ws = [f.getlength(ch) for ch in txt]; tw = sum(ws) + sp * (len(txt) - 1); x = (W - tw) / 2
        for ch, w in zip(txt, ws): d.text((x, 92 * SSx), ch, font=f, fill=255); x += w + sp
        fs = ImageFont.truetype(FONT_BI, 12 * SSx); sub = 'NIGHT  TOUGE  \u00b7  KANAGAWA'
        d.text(((W - fs.getlength(sub)) / 2, 176 * SSx), sub, font=fs, fill=255)
        out = tm.filter(ImageFilter.MaxFilter(7)); shd = out.filter(ImageFilter.GaussianBlur(5))
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        im.paste(Image.new('RGBA', (W, H), (0, 0, 0, 170)), (4 * SSx, 4 * SSx), shd)
        im.paste(Image.new('RGBA', (W, H), (14, 14, 40, 255)), (0, 0), out)
        g = np.zeros((H, W, 4), np.uint8); yy = np.linspace(0, 1, H)[:, None]
        g[..., 0] = (255 - 40 * yy).astype(np.uint8); g[..., 1] = (255 - 46 * yy).astype(np.uint8); g[..., 2] = 255; g[..., 3] = 255
        im.paste(Image.fromarray(g), (0, 0), tm)
        _A[k] = im.resize((480, 272), Image.LANCZOS)
    base = _A[k]; out = Image.new('RGBA', (480, 272), (0, 0, 0, 0))
    if u < 0.35: return out
    e = ease((u - 0.35) / 0.5); w = int(480 * e)
    rule = Image.new('RGBA', (480, 272), (0, 0, 0, 0)); dr = ImageDraw.Draw(rule)
    rw = int(300 * ease((u - 0.35) / 0.4)); dr.rectangle([240 - rw // 2, 168, 240 + rw // 2, 170], fill=(220, 24, 34, 235))
    out.alpha_composite(rule)
    c = base.copy(); a = c.getchannel('A').point(lambda x: int(x * min(1.0, (u - 0.35) / 0.25)))
    c.putalpha(a); s_ = 1.08 - 0.08 * e; cs = c.resize((int(480 * s_), int(272 * s_)), Image.LANCZOS)
    out.alpha_composite(cs, ((480 - cs.width) // 2, (272 - cs.height) // 2))
    return out

def logo(layout='stack'):
    k = ('logo', layout)
    if k not in _A:
        sys.path.insert(0, 'work/m21/t'); import logo as LG
        _A[k] = LG.render(480, 272, layout)
    return _A[k]

# ---------------------------------------------------------------- 3D frame
import carrender as CR
def project(pt, eye, R, f, W=480, H=272):
    q = R @ (np.asarray(pt) - eye)
    if q[2] < 0.3: return None
    return np.array([W / 2 + f * q[0] / q[2], H / 2 - f * q[1] / q[2]]), q[2]

def shadow(img, pos, fwd, eye, R, f, strength=0.6):
    up = np.array([0, 1.0, 0]); fz = fwd; fx = np.cross(up, fz); pts = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = project(pos + fx * 0.95 * a + fz * 2.3 * b + up * 0.02, eye, R, f)
        if p is None: return
        pts.append(p[0])
    m = np.zeros(img.shape[:2], np.float32); cv2.fillConvexPoly(m, np.round(np.array(pts) * 8).astype(np.int32), 1.0, shift=3)
    m = cv2.GaussianBlur(m, (0, 0), 3)
    img *= (1 - strength * m)[..., None]

def over(img, rgba):
    a = rgba[..., 3:4]; img[:] = img * (1 - a) + rgba[..., :3] * a

def aura_pass(img, rgba, t, power=1.0, color=None):
    """rainbow aura glow around a car sprite (aura_spa colours scrolled), additive."""
    a = rgba[..., 3]
    if a.max() <= 0: return
    g = cv2.GaussianBlur(cv2.dilate(a, np.ones((5, 5), np.uint8)), (0, 0), 7) * 1.6
    tex = aura_tex(color); H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    u = ((xx * 0.9 + t * 160) % 128).astype(int); v = ((yy * 1.2 - t * 90) % 128).astype(int)
    col = tex[v, u]
    img += col * np.clip(g - a * 0.7, 0, 1)[..., None] * 0.9 * power

def trail(img, pts_w, eye, R, f, t, width_m=1.3, power=1.0, color=None):
    """ribbon of the aura texture behind the Devil Z: pts_w = world points newest first."""
    tex = aura_tex(color); acc = np.zeros_like(img)
    P = [project(p, eye, R, f) for p in pts_w]
    for k in range(len(P) - 1):
        if P[k] is None or P[k + 1] is None: continue
        (a, za), (b, zb) = P[k], P[k + 1]
        if min(za, zb) < 2.5: continue
        wa, wb = min(f * width_m / za, 40.0), min(f * width_m / zb, 40.0)
        d = b - a; L = np.linalg.norm(d)
        if L < 0.5: continue
        n = np.array([-d[1], d[0]]) / L
        quad = np.array([a + n * wa / 2, b + n * wb / 2, b - n * wb / 2, a - n * wa / 2])
        m = np.zeros(img.shape[:2], np.float32)
        cv2.fillConvexPoly(m, np.round(quad * 8).astype(np.int32), 1.0, shift=3, lineType=cv2.LINE_AA)
        fade = (1 - k / len(P)) ** 1.3
        hue = tex[int((k * 9 + t * 200) % 128), (np.arange(img.shape[1]) * 2 + int(t * 300)) % 128]
        acc += m[..., None] * hue[None] * fade
    acc = cv2.GaussianBlur(acc, (0, 0), 2.5)
    img += acc * 0.95 * power

HAKONE_RENDERS = 'work/m45/hakone/renders'
NIGHT_H = np.array([0.66, 0.56, 0.50], np.float32)   # BGR grade for the mountain renders (moonlit blue)
def frame3d(n, ss=2, t=None, sh=None):
    if t is None: t = n / FPS
    if sh is None: sh = [s for s in SHOTS if s['t0'] <= t < s['t1']] or [SHOTS[-1]]; sh = sh[0]
    u = t - sh['t0']
    st = state(sh, u); M = HR if st.get('world') == 'h' else WR
    eye, tgt = np.asarray(st['eye'], float), np.asarray(st['target'], float)
    ti = t_in(sh)
    if ti is not None:                       # pan right as the bust comes in, so the car sits in the left half
        R0 = cam_R(eye, tgt, st['roll']); dist = np.linalg.norm(tgt - eye)
        if sh['kind'] == 'vig': k = {'chase': .30, 'side': .12, 'front': .25, 'orbit': .22}.get(V[sh['i']][6], .25)
        elif sh['kind'] == 'hvig': k = {'side': .10, 'front_hi': .20}.get(HV2[sh['i']][6], .2)
        else: k = .25
        tgt = tgt + R0[0] * dist * k * smooth((u - ti + 0.25) / 1.1)   # M50: ease-in-out (was ease-out: pan started at full speed)
    R = cam_R(eye, tgt, st['roll']); f = 380.0 * 480 / 640 * st['fov']
    plates = [] if HR.SPEC['name'].startswith('hakone') else sorted(p for p in glob.glob(HAKONE_RENDERS + '/hk_*_1080.png'))
    if sh['kind'] == 'hakone' and plates:      # real Hakone night render from the HAKONE fork: slow push-in on the plate
        pl = cv2.imread(plates[0]); D = sh['t1'] - sh['t0']; z = 1.0 + 0.10 * smooth(u / D)
        pl = cv2.resize(pl, (480, 272), interpolation=cv2.INTER_AREA)
        M2 = cv2.getRotationMatrix2D((240, 150), 0, z); img = cv2.warpAffine(pl, M2, (480, 272), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        return np.clip(img, 0, 255), st, sh, u
    img = M.render(eye, tgt, ss=ss, fov=st['fov'], roll=st['roll'], **({'fog0': st['fog0']} if 'fog0' in st else {})).astype(np.float32)
    if M is HR and not HR.SPEC['name'].startswith('hakone'): img *= NIGHT_H
    items = []
    for c in st['cars']:
        if isinstance(c, dict):
            cf, paint, lower, carbon = c['car']
            if 'pose' in c:
                items.append(dict(file=cf, pose=c['pose'], paint=paint, lower=lower, carbon=carbon, aura=c['aura'], trail=c['trail']))
            else:
                items.append(dict(file=cf, s=c['s'], lat=c['lat'], paint=paint, lower=lower, carbon=carbon, aura=c.get('aura'), vel=c.get('vel')))
        else:
            cf, cs, cl, paint, lower = c; items.append(dict(file=cf, s=cs, lat=cl, paint=paint, lower=lower, carbon=None, aura=None))
    if st['dz'] is not None:
        items.append(dict(file=DZ[0], s=st['dz'][0], lat=st['dz'][1], paint=DZ[1], lower=None, carbon=None, aura='rainbow'))
    for it in items: it['d'] = np.linalg.norm((it['pose']['pos'] + np.array([0, 0.6, 0]) if 'pose' in it else M.path(it['s'], it['lat'], 0.6)) - eye)
    smk = [(np.linalg.norm(p_ - eye), p_, r_, a_, tn_) for p_, r_, a_, tn_ in st.get('smoke', [])]; smk.sort(key=lambda r: -r[0])
    def flush(dmin):
        while smk and smk[0][0] > dmin:
            grp = []; d0 = smk[0][0]
            while smk and smk[0][0] > dmin: grp.append(smk.pop(0))
            for tn_ in set(g[4] for g in grp):
                CH.draw_smoke(img, [(g[1], g[2], g[3]) for g in grp if g[4] == tn_], eye, R, f, tn_)

    hero = st.get('hero', False)
    for it in sorted(items, key=lambda r: -r['d']):
        flush(it['d'] + 1.5)
        if 'pose' in it:
            pos = it['pose']['pos']; fw = it['pose']['fwd']; steer = it['pose']['steer']
        else:
            pos = M.path(it['s'], it['lat'], 0.0); fw = tangent(it['s'], M); steer = 0.0
        shadow(img, pos, fw, eye, R, f, 0.6 if it['aura'] is None else 0.5)
        rg = CR.render_world(CARS + it['file'] + '.bin', pos, fw, eye, R, f, (480, 272), ss=ss, paint=it['paint'],
                             lower=it['lower'], carbon=it['carbon'] or False, steer=steer)
        rg[..., :3] = np.clip(rg[..., :3], 0, 255)
        if 'trail' in it:                      # drift chase: ribbon follows the real (sliding) trajectory
            col = None if it['aura'] == 'rainbow' else it['aura']
            trail(img, it['trail'], eye, R, f, t + (0 if col is None else 0.37), 1.1 if col is None else 0.95, 0.95 if col is None else 0.8, col)
            aura_pass(img, rg, t + (0 if col is None else 0.37), 0.9, col)
        elif it['aura'] == 'rainbow':
            if sh['kind'] == 'akio': vel = 62 + (36 * (u - AK_SPLIT) if u > AK_SPLIT else 0)
            elif sh['kind'] == 'title': vel = 70
            elif 'vel' in st: vel = st['vel'] + 30
            else: vel = VSPEED + 80
            npt = 14 if sh['kind'] not in ('chase', 'htitle') else 4      # in the train the ribbon must end before Bunta
            pts = [M.path(it['s'] - 2.0 - vel * k / FPS, it['lat'], 0.55) for k in range(0, npt)]
            trail(img, pts, eye, R, f, t, 1.2, 1.0 if not hero or u > AK_SPLIT else 0.0)
            aura_pass(img, rg, t, 1.0 if hero else 0.8)
        elif it['aura'] is not None:
            vel = it['vel'] if it.get('vel') is not None else st.get('vel', 45) + 30
            pts = [M.path(it['s'] - 2.0 - vel * k / FPS, it['lat'], 0.55) for k in range(0, 4 if it['aura'] == RED else 9)]
            trail(img, pts, eye, R, f, t + 0.37, 1.0, 0.85, it['aura'])
            aura_pass(img, rg, t + 0.37, 0.9, it['aura'])
        over(img, rg)
    flush(-1.0)
    return np.clip(img, 0, 255), st, sh, u

# ---------------------------------------------------------------- 2D finishing
def speed_lines(img, amount, t, mode='h', seed=0):
    if amount <= 0.01: return
    rng = np.random.default_rng(seed + int(t * FPS)); H, W = img.shape[:2]; m = np.zeros((H, W), np.float32)
    for _ in range(int(26 * amount)):
        if mode == 'h':
            y = rng.uniform(0, H); x = rng.uniform(-200, W); L = rng.uniform(60, 220)
            cv2.line(m, (int(x), int(y)), (int(x + L), int(y)), rng.uniform(0.25, 0.8), 1, cv2.LINE_AA)
        else:
            a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(120, 200); r1 = r0 + rng.uniform(60, 200)
            c = np.array([W / 2, H / 2 - 20])
            cv2.line(m, tuple((c + r0 * np.array([math.cos(a), math.sin(a) * 0.62])).astype(int)),
                     tuple((c + r1 * np.array([math.cos(a), math.sin(a) * 0.62])).astype(int)), rng.uniform(0.3, 0.8), 1, cv2.LINE_AA)
    img += m[..., None] * 255 * min(amount, 1.0) * 0.55

def light_streaks(img, k=0.45):
    b = np.clip(img.max(2) - 170, 0, 85) / 85.0
    s = cv2.blur((img * b[..., None]).astype(np.float32), (71, 1))
    img += s * k * np.array([1.0, 0.92, 0.85])

def t_in(sh):
    if sh['kind'] == 'vig': return beat(4 * VBAR(sh['i']) + 3) - sh['t0'] - 0.25
    if sh['kind'] == 'hvig': return beat(4 * (HV0 + 3 * sh['i']) + 4) - sh['t0'] - 0.25
    if sh['kind'] == 'akio': return AK_TIN
    return None

def flash_amount(t, sh, st, u):
    a = 0.0
    for tb in [s['t0'] for s in SHOTS[1:]]:
        if 0 <= t - tb < 0.2: a = max(a, 0.85 * (1 - (t - tb) / 0.2))
    if st.get('tz') is not None and 0 <= u - st['tz'] < 0.16: a = max(a, 0.42 * (1 - (u - st['tz']) / 0.16))
    for tp in st.get('passes', []):
        if 0 <= u - tp < 0.12: a = max(a, 0.30 * (1 - (u - tp) / 0.12))
    k = (t - PH) / P_BEAT
    # M49b: per-beat 5% white pulse removed (read as a stutter every 0.38 s)
    return a

def finish(img, st, sh, u, t):
    k = sh['kind']
    light_streaks(img, 0.5 if k != 'title' else 0.35)
    mode = 'r' if (k == 'vig' and V[sh['i']][6] == 'chase') or (k == 'akio' and u > AK_SPLIT) or k in ('c_entry', 'c_front') else 'h'
    speed_lines(img, st['lines'], t, mode)
    rgb = cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb).convert('RGBA')
    if k == 'vig' or k == 'akio' or k == 'hvig':
        if k == 'vig': v = V[sh['i']]; name, car = v[1], v[5]; tin = t_in(sh)
        elif k == 'hvig': v = HV2[sh['i']]; name, car = v[1], v[5]; tin = t_in(sh)
        else: v = ('akio', 'Akio Asakura', '', 0, 0, '', '', 3); name, car = v[1], 'FAIRLADY Z S30  —  THE DEVIL Z'; tin = AK_TIN
        if u >= tin:
            p = portrait(v); e = ease((u - tin) / 0.45)
            # diagonal panel behind the bust
            pan = Image.new('RGBA', (480, 272), (0, 0, 0, 0)); d = ImageDraw.Draw(pan)
            x0 = 480 - int(205 * e)
            d.polygon([(x0 + 40, 0), (480, 0), (480, 272), (x0 - 30, 272)], fill=(14, 18, 52, 150))
            d.polygon([(x0 + 34, 0), (x0 + 40, 0), (x0 - 30, 272), (x0 - 36, 272)], fill=(220, 24, 34, 230))
            im.alpha_composite(pan)
            px = 480 - p.width + int((1 - e) * 200) - 6; py = 272 - p.height
            if u - tin < 0.12:   # white silhouette flash as it lands
                wf = Image.new('RGBA', p.size, (255, 255, 255, 255)); wf.putalpha(p.getchannel('A')); im.alpha_composite(wf, (px, py))
            else: im.alpha_composite(p, (px, py))
            tc = tin + 0.18
            if u >= tc:
                c = name_card(name, car); w = int(c.width * ease((u - tc) / 0.35))
                if w > 0: im.alpha_composite(c.crop((0, 0, w, c.height)), (0, 196))
    if k == 'logo':
        L = logo('stack'); e = ease(u / 0.5); s = 1.25 - 0.25 * e
        Ls = L.resize((int(480 * s), int(272 * s)), Image.LANCZOS); a = Ls.getchannel('A').point(lambda x: int(x * min(1, u / 0.12)))
        Ls.putalpha(a); im.alpha_composite(Ls, ((480 - Ls.width) // 2, (272 - Ls.height) // 2))
    if k == 'hakone':
        im.alpha_composite(hakone_card(u))
    if k == 'wend' and st.get('dz') is not None:          # far-away Devil Z: keep a soft rainbow glow readable
        pd = WR.path(st['dz'][0], st['dz'][1], 0.7); eye = np.asarray(st['eye'], float); Rw = cam_R(eye, np.asarray(st['target'], float), 0.0)
        q = Rw @ (pd - eye); dist = float(np.linalg.norm(pd - eye))
        if q[2] > 1.0 and dist > 45.0:
            f_ = 380.0 * 480 / 640; px_, py_ = 240 + f_ * q[0] / q[2], 136 - f_ * q[1] / q[2]
            amt = smooth((dist - 45.0) / 60.0); r_ = max(4.0, 520.0 / dist) * (1.0 + 0.12 * math.sin(t * 7.0))
            hue = (t * 0.35) % 1.0; import colorsys
            col = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(hue, 0.75, 1.0))
            gl = Image.new('RGBA', (480, 272), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
            for kk in range(6, 0, -1):
                rr = r_ * kk / 3.0; al = int(70 * amt * (7 - kk) / 6.0)
                gd.ellipse([px_ - rr, py_ - rr * 0.6, px_ + rr, py_ + rr * 0.6], fill=col + (al,))
            gl = gl.filter(ImageFilter.GaussianBlur(2.0)); im.alpha_composite(gl)
    if k == 'wend' and u >= WE_TITLE:
        L = logo('stack'); w_ = u - WE_TITLE; e = smooth(w_ / 1.2); s_ = 0.66 - 0.04 * e + 0.002 * w_
        bb = L.getchannel('A').getbbox(); Lc = L.crop(bb)
        Ls = Lc.resize((int(Lc.width * s_), int(Lc.height * s_)), Image.LANCZOS)
        a = Ls.getchannel('A').point(lambda x: int(x * smooth(w_ / 0.9))); Ls.putalpha(a)
        im.alpha_composite(Ls, ((480 - Ls.width) // 2, 8))
    if k == 'htitle':
        L = logo('stack'); e = ease(u / 0.35); s_ = 1.18 - 0.26 * e + 0.004 * u
        Ls = L.resize((int(480 * s_), int(272 * s_)), Image.LANCZOS)
        a = Ls.getchannel('A').point(lambda x: int(x * min(1, u / 0.15))); Ls.putalpha(a)
        im.alpha_composite(Ls, ((480 - Ls.width) // 2, (272 - Ls.height) // 2 - 4))
    if k == 'title':
        D = sh['t1'] - sh['t0']; L = logo('stack')
        if u > 0.0:
            e = ease(u / 0.8); s = 0.86 + 0.06 * e + 0.004 * u
            Ls = L.resize((int(480 * s), int(272 * s)), Image.LANCZOS)
            a = Ls.getchannel('A').point(lambda x: int(x * min(1, u / 0.3))); Ls.putalpha(a)
            im.alpha_composite(Ls, ((480 - Ls.width) // 2, (272 - Ls.height) // 2 - 4))
    out = np.asarray(im.convert('RGB')).astype(np.float32)
    fa = flash_amount(t, sh, st, u); out = out * (1 - fa) + 255 * fa
    if t > T_END - 1.0: out *= max(0.0, (T_END - t) / 1.0)
    if t < 0.4: out *= t / 0.4
    return np.clip(out, 0, 255).astype(np.uint8)

BLUR = (( -1 / 3, 0.25, 1), (0.0, 0.5, 2), (1 / 3, 0.25, 1))   # M50 motion blur: (frame offset, weight, ss), 0.67-frame shutter
def make_frame(n, ss=2):
    t = n / FPS; sh = [s for s in SHOTS if s['t0'] <= t < s['t1']] or [SHOTS[-1]]; sh = sh[0]
    if sh['kind'] in ('logo',):
        img, st, sh, u = frame3d(n, ss, t, sh); return finish(img, st, sh, u, t)
    acc = None
    for dt, w, sss in BLUR:
        tt = min(max(t + dt / FPS, sh['t0']), sh['t1'] - 1e-4)
        if sh['kind'] == 'akio' and (t - sh['t0'] - AK_SPLIT) * (tt - sh['t0'] - AK_SPLIT) < 0: tt = t      # in-shot cut
        im, st_, sh_, u_ = frame3d(n, sss, tt, sh)
        if dt == 0.0: st, u = st_, u_
        acc = im * w if acc is None else acc + im * w
    return finish(acc, st, sh, u, t)

def _job(a):
    n, ss, out = a
    p = '%s/%05d.png' % (out, n)
    if os.path.exists(p): return n
    im = make_frame(n, ss); Image.fromarray(im).save(p + '.tmp.png'); os.replace(p + '.tmp.png', p); return n

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'frames':
        step = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 1
        ss = int(sys.argv[sys.argv.index('--ss') + 1]) if '--ss' in sys.argv else 2
        jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 2
        out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else HERE + '/frames'
        only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
        os.makedirs(out, exist_ok=True)
        ns = list(range(0, NF, step))
        if '--new' in sys.argv:                 # frames before bar 58 are M44's, byte-identical: copy them
            import shutil
            n0 = int(math.ceil(FIRST_NEW * FPS))
            for n in range(n0):
                p = '%s/%05d.png' % (out, n)
                if not os.path.exists(p): shutil.copyfile('work/m44/video/frames/%05d.png' % n, p)
            ns = [n for n in ns if n >= n0]
        if only: ns = [int(x) for x in only.split(',')]
        import multiprocessing as mp
        with mp.Pool(jobs) as pool:
            for k, n in enumerate(pool.imap_unordered(_job, [(n, ss, out) for n in ns], chunksize=2)):
                if k % 50 == 0: print(k, len(ns), flush=True)
    elif cmd == 'shots':
        for s in SHOTS: print(s['kind'], s.get('i', ''), round(s['t0'], 2), round(s['t1'], 2))
