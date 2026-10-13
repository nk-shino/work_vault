# -*- coding: utf-8 -*-
"""Read-only xlsx inspector. Does NOT modify the source file.
No formula recalculation, no external links refreshed - cached values only."""
import re, sys, zipfile

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def shared_strings(z):
    try:
        x = z.read('xl/sharedStrings.xml').decode('utf-8', 'replace')
    except KeyError:
        return []
    out = []
    for si in re.findall(r'<si>(.*?)</si>', x, re.S):
        parts = re.findall(r'<t(?:\s[^>]*)?>(.*?)</t>', si, re.S)
        s = ''.join(parts)
        s = (s.replace('&lt;', '<').replace('&gt;', '>')
              .replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&'))
        s = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), s)
        s = re.sub(r'&#x([0-9A-Fa-f]+);', lambda m: chr(int(m.group(1), 16)), s)
        out.append(s)
    return out

def sheets(z):
    wb = z.read('xl/workbook.xml').decode('utf-8', 'replace')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8', 'replace')
    rmap = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    rmap2 = dict(re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', rels))
    for k, v in rmap2.items():
        rmap.setdefault(v, k)
    out = []
    for m in re.finditer(r'<sheet\b([^>]*)/?>', wb):
        a = m.group(1)
        name = re.search(r'name="([^"]*)"', a)
        sid = re.search(r'sheetId="([^"]*)"', a)
        state = re.search(r'state="([^"]*)"', a)
        rid = re.search(r'r:id="([^"]*)"', a)
        tgt = rmap.get(rid.group(1), '') if rid else ''
        if tgt and not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt.lstrip('/')
        nm = name.group(1) if name else '?'
        nm = re.sub(r'&#x([0-9A-Fa-f]+);', lambda mm: chr(int(mm.group(1), 16)), nm)
        nm = nm.replace('&amp;', '&')
        out.append((nm, sid.group(1) if sid else '', state.group(1) if state else 'visible', tgt))
    return out

def cells(z, target, ss, maxrows=100000):
    try:
        x = z.read(target).decode('utf-8', 'replace')
    except KeyError:
        return []
    rows = []
    for rm in re.finditer(r'<row\b([^>]*)>(.*?)</row>', x, re.S):
        attrs = rm.group(1)
        rnum = re.search(r'r="(\d+)"', attrs)
        rnum = int(rnum.group(1)) if rnum else 0
        cs = []
        for cm in re.finditer(r'<c\b([^>]*?)(?:/>|>(.*?)</c>)', rm.group(2), re.S):
            a = cm.group(1); body = cm.group(2) or ''
            ref = re.search(r'r="([A-Z]+\d+)"', a)
            t = re.search(r't="([^"]+)"', a)
            f = re.search(r'<f(?:\s[^>]*)?>(.*?)</f>', body, re.S)
            v = re.search(r'<v>(.*?)</v>', body, re.S)
            isr = re.findall(r'<t(?:\s[^>]*)?>(.*?)</t>', body, re.S)
            val = ''
            if t and t.group(1) == 's' and v:
                i = int(v.group(1))
                val = ss[i] if i < len(ss) else ''
            elif t and t.group(1) == 'inlineStr':
                val = ''.join(isr)
            elif v:
                val = v.group(1)
            val = (val.replace('&lt;', '<').replace('&gt;', '>')
                      .replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&'))
            if val or f:
                cs.append((ref.group(1) if ref else '', val, f.group(1) if f else None))
        if cs:
            rows.append((rnum, cs))
        if len(rows) >= maxrows:
            break
    return rows

def main(path, mode='sheets', sheetname=None, grep=None):
    z = zipfile.ZipFile(path)
    ss = shared_strings(z)
    sh = sheets(z)
    if mode == 'sheets':
        print('NAMES_IN_ZIP:')
        for n in z.namelist():
            if n.startswith('xl/') and (n.endswith('.xml') or n.endswith('.bin')):
                print('  ', n, z.getinfo(n).file_size)
        print('SHARED_STRINGS=%d' % len(ss))
        print('SHEETS:')
        for n, sid, st, tgt in sh:
            print('  name=%r sheetId=%s state=%s target=%s' % (n, sid, st, tgt))
        wb = z.read('xl/workbook.xml').decode('utf-8', 'replace')
        dn = re.findall(r'<definedName\b([^>]*)>(.*?)</definedName>', wb, re.S)
        print('DEFINED_NAMES=%d' % len(dn))
        for a, b in dn[:60]:
            print('   ', a.strip(), '->', b.strip()[:120])
        ext = [n for n in z.namelist() if 'externalLink' in n]
        print('EXTERNAL_LINKS:', ext)
        print('VBA:', [n for n in z.namelist() if 'vbaProject' in n])
    elif mode == 'dump':
        for n, sid, st, tgt in sh:
            if sheetname and n != sheetname:
                continue
            print('===== SHEET %r (state=%s) %s =====' % (n, st, tgt))
            for rnum, cs in cells(z, tgt, ss):
                line = ' | '.join('%s=%s' % (r, v if v else ('={%s}' % f if f else ''))
                                  for r, v, f in cs)
                print('R%d: %s' % (rnum, line))
    elif mode == 'grep':
        pat = re.compile(grep)
        for n, sid, st, tgt in sh:
            for rnum, cs in cells(z, tgt, ss):
                for r, v, f in cs:
                    if pat.search(v or '') or (f and pat.search(f)):
                        print('%s!%s (row %d): %s%s' % (n, r, rnum, v[:300], ('  FORMULA=' + f[:200]) if f else ''))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'sheets',
         sys.argv[3] if len(sys.argv) > 3 else None,
         sys.argv[4] if len(sys.argv) > 4 else None)
