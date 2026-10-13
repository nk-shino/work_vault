# -*- coding: utf-8 -*-
"""Read-only: count col A / col B values in each sheet of an xlsm. Never writes to source."""
import sys, zipfile, re
from collections import Counter
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

def shared(z):
    try:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
    except KeyError:
        return []
    out = []
    for si in root.findall(NS + 'si'):
        out.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    return out

def sheets(z):
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels}
    out = []
    for sh in wb.find(NS + 'sheets'):
        tgt = rmap.get(sh.get(RNS + 'id'), '')
        if tgt.startswith('/xl/'):
            tgt = tgt[1:]
        elif not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt
        out.append((sh.get('name'), sh.get('state', 'visible'), tgt))
    return out

def cellval(c, sst):
    t = c.get('t')
    if t == 'inlineStr':
        return ''.join(x.text or '' for x in c.iter(NS + 't'))
    v = c.find(NS + 'v')
    if v is None or v.text is None:
        return ''
    if t == 's':
        i = int(v.text)
        return sst[i] if 0 <= i < len(sst) else ''
    return v.text

def main(path):
    print('=' * 72)
    print('FILE:', path)
    z = zipfile.ZipFile(path)
    sst = shared(z)
    for name, state, tgt in sheets(z):
        try:
            root = ET.fromstring(z.read(tgt))
        except KeyError:
            print('  [%s] (%s) -- missing %s' % (name, state, tgt))
            continue
        colA, colB = [], Counter()
        maxrow = 0
        for row in root.iter(NS + 'row'):
            for c in row.findall(NS + 'c'):
                ref = c.get('r') or ''
                m = re.match(r'([A-Z]+)(\d+)', ref)
                if not m:
                    continue
                col, rn = m.group(1), int(m.group(2))
                maxrow = max(maxrow, rn)
                if col == 'A':
                    v = cellval(c, sst)
                    if v != '':
                        colA.append(v)
                elif col == 'B':
                    v = cellval(c, sst)
                    colB[v if v != '' else '(空)'] += 1
        print('  [%s] state=%s  maxrow=%d  A非空=%d  B記入=%d'
              % (name, state, maxrow, len(colA), sum(colB.values())))
        if colA:
            lead = sum(1 for v in colA if v[:1] == ' ')
            print('      A列 先頭空白あり=%d / なし=%d   例: %r'
                  % (lead, len(colA) - lead, colA[0][:40]))
        if colB:
            for k, v in colB.most_common(12):
                print('      B列 %-12s %d' % (k, v))

for p in sys.argv[1:]:
    try:
        main(p)
    except Exception as e:
        print('ERROR on %s: %r' % (p, e))
