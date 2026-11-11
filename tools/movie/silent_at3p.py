"""Silent ATRAC3plus track for PSMF without an encoder: the stock opening.pmf track ends with 39 identical
frames that decode (ffmpeg atrac3p) to digital zero. Replace every 744-byte frame body in the stock audio
PES with that frame, keeping the 8-byte frame headers (0f d0 28 5c 00 00 00 00), the 4-byte PES substream
headers (first-frame offsets) and all PES sizes/PTS — so the packet layout is byte-for-byte stock timing."""
import struct, mux_psmf as M
if not hasattr(M, "_orig_stock_audio"): M._orig_stock_audio = M.stock_audio
FR = 752; BODY = 744
def silent_audio(max_pts):
    aud, hdr, tail, sysh = M._orig_stock_audio(10**12)
    pays = [p[9 + p[8] + 4:] for pts, p in aud]
    stream = bytearray(b''.join(pays))
    sil = bytes(stream[len(stream) - BODY:])      # last frame body (verified silent)
    assert stream[len(stream) - FR:len(stream) - BODY] == b'\x0f\xd0\x28\x5c\x00\x00\x00\x00'
    for i in range(0, len(stream), FR):
        assert stream[i:i + 4] == b'\x0f\xd0\x28\x5c'
        stream[i + 8:i + FR] = sil
    out = []; o = 0
    for (pts, p), pay in zip(aud, pays):
        h = p[:9 + p[8] + 4]
        out.append((pts, h + bytes(stream[o:o + len(pay)]))); o += len(pay)
        if pts is not None and pts > max_pts: break
    return out, hdr, tail, sysh

def use_silent():
    """switch mux_psmf.build() to the silent track"""
    def sa(max_pts):
        out, h, t, s = silent_audio(max_pts)
        return [x for x in out if x[0] is None or x[0] <= max_pts], h, t, s
    M.stock_audio = sa
