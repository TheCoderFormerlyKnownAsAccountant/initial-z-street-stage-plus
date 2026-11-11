#!/usr/bin/env python3
"""Put your own song into the Initial Z opening movie (Linux/macOS; Windows uses intro_song.ps1).
usage: python3 intro_song.py ISO SONG [ATRACDENC]
Needs atracdenc (https://github.com/dcherednik/atracdenc) to encode the song to ATRAC3plus."""
import os, sys, struct, subprocess, base64, tempfile
H = os.path.dirname(os.path.abspath(__file__))
iso, song = sys.argv[1], sys.argv[2]
enc = sys.argv[3] if len(sys.argv) > 3 else 'atracdenc'
PMF_LBA, NFR, SKIP = int(open(os.path.join(H, 'data', 'intro_lba.txt')).read()), 2343, 2
HDR = bytes.fromhex('0fd028ff00000000')
SEG = [tuple(map(int, l.split())) for l in open(os.path.join(H, 'data', 'intro_segments.txt')) if l.strip()]
SIL = base64.b64decode(open(os.path.join(H, 'data', 'silent_frame.b64')).read())
tmp = tempfile.mkdtemp(); at3 = os.path.join(tmp, 'intro.oma'); src = song
if not song.lower().endswith('.wav'):
    src = os.path.join(tmp, 'intro.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', song, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', src])
subprocess.check_call([enc, '-e', 'atrac3plus', '-i', src, '-o', at3], stdout=subprocess.DEVNULL)
d = open(at3, 'rb').read()
assert d[:3] == b'EA3', 'unexpected atracdenc output'
data = d[(d[4] << 8) | d[5]:]
assert len(data) % 2048 == 0, 'unexpected ATRAC3plus frame size'
fr = [data[k:k + 2048] for k in range(0, len(data) - 2047, 2048)][SKIP:SKIP + NFR]
fr += [SIL] * (NFR - len(fr))
stream = b''.join(HDR + f for f in fr)
assert len(stream) == sum(n for _, n in SEG)
with open(iso, 'r+b') as f:
    p = 0
    for a, n in SEG:
        f.seek(PMF_LBA * 2048 + a); f.write(stream[p:p + n]); p += n
print('intro song written:', os.path.basename(song), '(%.1f s used)' % (min(len(fr), NFR) * 2048 / 44100))
