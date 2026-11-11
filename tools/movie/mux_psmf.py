#!/usr/bin/env python3
"""PSMF muxer for the Initial Z opening: H.264 Annex-B video (480x272 Main) + stock ATRAC3plus audio PES
copied verbatim from data/movie/opening.pmf. Layout mirrors the stock file: PSMF0014 0x800 header,
2048-byte MPEG-2 PS packs, per-GOP system header (0xBB) + private-stream-2 (0xBF) AU-size table,
video PES with PTS/DTS on AU starts, audio = private stream 1 (0xBD) PES. Packs ordered by
deadline (PTS - stock lead: video 92900, audio 16650 ticks), SCR monotonic >= 147/pack."""
import re, struct, subprocess, sys, os
sys.path.insert(0, 'work/m22/t')
import pmf as P
STOCK = 'game/initial_d/PSP_GAME/USRDIR/data/movie/opening.pmf'
PACK = 2048; FT = 3003; FIRST = 90000
VLEAD, ALEAD = 92900, 16650

def ts(b): return ((b[0] >> 1) & 7) << 30 | b[1] << 22 | (b[2] >> 1) << 15 | b[3] << 7 | b[4] >> 1

def stock_audio(max_pts):
    d = open(STOCK, 'rb').read(); out = []
    for off in range(0x800, len(d), PACK):
        pk = d[off:off + PACK]; p = 14 + (pk[13] & 7)
        while p + 6 <= PACK and pk[p:p + 3] == b'\x00\x00\x01':
            sid = pk[p + 3]; L = struct.unpack_from('>H', pk, p + 4)[0]
            if sid == 0xbd:
                pts = ts(pk[p + 9:p + 14]) if pk[p + 7] & 0x80 else None
                if pts is not None and pts > max_pts: return out, d[:0x800], pk[10:14], d[0x800 + 14:0x800 + 32]
                out.append((pts, pk[p:p + 6 + L]))
            p += 6 + L
    return out, d[:0x800], d[0x800 + 10:0x800 + 14], d[0x800 + 14:0x800 + 32]

def video_packs(aus, sysh, tail):
    gops = []; cur = []
    for i, au in enumerate(aus):
        if P.is_idr(au) and cur: gops.append(cur); cur = []
        cur.append((i, au))
    gops.append(cur)
    packs = []   # (deadline, bytes-without-pack-header)
    for g in gops:
        data = b''.join(a for _, a in g); starts = []; o = 0
        for idx, a in g: starts.append((o, idx)); o += len(a)
        pos = 0; first = True
        while pos < len(data):
            body = bytearray()
            if first:
                body += sysh
                tbl = struct.pack('>H', len(g))
                for k, (idx, a) in enumerate(g): tbl += struct.pack('>HH', 0x80 if k < len(g) - 1 else 0, len(a))
                b2 = b'\x01\xe0' + b'\x00' * 12 + struct.pack('>H', len(tbl)) + tbl
                body += b'\x00\x00\x01\xbf' + struct.pack('>H', len(b2)) + b2
            room = PACK - 14 - len(body) - 6
            here = [(o2, idx) for o2, idx in starts if pos <= o2 < pos + room]
            idx_dead = here[0][1] if here else max(i for o2, i in starts if o2 <= pos)
            if here:
                pts = FIRST + here[0][1] * FT
                opts = (b'\x81\xc1\x0d' + P.enc_ts(3, pts) + P.enc_ts(1, pts - FT) + b'\x1e\x60\x37') if (first and here[0][1] == 0) \
                    else (b'\x81\xc0\x0a' + P.enc_ts(3, pts) + P.enc_ts(1, pts - FT))
            else:
                opts = b'\x81\x00\x00'
            room = PACK - 14 - len(body) - 6 - len(opts)
            if here and here[0][0] >= pos + room:      # AU start no longer fits after the PTS bytes: no PTS here
                here = []; opts = b'\x81\x00\x00'; room = PACK - 14 - len(body) - 6 - len(opts)
                if any(pos <= o2 < pos + room for o2, _ in starts):   # tiny gain: AU start now fits again -> keep it simple
                    room = min(o2 for o2, _ in starts if pos <= o2 < pos + room) - pos
            rest = len(data) - pos
            if 0 < room - rest < 6: room -= 6
            # one AU start per PES: stop before the next AU start after the first one in this chunk
            nxt = [o2 for o2, idx in starts if pos < o2 < pos + room and (not here or o2 > here[0][0])]
            if nxt: room = nxt[0] - pos
            # never split an AU's start code across PES: if an AU starts in the last 5 bytes, end the PES before it
            tail5 = [o2 for o2, idx in starts if pos + room - 5 < o2 < pos + room and o2 > pos]
            if tail5:
                room = tail5[0] - pos
                if here and here[0][0] >= pos + room:
                    here = []; opts = b'\x81\x00\x00'
            chunk = data[pos:pos + room]; pos += len(chunk)
            slack = PACK - 14 - len(body) - 6 - len(opts) - len(chunk)
            if 0 < slack < 6:                      # too small for a padding packet: PES header stuffing bytes
                opts = opts[:2] + bytes([opts[2] + slack]) + opts[3:] + b'\xff' * slack
            body += b'\x00\x00\x01\xe0' + struct.pack('>H', len(opts) + len(chunk)) + opts + chunk
            packs.append((FIRST + idx_dead * FT - FT - VLEAD, bytes(body)))
            first = False
    return packs, len(gops)

def build(h264, out_pmf):
    es = P.clean_es(open(h264, 'rb').read()); aus = P.access_units(es); n = len(aus)
    last = FIRST + n * FT
    audio, hdr0, tail, sysh = stock_audio(last)
    vp, ngop = video_packs(aus, sysh, tail)
    ap = [(pts - ALEAD if pts is not None else None, pes) for pts, pes in audio]
    # audio PES without PTS inherit previous deadline
    prev = 0; ap2 = []
    for dl, pes in ap:
        prev = dl if dl is not None else prev; ap2.append((prev, pes))
    allp = sorted([(dl, 0, i, b) for i, (dl, b) in enumerate(vp)] + [(dl, 1, i, b) for i, (dl, b) in enumerate(ap2)])
    out = bytearray(); scr = 10147
    for dl, kind, _, body in allp:
        scr = max(scr + 147, min(dl, scr + 147 * 64)) if out else scr
        pk = bytearray(b'\x00\x00\x01\xba' + P.enc_scr(scr) + tail) + body
        left = PACK - len(pk)
        if left:
            if left < 6: raise RuntimeError('slack')
            pk += b'\x00\x00\x01\xbe' + struct.pack('>H', left - 6) + b'\xff' * (left - 6)
        assert len(pk) == PACK; out += pk
    hdr = bytearray(hdr0)
    struct.pack_into('>I', hdr, 0x0C, len(out))
    struct.pack_into('>I', hdr, 0x5C, last); struct.pack_into('>I', hdr, 0x76, last)
    open(out_pmf, 'wb').write(bytes(hdr) + bytes(out))
    return n, ngop, len(audio), len(out) // PACK

def encode(src_args, out_h264, kbps=3800, keyint=48):
    x = ('ref=1:bframes=0:keyint=%d:min-keyint=%d:scenecut=0:aud=1:nal-hrd=vbr:vbv-maxrate=%d:vbv-bufsize=%d:'
         'weightp=0:8x8dct=0:cabac=1' % (keyint, keyint, kbps + 1000, kbps + 1000))
    cmd = ['ffmpeg', '-y', '-loglevel', 'error'] + src_args + ['-vf', 'scale=480:272:out_range=full,fps=30000/1001,format=yuvj420p',
           '-c:v', 'libx264', '-profile:v', 'main', '-level', '2.1', '-b:v', '%dk' % kbps, '-maxrate', '%dk' % (kbps + 1000),
           '-bufsize', '%dk' % (kbps + 1000), '-x264-params', x, '-an', '-bsf:v', 'h264_mp4toannexb', '-f', 'h264', out_h264]
    subprocess.check_call(cmd)

if __name__ == '__main__':
    # test: 5 s synthetic
    src = ['-f', 'lavfi', '-i', 'testsrc2=size=480x272:rate=30000/1001:duration=5,drawtext=text=INITIAL Z TEST:fontsize=36:fontcolor=white:x=(w-tw)/2:y=h-60']
    encode(src, 'test5.h264')
    print(build('test5.h264', 'test5s.pmf'))
