#!/usr/bin/env python3
"""M48 opening: song INSIDE the PMF (ATRAC3plus track, stock layout) + low-bitrate video (v_low.h264, 2200 kbps).
Steps (run in order; step 1 needs the atracdenc binary):
  1. python3 build48.py encode   -> aud/song_pmf.at3 (RIFF ATRAC3plus) from aud/song_pmf.wav
  2. python3 build48.py mux      -> opening48.pmf (+ aud/check.wav, delay/level report)
aud/song_pmf.wav: m22/mu/at3/ss_16.at3 (the disc's own song) decoded, 2416 samples of lead-in so song t=0 = video frame 0
(audio PTS 85069 vs video 90000), faded out over the last 1.2 s of the 108.308 s video, padded to 2343 frames (108.81 s)."""
import os, sys, struct, subprocess, array, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); sys.path.insert(0, HERE)
import make47 as K
ENC = HERE + '/atracdenc/src/build/src/atracdenc'
FR, BODY = 752, 744
NFR = 2343

def encode():
    subprocess.check_call([ENC, '-e', 'atrac3plus', '-i', 'aud/song_pmf.wav', '-o', 'aud/song_pmf.at3', '--container', 'riff'])

def riff_frames(p):
    d = open(p, 'rb').read(); i = 12; fmt = data = None
    while i < len(d):
        cid = d[i:i + 4]; sz = struct.unpack_from('<I', d, i + 4)[0]
        if cid == b'fmt ': fmt = d[i + 8:i + 8 + sz]
        if cid == b'data': data = d[i + 8:i + 8 + sz]
        i += 8 + sz + (sz & 1)
    tag, ch, sr, abps, align, bits = struct.unpack_from('<HHIIHH', fmt)
    return [data[k:k + align] for k in range(0, len(data) - align + 1, align)], (ch, sr, align, abps * 8)

def decode_frames(frames, out_wav):
    import at3p_wav
    at3p_wav.wrap(b''.join(frames), len(frames), out_wav, fsize=len(frames[0]))
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', out_wav, '-f', 's16le', '-'], capture_output=True).stdout
    return array.array('h', raw)

def pcm(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 's16le', '-'], capture_output=True).stdout
    return array.array('h', raw)

def delay(ref, got, maxlag=8192):
    """encoder+decoder delay in samples: best lag of got vs ref on a loud 2 s window (mono)"""
    import numpy as np
    r = np.frombuffer(ref.tobytes(), np.int16).reshape(-1, 2).mean(1)
    g = np.frombuffer(got.tobytes(), np.int16).reshape(-1, 2).mean(1)
    s = 44100 * 20; w = r[s:s + 88200]
    best = max(range(0, maxlag), key=lambda L: float(np.dot(w, g[s + L:s + L + 88200])))
    return best

def pes_layout(stream, frb):
    """stock PES grammar for any frame size: payload 2013 (with the stock P-STD ext, every 10th PES) / 2016 bytes,
    PTS = first frame starting in the payload, 4-byte sub header = offset of that frame"""
    import pmf as P
    stock, hdr, tail, sysh = K.M._orig_stock_audio(10 ** 12)
    ext_hdr = stock[0][1][6:9 + stock[0][1][8]]
    out = []; pos = 0; i = 0
    while pos < len(stream):
        ext = (i % 10 == 0); size = 2013 if ext else 2016
        pay = stream[pos:pos + size]
        fi = -(-pos // frb); off = fi * frb - pos
        if off < len(pay):
            pts = int(round(K.A0 + fi * K.FDUR))
            h = (bytes(ext_hdr[:3]) + P.enc_ts(2, pts) + bytes(ext_hdr[8:])) if ext else (b'\x81\x80\x05' + P.enc_ts(2, pts))
            sub = struct.pack('>HH', 0, off)
        else:
            # same header size as the PTS forms (stuffing 0xff), so packs stay exactly 2048 bytes like stock
            pts = None; h = (bytes([0x81, 0x01, 0x08]) + bytes(ext_hdr[8:]) + b'\xff' * 5) if ext else b'\x81\x00\x05' + b'\xff' * 5
            sub = struct.pack('>HH', 0, 0xffff)
        body = h + sub + pay
        out.append((pts, b'\x00\x00\x01\xbd' + struct.pack('>H', len(body)) + body))
        pos += size; i += 1
    return out, hdr, tail, sysh

def mux():
    frames, (ch, sr, align, bps) = riff_frames('aud/song_pmf.at3')
    assert (ch, sr) == (2, 44100) and align % 8 == 0 and align // 8 - 1 <= 0xff, (ch, sr, align, bps)
    hdr8 = bytes([0x0f, 0xd0, 0x28, align // 8 - 1, 0, 0, 0, 0])   # stock 744 -> 0f d0 28 5c; PPSSPP size = code2*8+0x10
    FRB = align + 8
    print('frames', len(frames), 'bytes', align, 'kbps', bps / 1000, 'header', hdr8.hex())
    ref = pcm('aud/song_pmf.wav')
    got = decode_frames(frames, 'aud/rt.wav')
    lag = delay(ref, got); skip = round(lag / 2048)
    print('codec delay', lag, 'samples -> drop', skip, 'leading frames (residual', lag - skip * 2048, 'samples)')
    frames = frames[skip:]
    while len(frames) < NFR: frames.append(frames[-1])     # encoder tail is already silent (faded + padded wav)
    frames = frames[:NFR]
    stream = b''.join(hdr8 + f for f in frames)
    def song_audio(max_pts):
        return pes_layout(stream, FRB)
    if FRB == FR:     # stock frame size: stock PES verbatim layout (M47) with our payload
        def song_audio(max_pts):
            out, hdr, tail, sysh = K.synth_audio(max_pts)
            res = []; pos = 0
            for pts, p in out:
                hl = 9 + p[8] + 4; n = len(p) - hl
                res.append((pts, p[:hl] + stream[pos:pos + n])); pos += n
            assert pos == len(stream), (pos, len(stream))
            return res, hdr, tail, sysh
    K.M.stock_audio = song_audio
    info = K.M.build('v_low.h264', 'opening48.pmf')
    print('pmf', info, os.path.getsize('opening48.pmf'), hashlib.md5(open('opening48.pmf', 'rb').read()).hexdigest())
    # verify: pull the audio back out of the PMF and decode it
    d = open('opening48.pmf', 'rb').read(); s = bytearray()
    for off in range(0x800, len(d), 2048):
        pk = d[off:off + 2048]; q = 14 + (pk[13] & 7)
        while q + 6 <= 2048 and pk[q:q + 3] == b'\0\0\1':
            L = struct.unpack_from('>H', pk, q + 4)[0]
            if pk[q + 3] == 0xbd: s += pk[q + 9 + pk[q + 8] + 4:q + 6 + L]
            q += 6 + L
    assert bytes(s) == stream
    back = decode_frames([bytes(s[i + 8:i + FRB]) for i in range(0, len(s), FRB)], 'aud/check.wav')
    import numpy as np
    b = np.frombuffer(back.tobytes(), np.int16).astype(float); r = np.frombuffer(ref.tobytes(), np.int16).astype(float)
    n = min(len(b), len(r)) - 20000
    res = lag - skip * 2048
    bb = b[2 * res:2 * res + n] if res >= 0 else b[:n]
    rr = r[:len(bb)]
    print('decoded secs %.2f' % (len(back) / 2 / 44100), 'rms dBFS %.1f' % (20 * np.log10(np.sqrt((bb ** 2).mean()) / 32768)),
          'peak', int(abs(bb).max()), 'SNR vs source %.1f dB' % (10 * np.log10((rr ** 2).sum() / ((rr - bb) ** 2).sum())))

if __name__ == '__main__':
    {'encode': encode, 'mux': mux}[sys.argv[1]]()
