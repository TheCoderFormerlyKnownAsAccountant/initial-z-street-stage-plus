#!/usr/bin/env python3
"""Minimal ATRAC3 (fmt 0x270, LP2 132 kbps, STEREO mode) encoder, written for M16.

Decoder model = FFmpeg atrac3.c: per channel 192-byte sound unit:
  6 bits 0x28 | 2 bits bands_coded | per band 3 bits gain points (0) | 5 bits tonal (0) |
  spectrum: 5 bits num_subbands-1, 1 bit coding mode (1 = CLC), 3 bits selector per subband,
  6 bits scale factor per coded subband, CLC mantissas.
Signal path: 4-band QMF tree (analysis = adjoint of FFmpeg's iqmf, normalised) -> per band
MDCT 512/256 with the ATRAC3 analysis window (odd bands reversed) -> quantise with a
per-frame bit-allocation search.

  at3enc.py in.wav out.at3 [--loop]      (in.wav: 44100 Hz, 16-bit, stereo)
"""
import struct, sys
import numpy as np

QMF_HALF = [-0.00001461907, -0.00009205479, -0.000056157569, 0.00030117269, 0.0002422519, -0.00085293897,
            -0.0005205574, 0.0020340169, 0.00078333891, -0.0042153862, -0.00075614988, 0.0078402944,
            -0.000061169922, -0.01344162, 0.0024626821, 0.021736089, -0.007801671, -0.034090221,
            0.01880949, 0.054326009, -0.043596379, -0.099384367, 0.13207909, 0.46424159]
QW = np.zeros(48)
for i in range(24):
    QW[i] = QW[47 - i] = QMF_HALF[i] * 2.0

SUBBAND = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, 288, 320, 352, 384,
           416, 448, 480, 512, 576, 640, 704, 768, 896, 1024]
SF = 2.0 ** ((np.arange(64) - 15) / 3.0)
MAXQ = [0, 1.5, 2.5, 3.5, 4.5, 7.5, 15.5, 31.5]
CLC_BITS = [0, 4, 3, 3, 4, 4, 5, 6]          # sel 1: 4 bits per PAIR
LEVELS = [0, 1, 2, 3, 4, 7, 15, 31]           # max |mantissa| used
UNIT_BYTES = 384
N = 256


# ---------------------------------------------------------------- QMF
def iqmf(lo, hi):
    """FFmpeg ff_atrac_iqmf on whole signals (zero initial delay)."""
    M = len(lo)
    u = np.empty(2 * M); u[0::2] = lo + hi; u[1::2] = lo - hi
    t = np.concatenate([np.zeros(46), u])
    y = np.empty(2 * M)
    qe, qo = QW[0::2], QW[1::2]
    te, to = t[0::2], t[1::2]                 # te[m] = t[2m], to[m] = t[2m+1]
    # y[2j] = sum_i t[2j+1+2i] qo[i]; y[2j+1] = sum_i t[2j+2i] qe[i]
    y[0::2] = np.correlate(to, qo, 'valid')[:M]
    y[1::2] = np.correlate(te, qe, 'valid')[:M]
    return y


def qmf_adj(y):
    """Adjoint of iqmf: y (2M) -> lo, hi (M each)."""
    M = len(y) // 2
    qe, qo = QW[0::2], QW[1::2]
    to = np.convolve(y[0::2], qo)[:M + 23]
    te = np.convolve(y[1::2], qe)[:M + 23]
    t = np.empty(2 * (M + 23)); t[0::2] = te; t[1::2] = to
    u = t[46:46 + 2 * M]
    return u[0::2] + u[1::2], u[0::2] - u[1::2]


def _calib():
    rng = np.random.default_rng(1)
    x = rng.standard_normal(1 << 14)
    lo, hi = qmf_adj(x)
    y = iqmf(lo, hi)
    c = np.correlate(y, x, 'full'); k = int(np.argmax(np.abs(c))); D = k - (len(x) - 1)
    g = np.dot(y[D:], x[:len(x) - D]) / np.dot(x[:len(x) - D], x[:len(x) - D])
    return g, D


QG, QD = _calib()


def analysis(x):
    """x (len multiple of 1024) -> 4 band signals (len/4 each), FFmpeg band order 0..3."""
    lo, hi = qmf_adj(x / QG)               # synth(lo,hi) ~ x delayed QD
    b0, b1 = qmf_adj(lo / QG)
    b3, b2 = qmf_adj(hi / QG)              # decoder: iqmf(p4, p3) -> band 3 is the low input
    return [b0, b1, b2, b3]


# ---------------------------------------------------------------- MDCT
def _win():
    w = np.zeros(512)
    for i in range(256):
        w[i] = 0.5 * (np.sin(((i + 0.5) / 256.0 - 0.5) * np.pi) + 1.0)
    w[256:] = w[:256][::-1]
    return w


AWIN = _win()
_n = np.arange(512)[:, None]; _k = np.arange(256)[None, :]
COS = np.cos(np.pi / N * (_n + 0.5 + N / 2) * (_k + 0.5))      # 512 x 256


def mdct_frames(b, scale):
    """b: band signal, len = 256*F. Frame t uses samples [256(t-1), 256(t+1)) -> F frames."""
    F = len(b) // 256
    p = np.concatenate([np.zeros(256), b])
    idx = np.arange(F)[:, None] * 256 + np.arange(512)[None, :]
    blk = p[idx] * AWIN
    return scale * (blk @ COS)


# ---------------------------------------------------------------- bitstream
class BW:
    def __init__(self): self.v = 0; self.n = 0
    def put(self, val, bits):
        if bits: self.v = (self.v << bits) | (val & ((1 << bits) - 1)); self.n += bits
    def bytes(self, size):
        assert self.n <= size * 8, self.n
        return (self.v << (size * 8 - self.n)).to_bytes(size, 'big')


SB_SIZE = np.diff(SUBBAND)
WEIGHT = np.ones(32)


import json as _json, os as _os
_T = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'vlc_tabs.json')))
MVT = [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]   # mantissa_vlc_tab
VLC = []                                   # per selector: {symbol: (code, len)}
for t in _T:
    code, m = 0, {}
    for sym, ln in t:
        m[sym] = (code >> (32 - ln), ln); code += 1 << (32 - ln)
    VLC.append(m)
# length lookup arrays: selector s>=2 -> LEN[s][v+31]; selector 1 -> pair index 3*(a+1)+(b+1)
LEN = [None] * 8
for s in range(2, 8):
    a = np.full(63, 99); [a.__setitem__(v + 31, ln) for v, (c, ln) in VLC[s - 1].items()]; LEN[s] = a
PAIR_SYM = {p: i for i, p in enumerate(MVT)}
PAIR_LEN = np.full(9, 99)
for (a, b), i in PAIR_SYM.items(): PAIR_LEN[3 * (a + 1) + (b + 1)] = VLC[0][i][1]
SBI = np.repeat(np.arange(32), SB_SIZE)    # coefficient -> subband
NOISE_ALPHA = 0.3
HF_W = np.ones(32); HF_W[29:] = 0.5; HF_W[31] = 0.2   # relax >~16 kHz


def _sbsum(a):                              # (F,1024) -> (F,32)
    return np.add.reduceat(a, SUBBAND[:-1], axis=1)


SF_OFFS = (0, 1, 2)


def rd_tables(S):
    """D, R: (K, F, 32) over K = 1 + 7*len(SF_OFFS) choices (sel, sf offset); sf/sel per choice."""
    F = S.shape[0]
    mx = np.maximum.reduceat(np.abs(S), SUBBAND[:-1], axis=1)
    sf0 = np.searchsorted(SF, mx * 0.999999).clip(0, 63)
    D = [_sbsum(S * S)]; R = [np.zeros((F, 32))]; CH = [(0, 0)]; Q = {}
    for o in SF_OFFS:
        sf = (sf0 - o).clip(0, 63)
        scale = SF[sf][:, SBI]
        for s in range(1, 8):
            q = np.clip(np.rint(S / scale * MAXQ[s]), -LEVELS[s], LEVELS[s])
            rec = q / MAXQ[s] * scale
            D.append(_sbsum((S - rec) ** 2))
            if s == 1:
                qi = q.astype(int)
                pl = PAIR_LEN[3 * (qi[:, 0::2] + 1) + (qi[:, 1::2] + 1)]
                r = np.add.reduceat(pl, np.array(SUBBAND[:-1]) // 2, axis=1).astype(float)
            else:
                r = _sbsum(LEN[s][q.astype(int) + 31].astype(float))
            R.append(r + 6)
            CH.append((s, o)); Q[(s, o)] = q.astype(np.int8)
    return np.stack(D), np.stack(R), sf0, Q, CH


def plan(S, budget):
    F = S.shape[0]
    D, R, sf0, Q, CH = rd_tables(S)
    selmap = np.array([c[0] for c in CH]); offmap = np.array([c[1] for c in CH])
    en = D[0] / SB_SIZE + 1e-3
    w = (en ** -NOISE_ALPHA) * HF_W
    def choose(lam):
        return np.argmin(w[None] * D + lam[None, :, None] * R, 0)
    def cost(k):
        r = np.take_along_axis(R.transpose(1, 2, 0), k[..., None], 2)[..., 0]
        return side_cost(selmap[k]) + r.sum(1)
    lo, hi = np.full(F, -30.0), np.full(F, 30.0)
    for _ in range(30):
        mid = (lo + hi) / 2
        ok = cost(choose(2.0 ** mid)) <= budget
        hi = np.where(ok, mid, hi); lo = np.where(ok, lo, mid)
    k = choose(2.0 ** hi)
    assert (cost(k) <= budget).all()
    sel = selmap[k]; sf = (sf0 - offmap[k]).clip(0, 63)
    qsel = np.zeros(S.shape, np.int8)
    for kk, (s_, o) in enumerate(CH):
        if s_ == 0: continue
        m = (k == kk)[:, SBI]
        qsel[m] = Q[(s_, o)][m]
    return sel, sf, qsel


def side_cost(sel):
    nz = sel != 0
    last = np.where(nz.any(1), 31 - np.argmax(nz[:, ::-1], 1), 0)
    bands = np.minimum(3, (np.array(SUBBAND)[last + 1] - 1) >> 8)
    head = 6 + 2 + 3 * (bands + 1) + 5 + 5 + 1
    return head + 3 * (last + 1)


def encode_unit(sel, sf, q):
    nz = np.nonzero(sel)[0]
    last = int(nz[-1]) if len(nz) else 0
    bands = min(3, (SUBBAND[last + 1] - 1) >> 8)
    w = BW()
    w.put(0x28, 6); w.put(bands, 2)
    for _ in range(bands + 1): w.put(0, 3)
    w.put(0, 5)
    w.put(last, 5); w.put(0, 1)                             # 0 = VLC
    for i in range(last + 1): w.put(int(sel[i]), 3)
    for i in range(last + 1):
        if sel[i]: w.put(int(sf[i]), 6)
    for i in range(last + 1):
        s = int(sel[i])
        if not s: continue
        m = q[SUBBAND[i]:SUBBAND[i + 1]]
        if s == 1:
            for a, b in zip(m[0::2], m[1::2]):
                c, ln = VLC[0][PAIR_SYM[(int(a), int(b))]]; w.put(c, ln)
        else:
            tab = VLC[s - 1]
            for v in m:
                c, ln = tab[int(v)]; w.put(c, ln)
    return w.bytes(UNIT_BYTES)


def encode_channel(x, scale):
    bands = analysis(x)
    S = np.concatenate([mdct_frames(b, scale) for b in bands], 1)   # F x 1024 (band blocks)
    F = S.shape[0]
    for k in (1, 3):                                                  # odd bands reversed
        S[:, k * 256:(k + 1) * 256] = S[:, k * 256:(k + 1) * 256][:, ::-1]
    out = []
    for a in range(0, F, 1500):
        sel, sf, Q = plan(S[a:a + 1500], UNIT_BYTES * 8)
        for t in range(sel.shape[0]):
            out.append(encode_unit(sel[t], sf[t], Q[t]))
    return out


LOOP_START = 2048   # the game/sceAtrac ignores a loop that starts at sample 0 (plays once); 2048 loops


def riff(frames_l, frames_r, nsamples, loop=True, fact_off=0, loop_start=LOOP_START):
    data = b''.join(a + b for a, b in zip(frames_l, frames_r))
    ext = struct.pack('<HIHHHH', 1, 0x1000, 0, 0, 2, 0)
    fmt = struct.pack('<HHIIHHH', 0x270, 2, 44100, 33074, 768, 0, len(ext)) + ext
    fact = struct.pack('<II', nsamples, fact_off)
    chunks = [(b'fmt ', fmt), (b'fact', fact)]
    if loop:
        smpl = struct.pack('<9I', 0, 0, 22676, 60, 0, 0, 0, 1, 0x18) + struct.pack('<6I', 0, 0, loop_start, nsamples - 1, 0, 0)
        chunks.append((b'smpl', smpl))
    chunks.append((b'data', data))
    body = b'WAVE' + b''.join(c + struct.pack('<I', len(p)) + p for c, p in chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


SCALE = -1.0 / 128    # MDCT gain/polarity, calibrated against ffmpeg (test_at3.py)
FACT_OFF = 1024        # decoder delay; PSP sceAtrac skips it, loop points are relative to it
SHIFT = 0             # codec delay 1024 is signalled in fact.firstSampleOffset instead (FACT_OFF)


def encode(pcm, loop=True):
    """pcm: (n, 2) int16/float -> RIFF bytes."""
    n = len(pcm)
    x = pcm.astype(np.float64)
    x = np.concatenate([x[SHIFT:], np.zeros((SHIFT, 2))]) if SHIFT else x
    F = (n + 1023) // 1024 + 1
    x = np.concatenate([x, np.zeros((F * 1024 - n, 2))])
    L = encode_channel(x[:, 0], SCALE); R = encode_channel(x[:, 1], SCALE)
    return riff(L, R, n, loop, FACT_OFF)


if __name__ == '__main__':
    import wave
    w = wave.open(sys.argv[1]); assert w.getframerate() == 44100 and w.getsampwidth() == 2 and w.getnchannels() == 2
    pcm = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2)
    open(sys.argv[2], 'wb').write(encode(pcm, '--noloop' not in sys.argv))
