#!/usr/bin/env python3
"""Walk every generated talk table (8 M45 + 7 M40 WMP sets + Akio) the way the rivaldemo interpreter consumes it and
compare with the grammar of ALL stock talk tables in the same rivaldemo.bin (talkTbl_<stock name>NN.txt).

Interpreter model (from the stock files): a table is a list of "quoted" tokens, CRLF separated.
  P_n pose | D_n delay | C_n window/char slot | *_n speaker (charNameTbl line) | text (ends with \\n or not)
  W_n wait | N next page | K_n close window n | E end | plus the stock flow tokens (B/b/X/M/V/v/Y/y ...).
Checks per generated table: token kinds and kind bigrams all occur in stock; first token is a pose (or E); a text
token only after a speaker on an open window; every page ends 'W_n','N' and holds <= the stock max lines; each line
<= the stock max length; every opened window is closed (K_n) before E; nothing after E; speaker < charNameTbl lines;
pose < 10 (the WMP portraits carry 10 poses). Prints a stock comparison for several post-race tables.
"""
import gzip, re, sys
sys.path[:0] = ['plugin/scripts', 'work/m45/rivals/tools']
import xbb, ident45 as I
R = gzip.decompress(open('work/m45/rivals/files/rivaldemo/rivaldemo.bin.gz', 'rb').read())
X = {e['name']: R[e['offset']:e['offset'] + e['size']] for e in xbb.parse(R)}
spk_n = len([l for l in X['charNameTbl.txt'].split(b'\r\n') if l])
GEN = [x['key'] for x in I.IDS] + ['AKIO']
gen_files = {n for n in X if n.startswith('talkTbl_') and re.match(r'talkTbl_(%s)\d\d\.txt$' % '|'.join(GEN), n)}
stock_files = {n for n in X if re.match(r'talkTbl_[A-Z0-9]+\d\d\.txt$', n)} - gen_files


def toks(b):
    t = b.decode('cp932').split('\r\n')
    assert t[-1] == '', 'no CRLF at end'
    out = []
    for x in t[:-1]:
        x = x.strip(' \t\u3000')
        if not x: continue
        out.append(x.strip('"'))          # stock has a few sloppy tokens (BUNTA00, EVO514); generated ones are checked strictly below
    return out


CTRL = re.compile(r'^([A-Za-z*])(?:_(\d+))?$')
def kind(t):
    m = CTRL.match(t)
    if m and not t.endswith('\\n'): return m.group(1) + ('_' if m.group(2) is not None else '')
    return 'T'


def walk(name, tk, limits=None):
    """interpreter walk; returns (errors, pages, max_lines, max_len)"""
    err, pages, lines, maxl, maxlen, open_w, spk, cur = [], 0, 0, 0, 0, set(), None, None
    if tk == ['E']: return err, 0, 0, 0
    if kind(tk[0]) != 'P_': err.append('first token not a pose')
    for i, t in enumerate(tk):
        k = kind(t)
        if k == 'C_': cur = int(t[2:]); open_w.add(cur)
        elif k == '*_': spk = int(t[2:]); err += [] if spk < spk_n else [f'speaker {spk} >= {spk_n}']
        elif k == 'T':
            if cur is None or spk is None: err.append(f'text before window/speaker: {t}')
            lines += t.endswith('\\n'); maxlen = max(maxlen, len(t.replace('\\n', '')))
        elif k == 'N':
            if kind(tk[i - 1]) != 'W_': err.append('N not after W_n')
            maxl = max(maxl, lines); lines = 0; pages += 1
        elif k == 'K_': open_w.discard(int(t[2:]))
        elif k == 'E':
            if i != len(tk) - 1: err.append('tokens after E')
            if lines: err.append('unterminated page before E')
        elif k == 'P_' and limits and int(t[2:]) >= 10: err.append(f'pose {t}')
    if kind(tk[-1]) != 'E': err.append('no E')
    if open_w: err.append(f'windows left open {sorted(open_w)}')
    return err, pages, maxl, maxlen


S_kinds, S_bi, S_maxl, S_maxlen, s_err = set(), set(), 0, 0, 0
for n in sorted(stock_files):
    tk = toks(X[n]); ks = [kind(t) for t in tk]
    S_kinds |= set(ks); S_bi |= set(zip(ks, ks[1:]))
    e, p, ml, mlen = walk(n, tk); s_err += bool(e)
    S_maxl = max(S_maxl, ml); S_maxlen = max(S_maxlen, mlen)
print(f'stock: {len(stock_files)} tables, kinds {sorted(S_kinds)}, max lines/page {S_maxl}, max line {S_maxlen} chars, '
      f'{s_err} with walker remarks')
bad = 0
for n in sorted(gen_files):
    raw = X[n].decode('cp932').split('\r\n')
    strict = raw[-1] == '' and all(x.startswith('"') and x.endswith('"') and x.count('"') == 2 for x in raw[:-1])
    tk = toks(X[n]); ks = [kind(t) for t in tk]
    e, p, ml, mlen = walk(n, tk, limits=True)
    if not strict: e.append('token quoting/CRLF')
    if not set(ks) <= S_kinds: e.append(f'kinds not in stock {set(ks) - S_kinds}')
    nb = set(zip(ks, ks[1:])) - S_bi
    if nb: e.append(f'bigrams not in stock {nb}')
    if ml > S_maxl: e.append(f'{ml} lines on a page (stock max {S_maxl})')
    if mlen > S_maxlen: e.append(f'line {mlen} chars (stock max {S_maxlen})')
    if e: bad += 1; print('FAIL', n, e)
print(f'generated: {len(gen_files)} tables walked, {bad} failing')
for n in ('talkTbl_KENJI03.txt', 'talkTbl_KEISUKE21.txt', 'talkTbl_NAKAZATO04.txt', 'talkTbl_GOTO11.txt', 'talkTbl_HIRAMOTO11.txt', 'talkTbl_AKIO11.txt'):
    if n in X: print(f'{n:24s}', ' '.join(kind(t) for t in toks(X[n])))
sys.exit(1 if bad else 0)
