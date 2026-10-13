# -*- coding: utf-8 -*-
"""Read-only CSV structure + full-count verification. Does not modify sources."""
import sys, io, os

def sniff(path):
    raw = open(path, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    crlf = raw.count(b'\r\n')
    lf = raw.count(b'\n')
    cr = raw.count(b'\r')
    lone_lf = lf - crlf
    enc = None
    body = raw[3:] if bom else raw
    for e in ('utf-8', 'cp932'):
        try:
            txt = body.decode(e)
            enc = e
            break
        except UnicodeDecodeError:
            continue
    if enc is None:
        txt = body.decode('cp932', 'replace')
        enc = 'cp932(replace)'
    return raw, bom, crlf, lone_lf, cr - crlf, enc, txt

def main(path):
    raw, bom, crlf, lonelf, lonecr, enc, txt = sniff(path)
    print('FILE:', os.path.basename(path))
    print('  bytes=%d  encoding=%s  BOM=%s' % (len(raw), enc, bom))
    print('  CRLF=%d  lone-LF=%d  lone-CR=%d' % (crlf, lonelf, lonecr))
    lines = txt.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and lines[-1] == '':
        lines.pop()
    print('  total lines (non-empty tail trimmed) = %d' % len(lines))
    if not lines:
        return
    hdr = lines[0].split(',')
    print('  header fields = %d' % len(hdr))
    print('  header = %s' % ' | '.join(h.strip('"') for h in hdr))
    # column count distribution
    from collections import Counter
    cc = Counter(len(l.split(',')) for l in lines[1:])
    print('  data rows = %d ; column-count distribution = %s' % (len(lines) - 1, dict(cc)))
    print('  sample row 2 = %s' % lines[1][:300])
    # find loc column and qty column
    names = [h.strip('"').strip() for h in hdr]
    loc_i = qty_i = None
    for i, n in enumerate(names):
        if 'ロケーション' in n:
            loc_i = i
        if n in ('在庫数',) or ('在庫数' in n and qty_i is None):
            qty_i = i
    print('  loc col idx=%s (%s) ; qty col idx=%s (%s)' %
          (loc_i, names[loc_i] if loc_i is not None else '-',
           qty_i, names[qty_i] if qty_i is not None else '-'))
    if loc_i is None:
        return
    zero_rows = 0
    zero_and_le9 = 0
    locvals = Counter()
    bad = 0
    first_serial = last_serial = None
    for l in lines[1:]:
        f = l.split(',')
        if len(f) <= max(loc_i, qty_i or 0):
            bad += 1
            continue
        loc = f[loc_i].strip().strip('"')
        locvals[loc] += 1
        if '0確認' in loc or '０確認' in loc:
            zero_rows += 1
            if qty_i is not None:
                try:
                    q = int(float(f[qty_i].strip().strip('"')))
                    if q <= 9:
                        zero_and_le9 += 1
                        s = f[0].strip().strip('"')
                        if first_serial is None:
                            first_serial = s
                        last_serial = s
                except ValueError:
                    pass
    print('  >> rows containing "0確認" in location = %d' % zero_rows)
    print('  >> rows "0確認" AND qty<=9          = %d' % zero_and_le9)
    print('  >> first serial of that set = %r ; last = %r' % (first_serial, last_serial))
    print('  >> short rows skipped = %d' % bad)
    print('  >> top location values:')
    for k, v in locvals.most_common(15):
        print('       %-20s %d' % (k, v))

for p in sys.argv[1:]:
    main(p)
    print('-' * 70)
