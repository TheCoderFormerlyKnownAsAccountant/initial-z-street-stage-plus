"""Build the public Initial Z ISO (build 60 minus Daniel's music) and the xdelta patch players apply to their own discs."""
import os, sys, shutil, hashlib, subprocess, time
H = os.path.dirname(os.path.abspath(__file__)); os.chdir(H)
PROJ = os.path.abspath(os.path.join(H, '..', '..'))
IDSS = os.path.join(PROJ, 'Initital_D_Street_Stage_JAP_PSP-DMU.iso')
WMP = os.path.join(PROJ, 'Wangan_Midnight_Portable_JPN_PSP-Caravan.iso')
B59 = os.path.join(H, '..', 'build59', 'Initial_Z_StreetStagePlus_build59.iso')
B60 = os.path.join(H, '..', 'build60', 'Initial_Z_StreetStagePlus_build60.iso')
ISO = os.path.join(H, 'InitialZ_StreetStagePlus_v1.0.1.iso')
SRC = os.path.join(H, 'src_tmp.bin')
PATCH = os.path.join(H, 'InitialZ_v1.0.1.xdelta')
XD = os.path.join(H, 'xdelta3.exe')
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()
free = lambda: shutil.disk_usage(H).free / 1e9
log('free GB %.2f' % free())
if not os.path.exists(ISO):
    if free() > 2.1 + 1.6 + 0.6:
        shutil.copyfile(B60, ISO); log('copied build60 ISO')
    else:
        os.replace(B59, ISO); log('moved build59 ISO (low disk; build 60 kept; build 59 = build 60 with the old BOOT)')
r = subprocess.run([sys.executable, 'iso_tool.py', 'patch', ISO, ISO, '@rlpub.txt'])
log('iso_tool exit', r.returncode)
if r.returncode: sys.exit(1)
# zero what is left of each replaced file's old extent (old music / old name data must not stay in the image)
sys.path.insert(0, H); import iso_tool as T
def layout(p):
    iso = T._open(p); L = {r['path'].upper(): (r['lba'], r['size']) for r in T.walk(iso)}; iso.close(); return L
old = layout(B60); new = layout(ISO); zeroed = 0
with open(ISO, 'r+b') as fp:
    for line in open('rlpub.txt'):
        line = line.strip()
        if not line.startswith('--replace='): continue
        p = line[len('--replace='):].split('=', 1)[0].upper()
        (ol, os_), (nl, ns) = old[p], new[p]
        if ol != nl: log('moved, nothing to zero', p); continue
        a = nl * 2048 + (ns + 2047) // 2048 * 2048; b = ol * 2048 + (os_ + 2047) // 2048 * 2048
        if b > a: fp.seek(a); fp.write(b'\0' * (b - a)); zeroed += b - a
log('zeroed old extents bytes', zeroed)
r = subprocess.run([sys.executable, 'cleanslack.py', ISO, IDSS]); log('cleanslack exit', r.returncode)
if r.returncode: sys.exit(1)
r = subprocess.run([sys.executable, 'verifypub.py', ISO]); log('verify exit', r.returncode)
if r.returncode: sys.exit(1)
iso_md5 = md5(ISO); log('public ISO md5', iso_md5, os.path.getsize(ISO))
for p, want in ((IDSS, '225f1f56c37097c7a11ecaddd52abbf1'), (WMP, '85c3abab28df6509911461de9d58b9e9')):
    m = md5(p); log('source', os.path.basename(p), m, 'OK' if m == want else 'MISMATCH')
    if m != want: sys.exit(1)
if os.path.exists(SRC) and os.path.getsize(SRC) == os.path.getsize(IDSS) + os.path.getsize(WMP): log('source concat already present')
else:
  with open(SRC, 'wb') as o:
    for p in (IDSS, WMP):
        with open(p, 'rb') as f: shutil.copyfileobj(f, o, 1 << 24)
log('source concat', os.path.getsize(SRC), 'free GB %.2f' % free())
if os.path.exists(PATCH): os.remove(PATCH)
t = time.time()
r = subprocess.run([XD, '-e', '-6', '-S', 'djw', '-B', '1073741824', '-f', '-s', SRC, ISO, PATCH]); log('xdelta encode exit', r.returncode, '%.0f s' % (time.time() - t), os.path.getsize(PATCH) if os.path.exists(PATCH) else 0)
if r.returncode: sys.exit(1)
t = time.time(); h = hashlib.md5()
p = subprocess.Popen([XD, '-d', '-c', '-B', '1073741824', '-s', SRC, PATCH], stdout=subprocess.PIPE)
for b in iter(lambda: p.stdout.read(1 << 22), b''): h.update(b)
p.wait(); log('decode test exit', p.returncode, h.hexdigest(), 'MATCH' if h.hexdigest() == iso_md5 else 'DIFFERENT', '%.0f s' % (time.time() - t))
os.remove(SRC); log('removed temp source; patch md5', md5(PATCH))
open('public_md5.txt', 'w').write('%s  InitialZ_StreetStagePlus_v1.0.1.iso\n%s  InitialZ_v1.0.1.xdelta\n' % (iso_md5, md5(PATCH)))
log('DONE')
